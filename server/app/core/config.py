from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    max_upload_size: int
    database_url: str | None = None
    secret_key: str = "dev-secret-change-me-please-set-env"
    access_token_expire_minutes: int = 60
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    antivirus_enabled: bool = True
    clamscan_path: str = "clamscan"
    scan_timeout: int = 120

    def __post_init__(self) -> None:
        if self.max_upload_size <= 0 or self.scan_timeout <= 0:
            raise ValueError("上传大小和扫描超时必须大于零")

    @property
    def storage_dir(self) -> Path:
        return self.data_dir / "storage"

    @property
    def resolved_database_url(self) -> str:
        return self.database_url or f"sqlite:///{self.data_dir / 'app.db'}"

    @classmethod
    def from_env(cls) -> "Settings":
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = Path(os.getenv("CFS_DATA_DIR", str(base_dir / "data")))
        max_upload_size = int(os.getenv("CFS_MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))
        return cls(
            data_dir=data_dir,
            max_upload_size=max_upload_size,
            database_url=os.getenv("CFS_DATABASE_URL"),
            antivirus_enabled=os.getenv("CFS_ANTIVIRUS_ENABLED", "true").lower() != "false",
            clamscan_path=os.getenv("CFS_CLAMSCAN_PATH", "clamscan"),
            scan_timeout=int(os.getenv("CFS_SCAN_TIMEOUT", "120")),
            secret_key=os.getenv("CFS_SECRET_KEY", "dev-secret-change-me-please-set-env"),
            access_token_expire_minutes=int(os.getenv("CFS_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            default_admin_username=os.getenv("CFS_DEFAULT_ADMIN_USERNAME", "admin"),
            default_admin_password=os.getenv("CFS_DEFAULT_ADMIN_PASSWORD", "admin123"),
        )
