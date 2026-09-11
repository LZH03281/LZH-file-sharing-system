import csv
from io import StringIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
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


@router.get("/export")
def export_logs(
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> Response:
    logs = AuditService(db).list_recent(limit)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "username", "action", "file_id", "file_name", "result", "detail", "created_at"])
    for log in logs:
        writer.writerow(
            [
                log.id,
                log.user_id or "",
                log.username or "",
                log.action,
                log.file_id or "",
                log.file_name or "",
                log.result,
                log.detail or "",
                log.created_at.isoformat(),
            ]
        )
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="operation_logs.csv"'},
    )
