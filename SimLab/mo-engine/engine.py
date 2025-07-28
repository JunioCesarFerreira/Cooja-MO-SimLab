import os, sys, time
from bson import ObjectId
from threading import Thread
from datetime import datetime

project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from pylib import mongo_db
from pylib.mongo_db import SimulationStatus
from strategy.generator_random import GeneratorRandomStrategy
from strategy.nsga3 import NSGALoopStrategy  # futuro

SimStatus = mongo_db.SimulationStatus
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")

mongo = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)

active_strategies = {}  # exp_id -> instance


def select_strategy(exp_doc: dict):
    print("[Engine] select strategy...")
    exp_type = exp_doc.get("parameters", {}).get("type", "simple")
    if exp_type == "simple":
        print("simple")
        return GeneratorRandomStrategy(exp_doc, mongo)
    elif exp_type == "nsga3":
        print("nsga3")
        return NSGALoopStrategy(exp_doc, mongo)
    else:
        raise ValueError(f"[Engine] Tipo de experimento desconhecido: {exp_type}")


def process_experiment(exp_doc: dict):
    exp_id = str(exp_doc["_id"])
    print(f"[Engine] Processando experimento {exp_id}")
    try:
        strategy = select_strategy(exp_doc)
        active_strategies[exp_id] = strategy
        strategy.start()
    except Exception as e:
        print(f"[Erro] Falha ao iniciar estratégia para experimento {exp_id}: {e}")


def on_experiment_event(change: dict, is_full_doc = True):
    print("[Engine] on experiment event...")
    print(f"[Engine] change: {change}")

    if is_full_doc:
        exp_doc = change.get("fullDocument")
        if not exp_doc:
            print("[Engine] Documento ausente no evento.")
            return
        exp_id = str(exp_doc["_id"])
    else:
        exp_id = str(change["_id"])
    success = mongo.experiment_repo.update(exp_id, {
        "status": SimulationStatus.RUNNING,
        "start_time": datetime.now()
    })
    if success:
        if is_full_doc:
            process_experiment(exp_doc)
        else:
            process_experiment(change)


def watch_experiments():
    print("[Engine] Aguardando novos experimentos...")
    pipeline = [
        {
            "$match": {
                "operationType": {"$in": ["insert", "update", "replace"]},
                "fullDocument.status": "Waiting"
            }
        }
    ]
    mongo.experiment_repo.connection.watch_collection(
        "experiments", 
        pipeline, 
        on_experiment_event, 
        full_document="updateLookup"
        )


def on_simulation_result(change: dict):
    if change["operationType"] != "insert":
        return
    result = change.get("fullDocument")
    if not result:
        return

    sim_id = result.get("simulationId") or result.get("simulation_id")
    if not sim_id:
        return

    # Mapear qual experimento está ligado à simulação
    with mongo.simulation_repo.connection.connect() as db:
        sim_doc = db["simulations"].find_one({"_id": ObjectId(sim_id)})
        if not sim_doc:
            return
        exp_id = str(sim_doc.get("experiment_id"))  # precisa ser salvo junto à simulação!

    strategy = active_strategies.get(exp_id)
    if strategy:
        strategy.on_simulation_result(result)


def listen_results():
    pipeline = [{"$match": {"operationType": "insert"}}]
    mongo.simulation_repo.connection.watch_collection("simulations_results", pipeline, on_simulation_result)

if __name__ == "__main__":
    print("[Engine] Serviço iniciado.")
    mongo.experiment_repo.connection.waiting_ping()

    pending = mongo.experiment_repo.find_by_status("Waiting")

    while (len(pending) > 0):
        on_experiment_event(pending.pop(), is_full_doc=False)

    Thread(target=watch_experiments, daemon=True).start()
    Thread(target=listen_results, daemon=True).start()

    while True:
        time.sleep(10)
