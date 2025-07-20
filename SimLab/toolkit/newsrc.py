import os
import sys
import json
from pathlib import Path
from typing import cast
from dotenv import load_dotenv

# Adiciona o diretório raiz do projeto ao sys.path
project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Imports locais
from pylib.mongo_db import create_mongo_repository_factory
from pylib.mongo_db import MongoRepository
from pylib.dto import SourceRepository

# Carrega variáveis de ambiente
load_dotenv()

# Constantes
DATA_DIR = Path("data")
SRC_DIR = DATA_DIR / "src"
INPUT_FILE = DATA_DIR / "source.json"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")

def get_all_files_recursively(directory: Path) -> list[Path]:
    return [f for f in directory.rglob("*") if f.is_file()]

def main():
    if not INPUT_FILE.exists():
        print(f"[Erro] Arquivo {INPUT_FILE} não encontrado.")
        sys.exit(1)

    if not SRC_DIR.exists() or not SRC_DIR.is_dir():
        print(f"[Erro] Diretório {SRC_DIR} não encontrado.")
        sys.exit(1)

    # Carrega JSON do repositório
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            repo_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[Erro] JSON inválido: {e}")
        sys.exit(1)

    # Remove ID se vier como null
    repo_data.pop("id", None)

    name = repo_data.get("name", "Unnamed Source")
    description = repo_data.get("description", "")

    # Conecta ao MongoDB
    mdb: MongoRepository = create_mongo_repository_factory(MONGO_URI, DB_NAME)

    # Envia arquivos para GridFS
    file_ids: list[str] = []
    for file_path in get_all_files_recursively(SRC_DIR):
        try:
            file_id = mdb.fs_handler.upload_file(str(file_path), name=str(file_path.name))
            print(f"[OK] Arquivo {file_path} enviado. ID: {file_id}")
            file_ids.append(str(file_id))
        except Exception as e:
            print(f"[Erro] Falha ao enviar {file_path}: {e}")

    # Cria documento SourceRepository
    repository: SourceRepository = cast(SourceRepository, {
        "id": "",  # será ignorado
        "name": name,
        "description": description,
        "source_ids": file_ids
    })

    try:
        inserted_id = mdb.source_repo.insert(repository)
        print(f"[OK] SourceRepository inserido com ID: {inserted_id}")
    except Exception as e:
        print(f"[Erro] Falha ao inserir SourceRepository: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
