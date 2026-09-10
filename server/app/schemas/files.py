from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.models import FileModel


class FileRecord(BaseModel):
    id: str
    stored_name: str
    original_name: str
    size: int
    content_type: str
    sha256: str
    created_at: datetime


class FileSummary(BaseModel):
    id: str
    original_name: str
    size: int
    content_type: str
    visibility: Literal["shared", "private"]
    owner_id: int
    owner_name: str
    created_at: datetime
    can_delete: bool

    @classmethod
    def from_record(cls, record: FileRecord) -> "FileSummary":
        return cls(
            id=record.id,
            original_name=record.original_name,
            size=record.size,
            content_type=record.content_type,
            visibility="shared",
            owner_id=0,
            owner_name="",
            created_at=record.created_at,
            can_delete=True,
        )

    @classmethod
    def from_model(cls, record: FileModel, current_user_id: int, current_user_role: str) -> "FileSummary":
        return cls(
            id=record.id,
            original_name=record.original_name,
            size=record.size,
            content_type=record.content_type,
            visibility=record.visibility,
            owner_id=record.owner_id,
            owner_name=record.owner.username,
            created_at=record.created_at,
            can_delete=current_user_role == "admin" or record.owner_id == current_user_id,
        )
