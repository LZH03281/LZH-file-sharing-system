from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.models import UserModel
from app.schemas.logs import OperationLogSummary
from app.services.audit import AuditService

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[OperationLogSummary])
def list_logs(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> list[OperationLogSummary]:
    logs = AuditService(db).list_recent(limit)
    return [OperationLogSummary.model_validate(log) for log in logs]
