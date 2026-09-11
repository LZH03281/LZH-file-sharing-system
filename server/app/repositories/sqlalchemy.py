from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.core.security import hash_password
from app.models.models import FileModel, UserModel
from app.services.storage import StoredFile


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_username(self, username: str) -> UserModel | None:
        statement = select(UserModel).where(UserModel.username == username)
        return self.db.scalar(statement)

    def get_by_id(self, user_id: int) -> UserModel | None:
        return self.db.get(UserModel, user_id)

    def list_all(self) -> list[UserModel]:
        statement = select(UserModel).order_by(UserModel.id.asc())
        return list(self.db.scalars(statement))

    def count_admins(self) -> int:
        statement = select(func.count()).select_from(UserModel).where(UserModel.role == "admin")
        return self.db.scalar(statement) or 0

    def count_files_for_user(self, user_id: int) -> int:
        statement = select(func.count()).select_from(FileModel).where(FileModel.owner_id == user_id)
        return self.db.scalar(statement) or 0

    def next_available_id(self) -> int:
        used_ids = list(self.db.scalars(select(UserModel.id).order_by(UserModel.id.asc())))
        expected_id = 1
        for user_id in used_ids:
            if user_id > expected_id:
                break
            if user_id == expected_id:
                expected_id += 1
        return expected_id

    def transfer_files_to_user(self, from_user_id: int, to_user_id: int, visibility: str = "shared") -> int:
        statement = (
            update(FileModel)
            .where(FileModel.owner_id == from_user_id)
            .values(owner_id=to_user_id, visibility=visibility, access_password_hash=None)
        )
        result = self.db.execute(statement)
        self.db.commit()
        return result.rowcount or 0

    def create(self, username: str, password: str, role: str = "user") -> UserModel:
        if self.get_by_username(username) is not None:
            raise AppError("USERNAME_EXISTS", "用户名已存在", 409)
        user = UserModel(
            id=self.next_available_id(),
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_enabled(self, user_id: int, enabled: bool) -> UserModel:
        user = self.get_by_id(user_id)
        if user is None:
            raise AppError("USER_NOT_FOUND", "用户不存在", 404)
        user.enabled = enabled
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: UserModel) -> None:
        self.db.delete(user)
        self.db.commit()


class SqlAlchemyFileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, stored: StoredFile, owner: UserModel, visibility: str, access_password_hash: str | None = None) -> FileModel:
        record = FileModel(
            id=stored.id,
            stored_name=stored.stored_name,
            original_name=stored.original_name,
            owner_id=owner.id,
            size=stored.size,
            content_type=stored.content_type,
            visibility=visibility,
            access_password_hash=access_password_hash,
            sha256=stored.sha256,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return self.get_for_user(record.id, owner)

    def list_visible(self, user: UserModel) -> list[FileModel]:
        statement = self._visible_statement(user).order_by(FileModel.created_at.desc())
        return list(self.db.scalars(statement).unique())

    def search_visible(self, user: UserModel, query: str) -> list[FileModel]:
        statement = (
            self._visible_statement(user)
            .where(FileModel.original_name.ilike(f"%{query}%"))
            .order_by(FileModel.created_at.desc())
        )
        return list(self.db.scalars(statement).unique())

    def search_visible_by_owner_id(self, user: UserModel, owner_id: int) -> list[FileModel]:
        statement = (
            self._visible_statement(user)
            .where(FileModel.owner_id == owner_id)
            .order_by(FileModel.created_at.desc())
        )
        return list(self.db.scalars(statement).unique())

    def get_for_user(self, file_id: str, user: UserModel) -> FileModel:
        statement = self._visible_statement(user).where(FileModel.id == file_id)
        record = self.db.scalar(statement)
        if record is None:
            raise AppError("FILE_NOT_FOUND", "文件不存在", 404)
        return record

    def get_for_delete(self, file_id: str, user: UserModel) -> FileModel:
        record = self.get_for_user(file_id, user)
        if user.role != "admin" and record.owner_id != user.id:
            raise AppError("PERMISSION_DENIED", "没有删除该文件的权限", 403)
        return record

    def delete(self, record: FileModel) -> None:
        self.db.delete(record)
        self.db.commit()

    def _visible_statement(self, user: UserModel):
        statement = select(FileModel).options(joinedload(FileModel.owner))
        if user.role == "admin":
            return statement
        return statement


def ensure_default_admin(db: Session, username: str, password: str) -> None:
    repo = UserRepository(db)
    if repo.get_by_username(username) is None:
        repo.create(username=username, password=password, role="admin")
