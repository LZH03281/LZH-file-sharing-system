from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_settings, require_admin
from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import create_access_token, verify_password
from app.models.models import UserModel
from app.repositories.sqlalchemy import UserRepository
from app.schemas.auth import CreateUserRequest, LoginRequest, LoginResponse, RegisterRequest, UserSummary
from app.services.audit import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    audit = AuditService(db)
    user = UserRepository(db).get_by_username(data.username)
    if user is None or not user.enabled or not verify_password(data.password, user.password_hash):
        audit.record("login", "failed", detail=f"username={data.username}")
        raise AppError("INVALID_CREDENTIALS", "用户名或密码错误", 401)
    audit.record("login", "success", user=user)
    return LoginResponse(
        access_token=create_access_token(str(user.id), settings),
        user=UserSummary.model_validate(user),
    )


@router.post("/register", response_model=UserSummary, status_code=201)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> UserSummary:
    user = UserRepository(db).create(data.username, data.password, "user")
    AuditService(db).record(
        "register",
        "success",
        user=user,
        detail=f"registered={user.username}, role=user",
    )
    return UserSummary.model_validate(user)


@router.get("/me", response_model=UserSummary)
def me(current_user: UserModel = Depends(get_current_user)) -> UserSummary:
    return UserSummary.model_validate(current_user)


@router.post("/users", response_model=UserSummary, status_code=201)
def create_user(
    data: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> UserSummary:
    user = UserRepository(db).create(data.username, data.password, data.role)
    AuditService(db).record(
        "create_user",
        "success",
        user=current_user,
        detail=f"created={user.username}, role={user.role}",
    )
    return UserSummary.model_validate(user)
