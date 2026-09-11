APP_STYLE = """
QWidget {
    background: #fff8ec;
    color: #3f3428;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
}

QFrame#card {
    background: #fffdf8;
    border: 1px solid #f0d9b8;
    border-radius: 14px;
}

QFrame#heroCard {
    background: #fff2dc;
    border: 1px solid #efcf9d;
    border-radius: 18px;
}

QLabel#titleLabel {
    color: #8a4b1f;
    font-size: 26px;
    font-weight: 700;
}

QLabel#subtitleLabel,
QLabel#statusLabel {
    color: #8b765f;
}

QLabel#sectionTitleLabel {
    color: #6f4218;
    font-size: 16px;
    font-weight: 700;
    padding-bottom: 6px;
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
QComboBox {
    background: #fffdf8;
    border: 1px solid #edcfa5;
    border-radius: 6px;
    padding: 8px 10px;
    min-height: 24px;
}

QLineEdit:focus,
QComboBox:focus {
    border: 1px solid #e6a24e;
}

QPushButton {
    background: #f4b860;
    color: #3f2d17;
    border: none;
    border-radius: 6px;
    padding: 9px 16px;
    font-weight: 600;
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
    background: #fff2dc;
    border: 1px solid #edcfa5;
    color: #7a4b1f;
}

QPushButton#secondaryButton:hover {
    background: #ffe6bd;
}

QPushButton#profileButton {
    background: #ffffff;
    border: 1px solid #edcfa5;
    color: #7a4b1f;
    border-radius: 18px;
    padding: 9px 16px;
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
    background: #fffdf8;
    alternate-background-color: #fff6e8;
    border: 1px solid #f0d9b8;
    border-radius: 8px;
    gridline-color: #f2dfc4;
    selection-background-color: #ffe2af;
    selection-color: #3f3428;
}

QHeaderView::section {
    background: #f7d99f;
    color: #5f3a16;
    border: none;
    border-right: 1px solid #edcfa5;
    padding: 8px;
    font-weight: 700;
}

QProgressBar {
    background: #fff2dc;
    border: 1px solid #edcfa5;
    border-radius: 6px;
    color: #5f3a16;
    text-align: center;
    min-height: 24px;
}

QProgressBar::chunk {
    background: #f4b860;
    border-radius: 5px;
}
"""
