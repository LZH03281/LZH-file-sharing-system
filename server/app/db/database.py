from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings


class Base(DeclarativeBase):
    pass


def make_engine(settings: Settings):
    connect_args = {"check_same_thread": False} if settings.resolved_database_url.startswith("sqlite") else {}
    return create_engine(settings.resolved_database_url, connect_args=connect_args)


def make_session_factory(settings: Settings) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(settings), autocommit=False, autoflush=False)


def init_db(settings: Settings, session_factory: sessionmaker[Session]) -> None:
    import app.models.models

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    bind = session_factory.kw["bind"]
    Base.metadata.create_all(bind=bind)
    inspector = inspect(bind)
    if "files" in inspector.get_table_names():
        file_columns = {column["name"] for column in inspector.get_columns("files")}
        if "access_password_hash" not in file_columns:
            with bind.begin() as connection:
                connection.execute(text("ALTER TABLE files ADD COLUMN access_password_hash VARCHAR(255)"))


def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session]:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
