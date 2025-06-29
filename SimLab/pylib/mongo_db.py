from pymongo import MongoClient
import gridfs
from bson import ObjectId
from datetime import datetime
from typing import Optional
import time

class MongoExperimentManager:
    def __init__(self, mongo_uri: str, db_name: str, info_log: bool = False):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.info_log = info_log

    def _get_client(self):
        return MongoClient(self.mongo_uri)
        
#---------------------
# Métodos Genéricos
#---------------------
    # Armazena um arquivo no GridFS e retorna o ID.
    def insert_file(self, path: str, name: str) -> str:
        client = self._get_client()
        db = client[self.db_name]
        fs = gridfs.GridFS(db)

        with open(path, "rb") as f:
            file_id = fs.put(f, filename=name)

        client.close()
        return ObjectId(file_id)

    # Recupera um arquivo do GridFS e salva ele no local indicado
    def save_file_from_mongo(self, file_id, local_path):
        try:
            client = self._get_client()
            db = client[self.db_name]
            fs = gridfs.GridFS(db)

            grid_out = fs.get(ObjectId(file_id))

            with open(local_path, 'wb') as f:
                f.write(grid_out.read())
                
            if self.info_log:
                print(f"[INFO] Arquivo {local_path} salvo com sucesso.")
                
        except Exception as e:
            print(f"[ERRO] Falha ao salvar arquivo {file_id}: {e}")
            
        finally:
            client.close()

    # Insere um novo documento
    def insert_document(self, document: dict, collection_name: str) -> str:
        client = self._get_client()
        db = client[self.db_name]
        collection = db[collection_name]

        result = collection.insert_one(document)
        client.close()

        return ObjectId(result.inserted_id)

    # Pega um documento por ID
    def get_document_by_id(self, collection_name: str, document_id: ObjectId) -> Optional[dict]:
        client = self._get_client()
        db = client[self.db_name]
        collection = db[collection_name]

        result = collection.find_one({"_id": document_id})

        client.close()
        return result
    
    def get_collection(self, coll_name):
        client = self._get_client()
        db = client[self.db_name]
        return db[coll_name]
   
#---------------------
# Métodos Específicos
#--------------------- 
    # Insere um novo experimento
    def insert_experiment(
        self,
        experiment_data: dict,
        file_parameters: Optional[list[dict]] = None
    ) -> str:
        """
        Insere um experimento no MongoDB conforme a estrutura do modelo Experiment.
        """
        client = self._get_client()
        db = client[self.db_name]
        collection = db["experiments"]

        document = {
            "name": experiment_data.get("name", ""),
            "status": experiment_data.get("status", "Waiting"),
            "enqueuedTime": datetime.now(),
            "evolutiveParameters": experiment_data.get("evolutiveParameters", {}),
            "simulationModel": experiment_data.get("simulationModel", {}),
            "linkedFiles": [],
            "generations": []
        }

        if file_parameters:
            for file_param in file_parameters:
                try:
                    file_id = self.insert_file(file_param["filePath"], file_param["name"])
                    linked_file = {
                        "name": file_param["name"],
                        "fileId": file_id
                    }
                    document["linkedFiles"].append(linked_file)
                except Exception as e:
                    print(f"Erro ao processar arquivo {file_param['filePath']}: {str(e)}")
                    continue

        result = collection.insert_one(document)
        client.close()

        return ObjectId(result.inserted_id)

    # Retorna experimentos que estão com status Waiting
    def get_waiting_experiments(self) -> list[dict]:
        """
        Recupera todos os experimentos com status 'Waiting'.
        """
        client = self._get_client()
        db = client[self.db_name]
        collection = db["experiments"]

        waiting_experiments = list(collection.find({"status": "Waiting"}))

        client.close()
        return waiting_experiments

    # Retorna o primeiro experimento que esteja com status Waiting
    def get_first_waiting_experiment(self) -> Optional[dict]:
        """
        Recupera o primeiro experimento com status 'Waiting'.
        """
        client = self._get_client()
        db = client[self.db_name]
        collection = db["experiments"]

        experiment = collection.find_one({"status": "Waiting"})

        client.close()
        return experiment

    def find_pending_simulations(self):
        client = self._get_client()
        db = client[self.db_name]
        simqueue_coll = db["simqueue"]
        return simqueue_coll.find({"status": "waiting"})

    def update_experiment(self, experiment_id: str, updates: dict) -> bool:
        """
        Atualiza os campos de um experimento existente no MongoDB.
        """
        client = self._get_client()
        db = client[self.db_name]
        collection = db["experiments"]

        result = collection.update_one(
            {"_id": ObjectId(experiment_id)},
            {"$set": updates}
        )

        client.close()
        return result.modified_count > 0
            
    def update_simulation_status(self, sim_id, new_status):
        client = self._get_client()
        db = client[self.db_name]
        simqueue_coll = db["simqueue"]
        simqueue_coll.update_one(
            {"_id": ObjectId(sim_id)},
            {"$set": {"status": new_status, "timestamp": time.time()}}
        )
        print(f"[MongoDB] Simulação {sim_id} atualizada para status: {new_status}")
        
    def simulation_done(self, sim: dict, log_result_id: str):        
        # Atualiza o documento da simulação na coleção "simqueue":
        # define o status "done" e o campo simLogFile com o ID do log.
        client = self._get_client()
        db = client[self.db_name]
        simqueue_coll = db["simqueue"]
        generations_coll = db["generations"]
            
        log_oid = ObjectId(log_result_id)
    
        simqueue_coll.update_one(
            { "_id": sim["_id"] },
            { "$set": { "simLogFile": log_result_id, "status": "done", "timestamp": time.time() }}
        )
        
        update_result = generations_coll.update_one(
            { "_id": sim["generation_id"] },
            {
                "$set": {
                    "population.$[ind].simLogFile": log_oid
                }
            },
            array_filters=[
                { "ind.simulationFile": sim["simulationFile"] }
            ]
        )
        if update_result.matched_count == 0:
            print("[WARN] Nenhum indivíduo correspondente encontrado na geração.")
        
        client.close()

# Factory usando atributos globais
def factory(uri: str, db: str)-> MongoExperimentManager:
    return MongoExperimentManager(uri, db)