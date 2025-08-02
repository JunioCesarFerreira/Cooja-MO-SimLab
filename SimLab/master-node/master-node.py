import os
import sys
import time
import queue
import datetime
from scp import SCPClient
from paramiko import SSHClient
from threading import Thread
from pathlib import Path

# Adiciona o diretório do projeto ao sys.path para importar módulos locais
project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from pylib import sshscp, mongo_db
from dto import Simulation, Experiment, SourceRepository

# Configurações MongoDB 
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME: str = os.getenv("DB_NAME", "simlab")


# Diretórios utilizados
LOCAL_DIRECTORY: str = '.'
REMOTE_DIRECTORY: str = '/opt/contiki-ng/tools/cooja'
LOCAL_LOG_DIR: str = "logs"
Path(LOCAL_LOG_DIR).mkdir(exist_ok=True)

# Configurações SSH para acesso aos containers do Cooja
SSH_CONFIG: dict = {
    "username": "root",
    "password": "root",
    "hostnames": ["cooja1", "cooja2", "cooja3", "cooja4", "cooja5"],
    "ports": [2231, 2232, 2233, 2234, 2235]
}


# Recarrega lista de hosts e portas seguindo o padrão apresentado nos dados default
def reload_standard_hosts(number: int) -> None:
    SSH_CONFIG["hostnames"] = ["localhost" for i in range(number)]#[f"cooja{i}" for i in range(number)]
    SSH_CONFIG["ports"] = [2231 + i for i in range(number)]


# Pega arquivos do mongo e prepara para simulação no Cooja
def prepare_simulation_files(
    sim: Simulation,            # Objeto da simulação
    mongo: mongo_db.MongoRepository # Conexão com os repositórios MongoDB.
) -> tuple[bool, list[str], list[str]]:   # Lista de caminhos dos arquivos locais e nomes remotos.
    sim_id = str(sim["_id"])
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)

    local_xml = tmp_dir / f"simulation_{sim_id}.xml"
    local_dat = tmp_dir / f"positions_{sim_id}.dat"

    mongo.fs_handler.download_file(sim["csc_file_id"], str(local_xml))
    if sim["pos_file_id"] != "":
        mongo.fs_handler.download_file(sim["pos_file_id"], str(local_dat))

        local_files = [str(local_xml), str(local_dat)]
        remote_files = ["simulation.csc", "positions.dat"]
    else:
        local_files = [str(local_xml)]
        remote_files = ["simulation.csc"]

    exp: Experiment = mongo.experiment_repo.get_by_id(sim['experiment_id'])
    
    success = True
    if exp:
        src: SourceRepository = mongo.source_repo.get_by_id(exp["source_repository_id"])
        if src and "source_files" in src:
            for source_file in src["source_files"]:
                file_path = str(tmp_dir / source_file["file_name"])
                mongo.fs_handler.download_file(source_file["id"], file_path)
                local_files.append(file_path)
                remote_files.append(source_file["file_name"])
        else:
            success = False
            print(f"[WARN] Could not find repository {exp["source_repository_id"]} no experimento {sim['experiment_id']}")
    else:
        success = False
        print(f"[WARN] Failed to retrieve experiment data {sim['experiment_id']}")

    return success, local_files, remote_files


# Executa a simulação no container Cooja via SSH.
def run_cooja_simulation(
    sim: Simulation, # Objeto da simulação
    port: int,           # Porta SSH do container
    hostname: str,       # Hostname do container na rede docker
    mongo: mongo_db.MongoRepository # Conexão com os repositórios MongoDB
) -> None:
    ssh: SSHClient = sshscp.create_ssh_client(hostname, port, SSH_CONFIG["username"], SSH_CONFIG["password"])
    sim_id = str(sim["_id"])
    try:
        print(f"[{port}] Starting simulation {sim_id}...")
        mongo.simulation_repo.mark_running(sim_id)

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
        
        print(f"[{port}] Log saved with ID: {log_id}")
        
        mongo.simulation_repo.mark_done(sim["_id"], log_id)
        
    except Exception as e:
        print(f"[{port}] Simulation ERRROR {sim_id}: {e}")
        mongo.simulation_repo.mark_error(sim_id)
    finally:
        ssh.close()


