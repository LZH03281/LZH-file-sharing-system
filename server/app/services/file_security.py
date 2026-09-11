"""Local scanning only: uploaded bytes are never sent to a third-party service."""
from pathlib import Path
import subprocess
import threading
import unicodedata

from app.core.config import Settings
from app.core.errors import AppError


BLOCKED_SUFFIXES = set(".exe .dll .com .scr .msi .msp .bat .cmd .ps1 .psm1 .vbs .vbe .js .jse .wsf .wsh .hta .sh .bash .jar .class .lnk .url .reg .chm .iso .img .docm .dotm .xlsm .xltm .xlam .pptm .potm .ppam .sldm".split())


class FileSecurityService:
    def __init__(self, settings: Settings):
        self.settings = settings
        # Bound memory consumption from engines loading their signature databases.
        self._slot = threading.BoundedSemaphore(1)

    def check(self, path: Path, filename: str) -> None:
        name = unicodedata.normalize("NFKC", filename).rstrip(" .").lower()
        if any(unicodedata.category(c).startswith("C") for c in name):
            raise AppError("UNSAFE_FILE", "文件名包含控制或隐藏字符", 400)
        if any(suffix.rstrip(" .") in BLOCKED_SUFFIXES for suffix in Path(name).suffixes):
            raise AppError("UNSAFE_FILE", "禁止上传或下载可执行文件、脚本或宏文档", 400)
        with path.open("rb") as source:
            head = source.read(8)
        if head.startswith((b"MZ", b"\x7fELF", b"#!", b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce")):
            raise AppError("UNSAFE_FILE", "检测到可执行文件或脚本内容", 400)
        if not self.settings.antivirus_enabled:
            return
        if not self._slot.acquire(blocking=False):
            raise AppError("SCAN_BUSY", "扫描服务繁忙，请稍后重试", 503)
        try:
            result = subprocess.run(
                [self.settings.clamscan_path, "--no-summary", "--stdout",
                 "--alert-encrypted=yes", "--alert-exceeds-max=yes",
                 f"--max-filesize={self.settings.max_upload_size}",
                 f"--max-scansize={self.settings.max_upload_size * 4}",
                 "--max-recursion=16", "--max-files=1000", "--", str(path.resolve())],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=self.settings.scan_timeout, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AppError("SCAN_UNAVAILABLE", "病毒扫描不可用或超时，已拒绝文件，请联系管理员", 503) from exc
        finally:
            self._slot.release()
        if result.returncode == 1:
            raise AppError("FILE_INFECTED", "检测到病毒或无法安全检查的文件，已拒绝访问", 400)
        if result.returncode != 0:
            raise AppError("SCAN_UNAVAILABLE", "病毒扫描失败，已拒绝文件，请联系管理员", 503)
