import os, sys, time
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

def select_strategy(exp_doc: dict):
    print("[Engine] select strategy")
    exp_type = exp_doc.get("parameters", {}).get("type", "simple")
    print(f"[Engine] selected: {exp_type}")
    if exp_type == "simple":
        return GeneratorRandomStrategy(exp_doc, mongo)
    elif exp_type == "nsga3":
        return NSGALoopStrategy(exp_doc, mongo)
    else:
        raise ValueError(f"[Engine] Experiment type unknown: {exp_type}")


def process_experiment(exp_doc: dict):
    exp_id = str(exp_doc["_id"])
    print(f"[Engine] Processing experiment id: {exp_id}")
    try:
        strategy = select_strategy(exp_doc)
        strategy.start()
    except Exception as e:
        print(f"[Erro] Failed to start strategy for experiment {exp_id}: {e}")


def on_experiment_event(change: dict):
    print("[Engine] on experiment event...")
    print(f"[Engine] change: {change}")

    exp_doc = change.get("fullDocument")
    if not exp_doc:
        print("[Engine] Document missing from the event.")
        return
    exp_id = str(exp_doc["_id"])
        
    success = mongo.experiment_repo.update(exp_id, {
        "status": SimulationStatus.RUNNING,
        "start_time": datetime.now()
    })
    if success:
        process_experiment(exp_doc)


def run_experiment_event(change: dict):
    print("[Engine] run experiment event...")
    print(f"[Engine] change: {change}")

    exp_id = str(change["_id"])
    
    success = mongo.experiment_repo.update(exp_id, {
        "status": SimulationStatus.RUNNING,
        "start_time": datetime.now()
    })
    if success:
        process_experiment(change)
       

if __name__ == "__main__":
    print("[Engine] Service started.")
    exp_repo = mongo.experiment_repo
    exp_repo.connection.waiting_ping()

    pending = exp_repo.find_by_status(SimulationStatus.WAITING)

    while (len(pending) > 0):
        run_experiment_event(pending.pop())

    Thread(
        target=exp_repo.watch_experiments, 
        args=(on_experiment_event,),
        daemon=True).start()

    while True:
        time.sleep(10)
