from typing import Optional, Callable
from bson import ObjectId, errors

from mongo.connection import MongoDBConnection, EnumStatus
from dto import Experiment

class ExperimentRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, experiment: Experiment) -> ObjectId:
        with self.connection.connect() as db:
            return db["experiments"].insert_one(experiment).inserted_id

    def find_by_status(self, status: EnumStatus) -> list[Experiment]:
        with self.connection.connect() as db:
            return list(db["experiments"].find({"status": status}))

    def find_first_by_status(self, status: str) -> Optional[Experiment]:
        with self.connection.connect() as db:
            return db["experiments"].find_one({"status": status})

    def update(self, experiment_id: str, updates: dict) -> bool:
        updates["id"] = experiment_id
        with self.connection.connect() as db:
            result = db["experiments"].update_one({"_id": ObjectId(experiment_id)}, {"$set": updates})
            return result.modified_count > 0
        
    def get_by_id(self, experiment_id: str)->Experiment:
        try:
            oid = ObjectId(experiment_id)
        except errors.InvalidId:
            print("ID inválido")
        with self.connection.connect() as db:
            result = db["experiments"].find_one({"_id": oid})
            return result
            
    def watch_experiments(self, on_change: Callable[[dict], None]):
        print("[ExperimentRepository] Waiting new experiments...")
        pipeline = [
            {
                "$match": {
                    "operationType": {"$in": ["insert", "update", "replace"]},
                    "fullDocument.status": "Waiting"
                }
            }
        ]
        self.connection.watch_collection(
            "experiments", 
            pipeline, 
            on_change, 
            full_document="updateLookup"
            )