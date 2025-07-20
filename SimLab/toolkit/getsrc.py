import os
import sys
import json
from pathlib import Path
from bson import ObjectId
from dotenv import load_dotenv

# Adiciona o diretório raiz ao sys.path
project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from pylib.mongo_db import create_mongo_repository_factory
from pylib.mongo_db import MongoRepository
from pylib.dto import SourceRepository

# Carrega variáveis de ambiente
load_dotenv()

# Constantes
OUTPUT_DIR = Path("output") / "src"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")

def main():
    if len(sys.argv) < 2:
        print("Uso: python getsrc.py <source_repository_id>")
        sys.exit(1)

    source_id = sys.argv[1]
    output_path = OUTPUT_DIR / source_id
    output_path.mkdir(parents=True, exist_ok=True)

    # Conexão com o MongoDB
    mdb: MongoRepository = create_mongo_repository_factory(MONGO_URI, DB_NAME)

    # Busca repositório
    with mdb.source_repo.connection.connect() as db:
        raw_repo = db["sources"].find_one({"_id": ObjectId(source_id)})

        if not raw_repo:
            print(f"[Erro] Nenhum SourceRepository encontrado com ID: {source_id}")
            sys.exit(1)

        repo: SourceRepository = {
            "id": str(raw_repo["_id"]),
            "name": raw_repo.get("name", ""),
            "description": raw_repo.get("description", ""),
            "source_ids": raw_repo.get("source_ids", [])
        }

    # Baixa arquivos do GridFS
    for file_id in repo["source_ids"]:
        try:
            mdb.fs_handler.download_file(file_id, str(output_path / get_filename_from_gridfs(mdb, file_id)))
        except Exception as e:
            print(f"[Erro] Falha ao baixar arquivo {file_id}: {e}")

    # Salva metadados
    metadata = {
        "name": repo["name"],
        "description": repo["description"],
        "source_ids": repo["source_ids"]
    }

    with open(output_path / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[OK] Arquivos salvos em: {output_path}")

def get_filename_from_gridfs(mdb: MongoRepository, file_id: str) -> str:
    """
    Recupera o nome do arquivo original salvo no GridFS.
    """
    with mdb.fs_handler.connection.connect() as db:
        fs_files = db["fs.files"]
        file_doc = fs_files.find_one({"_id": ObjectId(file_id)})
        if file_doc and "filename" in file_doc:
            return file_doc["filename"]
        else:
            return f"{file_id}.bin"

if __name__ == "__main__":
    main()
