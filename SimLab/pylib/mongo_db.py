import logging
import time
from datetime import datetime
from typing import Optional, Generator

from bson import ObjectId
from pymongo import MongoClient
import gridfs
from contextlib import contextmanager

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
    def __init__(self, connection: MongoDBConnection, fs_handler: MongoGridFSHandler):
        self.connection = connection
        self.fs_handler = fs_handler

    def _build_experiment_document(self, data: dict, linked_files: list[dict]) -> dict:
        return {
            "name": data.get("name", ""),
            "status": data.get("status", STATUS_WAITING),
            "enqueuedTime": datetime.now(),
            "evolutiveParameters": data.get("evolutiveParameters", {}),
            "simulationModel": data.get("simulationModel", {}),
            "linkedFiles": linked_files,
            "generations": []
        }

    def _process_file_parameters(self, file_params: list[dict]) -> list[dict]:
        linked_files = []
        for param in file_params:
            try:
                file_id = self.fs_handler.upload_file(param["filePath"], param["name"])
                linked_files.append({"name": param["name"], "fileId": file_id})
            except Exception as e:
                logger.error(f"Erro ao processar arquivo {param['filePath']}: {e}")
        return linked_files

    def insert_experiment(self, experiment_data: dict, file_parameters: Optional[list[dict]] = None) -> ObjectId:
        linked_files = self._process_file_parameters(file_parameters or [])
        document = self._build_experiment_document(experiment_data, linked_files)
        with self.connection.connect() as db:
            return db["experiments"].insert_one(document).inserted_id

    def get_all_waiting(self) -> list[dict]:
        with self.connection.connect() as db:
            return list(db["experiments"].find({"status": STATUS_WAITING}))

    def get_first_waiting(self) -> Optional[dict]:
        with self.connection.connect() as db:
            return db["experiments"].find_one({"status": STATUS_WAITING})

    def update_experiment(self, experiment_id: str, updates: dict) -> bool:
        with self.connection.connect() as db:
            result = db["experiments"].update_one({"_id": ObjectId(experiment_id)}, {"$set": updates})
            return result.modified_count > 0


class SimulationQueueRepository:
    def __init__(self, connection: MongoDBConnection):
        self.connection = connection

    def find_pending_simulations(self):
        with self.connection.connect() as db:
            return db["simqueue"].find({"status": STATUS_WAITING})

    def update_status(self, sim_id: str, new_status: str):
        with self.connection.connect() as db:
            db["simqueue"].update_one(
                {"_id": ObjectId(sim_id)},
                {"$set": {"status": new_status, "timestamp": time.time()}}
            )
            logger.info(f"Simulação {sim_id} atualizada para status: {new_status}")

    def mark_simulation_done(self, sim: dict, log_result_id: str):
        log_oid = ObjectId(log_result_id)
        with self.connection.connect() as db:
            db["simqueue"].update_one(
                {"_id": sim["_id"]},
                {"$set": {"simLogFile": log_result_id, "status": STATUS_DONE, "timestamp": time.time()}}
            )
            update_result = db["generations"].update_one(
                {"_id": sim["generation_id"]},
                {"$set": {"population.$[ind].simLogFile": log_oid}},
                array_filters=[{"ind.simulationFile": sim["simulationFile"]}]
            )
            if update_result.matched_count == 0:
                logger.warning("Nenhum indivíduo correspondente encontrado na geração.")


# Fábrica de componentes

def factory(mongo_uri: str, db_name: str):
    connection = MongoDBConnection(mongo_uri, db_name)
    fs_handler = MongoGridFSHandler(connection)
    experiment_repo = ExperimentRepository(connection, fs_handler)
    simulation_repo = SimulationQueueRepository(connection)
    return experiment_repo, simulation_repo, fs_handler
