from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QActionGroup, QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QPushButton

from ui.style import (
    THEME_ORDER,
    THEMES,
    get_current_theme_key,
    get_theme_label,
    set_current_theme,
)


def _create_color_icon(color: str, size: int = 14) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(QPen(QColor(0, 0, 0, 35), 1))
    painter.drawEllipse(QRectF(1, 1, size - 2, size - 2))
    painter.end()
    return QIcon(pixmap)


class ThemePaletteButton(QPushButton):
    def __init__(self, parent=None, show_theme_name: bool = True) -> None:
        super().__init__(parent)
        self.show_theme_name = show_theme_name
        self.setObjectName("paletteButton")
        self.theme_menu = QMenu(self)
        self.theme_actions = {}
        palette_group = QActionGroup(self.theme_menu)
        palette_group.setExclusive(True)

        for theme_key in THEME_ORDER:
            theme = THEMES[theme_key]
            action = self.theme_menu.addAction(theme["label"])
            action.setIcon(_create_color_icon(theme["swatch_color"]))
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked=False, key=theme_key: self.apply_theme(key)
            )
            palette_group.addAction(action)
            self.theme_actions[theme_key] = action

        self.setMenu(self.theme_menu)
        self.sync_state()

    def sync_state(self) -> None:
        suffix = f" · {get_theme_label()}" if self.show_theme_name else ""
        self.setText(f"🎨 调色盘{suffix}")
        current_theme = get_current_theme_key()
        for theme_key, action in self.theme_actions.items():
            action.setChecked(theme_key == current_theme)

    def apply_theme(self, theme_key: str) -> None:
        style = set_current_theme(theme_key)
        app = QApplication.instance()
        if app is None:
            self.setStyleSheet(style)
            self.sync_state()
            return

        app.setStyleSheet(style)
        for widget in app.topLevelWidgets():
            widget.setStyleSheet(style)
        for widget in app.allWidgets():
            if isinstance(widget, ThemePaletteButton):
                widget.sync_state()