import logging
from datetime import datetime
from typing import Optional, Generator, NamedTuple

from bson import ObjectId
from pymongo import MongoClient
import gridfs
from contextlib import contextmanager

from dto import SourceRepository, Simulation, SimulationQueue, Experiment

# Constantes de status
STATUS_WAITING = "Waiting"
STATUS_DONE = "done"
STATUS_ERROR = "error"

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

    def find_by_status(self, status: str) -> list[Experiment]:
        with self.connection.connect() as db:
            return list(db["experiments"].find({"status": status}))

    def find_first_by_status(self, status: str) -> Optional[Experiment]:
        with self.connection.connect() as db:
            return db["experiments"].find_one({"status": status})

    def update(self, experiment_id: str, updates: dict) -> bool:
        with self.connection.connect() as db:
            result = db["experiments"].update_one({"_id": ObjectId(experiment_id)}, {"$set": updates})
            return result.modified_count > 0


class SimulationRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, simulation: Simulation) -> ObjectId:
        with self.connection.connect() as db:
            return db["simulations"].insert_one(simulation).inserted_id

    def update_status(self, sim_id: str, new_status: str):
        with self.connection.connect() as db:
            db["simulations"].update_one(
                {"_id": ObjectId(sim_id)},
                {"$set": {"status": new_status, "end_time": datetime.now()}}
            )
            logger.info(f"Simulação {sim_id} atualizada para status: {new_status}")


class SimulationQueueRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def insert(self, queue: SimulationQueue) -> ObjectId:
        with self.connection.connect() as db:
            return db["simqueue"].insert_one(queue).inserted_id

    def find_pending(self) -> list[SimulationQueue]:
        with self.connection.connect() as db:
            return list(db["simqueue"].find({"status": STATUS_WAITING}))

    def mark_done(self, queue_id: str):
        with self.connection.connect() as db:
            db["simqueue"].update_one(
                {"_id": ObjectId(queue_id)},
                {"$set": {"status": STATUS_DONE, "end_time": datetime.now()}}
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


# Fábrica de componentes


class MongoRepositoryFactory(NamedTuple):
    experiment_repo: ExperimentRepository
    simulation_repo: SimulationRepository
    simulation_queue_repo: SimulationQueueRepository
    source_repo: SourceRepositoryAccess
    fs_handler: MongoGridFSHandler


def create_mongo_repository_factory(mongo_uri: str, db_name: str) -> MongoRepositoryFactory:
    connection = MongoDBConnection(mongo_uri, db_name)
    fs_handler = MongoGridFSHandler(connection)
    experiment_repo = ExperimentRepository(connection)
    simulation_repo = SimulationRepository(connection)
    simulation_queue_repo = SimulationQueueRepository(connection)
    source_repo = SourceRepositoryAccess(connection)
    return MongoRepositoryFactory(
        experiment_repo=experiment_repo,
        simulation_repo=simulation_repo,
        simulation_queue_repo=simulation_queue_repo,
        source_repo=source_repo,
        fs_handler=fs_handler
    )
