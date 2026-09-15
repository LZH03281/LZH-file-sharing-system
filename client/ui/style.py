import colorsys
import re


APP_STYLE = """
QWidget {
    background: #fff7ea;
    color: #3f3428;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
}

QFrame#sidebar {
    background: #fff6e8;
    border: none;
    border-right: 1px solid #edcfa5;
}

QLabel#sidebarLogo {
    color: #7a4219;
    font-size: 20px;
    font-weight: 800;
    line-height: 1.25;
    padding: 8px 6px 16px 6px;
}

QLabel#sidebarUser {
    background: #ffffff;
    color: #7a4b1f;
    border: 1px solid #edcfa5;
    border-radius: 14px;
    padding: 12px;
    font-weight: 600;
}

QFrame#pageHeader {
    background: #fffdf8;
    border: 1px solid #f0d9b8;
    border-radius: 18px;
}

QFrame#card {
    background: #fffdf8;
    border: 1px solid #f0d9b8;
    border-radius: 16px;
}

QFrame#toolbarCard {
    background: #fffdf8;
    border: 1px solid #f0d9b8;
    border-radius: 16px;
}

QFrame#statCard {
    background: #fffdf8;
    border: 1px solid #f0d9b8;
    border-radius: 18px;
}

QFrame#statCard:hover {
    border: 1px solid #e6a24e;
}

QFrame#heroCard {
    background: #fff0d6;
    border: 1px solid #efcf9d;
    border-radius: 20px;
}

QLabel#titleLabel {
    color: #8a4b1f;
    font-size: 28px;
    font-weight: 800;
}

QLabel#subtitleLabel,
QLabel#statusLabel {
    color: #8b765f;
}

QLabel#sectionTitleLabel {
    color: #6f4218;
    font-size: 17px;
    font-weight: 800;
    padding-bottom: 8px;
}

QLabel#statValueLabel {
    color: #8a4b1f;
    font-size: 34px;
    font-weight: 800;
}

QLabel#profileNameLabel {
    color: #5f3613;
    font-size: 22px;
    font-weight: 700;
}

QLabel#avatarLabel {
    background: #f4b860;
    color: #ffffff;
    border-radius: 28px;
    min-width: 56px;
    min-height: 56px;
    font-size: 24px;
    font-weight: 800;
}

QLabel#pillLabel {
    background: #fff2dc;
    color: #8a4b1f;
    border: 1px solid #edcfa5;
    border-radius: 12px;
    padding: 4px 10px;
    font-weight: 600;
}

QLabel#onlinePill {
    background: #eaf7dc;
    color: #4f7a20;
    border: 1px solid #c7e4a5;
    border-radius: 12px;
    padding: 4px 10px;
    font-weight: 700;
}

QLabel#offlinePill {
    background: #f4eadc;
    color: #9b8064;
    border: 1px solid #ead6bb;
    border-radius: 12px;
    padding: 4px 10px;
    font-weight: 700;
}

QLabel#mutedLabel {
    color: #9b8064;
}

QLabel#valueLabel {
    color: #4d3520;
    font-weight: 700;
}

QFrame#infoRow {
    background: transparent;
    border: none;
    border-bottom: 1px solid #f2dfc4;
}

QLineEdit,
QComboBox,
QTextEdit,
QListWidget {
    background: #ffffff;
    border: 1px solid #edcfa5;
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 24px;
}

QLineEdit:focus,
QComboBox:focus,
QTextEdit:focus,
QListWidget:focus {
    border: 1px solid #e6a24e;
}

QTextEdit#messageView {
    background: #fffaf1;
    border: 1px solid #f0d9b8;
    border-radius: 12px;
    padding: 12px;
    line-height: 1.5;
}

QTextEdit#messageInput {
    background: #ffffff;
    border: 1px solid #edcfa5;
    border-radius: 12px;
    padding: 10px;
}

QListWidget {
    outline: none;
    padding: 6px;
}

QListWidget::item {
    background: #fff8ec;
    border: 1px solid #f2dfc4;
    border-radius: 10px;
    margin: 4px;
    padding: 10px;
}

QListWidget::item:selected {
    background: #ffe2af;
    border: 1px solid #e6a24e;
    color: #4d3520;
}

QPushButton {
    background: #f4b860;
    color: #3f2d17;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 700;
}

QPushButton#navButton {
    background: transparent;
    border: none;
    border-left: 4px solid transparent;
    border-radius: 12px;
    color: #7a4b1f;
    text-align: left;
    padding: 12px 13px;
    font-weight: 700;
}

QPushButton#navButton:hover {
    background: #ffeace;
}

QPushButton#navButton:checked {
    background: #ffe2b4;
    border-left: 4px solid #e6a24e;
    color: #5f3613;
    font-weight: 800;
}

QPushButton#logoutNavButton {
    background: transparent;
    border: none;
    color: #bf5a3c;
    text-align: left;
    padding: 12px 13px;
    font-weight: 700;
    border-radius: 12px;
}

QPushButton#logoutNavButton:hover {
    background: #ffe5d8;
}

QPushButton:hover {
    background: #efaa48;
}

QPushButton:pressed {
    background: #df9635;
}

QPushButton:disabled {
    background: #ead8bd;
    color: #9b8a74;
}

QPushButton#secondaryButton {
    background: #fff7e8;
    border: 1px solid #edcfa5;
    color: #7a4b1f;
}

QPushButton#secondaryButton:hover {
    background: #ffe6bd;
}

QPushButton#chatButton {
    background: #ffdfaa;
    border: 1px solid #e6a24e;
    color: #6f4218;
}

QPushButton#chatButton:hover {
    background: #ffd38c;
}

QPushButton#profileButton {
    background: #ffffff;
    border: 1px solid #edcfa5;
    color: #7a4b1f;
    border-radius: 20px;
    padding: 10px 18px;
}

QPushButton#profileButton:hover {
    background: #fff7e8;
    border: 1px solid #e6a24e;
}

QPushButton#dangerButton {
    background: #f08b66;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background: #e67850;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #fff6e8;
    border: 1px solid #f0d9b8;
    border-radius: 12px;
    gridline-color: #f2dfc4;
    selection-background-color: #ffe2af;
    selection-color: #3f3428;
}

QHeaderView::section {
    background: #f8dca8;
    color: #5f3a16;
    border: none;
    border-right: 1px solid #edcfa5;
    padding: 10px;
    font-weight: 700;
}

QProgressBar {
    background: #fff7e8;
    border: 1px solid #edcfa5;
    border-radius: 10px;
    color: #5f3a16;
    text-align: center;
    min-height: 26px;
}

QProgressBar::chunk {
    background: #f4b860;
    border-radius: 9px;
}

QPushButton#paletteButton {
    background: #fff2dc;
    border: 1px solid #edcfa5;
    color: #7a4b1f;
}

QPushButton#paletteButton:hover {
    background: #ffe6bd;
    border: 1px solid #e6a24e;
}

QToolButton#passwordToggle {
    background: transparent;
    border: none;
    padding: 0;
}

QToolButton#passwordToggle:hover,
QToolButton#passwordToggle:checked {
    background: transparent;
    border: none;
}

QLabel#errorIconLabel {
    background: transparent;
    border: none;
}

QMenu {
    background: #fffdf8;
    color: #3f3428;
    border: 1px solid #f0d9b8;
    border-radius: 10px;
    padding: 6px;
}

QMenu::item {
    border-radius: 8px;
    padding: 8px 28px 8px 12px;
}

QMenu::item:selected {
    background: #ffe2af;
    color: #4d3520;
}"""


