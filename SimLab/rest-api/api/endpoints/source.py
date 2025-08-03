from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from dto import SourceRepository, SourceFile
from pylib import mongo_db
import os
import shutil
from tempfile import NamedTemporaryFile

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0")
DB_NAME = os.getenv("DB_NAME", "simlab")
factory = mongo_db.create_mongo_repository_factory(MONGO_URI, DB_NAME)

router = APIRouter()


@router.post("/", response_model=str)
async def create_source_repository(
    name: str = Form(...),
    description: str = Form(""),
    files: list[UploadFile] = File(...)
):
    source_files: list[SourceFile] = []

    try:
        for upload in files:
            # Salva arquivo temporariamente
            with NamedTemporaryFile(delete=False) as tmp:
                shutil.copyfileobj(upload.file, tmp)
                tmp_path = tmp.name

            # Envia para o GridFS
            file_id = factory.fs_handler.upload_file(tmp_path, name=upload.filename)

            # Registra referência ao arquivo
            source_files.append({
                "id": str(file_id),
                "file_name": upload.filename
            })

            # Remove o arquivo temporário
            os.remove(tmp_path)

        # Cria e salva SourceRepository
        source_repo: SourceRepository = {
            "id": "",  # será ignorado
            "name": name,
            "description": description,
            "source_files": source_files
        }

        inserted_id = factory.source_repo.insert(source_repo)
        return str(inserted_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar repositório de fontes: {e}")


@router.get("/", response_model=list[SourceRepository])
def list_sources():
    return factory.source_repo.get_all()
