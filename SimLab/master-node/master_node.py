import threading
import queue
from pathlib import Path
from scp import SCPClient

import os, sys

# Para utilizar a biblioteca interna
project_path = os.path.abspath(os.path.join(os.getcwd(), "..")) 
if project_path not in sys.path:
    sys.path.insert(0, project_path)
    
from pylib import sshscp, mongo_db
    
# Configs de acesso ao MongoDB
MONGO_URI = "mongodb://localhost:27017/?replicaSet=rs0"
DB_NAME = "simlab"    
    
# Diretórios e credenciais SSH
LOCAL_DIRECTORY = '.'
REMOTE_DIRECTORY = '/opt/contiki-ng/tools/cooja'
LOCAL_LOG_DIR = "logs"
Path(LOCAL_LOG_DIR).mkdir(exist_ok=True)

CONTAINER_USERNAME = 'root'
CONTAINER_PASSWORD = 'root'
CONTAINER_HOSTNAME = 'localhost'
CONTAINER_PORTS = [2231, 2232, 2233, 2234, 2235]


# Prepara arquivos para simulação, transferindo do MongoDB para sistema local
def prepare_simulation_files(sim: dict)-> tuple[list[str],list[str]]:
    local_files = []
    remote_files = []

    sim_id = str(sim["_id"])

    # Verifica se existe diretório temporário para manipulação de arquivos
    if os.path.exists("tmp") == False:
        os.mkdir("tmp")
        
    # Arquivos temporários da simulação
    local_xml = f"tmp/simulation_{sim_id}.xml"
    local_dat = f"tmp/positions_{sim_id}.dat"
        
    # Obtém um instância para uso do MongoDB
    mongo = mongo_db.factory(MONGO_URI, DB_NAME)

    # Baixar arquivos do GridFS
    mongo.save_file_from_mongo(sim["simulationFile"], local_xml)
    mongo.save_file_from_mongo(sim["positionsFile"], local_dat)
    
    local_files.extend([local_xml, local_dat])
    remote_files.extend(["simulation.csc", "positions.dat"])

    # Carrega arquivos extras do experimento
    exp = mongo.get_document_by_id("experiments", sim["experiment_id"])
    if exp and "linkedFiles" in exp:
        for f in exp["linkedFiles"]:
            fid = f["fileId"]
            local_path = f"tmp/{f['name']}" 
            mongo.save_file_from_mongo(fid, local_path)
            local_files.append(local_path)
            remote_name = f['name']
            if remote_name == 'simulation.xml':
                remote_name = 'simulation.csc'
            remote_files.append(remote_name)
    else:
        print(f"[WARN] Nenhum arquivo extra vinculado encontrado para o experimento {sim['experiment_id']}")

    return local_files, remote_files

def run_cooja_simulation(sim: dict, port, mongo: mongo_db.MongoExperimentManager):
    ssh = sshscp.create_ssh_client(CONTAINER_HOSTNAME, port, CONTAINER_USERNAME, CONTAINER_PASSWORD)
    try:        
        sim_id = str(sim["_id"])
        
        print(f"[{port}] Iniciando simulação {sim_id}...")
        mongo.update_simulation_status(sim_id, "running")

        command = f"""
        cd ../{REMOTE_DIRECTORY} && \
        /opt/java/openjdk/bin/java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc
        """
        stdin, stdout, stderr = ssh.exec_command(command)

        for line in iter(stdout.readline, ""):
            print(f"[{port}][stdout] {line}", end="")
        for line in iter(stderr.readline, ""):
            print(f"[{port}][stderr] {line}", end="")

        # Copia o log da simulação para o sistema de arquivos local
        log_path = f"{LOCAL_LOG_DIR}/sim_{sim_id}.log"
        with SCPClient(ssh.get_transport()) as scp_client:
            print(f"[{port}] Copiando log da simulação para {log_path}")
            scp_client.get(f"{REMOTE_DIRECTORY}/COOJA.testlog", log_path)

        # Insere o log no GridFS e obtém o seu ID
        log_result_id = mongo.insert_file(log_path, "sim_result.log")
        print(f"[{port}] Simulação {sim_id} finalizada com sucesso. Log inserido com ID: {log_result_id}")

        mongo.simulation_done(sim, log_result_id)
        
    except Exception as e:
        print(f"[{port}] ERRO durante a simulação {sim_id}: {e}")
        mongo.update_simulation_status(sim_id, "error")
    finally:
        ssh.close()

def simulation_worker(sim_queue, port):
    mongo = mongo_db.factory(MONGO_URI, DB_NAME)
    while True:
        sim = sim_queue.get()
        if sim is None:
            break
        sim_id = str(sim["_id"])

        local_files, remote_files = prepare_simulation_files(sim)
        try:
            print(f"[{port}] Preparando simulação {sim_id}")
            ssh = sshscp.create_ssh_client(CONTAINER_HOSTNAME, port, CONTAINER_USERNAME, CONTAINER_PASSWORD)
            sshscp.send_files_scp(ssh, LOCAL_DIRECTORY, REMOTE_DIRECTORY, local_files, remote_files)
            ssh.close()

            run_cooja_simulation(sim, port, mongo)
            
        except Exception as e:
            print(f"[{port}] ERRO geral na simulação {sim_id}: {e}")
            mongo.update_simulation_status(sim_id, "error")
        finally:
            sim_queue.task_done()

def start_workers(num_workers=5):
    q = queue.Queue()
    for i in range(num_workers):
        t = threading.Thread(target=simulation_worker, args=(q, CONTAINER_PORTS[i]), daemon=True)
        t.start()
    print("[Sistema] Workers iniciados.")
    return q

def load_initial_waiting_jobs(sim_queue):
    print("[load] Buscando simulações pendentes no início...")
    mongo = mongo_db.factory(MONGO_URI, DB_NAME)
    pending_jobs = mongo.find_pending_simulations()
    count = 0
    for doc in pending_jobs:
        print(f"[load] Simulação pendente encontrada: {doc['_id']}")
        sim_queue.put(doc)
        count += 1
    print(f"[load] Total de simulações adicionadas à fila: {count}")


sim_queue = start_workers()
load_initial_waiting_jobs(sim_queue)
