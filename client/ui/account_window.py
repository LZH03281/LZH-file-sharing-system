from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from api_client.client import ApiClient, ApiError
from ui.style import APP_STYLE


INITIAL_ADMIN_USERNAME = "admin"


class AccountDialog(QDialog):
    def __init__(self, api_client: ApiClient, parent=None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.users: list[dict] = []
        current_user = self.api_client.current_user or {}
        self.is_initial_admin = (
            current_user.get("role") == "admin"
            and current_user.get("username") == INITIAL_ADMIN_USERNAME
        )

        self.setWindowTitle("账号管理")
        self.resize(780, 540)
        self.setStyleSheet(APP_STYLE)

        title = QLabel("账号管理")
        title.setObjectName("titleLabel")
        subtitle_text = "管理员可注册普通账号、停用/启用账号，并删除普通用户账号。"
        if self.is_initial_admin:
            subtitle_text += " 初始 admin 可额外创建/管理管理员账号，管理员总数最多 3 个。"
        else:
            subtitle_text += " 非初始管理员无权管理管理员账号。"
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("新用户名")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("至少 6 位密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_box = QComboBox()
        self.role_box.addItem("普通用户", "user")
        if self.is_initial_admin:
            self.role_box.addItem("管理员", "admin")
        self.create_button = QPushButton("注册新账号")
        self.create_button.clicked.connect(self.create_user)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("用户名", self.username_input)
        form.addRow("密码", self.password_input)
        form.addRow("角色", self.role_box)

        create_layout = QHBoxLayout()
        create_layout.addLayout(form)
        create_layout.addWidget(self.create_button)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "用户名", "角色", "状态", "创建时间"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.refresh_users)
        self.disable_button = QPushButton("停用账号")
        self.disable_button.setObjectName("dangerButton")
        self.disable_button.clicked.connect(lambda: self.update_selected_user(False))
        self.enable_button = QPushButton("启用账号")
        self.enable_button.clicked.connect(lambda: self.update_selected_user(True))
        self.delete_button = QPushButton("删除账号")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_selected_user)
        self.close_button = QPushButton("关闭")
        self.close_button.setObjectName("secondaryButton")
        self.close_button.clicked.connect(self.accept)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.refresh_button)
        action_layout.addWidget(self.disable_button)
        action_layout.addWidget(self.enable_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addStretch()
        action_layout.addWidget(self.close_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(create_layout)
        layout.addWidget(self.table)
        layout.addLayout(action_layout)
        self.setLayout(layout)
        self.refresh_users()

    def refresh_users(self) -> None:
        try:
            self.users = self.api_client.list_users()
        except ApiError as exc:
            QMessageBox.warning(self, "刷新失败", exc.message)
            return
        self.render_users()

    def create_user(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        role = self.role_box.currentData()
        if not username:
            QMessageBox.warning(self, "创建失败", "用户名不能为空")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "创建失败", "密码至少 6 位")
            return
        try:
            self.api_client.create_user(username, password, role)
        except ApiError as exc:
            QMessageBox.warning(self, "创建失败", exc.message)
            return
        self.username_input.clear()
        self.password_input.clear()
        QMessageBox.information(self, "创建成功", "账号已创建")
        self.refresh_users()

    def update_selected_user(self, enabled: bool) -> None:
        user = self.selected_user()
        if user is None:
            return
        if not self.can_manage_user(user):
            return
        action = "启用" if enabled else "停用"
        reply = QMessageBox.question(
            self,
            "确认操作",
            f"确定要{action}账号 {user['username']} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api_client.set_user_enabled(user["id"], enabled)
        except ApiError as exc:
            QMessageBox.warning(self, "操作失败", exc.message)
            return
        self.refresh_users()

    def delete_selected_user(self) -> None:
        user = self.selected_user()
        if user is None:
            return
        if not self.can_manage_user(user, delete=True):
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除账号 {user['username']} 吗？该操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api_client.delete_user(user["id"])
        except ApiError as exc:
            QMessageBox.warning(self, "删除失败", exc.message)
            return
        QMessageBox.information(self, "删除成功", "账号已删除")
        self.refresh_users()

    def selected_user(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.users):
            QMessageBox.information(self, "请选择账号", "请先选择一个账号")
            return None
        return self.users[row]

    def can_manage_user(self, user: dict, delete: bool = False) -> bool:
        current_user = self.api_client.current_user or {}
        if user["id"] == current_user.get("id"):
            message = "不能删除当前登录账号" if delete else "不能停用/启用当前登录账号"
            QMessageBox.warning(self, "操作不可用", message)
            return False
        if user["role"] == "admin" and user["username"] == INITIAL_ADMIN_USERNAME:
            QMessageBox.warning(self, "操作不可用", "初始 admin 账号不可删除或停用")
            return False
        if user["role"] == "admin" and not self.is_initial_admin:
            QMessageBox.warning(self, "权限不足", "只有初始 admin 可以管理管理员账号")
            return False
        return True

    def render_users(self) -> None:
        self.table.setRowCount(len(self.users))
        for row, user in enumerate(self.users):
            values = [
                user["id"],
                user["username"],
                "管理员" if user["role"] == "admin" else "普通用户",
                "启用" if user["enabled"] else "已停用",
                self.format_time(user["created_at"]),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column in {0, 2, 3}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()

    @staticmethod
    def format_time(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return value
