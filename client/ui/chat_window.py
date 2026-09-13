from datetime import datetime
from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from api_client.client import ApiClient, ApiError
from ui.style import APP_STYLE
from workers.chat_worker import ChatWebSocketThread


class ChatDialog(QDialog):
    def __init__(self, api_client: ApiClient, parent=None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.users: list[dict] = []
        self.current_peer: dict | None = None
        self.chat_thread: ChatWebSocketThread | None = None

        self.setWindowTitle("实时聊天")
        self.resize(900, 620)
        self.setStyleSheet(APP_STYLE)

        title = QLabel("实时聊天")
        title.setObjectName("titleLabel")
        subtitle = QLabel("局域网内用户单聊，支持在线实时推送和历史记录")
        subtitle.setObjectName("subtitleLabel")
        self.status_label = QLabel("未连接")
        self.status_label.setObjectName("offlinePill")

        header = QFrame()
        header.setObjectName("heroCard")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_text = QVBoxLayout()
        header_text.setSpacing(6)
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header_layout.addLayout(header_text)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header.setLayout(header_layout)

        self.user_list = QListWidget()
        self.user_list.currentRowChanged.connect(self.select_user)
        self.refresh_users_button = QPushButton("刷新用户")
        self.refresh_users_button.setObjectName("secondaryButton")
        self.refresh_users_button.clicked.connect(self.load_users)

        users_card = QFrame()
        users_card.setObjectName("card")
        users_layout = QVBoxLayout()
        users_layout.setContentsMargins(14, 14, 14, 14)
        users_layout.setSpacing(10)
        users_title = QLabel("用户列表")
        users_title.setObjectName("sectionTitleLabel")
        users_hint = QLabel("选择用户后加载历史记录")
        users_hint.setObjectName("mutedLabel")
        users_layout.addWidget(users_title)
        users_layout.addWidget(users_hint)
        users_layout.addWidget(self.user_list)
        users_layout.addWidget(self.refresh_users_button)
        users_card.setLayout(users_layout)

        self.chat_title = QLabel("请选择用户开始聊天")
        self.chat_title.setObjectName("sectionTitleLabel")
        self.chat_hint = QLabel("消息通过 WebSocket 实时发送，历史记录保存在服务器 SQLite 中")
        self.chat_hint.setObjectName("mutedLabel")
        self.messages_view = QTextEdit()
        self.messages_view.setObjectName("messageView")
        self.messages_view.setReadOnly(True)
        self.message_input = QTextEdit()
        self.message_input.setObjectName("messageInput")
        self.message_input.setPlaceholderText("输入聊天内容，最多 1000 字")
        self.message_input.setFixedHeight(96)
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setEnabled(False)

        chat_card = QFrame()
        chat_card.setObjectName("card")
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(16, 14, 16, 14)
        chat_layout.setSpacing(10)
        title_row = QHBoxLayout()
        title_row.addWidget(self.chat_title)
        title_row.addStretch()
        chat_layout.addLayout(title_row)
        chat_layout.addWidget(self.chat_hint)
        chat_layout.addWidget(self.messages_view)
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        input_row.addWidget(self.message_input)
        input_row.addWidget(self.send_button)
        chat_layout.addLayout(input_row)
        chat_card.setLayout(chat_layout)

        body = QHBoxLayout()
        body.setSpacing(14)
        body.addWidget(users_card, 2)
        body.addWidget(chat_card, 5)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(header)
        layout.addLayout(body)
        self.setLayout(layout)

        self.load_users()
        self.start_chat_thread()

    def load_users(self) -> None:
        try:
            self.users = self.api_client.list_chat_users()
        except ApiError as exc:
            QMessageBox.warning(self, "加载失败", exc.message)
            return
        selected_id = self.current_peer.get("id") if self.current_peer else None
        self.user_list.clear()
        selected_row = -1
        for index, user in enumerate(self.users):
            status = "● 在线" if user.get("online") else "○ 离线"
            role = "管理员" if user.get("role") == "admin" else "用户"
            item = QListWidgetItem(f"{status}\n{user['username']} · ID {user['id']} · {role}")
            item.setData(Qt.ItemDataRole.UserRole, user)
            self.user_list.addItem(item)
            if user["id"] == selected_id:
                selected_row = index
        if selected_row >= 0:
            self.user_list.setCurrentRow(selected_row)

    def select_user(self, row: int) -> None:
        item = self.user_list.item(row)
        if item is None:
            self.current_peer = None
            self.chat_title.setText("请选择用户开始聊天")
            self.send_button.setEnabled(False)
            return
        self.current_peer = item.data(Qt.ItemDataRole.UserRole)
        self.chat_title.setText(f"正在与 {self.current_peer['username']} 聊天")
        peer_status = "在线" if self.current_peer.get("online") else "离线"
        self.chat_hint.setText(f"对方当前{peer_status}；离线消息会保存为历史记录")
        self.send_button.setEnabled(True)
        self.load_history()

    def load_history(self) -> None:
        if self.current_peer is None:
            return
        try:
            messages = self.api_client.get_chat_history(self.current_peer["id"])
        except ApiError as exc:
            QMessageBox.warning(self, "加载历史失败", exc.message)
            return
        self.messages_view.clear()
        for message in messages:
            self.append_message(message)

    def start_chat_thread(self) -> None:
        try:
            ws_url = self.api_client.chat_ws_url()
        except ApiError as exc:
            QMessageBox.warning(self, "聊天不可用", exc.message)
            return
        self.chat_thread = ChatWebSocketThread(ws_url)
        self.chat_thread.connected.connect(self.on_connected)
        self.chat_thread.disconnected.connect(self.on_disconnected)
        self.chat_thread.message_received.connect(self.on_message_received)
        self.chat_thread.error_received.connect(self.on_chat_error)
        self.chat_thread.start()

    def send_message(self) -> None:
        if self.current_peer is None or self.chat_thread is None:
            QMessageBox.information(self, "请选择用户", "请先选择一个聊天对象")
            return
        content = self.message_input.toPlainText().strip()
        if not content:
            return
        if len(content) > 1000:
            QMessageBox.warning(self, "发送失败", "聊天内容不能超过 1000 字")
            return
        self.chat_thread.send_message(self.current_peer["id"], content)
        self.message_input.clear()

    def on_message_received(self, message: dict) -> None:
        current_user = self.api_client.current_user or {}
        peer_id = self.current_peer.get("id") if self.current_peer else None
        related_user_ids = {message.get("sender_id"), message.get("receiver_id")}
        if peer_id in related_user_ids and current_user.get("id") in related_user_ids:
            self.append_message(message)
        else:
            QMessageBox.information(self, "收到新消息", f"{message.get('sender_name', '用户')} 发来一条新消息")
            self.load_users()

    def on_chat_error(self, message: str) -> None:
        self.status_label.setText("连接异常")
        self.status_label.setObjectName("offlinePill")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        QMessageBox.warning(self, "聊天提示", message)

    def append_message(self, message: dict) -> None:
        current_user = self.api_client.current_user or {}
        mine = message.get("sender_id") == current_user.get("id")
        sender = "我" if mine else message.get("sender_name", "对方")
        created_at = self.format_time(str(message.get("created_at", "")))
        content = escape(str(message.get("content", ""))).replace("\n", "<br>")
        align = "right" if mine else "left"
        bubble_color = "#ffe0a8" if mine else "#ffffff"
        border_color = "#efc482" if mine else "#f0d9b8"
        name_color = "#8a4b1f" if mine else "#6f4218"
        self.messages_view.append(
            f"""
            <div align="{align}" style="margin: 8px 0;">
              <span style="color:#9b8064; font-size:12px;">{escape(sender)} · {escape(created_at)}</span><br>
              <span style="
                display:inline-block;
                background:{bubble_color};
                border:1px solid {border_color};
                border-radius:12px;
                padding:8px 10px;
                color:#3f3428;
                max-width:520px;
              "><b style="color:{name_color};"></b>{content}</span>
            </div>
            """
        )
        self.messages_view.verticalScrollBar().setValue(self.messages_view.verticalScrollBar().maximum())

    def on_connected(self) -> None:
        self.status_label.setText("已连接")
        self.status_label.setObjectName("onlinePill")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.load_users()

    def on_disconnected(self) -> None:
        self.status_label.setText("已断开")
        self.status_label.setObjectName("offlinePill")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def closeEvent(self, event) -> None:
        if self.chat_thread is not None:
            self.chat_thread.stop()
            self.chat_thread.wait(1500)
        super().closeEvent(event)

    @staticmethod
    def format_time(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%m-%d %H:%M")
        except ValueError:
            return value
