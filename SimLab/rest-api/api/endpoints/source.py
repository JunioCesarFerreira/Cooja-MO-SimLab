from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from dto import SourceRepository, SourceFile
from pylib import mongo_db
import os
import shutil
from tempfile import NamedTemporaryFile
from zipfile import ZipFile
import tempfile
from bson import ObjectId

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


@router.get("/{repository_id}/download")
def download_source_repository(repository_id: str):
    try:
        repo = factory.source_repo.get_by_id(repository_id)
        if not repo:
            raise HTTPException(status_code=404, detail="SourceRepository não encontrado")

        source_files = repo.get("source_files", [])
        if not source_files:
            raise HTTPException(status_code=404, detail="Nenhum arquivo encontrado no repositório")

        # Cria um arquivo .zip temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip_file:
            with ZipFile(tmp_zip_file.name, "w") as zipf:
                for file in source_files:
                    file_id = file["id"]
                    file_name = file["file_name"]

                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        factory.fs_handler.download_file(ObjectId(file_id), tmp_file.name)
                        zipf.write(tmp_file.name, arcname=file_name)
                        tmp_file.close()
                        os.remove(tmp_file.name)

            tmp_zip_path = tmp_zip_file.name

        return FileResponse(
            tmp_zip_path,
            filename=f"repository_{repository_id}.zip",
            media_type="application/zip"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao baixar arquivos do repositório: {e}")