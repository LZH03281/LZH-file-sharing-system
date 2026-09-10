from collections.abc import Generator

from sqlalchemy import create_engine
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


def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session]:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
