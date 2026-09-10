from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from api_client.client import ApiClient, ApiError
from ui.style import APP_STYLE


class LoginWindow(QWidget):
    login_success = pyqtSignal()

    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle("共享文件服务器 - 登录")
        self.resize(460, 320)
        self.setStyleSheet(APP_STYLE)

        self.server_input = QLineEdit("http://127.0.0.1:8000")
        self.username_input = QLineEdit("admin")
        self.password_input = QLineEdit("admin123")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.login)
        self.register_button = QPushButton("注册账号")
        self.register_button.setObjectName("secondaryButton")
        self.register_button.clicked.connect(self.open_register_dialog)
        self.password_input.returnPressed.connect(self.login)

        title_label = QLabel("共享文件服务器")
        title_label.setObjectName("titleLabel")
        subtitle_label = QLabel("登录后即可上传、下载和管理共享文件")
        subtitle_label.setObjectName("subtitleLabel")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(14)
        form.addRow("服务器", self.server_input)
        form.addRow("用户名", self.username_input)
        form.addRow("密码", self.password_input)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(28, 26, 28, 26)
        card_layout.setSpacing(16)
        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addLayout(form)
        card_layout.addWidget(self.status_label)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addWidget(self.register_button)
        button_layout.addWidget(self.login_button)
        card_layout.addLayout(button_layout)
        card.setLayout(card_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(card)
        self.setLayout(layout)

    def login(self) -> None:
        self.login_button.setEnabled(False)
        self.status_label.setText("正在登录...")
        self.api_client.configure(self.server_input.text().strip())
        try:
            self.api_client.login(
                self.username_input.text().strip(),
                self.password_input.text(),
            )
        except ApiError as exc:
            self.status_label.setText(exc.message)
            QMessageBox.warning(self, "登录失败", exc.message)
        else:
            self.status_label.setText("")
            self.login_success.emit()
        finally:
            self.login_button.setEnabled(True)

    def open_register_dialog(self) -> None:
        self.api_client.configure(self.server_input.text().strip())
        dialog = RegisterDialog(self.api_client, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.username_input.setText(dialog.username)
            self.password_input.setText("")
            self.status_label.setText("注册成功，请使用新账号登录")


class RegisterDialog(QDialog):
    def __init__(self, api_client: ApiClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.username = ""
        self.setWindowTitle("注册普通用户")
        self.setStyleSheet(APP_STYLE)
        self.resize(380, 240)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("至少 6 位密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("再次输入密码")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.status_label = QLabel("注册后默认身份为普通用户")
        self.status_label.setObjectName("statusLabel")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(14)
        form.addRow("用户名", self.username_input)
        form.addRow("密码", self.password_input)
        form.addRow("确认密码", self.confirm_input)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("注册")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        self.buttons.accepted.connect(self.register)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    def register(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        if not username:
            self.status_label.setText("用户名不能为空")
            return
        if len(password) < 6:
            self.status_label.setText("密码至少 6 位")
            return
        if password != confirm:
            self.status_label.setText("两次输入的密码不一致")
            return

        try:
            self.api_client.register(username, password)
        except ApiError as exc:
            self.status_label.setText(exc.message)
            QMessageBox.warning(self, "注册失败", exc.message)
            return

        self.username = username
        QMessageBox.information(self, "注册成功", "账号已创建，请返回登录")
        self.accept()
