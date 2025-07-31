# api/endpoints/experiment.py
from fastapi import APIRouter, HTTPException
from dto import Experiment    
from pylib import mongo_db
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")
factory = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)

router = APIRouter()

@router.post("/", response_model=str)
def create_experiment(experiment: Experiment):
    try:
        exp_id = factory.experiment_repo.insert(experiment)
        return str(exp_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/", response_model=str)
def update_experiment(experiment: Experiment):
    try:
        exp_id = factory.experiment_repo.update(experiment)
        return str(exp_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/waiting", response_model=list[Experiment])
def get_waiting_experiments():
    return factory.experiment_repo.find_by_status("Waiting")

@router.patch("/{experiment_id}", response_model=bool)
def update_experiment(experiment_id: str, updates: dict):
    return factory.experiment_repo.update(experiment_id, updates)
