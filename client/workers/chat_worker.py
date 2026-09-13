import json
from queue import Empty, Queue
import threading

from PyQt6.QtCore import QThread, pyqtSignal
import websocket


class ChatWebSocketThread(QThread):
    connected = pyqtSignal()
    message_received = pyqtSignal(dict)
    error_received = pyqtSignal(str)
    disconnected = pyqtSignal()

    def __init__(self, ws_url: str) -> None:
        super().__init__()
        self.ws_url = ws_url
        self._outbox: Queue[dict] = Queue()
        self._stop_event = threading.Event()
        self._socket: websocket.WebSocket | None = None

    def run(self) -> None:
        try:
            self._socket = websocket.create_connection(self.ws_url, timeout=8)
            self.connected.emit()
            while not self._stop_event.is_set():
                self._flush_outbox()
                self._socket.settimeout(0.5)
                try:
                    raw_message = self._socket.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if not raw_message:
                    break
                try:
                    payload = json.loads(raw_message)
                except json.JSONDecodeError:
                    self.error_received.emit("收到无法解析的聊天消息")
                    continue
                if payload.get("type") == "message":
                    self.message_received.emit(payload["message"])
                elif payload.get("type") == "error":
                    self.error_received.emit(str(payload.get("message", "聊天消息发送失败")))
        except Exception as exc:
            if not self._stop_event.is_set():
                self.error_received.emit(f"聊天连接失败：{exc}")
        finally:
            self._close_socket()
            self.disconnected.emit()

    def send_message(self, receiver_id: int, content: str) -> None:
        self._outbox.put({"receiver_id": receiver_id, "content": content})

    def stop(self) -> None:
        self._stop_event.set()
        self._close_socket()

    def _flush_outbox(self) -> None:
        if self._socket is None:
            return
        while True:
            try:
                payload = self._outbox.get_nowait()
            except Empty:
                return
            self._socket.send(json.dumps(payload, ensure_ascii=False))

    def _close_socket(self) -> None:
        if self._socket is None:
            return
        try:
            self._socket.close()
        except Exception:
            pass
        self._socket = None
