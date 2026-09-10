from datetime import datetime

from pydantic import BaseModel


class OperationLogSummary(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    action: str
    file_id: str | None
    file_name: str | None
    result: str
    detail: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
