from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel


LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "branding" / "logo.png"


def create_logo_label(max_width: int, max_height: int, fallback_text: str) -> QLabel:
    label = QLabel()
    pixmap = QPixmap(str(LOGO_PATH))
    if pixmap.isNull():
        label.setText(fallback_text)
    else:
        label.setPixmap(
            pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    return label