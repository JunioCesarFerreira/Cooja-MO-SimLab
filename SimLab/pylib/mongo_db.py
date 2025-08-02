import logging
import time
import pymongo
import gridfs
import queue
from datetime import datetime
from typing import Optional, Generator, NamedTuple, Callable, Any
from enum import Enum
from bson import ObjectId, errors
from pymongo import MongoClient
from contextlib import contextmanager
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from dto import SourceFile, SourceRepository, Simulation, Generation, Experiment

# Constantes de status
class SimulationStatus(str, Enum):
    WAITING = "Waiting"
    RUNNING = "Running"
    DONE = "Done"
    ERROR = "Error"

logger = logging.getLogger(__name__)

class MongoDBConnection:
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name

    @contextmanager
    def connect(self) -> Generator:
        client = MongoClient(self.uri)
        try:
            yield client[self.db_name]
        finally:
            client.close()
    
    def waiting_ping(self) -> None:
        while True:
            try:
                with MongoClient(self.uri) as client:
                    client.admin.command("ping")
                break
            except pymongo.errors.ConnectionFailure:
                print("[WorkGenerator] Aguardando conexão com MongoDB...")
                time.sleep(3)
    
    def watch_collection(self,
        collection_name: str,
        pipeline: list[dict],
        on_change: Callable[[dict], None],
        full_document: str = "default"
        ) -> None:
        """
        Observa alterações em uma coleção específica com um pipeline dado.

        Args:
            collection_name (str): Nome da coleção MongoDB.
            pipeline (list): Pipeline de agregação (ex: [$match]).
            on_change (Callable): Função de callback chamada a cada evento.
            full_document (str): Modo de recuperação do documento completo.
        """
        with self.connect() as db:
            collection: Collection = db[collection_name]
            try:
                with collection.watch(pipeline, full_document=full_document) as stream:
                    for change in stream:
                        on_change(change)
            except PyMongoError as e:
                print(f"[watch_collection] Erro ao observar coleção '{collection_name}': {e}")


class MongoGridFSHandler:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def upload_file(self, path: str, name: str) -> ObjectId:
        with self.connection.connect() as db:
            fs = gridfs.GridFS(db)
            with open(path, "rb") as f:
                file_id = fs.put(f, filename=name)
        return ObjectId(file_id)

    def download_file(self, file_id: str, local_path: str):
        try:
            with self.connection.connect() as db:
                fs = gridfs.GridFS(db)
                grid_out = fs.get(ObjectId(file_id))
                with open(local_path, 'wb') as f:
                    f.write(grid_out.read())
                logger.info(f"Arquivo {local_path} salvo com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao salvar arquivo {file_id}: {e}")


class ExperimentRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, experiment: Experiment) -> ObjectId:
        with self.connection.connect() as db:
            return db["experiments"].insert_one(experiment).inserted_id

    def find_by_status(self, status: SimulationStatus) -> list[Experiment]:
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


class GenerationRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, gen: Generation) -> ObjectId:
        with self.connection.connect() as db:
            return db["generations"].insert_one(gen).inserted_id

    def update(self, generation_id: str, updates: dict) -> bool:
        updates["id"] = generation_id
        with self.connection.connect() as db:
            result = db["generations"].update_one({"_id": ObjectId(generation_id)}, {"$set": updates})
            return result.modified_count > 0
        
    def find_pending(self) -> list[Generation]:
        with self.connection.connect() as db:
            return list(db["generations"].find({"status": SimulationStatus.WAITING}))

    def mark_done(self, queue_id: str):
        with self.connection.connect() as db:
            db["generations"].update_one(
                {"_id": ObjectId(queue_id)},
                {"$set": {"status": SimulationStatus.DONE, "end_time": datetime.now()}}
            )


class SimulationRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, simulation: Simulation) -> ObjectId:
        with self.connection.connect() as db:
            return db["simulations"].insert_one(simulation).inserted_id

    def find_pending(self) -> list[Simulation]:
        with self.connection.connect() as db:
            return list(db["simulations"].find({"status": SimulationStatus.WAITING}))
        
    def find_pending_by_generation(self, gen_id: ObjectId) -> list[Simulation]:
        with self.connection.connect() as db:
            return list(db["simulations"].find(
                {
                    "status": SimulationStatus.WAITING,
                    "generation_id": gen_id
                }))
    
    def mark_running(self, sim_id: ObjectId):
        with self.connection.connect() as db:
            db["simulations"].update_one(
                {"_id": sim_id},
                {"$set": {
                    "status": SimulationStatus.RUNNING, 
                    "start_time": datetime.now(),
                    }
                 }
            )
    
    def mark_done(self, sim_id: ObjectId, log_id: ObjectId):
        with self.connection.connect() as db:
            db["simulations"].update_one(
                {"_id": sim_id},
                {"$set": {
                    "status": SimulationStatus.DONE, 
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
                    "status": SimulationStatus.ERROR, 
                    "end_time": datetime.now(),
                    }
                 }
            )


class SourceRepositoryAccess:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, source: SourceRepository) -> ObjectId:
        with self.connection.connect() as db:
            return db["sources"].insert_one(source).inserted_id

    def get_all(self) -> list[SourceRepository]:
        with self.connection.connect() as db:
            return list(db["sources"].find())
    
    # Adiciona um novo arquivo (SourceFile) à lista source_ids de um SourceRepository.
    def append_source_file(self, repository_id: str, new_source_file: SourceFile) -> bool:
        with self.connection.connect() as db:
            result = db["sources"].update_one(
                {"_id": ObjectId(repository_id)},
                {"$addToSet": {"source_ids": new_source_file}}  # evita duplicatas exatas
            )
            return result.modified_count > 0

    # Atualiza os campos de metadados de um SourceRepository (exceto 'source_ids').
    def update_metadata(self, repository_id: str, updates: dict[str, Any]) -> bool:
        allowed_keys = {"name", "description"}  # adicione mais campos permitidos se necessário
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_keys}

        if not filtered_updates:
            return False

        with self.connection.connect() as db:
            result = db["sources"].update_one(
                {"_id": ObjectId(repository_id)},
                {"$set": filtered_updates}
            )
            return result.modified_count > 0
    
    # Recupera um SourceRepository pelo seu ID.
    def get_by_id(self, repository_id: str) -> Optional[SourceRepository]:
        with self.connection.connect() as db:
            return db["sources"].find_one({"_id": ObjectId(repository_id)})


# Fábrica de componentes


class MongoRepository(NamedTuple):
    experiment_repo: ExperimentRepository
    simulation_repo: SimulationRepository
    generation_repo: GenerationRepository
    source_repo: SourceRepositoryAccess
    fs_handler: MongoGridFSHandler


def create_mongo_repository_factory(mongo_uri: str, db_name: str) -> MongoRepository:
    connection = MongoDBConnection(mongo_uri, db_name)
    fs_handler = MongoGridFSHandler(connection)
    experiment_repo = ExperimentRepository(connection)
    simulation_repo = SimulationRepository(connection)
    simulation_queue_repo = GenerationRepository(connection)
    source_repo = SourceRepositoryAccess(connection)
    return MongoRepository(
        experiment_repo=experiment_repo,
        simulation_repo=simulation_repo,
        generation_repo=simulation_queue_repo,
        source_repo=source_repo,
        fs_handler=fs_handler
    )
