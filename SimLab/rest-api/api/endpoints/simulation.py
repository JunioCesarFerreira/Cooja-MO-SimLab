# api/endpoints/simulation.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from bson import ObjectId
import tempfile
from dto import SimulationDto    
from pylib import mongo_db
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")
factory = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)

router = APIRouter()

@router.post("/", response_model=str)
def create_simulation(simulation: SimulationDto):
    try:
        sim_id = factory.simulation_repo.insert(simulation)
        return str(sim_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{simulation_id}", response_model=SimulationDto)
def get_generation_by_id(simulation_id: str):
    try:
        experiment = factory.experiment_repo.get_by_id(simulation_id)
        if not experiment:
            raise HTTPException(status_code=204, detail="Simulation not found")
        return experiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/{sim_id}/download/{field_name}")
def download_simulation_file(sim_id: str, field_name: str):
    """
    Faz o download de um arquivo da simulação com base no campo:
    field_name deve ser 'log_cooja_id', 'topology_picture_id', 'runtime_log_id', etc.
    """
    try:
        sim = factory.simulation_repo.get_by_id(sim_id)
        if not sim:
            raise HTTPException(status_code=404, detail="Simulação não encontrada")

        file_id = sim.get(field_name)
        if not file_id:
            raise HTTPException(status_code=404, detail=f"Campo '{field_name}' não encontrado ou sem valor")

        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            factory.fs_handler.download_file(ObjectId(file_id), tmp_file.name)
            file_path = tmp_file.name

        return FileResponse(
            file_path,
            filename=f"{field_name}_{sim_id}",
            media_type="application/octet-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao baixar arquivo '{field_name}': {e}")
    
@router.patch("/{sim_id}/status", response_model=bool)
def update_simulation_status(sim_id: str, new_status: str):
    try:
        factory.simulation_repo.update_status(sim_id, new_status)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))