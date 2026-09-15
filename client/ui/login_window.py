from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QTextOption
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
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from api_client.client import ApiClient, ApiError
from ui.branding import create_logo_label, load_icon, load_pixmap
from ui.style import get_app_style
from ui.theme_palette import ThemePaletteButton


class LoginWindow(QWidget):
    login_success = pyqtSignal()

    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle("千共*万享 - 登录")
        self.resize(460, 320)
        self.setStyleSheet(get_app_style())

        self.server_input = QLineEdit("http://127.0.0.1:8000")
        self.username_input = QLineEdit("admin")
        self.password_input = QLineEdit("admin123")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.eye_open_icon = load_icon("eye_open.png")
        self.eye_closed_icon = load_icon("eye_closed.png")
        self.password_toggle = QToolButton()
        self.password_toggle.setIcon(self.eye_closed_icon)
        self.password_toggle.setIconSize(QSize(32, 32))
        self.password_toggle.setObjectName("passwordToggle")
        self.password_toggle.setCheckable(True)
        self.password_toggle.setToolTip("显示密码")
        self.password_toggle.setAccessibleName("显示或隐藏密码")
        self.password_toggle.setFixedSize(40, 40)
        self.password_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.password_toggle.toggled.connect(self.toggle_password_visibility)
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.login)
        self.register_button = QPushButton("注册账号")
        self.register_button.setObjectName("secondaryButton")
        self.register_button.clicked.connect(self.open_register_dialog)
        self.password_input.returnPressed.connect(self.login)

        title_label = create_logo_label(220, 56, "千共*万享")
        title_label.setObjectName("titleLabel")
        subtitle_label = QLabel("登录后即可上传、下载和管理共享文件")
        subtitle_label.setObjectName("subtitleLabel")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(14)
        form.addRow("服务器", self.server_input)
        form.addRow("用户名", self.username_input)
        password_row = QWidget()
        password_row_layout = QHBoxLayout(password_row)
        password_row_layout.setContentsMargins(0, 0, 0, 0)
        password_row_layout.setSpacing(6)
        password_row_layout.addWidget(self.password_input, 1)
        password_row_layout.addWidget(self.password_toggle)
        form.addRow("密码", password_row)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(28, 26, 28, 26)
        card_layout.setSpacing(16)
        header_layout = QHBoxLayout()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.palette_button = ThemePaletteButton(self, show_theme_name=False)
        header_layout.addWidget(self.palette_button)
        card_layout.addLayout(header_layout)
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

    def toggle_password_visibility(self, visible: bool) -> None:
        echo_mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(echo_mode)
        self.password_toggle.setIcon(self.eye_open_icon if visible else self.eye_closed_icon)
        self.password_toggle.setToolTip("隐藏密码" if visible else "显示密码")

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
            self.status_label.setText("")
            LoginErrorDialog(exc.message or "登录失败", self).exec()
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


class LoginErrorDialog(QDialog):
    def __init__(self, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("登录失败")
        self.resize(620, 310)
        self.setStyleSheet(get_app_style())

        title_label = QLabel("登录失败")
        title_label.setObjectName("sectionTitleLabel")

        icon_label = QLabel()
        icon_label.setObjectName("errorIconLabel")
        icon_label.setFixedSize(120, 120)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_pixmap = load_pixmap("login_error.png")
        if not icon_pixmap.isNull():
            icon_label.setPixmap(
                icon_pixmap.scaled(
                    114,
                    114,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            icon_label.setText("!")

        message_view = QTextEdit()
        message_view.setObjectName("messageView")
        message_view.setReadOnly(True)
        message_view.setAcceptRichText(False)
        message_view.setPlainText(message)
        message_view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        message_view.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        message_view.setMinimumHeight(120)

        message_row = QHBoxLayout()
        message_row.setSpacing(14)
        message_row.addWidget(icon_label)
        message_row.addWidget(message_view, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout()
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        layout.addWidget(title_label)
        layout.addLayout(message_row)
        layout.addWidget(buttons)
        self.setLayout(layout)


class RegisterDialog(QDialog):
    def __init__(self, api_client: ApiClient, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.username = ""
        self.setWindowTitle("注册普通用户")
        self.setStyleSheet(get_app_style())
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
        password_row = QWidget()
        password_row_layout = QHBoxLayout(password_row)
        password_row_layout.setContentsMargins(0, 0, 0, 0)
        password_row_layout.setSpacing(6)
        password_row_layout.addWidget(self.password_input, 1)
        password_row_layout.addWidget(self.password_toggle)
        form.addRow("密码", password_row)
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

        ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        ok_button.setEnabled(False)
        cancel_button.setEnabled(False)
        self.status_label.setText("正在注册...")
        try:
            self.api_client.register(username, password)
        except ApiError as exc:
            self.status_label.setText(exc.message)
            ok_button.setEnabled(True)
            cancel_button.setEnabled(True)
            QMessageBox.warning(self, "注册失败", exc.message)
            return

        self.username = username
        self.accept()
        QMessageBox.information(self.parentWidget(), "注册成功", "账号已创建，请使用新账号登录")
