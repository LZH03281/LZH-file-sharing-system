from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import OperationLogModel, UserModel


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        action: str,
        result: str,
        user: UserModel | None = None,
        file_id: str | None = None,
        file_name: str | None = None,
        detail: str | None = None,
    ) -> None:
        log = OperationLogModel(
            user_id=user.id if user else None,
            username=user.username if user else None,
            action=action,
            file_id=file_id,
            file_name=file_name,
            result=result,
            detail=detail[:255] if detail else None,
        )
        self.db.add(log)
        self.db.commit()

    def list_recent(self, limit: int = 100) -> list[OperationLogModel]:
        safe_limit = max(1, min(limit, 500))
        statement = select(OperationLogModel).order_by(OperationLogModel.created_at.desc()).limit(safe_limit)
        return list(self.db.scalars(statement))
