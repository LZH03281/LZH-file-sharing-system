from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from api_client.client import ApiClient, ApiError


class LoginWindow(QWidget):
    login_success = pyqtSignal()

    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle("共享文件服务器 - 登录")
        self.resize(380, 210)

        self.server_input = QLineEdit("http://127.0.0.1:8000")
        self.username_input = QLineEdit("admin")
        self.password_input = QLineEdit("admin123")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.status_label = QLabel("")
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.login)
        self.password_input.returnPressed.connect(self.login)

        form = QFormLayout()
        form.addRow("服务器", self.server_input)
        form.addRow("用户名", self.username_input)
        form.addRow("密码", self.password_input)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.status_label)
        layout.addWidget(self.login_button)
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
