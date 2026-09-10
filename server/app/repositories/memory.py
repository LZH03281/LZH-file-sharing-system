from collections import OrderedDict
from datetime import datetime, timezone

from fastapi import status

from app.core.errors import AppError
from app.schemas.files import FileRecord
from app.services.storage import StoredFile


class InMemoryFileRepository:
    def __init__(self) -> None:
        self._records: OrderedDict[str, FileRecord] = OrderedDict()

    def add(self, stored: StoredFile) -> FileRecord:
        record = FileRecord(
            id=stored.id,
            stored_name=stored.stored_name,
            original_name=stored.original_name,
            size=stored.size,
            content_type=stored.content_type,
            sha256=stored.sha256,
            created_at=datetime.now(timezone.utc),
        )
        self._records[record.id] = record
        return record

    def list(self) -> list[FileRecord]:
        return list(reversed(self._records.values()))

    def get(self, file_id: str) -> FileRecord:
        record = self._records.get(file_id)
        if record is None:
            raise AppError("FILE_NOT_FOUND", "文件不存在", status.HTTP_404_NOT_FOUND)
        return record

    def delete(self, file_id: str) -> None:
        if file_id not in self._records:
            raise AppError("FILE_NOT_FOUND", "文件不存在", status.HTTP_404_NOT_FOUND)
        del self._records[file_id]