# Consome fila de simulações.
def simulation_worker(
    sim_queue: queue.Queue, # Fila de simulações.
    port: int,              # Porta do container.
    hostname: str           # Nome do host na rede docker.
) -> None:
    mongo = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)
    while True:
        sim = sim_queue.get()
        if sim is None:
            break

        sim_id = str(sim["_id"])
        success, local_files, remote_files = prepare_simulation_files(sim, mongo)
        if success:
            try:
                print(f"[{port}] Sending simulation files {sim_id}")
                print(f"create ssh client: {hostname}, {port}, {SSH_CONFIG["username"]}, {SSH_CONFIG["password"]}")
                ssh = sshscp.create_ssh_client(hostname, port, SSH_CONFIG["username"], SSH_CONFIG["password"])
                print("sending scp files")
                sshscp.send_files_scp(ssh, LOCAL_DIRECTORY, REMOTE_DIRECTORY, local_files, remote_files)
                ssh.close()
                print("running cooja simulation")
                run_cooja_simulation(sim, port, hostname, mongo)
            except Exception as e:
                print(f"[{port}] General ERROR in simulation {sim_id}: {e}")
                mongo.simulation_repo.mark_error(sim_id)
            finally:
                sim_queue.task_done()


# Inicializa múltiplas threads (workers) para execução paralela de simulações.
def start_workers(
    num_workers: int = 5 # Quantidade de containers Cooja disponíveis
    ) -> queue.Queue:    # Fila de simulações.
    q: queue.Queue = queue.Queue()
    for i in range(num_workers):
        t = Thread(
            target=simulation_worker,
            args=(q, SSH_CONFIG["ports"][i], SSH_CONFIG["hostnames"][i]),
            daemon=True
        )
        t.start()
    print("[Sistema] Workers starded.")
    return q

def on_generation_event(change: dict):
    mongo = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)
    print("[Master-Node] on generation event...")
    print(f"[Master-Node] change: {change}")

    gen_doc = change.get("fullDocument")
    if not gen_doc:
        print("[Master-Node] Document missing from the event.")
        return
    gen_id = str(gen_doc["_id"])
    
    success = mongo.generation_repo.update(gen_id, {
        "status": mongo_db.SimulationStatus.RUNNING,
        "start_time": datetime.now()
    })
    if success:
        list_sim = mongo.simulation_repo.find_pending_by_generation(gen_id)
        for sim in list_sim:
            sim_queue.put(sim)

def make_generation_event_handler(sim_queue: queue.Queue) -> callable:
    def on_generation_event(change: dict):
        mongo = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)
        print("[Master-Node] on generation event...")
        print(f"[Master-Node] change: {change}")

        gen_doc = change.get("fullDocument")
        if not gen_doc:
            print("[Master-Node] Document missing from the event.")
            return
        gen_id = str(gen_doc["_id"])
        
        success = mongo.generation_repo.update(gen_id, {
            "status": mongo_db.SimulationStatus.RUNNING,
            "start_time": datetime.datetime.now()
        })
        if success:
            list_sim = mongo.simulation_repo.find_pending_by_generation(gen_id)
            for sim in list_sim:
                sim_queue.put(sim)
    return on_generation_event


def watch_generations(mongo: mongo_db.MongoRepository, sim_queue: queue.Queue):
    print("[Master-Node] Aguardando novas Gerações...")
    pipeline = [
        {
            "$match": {
                "operationType": {"$in": ["insert", "update", "replace"]},
                "fullDocument.status": "Waiting"
            }
        }
    ]
    event_handler = make_generation_event_handler(sim_queue)
    mongo.generation_repo.connection.watch_collection(
        "generations", 
        pipeline, 
        event_handler, 
        full_document="updateLookup"
    )

# Descarrega fila antes de iniciar threads
def load_initial_waiting_jobs(mongo: mongo_db.MongoRepository, sim_queue: queue.Queue) -> None:
    print("[load] Buscando simulações pendentes...")
    pending = mongo.simulation_repo.find_pending()
    for sim in pending:
        print(f"[load] Pending simulation: {sim['id']} | {sim['_id']}")
        sim_queue.put(sim)


# MAIN --------------------------------------------------------------------------------
if __name__ == "__main__":
    NUMBER_OF_CONTAINERS: int = 5

    print("start")
    print(f"number of containers: {NUMBER_OF_CONTAINERS}")
    reload_standard_hosts(NUMBER_OF_CONTAINERS)

    print(f"env:\n\tMONGO_URI: {MONGO_URI}\n\tDB_NAME: {DB_NAME}")
    mongo = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)
    
    sim_queue = start_workers(NUMBER_OF_CONTAINERS)
    load_initial_waiting_jobs(mongo, sim_queue)

    Thread(
        target=watch_generations, 
        args=(mongo, sim_queue),
        daemon=True
        ).start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")
# --------------------------------------------------------------------------------------
