from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api import auth, files
from app.core.config import Settings
from app.core.errors import AppError, app_error_handler, http_error_handler
from app.db.database import init_db, make_session_factory
from app.repositories.sqlalchemy import ensure_default_admin
from app.services.storage import StorageService


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings.from_env()
    session_factory = make_session_factory(app_settings)
    init_db(app_settings, session_factory)
    with session_factory() as db:
        ensure_default_admin(
            db,
            app_settings.default_admin_username,
            app_settings.default_admin_password,
        )

    app = FastAPI(title="Shared File Server", version="0.1.0")
    app.state.settings = app_settings
    app.state.session_factory = session_factory
    app.state.storage_service = StorageService(app_settings)

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, http_error_handler)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(files.router)
    return app


app = create_app()
