# api/endpoints/simqueue.py
from fastapi import APIRouter, HTTPException
from dto import GenerationDto    
from pylib import mongo_db
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")
factory = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)

router = APIRouter()

@router.post("/", response_model=str)
def create_generation(generation: GenerationDto):
    try:
        queue_id = factory.generation_repo.insert(generation)
        return str(queue_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/{generation_id}", response_model=GenerationDto)
def get_generation_by_id(generation_id: str):
    try:
        generation = factory.generation_repo.get_by_id(generation_id)
        if not generation:
            raise HTTPException(status_code=204, detail="Generation not found")
        return generation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/waiting", response_model=list[GenerationDto])
def get_waiting_generations():
    return factory.generation_repo.find_pending()


@router.patch("/{sim_id}/status", response_model=bool)
def update_generation_status(sim_id: str, new_status: str):
    try:
        factory.generation_repo.update_status(sim_id, new_status)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{queue_id}/done", response_model=bool)
def mark_queue_done(queue_id: str):
    try:
        factory.generation_repo.mark_done(queue_id)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
