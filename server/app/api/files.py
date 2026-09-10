from typing import Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, Response

from app.api.deps import get_current_user, get_file_repository, get_storage_service
from app.core.errors import AppError
from app.models.models import UserModel
from app.repositories.sqlalchemy import SqlAlchemyFileRepository
from app.schemas.files import FileSummary
from app.services.audit import AuditService
from app.services.storage import StorageService

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=list[FileSummary])
def list_files(
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    current_user: UserModel = Depends(get_current_user),
) -> list[FileSummary]:
    return [
        FileSummary.from_model(record, current_user.id, current_user.role)
        for record in repository.list_visible(current_user)
    ]


@router.get("/search", response_model=list[FileSummary])
def search_files(
    q: str,
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    current_user: UserModel = Depends(get_current_user),
) -> list[FileSummary]:
    return [
        FileSummary.from_model(record, current_user.id, current_user.role)
        for record in repository.search_visible(current_user, q.strip())
    ]


@router.post("/upload", response_model=FileSummary, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    visibility: Literal["shared", "private"] = Form("shared"),
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    storage: StorageService = Depends(get_storage_service),
    current_user: UserModel = Depends(get_current_user),
) -> FileSummary:
    stored = await storage.save_upload(file)
    try:
        record = repository.add(stored, current_user, visibility)
    except Exception:
        storage.delete(stored.stored_name)
        AuditService(repository.db).record("upload", "failed", user=current_user, detail=stored.original_name)
        raise
    AuditService(repository.db).record(
        "upload",
        "success",
        user=current_user,
        file_id=record.id,
        file_name=record.original_name,
    )
    return FileSummary.from_model(record, current_user.id, current_user.role)


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    storage: StorageService = Depends(get_storage_service),
    current_user: UserModel = Depends(get_current_user),
) -> FileResponse:
    record = repository.get_for_user(file_id, current_user)
    path = storage.resolve_existing(record.stored_name)
    AuditService(repository.db).record(
        "download",
        "success",
        user=current_user,
        file_id=record.id,
        file_name=record.original_name,
    )
    return FileResponse(
        path=path,
        media_type=record.content_type,
        filename=record.original_name,
    )


@router.delete("/{file_id}", status_code=204)
def delete_file(
    file_id: str,
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    storage: StorageService = Depends(get_storage_service),
    current_user: UserModel = Depends(get_current_user),
) -> Response:
    record = repository.get_for_delete(file_id, current_user)
    file_name = record.original_name
    stored_name = record.stored_name
    repository.delete(record)
    try:
        storage.delete(stored_name)
    except AppError:
        pass
    AuditService(repository.db).record(
        "delete",
        "success",
        user=current_user,
        file_id=file_id,
        file_name=file_name,
    )
    return Response(status_code=204)
