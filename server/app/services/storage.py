from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile, status
from starlette.concurrency import run_in_threadpool
from app.services.file_security import FileSecurityService

from app.core.config import Settings
from app.core.errors import AppError


@dataclass(frozen=True)
class StoredFile:
    id: str
    stored_name: str
    original_name: str
    size: int
    content_type: str
    sha256: str


class StorageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.security = FileSecurityService(settings)
        self.storage_dir = settings.storage_dir.resolve()
        self.tmp_dir = (self.storage_dir / ".tmp").resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> StoredFile:
        original_name = self._safe_original_name(upload.filename)
        file_id = str(uuid4())
        stored_name = file_id
        final_path = self._resolve_storage_path(stored_name)
        tmp_path = self._resolve_tmp_path(f"{file_id}.uploading")
        digest = hashlib.sha256()
        size = 0

        try:
            with tmp_path.open("wb") as target:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > self.settings.max_upload_size:
                        raise AppError(
                            "FILE_TOO_LARGE",
                            "文件大小超过限制",
                            status.HTTP_413_CONTENT_TOO_LARGE,
                        )
                    digest.update(chunk)
                    target.write(chunk)

            await run_in_threadpool(self.security.check, tmp_path, original_name)
            os.replace(tmp_path, final_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

        return StoredFile(
            id=file_id,
            stored_name=stored_name,
            original_name=original_name,
            size=size,
            content_type=upload.content_type or "application/octet-stream",
            sha256=digest.hexdigest(),
        )

    def resolve_existing(self, stored_name: str) -> Path:
        path = self._resolve_storage_path(stored_name)
        if not path.is_file():
            raise AppError(
                "STORED_FILE_MISSING",
                "文件数据不存在",
                status.HTTP_404_NOT_FOUND,
            )
        return path

    def delete(self, stored_name: str) -> None:
        path = self._resolve_storage_path(stored_name)
        if not path.exists():
            raise AppError(
                "STORED_FILE_MISSING",
                "文件数据不存在",
                status.HTTP_404_NOT_FOUND,
            )
        path.unlink()

    def _resolve_storage_path(self, stored_name: str) -> Path:
        path = (self.storage_dir / stored_name).resolve()
        if not path.is_relative_to(self.storage_dir):
            raise AppError("INVALID_PATH", "文件路径不安全", status.HTTP_400_BAD_REQUEST)
        return path

    def _resolve_tmp_path(self, stored_name: str) -> Path:
        path = (self.tmp_dir / stored_name).resolve()
        if not path.is_relative_to(self.tmp_dir):
            raise AppError("INVALID_PATH", "临时文件路径不安全", status.HTTP_400_BAD_REQUEST)
        return path

    def _safe_original_name(self, filename: str | None) -> str:
        if filename is None:
            raise AppError("INVALID_FILENAME", "文件名不能为空", status.HTTP_400_BAD_REQUEST)

        normalized = filename.replace("\\", "/")
        name = Path(normalized).name.strip()
        if not name or name in {".", ".."} or "\x00" in name:
            raise AppError("INVALID_FILENAME", "文件名不合法", status.HTTP_400_BAD_REQUEST)
        if len(name) > 255:
            raise AppError("INVALID_FILENAME", "文件名过长", status.HTTP_400_BAD_REQUEST)
        return name
