import threading
import queue
from pathlib import Path
from scp import SCPClient
import os
import sys

# Configura caminho do projeto para acessar pylib
project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from pylib import sshscp, mongo_db

# Configurações MongoDB 
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")

# Configurações de caminhos
LOCAL_DIRECTORY = '.'
REMOTE_DIRECTORY = '/opt/contiki-ng/tools/cooja'
LOCAL_LOG_DIR = "logs"
Path(LOCAL_LOG_DIR).mkdir(exist_ok=True)

# Credenciais
SSH_CONFIG = {
    "username": "root",
    "password": "root",
    "hostname": "localhost",
    "ports": [2231, 2232, 2233, 2234, 2235]
}

def prepare_simulation_files(sim, mongo):
    sim_id = str(sim["_id"])
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)

    local_xml = tmp_dir / f"simulation_{sim_id}.xml"
    local_dat = tmp_dir / f"positions_{sim_id}.dat"

    mongo.fs_handler.download_file(sim["simulationFile"], str(local_xml))
    mongo.fs_handler.download_file(sim["positionsFile"], str(local_dat))

    local_files = [str(local_xml), str(local_dat)]
    remote_files = ["simulation.csc", "positions.dat"]

    exp = mongo.experiment_repo.find_first_by_status("Waiting")
    if exp and "linkedFiles" in exp:
        for f in exp["linkedFiles"]:
            file_path = tmp_dir / f["name"]
            mongo.fs_handler.download_file(f["fileId"], str(file_path))
            local_files.append(str(file_path))
            remote_name = "simulation.csc" if f["name"] == "simulation.xml" else f["name"]
            remote_files.append(remote_name)
    else:
        print(f"[WARN] Nenhum arquivo extra vinculado para experimento {sim['experiment_id']}")

    return local_files, remote_files

def run_cooja_simulation(sim, port, mongo):
    ssh = sshscp.create_ssh_client(SSH_CONFIG["hostname"], port, SSH_CONFIG["username"], SSH_CONFIG["password"])
    sim_id = str(sim["_id"])
    try:
        print(f"[{port}] Iniciando simulação {sim_id}...")
        mongo.simulation_repo.update_status(sim_id, "running")

        command = f"cd ../{REMOTE_DIRECTORY} && /opt/java/openjdk/bin/java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc"
        stdin, stdout, stderr = ssh.exec_command(command)

        for line in iter(stdout.readline, ""):
            print(f"[{port}][stdout] {line}", end="")
        for line in iter(stderr.readline, ""):
            print(f"[{port}][stderr] {line}", end="")

        log_path = f"{LOCAL_LOG_DIR}/sim_{sim_id}.log"
        with SCPClient(ssh.get_transport()) as scp:
            print(f"[{port}] Copiando log para {log_path}")
            scp.get(f"{REMOTE_DIRECTORY}/COOJA.testlog", log_path)

        log_id = mongo.fs_handler.upload_file(log_path, "sim_result.log")
        print(f"[{port}] Log salvo com ID: {log_id}")
        mongo.simulation_queue_repo.mark_done(sim["_id"])
    except Exception as e:
        print(f"[{port}] ERRO na simulação {sim_id}: {e}")
        mongo.simulation_repo.update_status(sim_id, "error")
    finally:
        ssh.close()

def simulation_worker(sim_queue, port):
    mongo = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)
    while True:
        sim = sim_queue.get()
        if sim is None:
            break

        sim_id = str(sim["_id"])
        local_files, remote_files = prepare_simulation_files(sim, mongo)
        try:
            print(f"[{port}] Enviando arquivos da simulação {sim_id}")
            ssh = sshscp.create_ssh_client(SSH_CONFIG["hostname"], port, SSH_CONFIG["username"], SSH_CONFIG["password"])
            sshscp.send_files_scp(ssh, LOCAL_DIRECTORY, REMOTE_DIRECTORY, local_files, remote_files)
            ssh.close()

            run_cooja_simulation(sim, port, mongo)
        except Exception as e:
            print(f"[{port}] ERRO geral na simulação {sim_id}: {e}")
            mongo.simulation_repo.update_status(sim_id, "error")
        finally:
            sim_queue.task_done()

def start_workers(num_workers=5):
    q = queue.Queue()
    for i in range(num_workers):
        t = threading.Thread(target=simulation_worker, args=(q, SSH_CONFIG["ports"][i]), daemon=True)
        t.start()
    print("[Sistema] Workers iniciados.")
    return q

def load_initial_waiting_jobs(sim_queue):
    print("[load] Buscando simulações pendentes...")
    mongo = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)
    pending = mongo.simulation_queue_repo.find_pending()
    for sim in pending:
        print(f"[load] Simulação pendente: {sim['_id']}")
        sim_queue.put(sim)

if __name__ == "__main__":
    sim_queue = start_workers()
    load_initial_waiting_jobs(sim_queue)
