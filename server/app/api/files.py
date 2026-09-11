import re
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, Response

from app.api.deps import get_current_user, get_file_repository, get_settings, get_storage_service
from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models.models import UserModel
from app.repositories.sqlalchemy import SqlAlchemyFileRepository
from app.schemas.files import FileSummary
from app.services.audit import AuditService
from app.services.storage import StorageService

router = APIRouter(prefix="/files", tags=["files"])

PRIVATE_PASSWORD_PATTERN = re.compile(r"^[A-Za-z0-9]{6}$")


def is_initial_admin(user: UserModel, settings: Settings) -> bool:
    return user.role == "admin" and user.username == settings.default_admin_username


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


@router.get("/search/owner", response_model=list[FileSummary])
def search_files_by_owner_id(
    owner_id: int,
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    current_user: UserModel = Depends(get_current_user),
) -> list[FileSummary]:
    return [
        FileSummary.from_model(record, current_user.id, current_user.role)
        for record in repository.search_visible_by_owner_id(current_user, owner_id)
    ]


@router.post("/upload", response_model=FileSummary, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    visibility: Literal["shared", "private"] = Form("shared"),
    access_password: str | None = Form(None),
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    storage: StorageService = Depends(get_storage_service),
    current_user: UserModel = Depends(get_current_user),
) -> FileSummary:
    access_password_hash = None
    if visibility == "private":
        if access_password is None or not PRIVATE_PASSWORD_PATTERN.fullmatch(access_password):
            raise AppError("INVALID_PRIVATE_PASSWORD", "private 文件密码必须是 6 位数字或大小写字母", 400)
        access_password_hash = hash_password(access_password)
    try:
        stored = await storage.save_upload(file)
    except AppError as exc:
        AuditService(repository.db).record("upload", "failed", user=current_user, detail=exc.code)
        raise
    try:
        record = repository.add(stored, current_user, visibility, access_password_hash)
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
    access_password: str | None = None,
    repository: SqlAlchemyFileRepository = Depends(get_file_repository),
    storage: StorageService = Depends(get_storage_service),
    settings: Settings = Depends(get_settings),
    current_user: UserModel = Depends(get_current_user),
) -> FileResponse:
    record = repository.get_for_user(file_id, current_user)
    if record.visibility == "private" and not is_initial_admin(current_user, settings):
        if not access_password or not record.access_password_hash:
            raise AppError("PRIVATE_PASSWORD_REQUIRED", "访问 private 文件需要输入文件密码", 403)
        if not verify_password(access_password, record.access_password_hash):
            raise AppError("INVALID_PRIVATE_PASSWORD", "文件密码错误", 403)
    path = storage.resolve_existing(record.stored_name)
    try:
        storage.security.check(path, record.original_name)
    except AppError as exc:
        AuditService(repository.db).record("download", "failed", user=current_user,
                                           file_id=record.id, detail=exc.code)
        raise
    AuditService(repository.db).record(
        "download",
        "success",
        user=current_user,
        file_id=record.id,
        file_name=record.original_name,
    )
    return FileResponse(
        path=path,
        media_type="application/octet-stream",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"},
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
