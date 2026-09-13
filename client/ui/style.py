APP_STYLE = """
QWidget {
    background: #fff8ec;
    color: #3f3428;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
}

QFrame#sidebar {
    background: #fff2dc;
    border: none;
    border-right: 1px solid #edcfa5;
}

QLabel#sidebarLogo {
    color: #7a4219;
    font-size: 18px;
    font-weight: 800;
    line-height: 1.25;
    padding: 6px 4px 12px 4px;
}

QLabel#sidebarUser {
    background: #fffaf1;
    color: #7a4b1f;
    border: 1px solid #edcfa5;
    border-radius: 12px;
    padding: 10px;
    font-weight: 600;
}

QFrame#pageHeader {
    background: #fffaf1;
    border: 1px solid #f0d9b8;
    border-radius: 16px;
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

QLabel#statValueLabel {
    color: #8a4b1f;
    font-size: 30px;
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
    background: #fffdf8;
    border: 1px solid #edcfa5;
    border-radius: 6px;
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
    border-radius: 6px;
    padding: 9px 16px;
    font-weight: 600;
}

QPushButton#navButton {
    background: transparent;
    border: none;
    border-left: 4px solid transparent;
    border-radius: 0;
    color: #7a4b1f;
    text-align: left;
    padding: 11px 12px;
    font-weight: 600;
}

QPushButton#navButton:hover {
    background: #ffeace;
}

QPushButton#navButton:checked {
    background: #ffe0ad;
    border-left: 4px solid #e6a24e;
    color: #5f3613;
    font-weight: 800;
}

QPushButton#logoutNavButton {
    background: transparent;
    border: none;
    color: #bf5a3c;
    text-align: left;
    padding: 11px 12px;
    font-weight: 700;
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
    background: #fff2dc;
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