DEFAULT_THEME_KEY = "rena"
THEME_ORDER = ("murasame", "yoshino", "mako", "rena")
THEMES = {
    "murasame": {
        "label": "丛雨",
        "swatch_color": "#7ada98",
        "hue_offset": 103.0,
        "saturation_scale": 0.65,
    },
    "yoshino": {
        "label": "芳乃",
        "swatch_color": "#da7a96",
        "hue_offset": -53.0,
        "saturation_scale": 0.65,
    },
    "mako": {
        "label": "茉子",
        "swatch_color": "#7aa9da",
        "hue_offset": 175.0,
        "saturation_scale": 0.65,
    },
    "rena": {
        "label": "蕾娜",
        "swatch_color": "#f4b860",
        "hue_offset": 0.0,
        "saturation_scale": 1.0,
    },
}

_PRESERVED_THEME_COLORS = frozenset(
    {
        "#bf5a3c",
        "#c7e4a5",
        "#e67850",
        "#eaf7dc",
        "#f08b66",
        "#ffffff",
    }
)
_CURRENT_THEME_KEY = DEFAULT_THEME_KEY
_HEX_COLOR_PATTERN = re.compile(r"#[0-9a-fA-F]{6}")


def _shift_color(hex_color: str, hue_offset: float, saturation_scale: float) -> str:
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) / 255 for index in (0, 2, 4))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    hue = (hue + hue_offset / 360.0) % 1.0
    saturation = min(1.0, saturation * saturation_scale)
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )


def _theme_color_map(theme_key: str | None = None) -> dict[str, str]:
    key = theme_key or _CURRENT_THEME_KEY
    if key not in THEMES:
        raise KeyError(f"Unknown theme: {key}")
    definition = THEMES[key]
    if key == DEFAULT_THEME_KEY:
        return {}
    return {
        color: (
            color
            if color in _PRESERVED_THEME_COLORS
            else _shift_color(
                color,
                float(definition["hue_offset"]),
                float(definition["saturation_scale"]),
            )
        )
        for color in {match.group(0).lower() for match in _HEX_COLOR_PATTERN.finditer(APP_STYLE)}
    }


def get_app_style(theme_key: str | None = None) -> str:
    key = theme_key or _CURRENT_THEME_KEY
    color_map = _theme_color_map(key)
    if not color_map:
        return APP_STYLE
    return _HEX_COLOR_PATTERN.sub(
        lambda match: color_map.get(match.group(0).lower(), match.group(0)),
        APP_STYLE,
    )


def set_current_theme(theme_key: str) -> str:
    global _CURRENT_THEME_KEY
    if theme_key not in THEMES:
        raise KeyError(f"Unknown theme: {theme_key}")
    _CURRENT_THEME_KEY = theme_key
    return get_app_style(theme_key)


def get_current_theme_key() -> str:
    return _CURRENT_THEME_KEY


def get_theme_label(theme_key: str | None = None) -> str:
    key = theme_key or _CURRENT_THEME_KEY
    return str(THEMES[key]["label"])


def get_chat_palette(theme_key: str | None = None) -> dict[str, str]:
    key = theme_key or _CURRENT_THEME_KEY
    if key not in THEMES:
        raise KeyError(f"Unknown theme: {key}")
    definition = THEMES[key]

    def themed(color: str) -> str:
        if key == DEFAULT_THEME_KEY or color in _PRESERVED_THEME_COLORS:
            return color
        return _shift_color(
            color,
            float(definition["hue_offset"]),
            float(definition["saturation_scale"]),
        )

    return {
        "text": themed("#3f3428"),
        "muted": themed("#9b8064"),
        "mine_bubble": themed("#ffe0a8"),
        "mine_border": themed("#efc482"),
        "mine_name": themed("#8a4b1f"),
        "peer_bubble": "#ffffff",
        "peer_border": themed("#f0d9b8"),
        "peer_name": themed("#6f4218"),
    }
