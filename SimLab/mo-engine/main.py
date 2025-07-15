import pymongo
import time
import os
from threading import Thread
from datetime import datetime

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
client = pymongo.MongoClient(MONGO_URI)

# Aguarda MongoDB estar pronto
while True:
    try:
        client.admin.command("ping")
        break
    except pymongo.errors.ConnectionFailure:
        print("[WorkGenerator] Aguardando conexão com MongoDB...")
        time.sleep(3)

db = client.simulation_db

# Coleções existentes
simulations_collection = db.simulations
tasks_collection = db.simulations_tasks
results_collection = db.simulations_results

NUM_TASKS = 15  # Número de tarefas por lote


def generate_tasks(sim_id):
    """
    Gera 15 tarefas para a simulação especificada por sim_id,
    colocando-as em simulations_tasks.
    """
    tasks = [
        {"simulationId": sim_id, "config": {"param": i}, "status": "pending"}
        for i in range(NUM_TASKS)
    ]
    tasks_collection.insert_many(tasks)
    print(f"[WorkGenerator] {NUM_TASKS} tarefas geradas para a simulação {sim_id}.")


def watch_simulations():
    """
    Observa a coleção 'simulations' e atualiza o status de simulações 'Queued'.
    Tratamento mais robusto para diferentes tipos de change stream events.
    """
    print("[WorkGenerator] Observando a coleção 'simulations' em busca de Status='Queued'...")
    
    pipeline = [
        {'$match': {
            'operationType': {'$in': ['insert', 'update', 'replace']},
            '$or': [
                {'fullDocument.Status': 'Queued'},
                {'updateDescription.updatedFields.Status': 'Queued'}
            ]
        }}
    ]
    
    with simulations_collection.watch(pipeline) as stream:
        for change in stream:
            try:
                op_type = change.get("operationType")
                
                # Extrai o documento dependendo do tipo de operação
                if op_type == 'insert' or op_type == 'replace':
                    doc = change.get("fullDocument", {})
                elif op_type == 'update':
                    # Para updates, pode precisar pegar do updateDescription
                    doc = simulations_collection.find_one({"_id": change["documentKey"]["_id"]})
                else:
                    continue
                
                # Verifica se o status é 'Queued'
                status = doc.get("Status")
                if status == "Queued":
                    sim_id = doc["_id"]
                    try:
                        # Atualiza o status
                        result = simulations_collection.update_one(
                            {"_id": sim_id, "Status": "Queued"},
                            {"$set": {
                                "Status": "Running", 
                                "StartTime": datetime.now()
                            }},
                            upsert=False
                        )

                        # Verifica se o update realmente ocorreu
                        if result.modified_count > 0:
                            print(f"[WorkGenerator] Simulação {sim_id} atualizada para 'Running'.")
                            generate_tasks(sim_id)
                        else:
                            print(f"[WorkGenerator] Nenhum documento atualizado para {sim_id}.")
                    
                    except Exception as e:
                        print(f"[WorkGenerator] Erro ao atualizar status: {e}")
            
            except Exception as general_error:
                print(f"[WorkGenerator] Erro geral no processamento de change stream: {general_error}")
                print(f"Detalhes do change: {change}")


def listen_results():
    """
    Continua igual ao seu código original, mas observe que:
    - Ele monitora a coleção 'simulations_results'
    - Quando detecta que todas as 15 tarefas (NUM_TASKS) foram concluídas,
      gera um novo lote de tarefas (ou faz outra ação que você queira).
    """
    completed_tasks = set()
    print("[WorkGenerator] Aguardando conclusão das tarefas (Change Stream em 'simulations_results')...")

    with results_collection.watch() as stream:
        for change in stream:
            if change["operationType"] == "insert":
                result = change["fullDocument"]
                task_id = result["task_id"]
                completed_tasks.add(str(task_id))  # Adiciona a tarefa concluída ao conjunto

                print(f"[WorkGenerator] Resultado recebido: {result}")

                if len(completed_tasks) == NUM_TASKS:
                    print("[WorkGenerator] Todas as tarefas foram concluídas! Gerando novo lote...")
                    time.sleep(2)  # Simula tempo de processamento antes de gerar novas tarefas
                    # Aqui, no seu fluxo, você poderia buscar qual sim_id está associado às tasks
                    # e marcar a simulação como "Completed", por exemplo.
                    # Mas no exemplo original, você simplesmente gera outro lote "genérico":

                    generate_tasks(None)  # ou passe o simId se quiser ligar a uma sim específica
                    completed_tasks.clear()


if __name__ == "__main__":
    print("Iniciando Work Generator!")

    # Executa duas threads: 
    #   1) Uma observando simulations (Status='Queued')
    #   2) Outra observando results (para saber quando concluem)
    t1 = Thread(target=watch_simulations, daemon=True)
    t2 = Thread(target=listen_results, daemon=True)

    t1.start()
    t2.start()

    # Mantém o main vivo; threads rodam como daemon
    while True:
        time.sleep(10)
