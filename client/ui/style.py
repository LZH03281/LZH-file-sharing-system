APP_STYLE = """
QWidget {
    background: #fff8ec;
    color: #3f3428;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
}

QFrame#card {
    background: #ffffff;
    border: 1px solid #f0d9b8;
    border-radius: 8px;
}

QLabel#titleLabel {
    color: #8a4b1f;
    font-size: 24px;
    font-weight: 700;
}

QLabel#subtitleLabel,
QLabel#statusLabel {
    color: #8b765f;
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
