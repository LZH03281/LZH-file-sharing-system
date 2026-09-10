from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from api_client.client import ApiClient, ApiError
from ui.style import APP_STYLE
from workers.transfer_worker import TransferThread


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.api_client = api_client
        self.files: list[dict] = []
        self.worker: TransferThread | None = None
        self.setWindowTitle("共享文件服务器")
        self.resize(1060, 680)
        self.setStyleSheet(APP_STYLE)

        title_label = QLabel("共享文件服务器")
        title_label.setObjectName("titleLabel")
        self.subtitle_label = QLabel("简洁、安全地管理团队共享文件")
        self.subtitle_label.setObjectName("subtitleLabel")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名搜索")
        self.search_input.returnPressed.connect(self.search_files)
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self.search_files)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.refresh_files)
        self.logout_button = QPushButton("退出登录")
        self.logout_button.setObjectName("secondaryButton")
        self.logout_button.clicked.connect(self.logout_requested.emit)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.search_button)
        top_layout.addWidget(self.refresh_button)
        top_layout.addWidget(self.logout_button)

        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(self.subtitle_label)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["文件名", "大小", "上传者", "可见性", "MIME", "上传时间", "可删除"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(90)

        self.visibility_box = QComboBox()
        self.visibility_box.addItems(["shared", "private"])
        self.upload_button = QPushButton("上传")
        self.upload_button.clicked.connect(self.upload_file)
        self.download_button = QPushButton("下载")
        self.download_button.clicked.connect(self.download_file)
        self.delete_button = QPushButton("删除")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_file)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_layout.addWidget(QLabel("可见性"))
        action_layout.addWidget(self.visibility_box)
        action_layout.addWidget(self.upload_button)
        action_layout.addWidget(self.download_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addWidget(self.progress_bar)

        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.addWidget(self.table)
        table_card.setLayout(table_layout)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        layout.addLayout(header_layout)
        layout.addLayout(top_layout)
        layout.addWidget(table_card)
        layout.addLayout(action_layout)
        content.setLayout(layout)
        self.setCentralWidget(content)

    def refresh_files(self) -> None:
        self.update_user_summary()
        try:
            self.files = self.api_client.list_files()
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        self.render_files()

    def update_user_summary(self) -> None:
        user = self.api_client.current_user or {}
        username = user.get("username", "未登录")
        role = user.get("role", "user")
        role_text = "管理员" if role == "admin" else "普通用户"
        self.subtitle_label.setText(f"当前用户：{username}（{role_text}）")

    def search_files(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            self.refresh_files()
            return
        try:
            self.files = self.api_client.search_files(query)
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        self.render_files()

    def upload_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择要上传的文件")
        if not path:
            return
        self.start_transfer(
            TransferThread(
                self.api_client,
                "upload",
                path,
                visibility=self.visibility_box.currentText(),
            )
        )

    def download_file(self) -> None:
        item = self.selected_file()
        if item is None:
            return
        default_name = item["original_name"]
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", default_name)
        if not path:
            return
        self.start_transfer(TransferThread(self.api_client, "download", item["id"], target=path))

    def delete_file(self) -> None:
        item = self.selected_file()
        if item is None:
            return
        if not item.get("can_delete"):
            QMessageBox.warning(self, "无法删除", "当前账号没有删除该文件的权限")
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除 {item['original_name']} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api_client.delete_file(item["id"])
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        self.refresh_files()

    def start_transfer(self, worker: TransferThread) -> None:
        self.worker = worker
        self.set_actions_enabled(False)
        self.progress_bar.setValue(0)
        worker.progress_changed.connect(self.progress_bar.setValue)
        worker.succeeded.connect(self.on_transfer_succeeded)
        worker.failed.connect(self.on_transfer_failed)
        worker.finished.connect(lambda: self.set_actions_enabled(True))
        worker.start()

    def on_transfer_succeeded(self, message: str) -> None:
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "完成", message)
        self.refresh_files()

    def on_transfer_failed(self, message: str) -> None:
        QMessageBox.warning(self, "传输失败", message)

    def selected_file(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.files):
            QMessageBox.information(self, "请选择文件", "请先在表格中选择一个文件")
            return None
        return self.files[row]

    def render_files(self) -> None:
        self.table.setRowCount(len(self.files))
        for row, item in enumerate(self.files):
            values = [
                item["original_name"],
                self.format_size(item["size"]),
                item.get("owner_name", ""),
                item["visibility"],
                item["content_type"],
                self.format_time(item["created_at"]),
                "是" if item.get("can_delete") else "否",
            ]
            for column, value in enumerate(values):
                table_item = QTableWidgetItem(str(value))
                if column in {1, 3, 6}:
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, table_item)
        self.table.resizeColumnsToContents()

    def set_actions_enabled(self, enabled: bool) -> None:
        self.upload_button.setEnabled(enabled)
        self.download_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.search_button.setEnabled(enabled)

    def handle_api_error(self, exc: ApiError) -> None:
        if exc.status_code == 401:
            QMessageBox.warning(self, "登录已失效", exc.message)
            self.logout_requested.emit()
            return
        QMessageBox.warning(self, "请求失败", exc.message)

    @staticmethod
    def format_size(size: int) -> str:
        value = float(size)
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
            value /= 1024
        return f"{size} B"

    @staticmethod
    def format_time(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value
