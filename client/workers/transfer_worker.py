from pathlib import Path
from typing import Literal

from PyQt6.QtCore import QThread, pyqtSignal

from api_client.client import ApiClient


class TransferThread(QThread):
    progress_changed = pyqtSignal(int)
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(
        self,
        api_client: ApiClient,
        operation: Literal["upload", "download"],
        source: str,
        target: str | None = None,
        visibility: str = "shared",
    ) -> None:
        super().__init__()
        self.api_client = api_client
        self.operation = operation
        self.source = source
        self.target = target
        self.visibility = visibility

    def run(self) -> None:
        try:
            if self.operation == "upload":
                self.api_client.upload_file(
                    self.source,
                    self.visibility,
                    progress=self._emit_progress,
                )
                self.succeeded.emit("上传完成")
            else:
                if self.target is None:
                    raise ValueError("下载目标路径不能为空")
                self.api_client.download_file(
                    self.source,
                    Path(self.target),
                    progress=self._emit_progress,
                )
                self.succeeded.emit("下载完成")
        except Exception as exc:
            self.failed.emit(str(exc))

    def _emit_progress(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress_changed.emit(0)
            return
        value = max(0, min(100, int(current * 100 / total)))
        self.progress_changed.emit(value)
