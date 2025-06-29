# api/endpoints/simulation.py
from fastapi import APIRouter, HTTPException
from dto import Simulation    
from pylib import mongo_db

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "my_simulation_db"
factory = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)

router = APIRouter()

@router.post("/", response_model=str)
def create_simulation(simulation: Simulation):
    try:
        sim_id = factory.simulation_repo.insert(simulation)
        return str(sim_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{sim_id}/status", response_model=bool)
def update_simulation_status(sim_id: str, new_status: str):
    try:
        factory.simulation_repo.update_status(sim_id, new_status)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
