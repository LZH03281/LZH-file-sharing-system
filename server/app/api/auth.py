from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_settings, require_admin
from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import create_access_token, verify_password
from app.models.models import UserModel
from app.repositories.sqlalchemy import UserRepository
from app.schemas.auth import (
    CreateUserRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UpdateUserStatusRequest,
    UserSummary,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_ADMIN_ACCOUNTS = 3


def is_initial_admin(user: UserModel, settings: Settings) -> bool:
    return user.role == "admin" and user.username == settings.default_admin_username


def ensure_can_manage_target_admin(
    current_user: UserModel,
    target_user: UserModel,
    settings: Settings,
    action: str,
) -> None:
    if target_user.role != "admin":
        return
    if target_user.username == settings.default_admin_username and action == "delete":
        raise AppError("CANNOT_DELETE_INITIAL_ADMIN", "初始管理员账号不可删除", 400)
    if target_user.username == settings.default_admin_username and action == "disable":
        raise AppError("CANNOT_DISABLE_INITIAL_ADMIN", "初始管理员账号不可停用", 400)
    if not is_initial_admin(current_user, settings):
        raise AppError("PERMISSION_DENIED", "只有初始管理员可以管理管理员账号", 403)


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


@router.get("/users", response_model=list[UserSummary])
def list_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
) -> list[UserSummary]:
    users = UserRepository(db).list_all()
    return [UserSummary.model_validate(user) for user in users]


@router.post("/users", response_model=UserSummary, status_code=201)
def create_user(
    data: CreateUserRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: UserModel = Depends(require_admin),
) -> UserSummary:
    repo = UserRepository(db)
    if data.role == "admin":
        if not is_initial_admin(current_user, settings):
            raise AppError("PERMISSION_DENIED", "只有初始管理员可以创建管理员账号", 403)
        if repo.count_admins() >= MAX_ADMIN_ACCOUNTS:
            raise AppError("ADMIN_LIMIT_REACHED", "管理员账号数量已达上限", 409)
    user = repo.create(data.username, data.password, data.role)
    AuditService(db).record(
        "create_user",
        "success",
        user=current_user,
        detail=f"created={user.username}, role={user.role}",
    )
    return UserSummary.model_validate(user)


@router.patch("/users/{user_id}/enabled", response_model=UserSummary)
def update_user_status(
    user_id: int,
    data: UpdateUserStatusRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: UserModel = Depends(require_admin),
) -> UserSummary:
    if user_id == current_user.id and not data.enabled:
        raise AppError("CANNOT_DISABLE_SELF", "不能停用当前登录的管理员账号", 400)
    repo = UserRepository(db)
    target_user = repo.get_by_id(user_id)
    if target_user is None:
        raise AppError("USER_NOT_FOUND", "用户不存在", 404)
    ensure_can_manage_target_admin(
        current_user,
        target_user,
        settings,
        "enable" if data.enabled else "disable",
    )
    user = repo.set_enabled(user_id, data.enabled)
    AuditService(db).record(
        "update_user_status",
        "success",
        user=current_user,
        detail=f"target={user.username}, enabled={user.enabled}",
    )
    return UserSummary.model_validate(user)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: UserModel = Depends(require_admin),
) -> Response:
    repo = UserRepository(db)
    target_user = repo.get_by_id(user_id)
    if target_user is None:
        raise AppError("USER_NOT_FOUND", "用户不存在", 404)
    if target_user.id == current_user.id:
        raise AppError("CANNOT_DELETE_SELF", "不能删除当前登录账号", 400)
    ensure_can_manage_target_admin(current_user, target_user, settings, "delete")
    initial_admin = repo.get_by_username(settings.default_admin_username)
    if initial_admin is None:
        raise AppError("INITIAL_ADMIN_NOT_FOUND", "初始管理员账号不存在", 500)
    username = target_user.username
    role = target_user.role
    transferred_files = repo.transfer_files_to_user(target_user.id, initial_admin.id, "shared")
    repo.delete(target_user)
    AuditService(db).record(
        "delete_user",
        "success",
        user=current_user,
        detail=f"deleted={username}, role={role}, transferred_files={transferred_files}",
    )
    return Response(status_code=204)
