from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from api_client.client import ApiClient
from ui.style import APP_STYLE


class ProfileDialog(QDialog):
    def __init__(self, api_client: ApiClient, parent=None) -> None:
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("个人主页")
        self.resize(420, 300)
        self.setStyleSheet(APP_STYLE)

        user = self.api_client.current_user or {}
        role = user.get("role", "user")
        role_text = "管理员" if role == "admin" else "普通用户"

        title = QLabel("个人主页")
        title.setObjectName("titleLabel")
        subtitle = QLabel("查看当前登录账号的基础信息")
        subtitle.setObjectName("subtitleLabel")

        avatar = QLabel((user.get("username") or "U")[:1].upper())
        avatar.setObjectName("avatarLabel")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        username = QLabel(str(user.get("username", "未登录")))
        username.setObjectName("profileNameLabel")
        account_type = QLabel(role_text)
        account_type.setObjectName("pillLabel")
        account_type.setAlignment(Qt.AlignmentFlag.AlignCenter)

        identity_layout = QVBoxLayout()
        identity_layout.addWidget(username)
        identity_layout.addWidget(account_type, alignment=Qt.AlignmentFlag.AlignLeft)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        header_layout.addWidget(avatar)
        header_layout.addLayout(identity_layout)
        header_layout.addStretch()

        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(18, 16, 18, 16)
        info_layout.setSpacing(10)
        info_layout.addWidget(self.info_row("用户 ID", str(user.get("id", "-"))))
        info_layout.addWidget(self.info_row("用户名", str(user.get("username", "-"))))
        info_layout.addWidget(self.info_row("账号类型", role_text))
        info_card.setLayout(info_layout)

        close_button = QPushButton("关闭")
        close_button.setObjectName("secondaryButton")
        close_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(header_layout)
        layout.addWidget(info_card)
        layout.addStretch()
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

    @staticmethod
    def info_row(label_text: str, value_text: str) -> QFrame:
        row = QFrame()
        row.setObjectName("infoRow")
        label = QLabel(label_text)
        label.setObjectName("mutedLabel")
        value = QLabel(value_text)
        value.setObjectName("valueLabel")
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(value)
        row.setLayout(layout)
        return row
