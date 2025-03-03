import pymongo
import time
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/?replicaSet=rs0")
client = pymongo.MongoClient(MONGO_URI)

# Aguarda MongoDB estar pronto
while True:
    try:
        client.admin.command('ping')
        break
    except pymongo.errors.ConnectionFailure:
        print("[WorkGenerator] Aguardando conexão com MongoDB...")
        time.sleep(3)

db = client.simulation_db
tasks_collection = db.simulations_tasks
results_collection = db.simulations_results

NUM_TASKS = 15  # Número de tarefas por lote

def generate_tasks():
    """Gera 15 tarefas para a fila"""
    tasks = [{"config": {"param": i}, "status": "pending"} for i in range(NUM_TASKS)]
    print("Inserindo tarefa na fila...")
    tasks_collection.insert_many(tasks)
    print(f"[WorkGenerator] {NUM_TASKS} tarefas publicadas no MongoDB.")

def listen_results():
    """Escuta resultados e espera todas as tarefas serem concluídas"""
    completed_tasks = set()
    print("[WorkGenerator] Aguardando conclusão das tarefas...")

    with results_collection.watch() as stream:
        for change in stream:
            result = change["fullDocument"]
            task_id = result["task_id"]
            completed_tasks.add(str(task_id))  # Adiciona a tarefa concluída ao conjunto
            
            print(f"[WorkGenerator] Resultado recebido: {result}")
            
            if len(completed_tasks) == NUM_TASKS:
                print("[WorkGenerator] Todas as tarefas foram concluídas! Gerando novo lote...")
                time.sleep(2)  # Simula tempo de processamento antes de gerar novas tarefas
                generate_tasks()
                completed_tasks.clear()

if __name__ == "__main__":
    print("Iniciando Work Generator!")
    generate_tasks()  # Gera a primeira leva de tarefas
    listen_results()  # Escuta até todas serem concluídas
