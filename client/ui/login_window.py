from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QFormLayout,
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
        card_layout.addWidget(self.login_button)
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
