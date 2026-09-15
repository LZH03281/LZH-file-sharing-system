from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextOption
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.branding import load_pixmap
from ui.style import get_app_style


class AppErrorDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        parent: QWidget | None = None,
        icon_filename: str = "internal_error.png",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(620, 310)
        self.setStyleSheet(get_app_style())

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitleLabel")

        icon_label = QLabel()
        icon_label.setObjectName("errorIconLabel")
        icon_label.setFixedSize(120, 120)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_pixmap = load_pixmap(icon_filename)
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


def show_error_dialog(parent: QWidget | None, title: str, message: str) -> int:
    return AppErrorDialog(title, message, parent).exec()