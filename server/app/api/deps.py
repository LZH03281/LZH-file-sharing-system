from collections.abc import Generator

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models.models import UserModel
from app.repositories.sqlalchemy import SqlAlchemyFileRepository, UserRepository
from app.services.storage import StorageService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Generator[Session]:
    session_factory = request.app.state.session_factory
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_file_repository(db: Session = Depends(get_db)) -> SqlAlchemyFileRepository:
    return SqlAlchemyFileRepository(db)


def get_storage_service(request: Request) -> StorageService:
    return request.app.state.storage_service


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserModel:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError("NOT_AUTHENTICATED", "请先登录", 401)
    token = authorization.split(" ", 1)[1].strip()
    user_id = decode_access_token(token, settings)
    user = db.get(UserModel, int(user_id)) if user_id.isdigit() else None
    if user is None or not user.enabled:
        raise AppError("INVALID_TOKEN", "登录状态无效或已过期", 401)
    return user


def require_admin(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.role != "admin":
        raise AppError("PERMISSION_DENIED", "需要管理员权限", 403)
    return current_user
