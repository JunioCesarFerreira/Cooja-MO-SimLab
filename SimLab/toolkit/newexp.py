import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import cast
from bson import ObjectId

# Adiciona o diretório do projeto ao sys.path
project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Importações locais
from pylib.mongo_db import create_mongo_repository_factory
from pylib.mongo_db import MongoRepository
from pylib.dto import Experiment

# Carrega variáveis de ambiente
load_dotenv()

# Constantes
DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "experiment.json"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")

def sanitize_experiment(data: dict) -> Experiment:
    """
    Preenche campos obrigatórios e padrões, convertendo para o formato esperado de Experiment.
    """
    if data.get("id") is None:
        data.pop("id", None)

    now = datetime.now()

    return cast(Experiment, {
        "id": "",  # será ignorado no Mongo
        "name": data.get("name", "Unnamed Experiment"),
        "status": data.get("status", "Waiting"),
        "created_time": now,
        "start_time": data.get("start_time", None),
        "end_time": data.get("end_time", None),
        "parameters": data.get("parameters", {}),
        "generations_ids": data.get("generations_ids", []),
        "source_repository_id": ObjectId(data.get("source_repository_id", "")),
    })

def main():
    print(f"mongodb: {MONGO_URI}")
    if not INPUT_FILE.exists():
        print(f"[Erro] Arquivo de entrada não encontrado: {INPUT_FILE}")
        sys.exit(1)

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[Erro] JSON inválido: {e}")
        sys.exit(1)

    experiment_data: Experiment = sanitize_experiment(raw_data)

    mdb: MongoRepository = create_mongo_repository_factory(MONGO_URI, DB_NAME)

    try:
        inserted_id = mdb.experiment_repo.insert(experiment_data)
        print(f"[OK] Experimento inserido com ID: {inserted_id}")
    except Exception as e:
        print(f"[Erro] Falha ao inserir experimento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
