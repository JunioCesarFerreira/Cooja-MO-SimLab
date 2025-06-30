# api/endpoints/source.py
from fastapi import APIRouter, HTTPException
from dto import SourceRepository    
from pylib import mongo_db
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")
factory = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)

router = APIRouter()

@router.post("/", response_model=str)
def create_source(source: SourceRepository):
    try:
        source_id = factory.source_repo.insert(source)
        return str(source_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=list[SourceRepository])
def list_sources():
    return factory.source_repo.get_all()
