import threading
import queue
import time
import paramiko
from pymongo import MongoClient
from bson import ObjectId
from scp import SCPClient
from pathlib import Path

# Configurações do MongoDB
MONGO_URI = "mongodb://localhost:27017/?replicaSet=rs0"
DB_NAME = "simlab"
COLLECTION = "simqueue"

# Diretórios e credenciais SSH
LOCAL_DIRECTORY = '.'
REMOTE_DIRECTORY = '/opt/contiki-ng/tools/cooja'
LOCAL_LOG_DIR = "logs"
Path(LOCAL_LOG_DIR).mkdir(exist_ok=True)

CONTAINER_USERNAME = 'root'
CONTAINER_PASSWORD = 'root'
CONTAINER_HOSTNAME = 'localhost'
CONTAINER_PORTS = [2231, 2232, 2233, 2234, 2235]

LOCAL_FILES = [
    "temp/simulation.xml", 
    "temp/positions.dat",
    "data/Makefile", 
    "data/project-conf.h",
    "data/udp-client.c", 
    "data/udp-server.c"
]
REMOTE_FILES = [
    "simulation.csc", 
    "positions.dat",
    "Makefile", 
    "project-conf.h",
    "udp-client.c", 
    "udp-server.c"
]

# MongoDB client global
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION]

# SSH utils
def create_ssh_client(hostname, port, username, password):
    print(f"[{port}] Estabelecendo conexão SSH...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)
    print(f"[{port}] Conexão SSH estabelecida.")
    return client

def send_files_scp(client, local_path, remote_path, source_files, target_files, port):
    print(f"[{port}] Enviando arquivos para o container via SCP...")
    with SCPClient(client.get_transport()) as scp:
        for src, dest in zip(source_files, target_files):
            print(f"[{port}] Enviando: {src} -> {remote_path}/{dest}")
            scp.put(local_path + "/" + src, remote_path + "/" + dest)
    print(f"[{port}] Arquivos enviados com sucesso.")

def update_status(sim_id, new_status):
    collection.update_one(
        {"_id": ObjectId(sim_id)},
        {"$set": {"status": new_status, "timestamp": time.time()}}
    )
    print(f"[MongoDB] Simulação {sim_id} atualizada para status: {new_status}")

def run_cooja_simulation(simulation_id, port):
    ssh = create_ssh_client(CONTAINER_HOSTNAME, port, CONTAINER_USERNAME, CONTAINER_PASSWORD)
    try:
        print(f"[{port}] Iniciando simulação {simulation_id}...")
        update_status(simulation_id, "running")

        command = f"""
        cd ../{REMOTE_DIRECTORY} && \
        /opt/java/openjdk/bin/java --enable-preview -Xms4g -Xmx4g -jar build/libs/cooja.jar --no-gui simulation.csc
        """
        stdin, stdout, stderr = ssh.exec_command(command)

        for line in iter(stdout.readline, ""):
            print(f"[{port}][stdout] {line}", end="")
        for line in iter(stderr.readline, ""):
            print(f"[{port}][stderr] {line}", end="")

        log_path = f"{LOCAL_LOG_DIR}/sim_{simulation_id}.log"
        with SCPClient(ssh.get_transport()) as scp_client:
            print(f"[{port}] Copiando log da simulação para {log_path}")
            scp_client.get(f"{REMOTE_DIRECTORY}/COOJA.testlog", log_path)

        print(f"[{port}] Simulação {simulation_id} finalizada com sucesso.")
        update_status(simulation_id, "done")
    except Exception as e:
        print(f"[{port}] ERRO durante a simulação {simulation_id}: {e}")
        update_status(simulation_id, "error")
    finally:
        ssh.close()

def simulation_worker(sim_queue, port):
    while True:
        sim = sim_queue.get()
        if sim is None:
            break
        sim_id = str(sim["_id"])

        try:
            print(f"[{port}] Preparando simulação {sim_id}")
            ssh = create_ssh_client(CONTAINER_HOSTNAME, port, CONTAINER_USERNAME, CONTAINER_PASSWORD)
            send_files_scp(ssh, LOCAL_DIRECTORY, REMOTE_DIRECTORY, LOCAL_FILES, REMOTE_FILES, port)
            ssh.close()

            run_cooja_simulation(sim_id, port)
        except Exception as e:
            print(f"[{port}] ERRO geral na simulação {sim_id}: {e}")
            update_status(sim_id, "error")
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
    print("[MongoDB] Buscando simulações pendentes no início...")
    pending_jobs = collection.find({"status": "waiting"})
    count = 0
    for doc in pending_jobs:
        print(f"[MongoDB] Simulação pendente encontrada: {doc['_id']}")
        sim_queue.put(doc)
        count += 1
    print(f"[MongoDB] Total de simulações adicionadas à fila: {count}")

def watch_simqueue(sim_queue):
    print("[MongoDB] Iniciando monitoramento da fila (watch)...")
    pipeline = [{"$match": {"fullDocument.status": "waiting"}}]
    with db[COLLECTION].watch(pipeline) as stream:
        for change in stream:
            doc = change["fullDocument"]
            print(f"[MongoDB] Novo item com status 'waiting': {doc['_id']}")
            sim_queue.put(doc)

if __name__ == "__main__":
    sim_queue = start_workers()
    load_initial_waiting_jobs(sim_queue)
    watch_simqueue(sim_queue)
