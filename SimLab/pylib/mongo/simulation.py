from datetime import datetime
from bson import ObjectId

from dto import Simulation
from mongo.connection import MongoDBConnection, EnumStatus

class SimulationRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, simulation: Simulation) -> ObjectId:
        with self.connection.connect() as db:
            return db["simulations"].insert_one(simulation).inserted_id

    def find_pending(self) -> list[Simulation]:
        with self.connection.connect() as db:
            return list(db["simulations"].find({"status": EnumStatus.WAITING}))
        
    def find_pending_by_generation(self, gen_id: ObjectId) -> list[Simulation]:
        with self.connection.connect() as db:
            return list(db["simulations"].find(
                {
                    "status": EnumStatus.WAITING,
                    "generation_id": gen_id
                }))
    
    def mark_running(self, sim_id: ObjectId):
        with self.connection.connect() as db:
            db["simulations"].update_one(
                {"_id": sim_id},
                {"$set": {
                    "status": EnumStatus.RUNNING, 
                    "start_time": datetime.now(),
                    }
                 }
            )
    
    def mark_done(self, sim_id: ObjectId, log_id: ObjectId):
        with self.connection.connect() as db:
            db["simulations"].update_one(
                {"_id": sim_id},
                {"$set": {
                    "status": EnumStatus.DONE, 
                    "end_time": datetime.now(),
                    "log_cooja_id": log_id,
                    }
                 }
            )
            
    def mark_error(self, sim_id: ObjectId):
        with self.connection.connect() as db:
            db["simulations"].update_one(
                {"_id": sim_id},
                {"$set": {
                    "status": EnumStatus.ERROR, 
                    "end_time": datetime.now(),
                    }
                 }
            )
