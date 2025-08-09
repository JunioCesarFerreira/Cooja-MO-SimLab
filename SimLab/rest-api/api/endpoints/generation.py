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

@router.put("/", response_model=str)
def update_generarion(generation: GenerationDto):
    try:
        exp_id = factory.generation_repo.update(generation)
        return str(exp_id)
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
    
    
@router.get("/by-status/{status}", response_model=list[GenerationDto])
def get_waiting_generations(status: str):
    return factory.generation_repo.find_by_status(status)


@router.patch("/{gen_id}/status", response_model=bool)
def update_generation_status(gen_id: str, new_status: str):
    try:
        factory.generation_repo.update_status(gen_id, new_status)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
