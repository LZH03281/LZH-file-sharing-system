from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from api_client.client import ApiClient, ApiError
from ui.chat_window import ChatDialog
from ui.profile_window import ProfileDialog
from ui.style import APP_STYLE
from workers.transfer_worker import TransferThread


INITIAL_ADMIN_USERNAME = "admin"


def is_six_digit_or_letter_password(value: str) -> bool:
    return len(value) == 6 and value.isalnum() and value.isascii()


class MainWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, api_client: ApiClient) -> None:
        super().__init__()
        self.api_client = api_client
        self.all_files: list[dict] = []
        self.files: list[dict] = []
        self.file_pages: dict[str, dict] = {}
        self.current_pages: dict[str, int] = {"center": 1, "mine": 1}
        self.active_file_scope = "center"
        self.page_size = 20
        self.worker: TransferThread | None = None
        self.nav_buttons: dict[str, QPushButton] = {}
        self.users: list[dict] = []
        self.header_user_buttons: list[QPushButton] = []

        self.setWindowTitle("共享文件服务器")
        self.setMinimumSize(1200, 720)
        self.resize(1280, 760)
        self.setStyleSheet(APP_STYLE)

        root = QWidget()
        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self.create_sidebar())

        self.stack = QStackedWidget()
        self.home_page = self.create_home_page()
        self.file_center_page = self.create_file_page("center", "文件中心", "管理、上传和下载服务器中的文件")
        self.my_files_page = self.create_file_page("mine", "我的文件", "查看和管理由当前账号上传的文件")
        self.logs_page = self.create_logs_page()
        self.account_page = self.create_account_page()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.file_center_page)
        self.stack.addWidget(self.my_files_page)
        self.stack.addWidget(self.logs_page)
        self.stack.addWidget(self.account_page)
        root_layout.addWidget(self.stack, 1)
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        self.show_page("home")

    def create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(8)

        logo = QLabel("共享文件服务器\nFileShare")
        logo.setObjectName("sidebarLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(logo)
        layout.addSpacing(12)

        nav_items = [
            ("home", "🏠 首页"),
            ("center", "📁 文件中心"),
            ("mine", "👤 我的文件"),
            ("chat", "💬 实时聊天"),
            ("logs", "📋 操作日志"),
            ("account", "⚙ 账号管理"),
        ]
        for key, text in nav_items:
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCheckable(True)
            if key == "chat":
                button.clicked.connect(self.open_chat_dialog)
            else:
                button.clicked.connect(lambda checked=False, page=key: self.show_page(page))
            self.nav_buttons[key] = button
            layout.addWidget(button)

        layout.addStretch()
        self.sidebar_user_label = QLabel("未登录")
        self.sidebar_user_label.setObjectName("sidebarUser")
        layout.addWidget(self.sidebar_user_label)
        logout_button = QPushButton("退出登录")
        logout_button.setObjectName("logoutNavButton")
        logout_button.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout_button)
        sidebar.setLayout(layout)
        return sidebar

    def create_page_shell(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)
        header = QFrame()
        header.setObjectName("pageHeader")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(18, 14, 18, 14)
        title_layout = QVBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("subtitleLabel")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_user_button = QPushButton("个人主页")
        header_user_button.setObjectName("profileButton")
        header_user_button.clicked.connect(self.open_profile_dialog)
        self.header_user_buttons.append(header_user_button)
        header_layout.addWidget(header_user_button)
        header.setLayout(header_layout)
        layout.addWidget(header)
        page.setLayout(layout)
        return page, layout

    def create_home_page(self) -> QWidget:
        page, layout = self.create_page_shell("首页", "项目概览、快捷入口和最近文件")

        welcome_card = QFrame()
        welcome_card.setObjectName("heroCard")
        welcome_layout = QVBoxLayout()
        welcome_layout.setContentsMargins(22, 20, 22, 20)
        self.home_welcome_label = QLabel("欢迎回来")
        self.home_welcome_label.setObjectName("titleLabel")
        self.home_role_label = QLabel("普通用户")
        self.home_role_label.setObjectName("subtitleLabel")
        quick_layout = QHBoxLayout()
        upload_shortcut = QPushButton("上传文件")
        upload_shortcut.clicked.connect(lambda: self.show_page("center"))
        browse_shortcut = QPushButton("浏览文件")
        browse_shortcut.setObjectName("secondaryButton")
        browse_shortcut.clicked.connect(lambda: self.show_page("center"))
        mine_shortcut = QPushButton("我的文件")
        mine_shortcut.setObjectName("secondaryButton")
        mine_shortcut.clicked.connect(lambda: self.show_page("mine"))
        quick_layout.addWidget(upload_shortcut)
        quick_layout.addWidget(browse_shortcut)
        quick_layout.addWidget(mine_shortcut)
        quick_layout.addStretch()
        welcome_layout.addWidget(self.home_welcome_label)
        welcome_layout.addWidget(self.home_role_label)
        welcome_layout.addSpacing(8)
        welcome_layout.addLayout(quick_layout)
        welcome_card.setLayout(welcome_layout)
        layout.addWidget(welcome_card)

        stats_layout = QHBoxLayout()
        self.total_files_value = QLabel("0")
        self.my_files_value = QLabel("0")
        self.shared_files_value = QLabel("0")
        stats_layout.addWidget(self.create_stat_card("文件总数", self.total_files_value))
        stats_layout.addWidget(self.create_stat_card("我的文件", self.my_files_value))
        stats_layout.addWidget(self.create_stat_card("共享文件", self.shared_files_value))
        layout.addLayout(stats_layout)

        recent_layout = QHBoxLayout()
        self.recent_files_table = self.create_table(["文件名", "上传者", "上传时间"])
        recent_layout.addWidget(self.create_card_with_widget("最近文件", self.recent_files_table), 2)
        self.recent_activity_title = QLabel("最近活动")
        self.recent_activity_title.setObjectName("sectionTitleLabel")
        self.recent_activity_label = QLabel("最近活动可通过“操作日志”页面导出查看。")
        self.recent_activity_label.setObjectName("mutedLabel")
        self.recent_activity_label.setWordWrap(True)
        self.recent_activity_card = QFrame()
        self.recent_activity_card.setObjectName("card")
        recent_activity_layout = QVBoxLayout()
        recent_activity_layout.setContentsMargins(18, 18, 18, 18)
        recent_activity_layout.addWidget(self.recent_activity_title)
        recent_activity_layout.addWidget(self.recent_activity_label)
        recent_activity_layout.addStretch()
        self.recent_activity_card.setLayout(recent_activity_layout)
        recent_layout.addWidget(self.recent_activity_card, 1)
        layout.addLayout(recent_layout, 1)
        return page

    def create_stat_card(self, title: str, value_label: QLabel) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)
        title_label = QLabel(title)
        title_label.setObjectName("mutedLabel")
        value_label.setObjectName("statValueLabel")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_card_with_widget(self, title: str, widget: QWidget) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        label = QLabel(title)
        label.setObjectName("sectionTitleLabel")
        layout.addWidget(label)
        layout.addWidget(widget)
        card.setLayout(layout)
        return card

    def create_file_page(self, scope: str, title: str, subtitle: str) -> QWidget:
        page, layout = self.create_page_shell(title, subtitle)
        search_input = QLineEdit()
        search_input.setPlaceholderText("输入文件名搜索")
        search_type_box = QComboBox()
        search_type_box.addItem("按文件名", "filename")
        search_type_box.addItem("按用户ID", "owner_id")
        search_type_box.currentIndexChanged.connect(lambda: self.update_search_placeholder(scope))
        visibility_filter_box = QComboBox()
        visibility_filter_box.addItem("全部文件", "all")
        visibility_filter_box.addItem("共享文件", "shared")
        visibility_filter_box.addItem("私有文件", "private")
        visibility_filter_box.currentIndexChanged.connect(lambda: self.apply_file_filters(scope))
        search_input.returnPressed.connect(lambda: self.search_files(scope))
        search_button = QPushButton("搜索")
        search_button.clicked.connect(lambda: self.search_files(scope))
        refresh_button = QPushButton("刷新")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self.refresh_files)

        search_card = QFrame()
        search_card.setObjectName("card")
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(16, 14, 16, 14)
        search_layout.setSpacing(10)
        search_layout.addWidget(QLabel("文件检索"))
        search_layout.addWidget(search_type_box)
        if scope == "center":
            search_layout.addWidget(QLabel("可见性"))
            search_layout.addWidget(visibility_filter_box)
        search_layout.addWidget(search_input, 1)
        search_layout.addWidget(search_button)
        search_layout.addWidget(refresh_button)
        search_card.setLayout(search_layout)
        layout.addWidget(search_card)

        table = self.create_table(["文件名", "大小", "上传者", "可见性", "MIME", "上传时间", "可删除"])
        table_card = QFrame()
        table_card.setObjectName("card")
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.addWidget(table)
        pagination_layout = QHBoxLayout()
        prev_button = QPushButton("上一页")
        prev_button.setObjectName("secondaryButton")
        prev_button.clicked.connect(lambda: self.previous_page(scope))
        page_label = QLabel("第 1 / 1 页")
        page_label.setObjectName("statusLabel")
        next_button = QPushButton("下一页")
        next_button.setObjectName("secondaryButton")
        next_button.clicked.connect(lambda: self.next_page(scope))
        pagination_layout.addStretch()
        pagination_layout.addWidget(prev_button)
        pagination_layout.addWidget(page_label)
        pagination_layout.addWidget(next_button)
        table_layout.addLayout(pagination_layout)
        table_card.setLayout(table_layout)
        layout.addWidget(table_card, 1)

        visibility_box = QComboBox()
        visibility_box.addItem("共享文件", "shared")
        visibility_box.addItem("私有文件", "private")
        upload_button = QPushButton("上传文件")
        upload_button.clicked.connect(self.upload_file)
        download_button = QPushButton("下载文件")
        download_button.clicked.connect(self.download_file)
        delete_button = QPushButton("删除文件")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_file)
        progress_bar = QProgressBar()
        progress_bar.setValue(0)

        action_card = QFrame()
        action_card.setObjectName("card")
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(16, 14, 16, 14)
        action_layout.setSpacing(10)
        action_layout.addWidget(QLabel("上传可见性"))
        action_layout.addWidget(visibility_box)
        action_layout.addWidget(upload_button)
        action_layout.addWidget(download_button)
        action_layout.addWidget(delete_button)
        action_layout.addWidget(progress_bar, 1)
        action_card.setLayout(action_layout)
        layout.addWidget(action_card)

        self.file_pages[scope] = {
            "search_input": search_input,
            "search_type_box": search_type_box,
            "visibility_filter_box": visibility_filter_box,
            "search_button": search_button,
            "refresh_button": refresh_button,
            "table": table,
            "prev_button": prev_button,
            "next_button": next_button,
            "page_label": page_label,
            "visibility_box": visibility_box,
            "upload_button": upload_button,
            "download_button": download_button,
            "delete_button": delete_button,
            "progress_bar": progress_bar,
            "files": [],
        }
        return page

    def create_logs_page(self) -> QWidget:
        page, layout = self.create_page_shell("操作日志", "查看系统操作记录；当前版本保留已有导出日志能力")
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(22, 20, 22, 20)
        hint = QLabel("当前客户端已有功能为导出操作日志 CSV。日志表格浏览可作为后续 UI 扩展，不新增后端接口。")
        hint.setObjectName("subtitleLabel")
        hint.setWordWrap(True)
        export_button = QPushButton("导出日志")
        export_button.clicked.connect(self.export_logs)
        self.logs_permission_hint = QLabel("")
        self.logs_permission_hint.setObjectName("mutedLabel")
        card_layout.addWidget(hint)
        card_layout.addSpacing(8)
        card_layout.addWidget(export_button, alignment=Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(self.logs_permission_hint)
        card_layout.addStretch()
        card.setLayout(card_layout)
        layout.addWidget(card, 1)
        return page

    def create_account_page(self) -> QWidget:
        page, layout = self.create_page_shell("账号管理", "管理员可注册、启用、停用和删除账号")
        self.account_subtitle = QLabel("")
        self.account_subtitle.setObjectName("subtitleLabel")
        self.account_subtitle.setWordWrap(True)
        layout.addWidget(self.account_subtitle)

        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QHBoxLayout()
        form_layout.setContentsMargins(16, 14, 16, 14)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("新用户名")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("至少 6 位密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_box = QComboBox()
        self.create_button = QPushButton("注册新账号")
        self.create_button.clicked.connect(self.create_user)
        form_layout.addWidget(QLabel("用户名"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("密码"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(QLabel("角色"))
        form_layout.addWidget(self.role_box)
        form_layout.addWidget(self.create_button)
        form_card.setLayout(form_layout)
        layout.addWidget(form_card)

        self.account_table = self.create_table(["ID", "用户名", "角色", "状态", "创建时间"])
        layout.addWidget(self.create_card_with_widget("账号列表", self.account_table), 1)

        action_card = QFrame()
        action_card.setObjectName("card")
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(16, 14, 16, 14)
        self.account_refresh_button = QPushButton("刷新")
        self.account_refresh_button.setObjectName("secondaryButton")
        self.account_refresh_button.clicked.connect(self.refresh_users)
        self.disable_button = QPushButton("停用账号")
        self.disable_button.setObjectName("dangerButton")
        self.disable_button.clicked.connect(lambda: self.update_selected_user(False))
        self.enable_button = QPushButton("启用账号")
        self.enable_button.clicked.connect(lambda: self.update_selected_user(True))
        self.account_delete_button = QPushButton("删除账号")
        self.account_delete_button.setObjectName("dangerButton")
        self.account_delete_button.clicked.connect(self.delete_selected_user)
        action_layout.addWidget(self.account_refresh_button)
        action_layout.addWidget(self.disable_button)
        action_layout.addWidget(self.enable_button)
        action_layout.addWidget(self.account_delete_button)
        action_layout.addStretch()
        action_card.setLayout(action_layout)
        layout.addWidget(action_card)
        return page

    def create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setMinimumSectionSize(90)
        return table

    def show_page(self, page: str) -> None:
        indexes = {"home": 0, "center": 1, "mine": 2, "logs": 3, "account": 4}
        if page in {"account", "logs"} and not self.current_user_is_admin():
            message = "账号管理需要管理员权限" if page == "account" else "操作日志仅管理员可访问"
            QMessageBox.warning(self, "权限不足", message)
            return
        self.stack.setCurrentIndex(indexes[page])
        for key, button in self.nav_buttons.items():
            if key != "chat":
                button.setChecked(key == page)
        if page in self.file_pages:
            self.active_file_scope = page
            self.render_file_scope(page)
        if page == "account":
            self.refresh_users()
        self.update_user_summary()

    def refresh_files(self) -> None:
        self.update_user_summary()
        try:
            self.all_files = self.api_client.list_files()
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        for scope in self.file_pages:
            self.file_pages[scope]["files"] = self.filtered_files_for_scope(scope)
            self.current_pages[scope] = 1
            self.render_file_scope(scope)
        self.render_home()

    def update_user_summary(self) -> None:
        user = self.api_client.current_user or {}
        username = user.get("username", "未登录")
        user_id = user.get("id", "-")
        role = user.get("role", "user")
        role_text = "管理员" if role == "admin" else "普通用户"
        self.sidebar_user_label.setText(f"{username}\n{role_text} · ID {user_id}")
        for button in self.header_user_buttons:
            button.setText(f"{username} · ID {user_id}")
        if hasattr(self, "home_welcome_label"):
            self.home_welcome_label.setText(f"欢迎回来，{username}")
            self.home_role_label.setText(f"{role_text} · ID {user_id}")
        account_button = self.nav_buttons.get("account")
        logs_button = self.nav_buttons.get("logs")
        if account_button:
            account_button.setVisible(role == "admin")
        if logs_button:
            logs_button.setVisible(role == "admin")
        if hasattr(self, "logs_permission_hint"):
            self.logs_permission_hint.setText("管理员可导出操作日志。" if role == "admin" else "当前账号无权导出操作日志。")
        if hasattr(self, "recent_activity_card"):
            self.recent_activity_card.setVisible(True)
        self.render_account_policy()

    def render_home(self) -> None:
        user = self.api_client.current_user or {}
        user_id = user.get("id")
        total = len(self.all_files)
        mine = len([item for item in self.all_files if item.get("owner_id") == user_id or item.get("owner_name") == user.get("username")])
        shared = len([item for item in self.all_files if item.get("visibility") == "shared"])
        self.total_files_value.setText(str(total))
        self.my_files_value.setText(str(mine))
        self.shared_files_value.setText(str(shared))
        recent = self.all_files[:5]
        self.recent_files_table.setRowCount(len(recent))
        for row, item in enumerate(recent):
            values = [item.get("original_name", ""), item.get("owner_name", ""), self.format_time(item.get("created_at", ""))]
            for column, value in enumerate(values):
                self.recent_files_table.setItem(row, column, QTableWidgetItem(str(value)))
        self.render_home_side_card()

    def render_home_side_card(self) -> None:
        if self.current_user_is_admin():
            self.recent_activity_title.setText("最近活动")
            self.recent_activity_label.setText("管理员可进入“操作日志”页面导出系统操作记录。")
            return
        self.recent_activity_title.setText("最近消息")
        try:
            users = self.api_client.list_chat_users()
            current_user = self.api_client.current_user or {}
            snippets = []
            for user in users[:8]:
                history = self.api_client.get_chat_history(user["id"])
                received = [
                    message
                    for message in history
                    if message.get("receiver_id") == current_user.get("id")
                ]
                if not received:
                    continue
                latest = received[-1]
                content = str(latest.get("content", "")).replace("\n", " ")
                if len(content) > 28:
                    content = content[:28] + "..."
                snippets.append(
                    f"{latest.get('sender_name', user.get('username', '用户'))}：{content}\n{self.format_time(latest.get('created_at', ''))}"
                )
            if snippets:
                self.recent_activity_label.setText("\n\n".join(snippets[:4]))
            else:
                self.recent_activity_label.setText("暂无收到的新消息。")
        except ApiError:
            self.recent_activity_label.setText("最近消息暂时无法加载。")

    def filtered_files_for_scope(self, scope: str) -> list[dict]:
        user = self.api_client.current_user or {}
        if scope == "mine":
            return [item for item in self.all_files if item.get("owner_id") == user.get("id") or item.get("owner_name") == user.get("username")]
        return list(self.all_files)

    def apply_file_filters(self, scope: str) -> None:
        widgets = self.file_pages[scope]
        files = self.filtered_files_for_scope(scope)
        visibility = widgets["visibility_filter_box"].currentData()
        if scope == "center" and visibility != "all":
            files = [item for item in files if item.get("visibility") == visibility]
        query = widgets["search_input"].text().strip()
        if query and widgets["search_type_box"].currentData() == "filename":
            files = [item for item in files if query.lower() in item.get("original_name", "").lower()]
        elif query and widgets["search_type_box"].currentData() == "owner_id" and query.isdigit():
            files = [item for item in files if item.get("owner_id") == int(query)]
        widgets["files"] = files
        self.current_pages[scope] = 1
        self.render_file_scope(scope)

    def render_file_scope(self, scope: str) -> None:
        widgets = self.file_pages[scope]
        files = widgets["files"]
        current_page = self.current_pages[scope]
        total_pages = self.total_pages(files)
        current_page = max(1, min(current_page, total_pages))
        self.current_pages[scope] = current_page
        start = (current_page - 1) * self.page_size
        page_files = files[start : start + self.page_size]

        table: QTableWidget = widgets["table"]
        table.setRowCount(len(page_files))
        for row, item in enumerate(page_files):
            values = [
                item.get("original_name", ""),
                self.format_size(int(item.get("size", 0))),
                item.get("owner_name", ""),
                "共享" if item.get("visibility") == "shared" else "私有（需密码）",
                item.get("content_type", ""),
                self.format_time(item.get("created_at", "")),
                "是" if item.get("can_delete") else "否",
            ]
            for column, value in enumerate(values):
                table_item = QTableWidgetItem(str(value))
                if column in {1, 3, 6}:
                    table_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, column, table_item)
        table.resizeColumnsToContents()
        widgets["page_label"].setText(f"第 {current_page} / {total_pages} 页，共 {len(files)} 个文件")
        widgets["prev_button"].setEnabled(current_page > 1)
        widgets["next_button"].setEnabled(current_page < total_pages)

    def open_profile_dialog(self) -> None:
        dialog = ProfileDialog(self.api_client, self)
        dialog.exec()

    def open_chat_dialog(self) -> None:
        for key, button in self.nav_buttons.items():
            button.setChecked(False)
        dialog = ChatDialog(self.api_client, self)
        dialog.exec()

    def export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出操作日志", "operation_logs.csv", "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            self.api_client.export_logs_csv(path)
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        except OSError as exc:
            QMessageBox.warning(self, "导出失败", f"无法保存日志文件：{exc}")
            return
        QMessageBox.information(self, "导出完成", "操作日志已导出")

    def update_search_placeholder(self, scope: str) -> None:
        widgets = self.file_pages[scope]
        if widgets["search_type_box"].currentData() == "owner_id":
            widgets["search_input"].setPlaceholderText("输入上传者用户 ID")
        else:
            widgets["search_input"].setPlaceholderText("输入文件名搜索")

    def search_files(self, scope: str) -> None:
        widgets = self.file_pages[scope]
        query = widgets["search_input"].text().strip()
        if not query:
            self.apply_file_filters(scope)
            return
        try:
            if widgets["search_type_box"].currentData() == "owner_id":
                if not query.isdigit():
                    QMessageBox.warning(self, "检索失败", "用户 ID 必须是数字")
                    return
                result = self.api_client.search_files_by_owner_id(int(query))
            else:
                result = self.api_client.search_files(query)
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        if scope == "mine":
            user = self.api_client.current_user or {}
            result = [item for item in result if item.get("owner_id") == user.get("id") or item.get("owner_name") == user.get("username")]
        visibility = widgets["visibility_filter_box"].currentData()
        if scope == "center" and visibility != "all":
            result = [item for item in result if item.get("visibility") == visibility]
        widgets["files"] = result
        self.current_pages[scope] = 1
        self.render_file_scope(scope)

    def upload_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择要上传的文件")
        if not path:
            return
        widgets = self.file_pages[self.active_file_scope]
        visibility = widgets["visibility_box"].currentData()
        access_password = None
        if visibility == "private":
            access_password = self.ask_private_password("设置 private 文件密码")
            if access_password is None:
                return
        self.start_transfer(
            TransferThread(
                self.api_client,
                "upload",
                path,
                visibility=visibility,
                access_password=access_password,
            )
        )

    def download_file(self) -> None:
        item = self.selected_file()
        if item is None:
            return
        default_name = item["original_name"]
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", default_name)
        if not path:
            return
        access_password = None
        if item["visibility"] == "private" and not self.current_user_is_initial_admin():
            access_password = self.ask_private_password("输入 private 文件密码")
            if access_password is None:
                return
        self.start_transfer(
            TransferThread(
                self.api_client,
                "download",
                item["id"],
                target=path,
                access_password=access_password,
            )
        )

    def delete_file(self) -> None:
        item = self.selected_file()
        if item is None:
            return
        if not item.get("can_delete"):
            QMessageBox.warning(self, "无法删除", "当前账号没有删除该文件的权限")
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除 {item['original_name']} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api_client.delete_file(item["id"])
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        self.refresh_files()

    def start_transfer(self, worker: TransferThread) -> None:
        self.worker = worker
        self.set_actions_enabled(False)
        self.current_progress_bar().setValue(0)
        worker.progress_changed.connect(self.current_progress_bar().setValue)
        worker.succeeded.connect(self.on_transfer_succeeded)
        worker.failed.connect(self.on_transfer_failed)
        worker.finished.connect(lambda: self.set_actions_enabled(True))
        worker.start()

    def on_transfer_succeeded(self, message: str) -> None:
        self.current_progress_bar().setValue(100)
        QMessageBox.information(self, "完成", message)
        self.refresh_files()

    def on_transfer_failed(self, message: str) -> None:
        QMessageBox.warning(self, "传输失败", message)

    def selected_file(self) -> dict | None:
        widgets = self.file_pages[self.active_file_scope]
        table: QTableWidget = widgets["table"]
        row = table.currentRow()
        page_start = (self.current_pages[self.active_file_scope] - 1) * self.page_size
        file_index = page_start + row
        files = widgets["files"]
        if row < 0 or file_index >= len(files):
            QMessageBox.information(self, "请选择文件", "请先在表格中选择一个文件")
            return None
        return files[file_index]

    def current_progress_bar(self) -> QProgressBar:
        return self.file_pages[self.active_file_scope]["progress_bar"]

    def current_user_is_admin(self) -> bool:
        return (self.api_client.current_user or {}).get("role") == "admin"

    def current_user_is_initial_admin(self) -> bool:
        user = self.api_client.current_user or {}
        return user.get("role") == "admin" and user.get("username") == INITIAL_ADMIN_USERNAME

    def ask_private_password(self, title: str) -> str | None:
        while True:
            password, ok = QInputDialog.getText(
                self,
                title,
                "请输入 6 位密码（数字、大小写字母）：",
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                return None
            password = password.strip()
            if is_six_digit_or_letter_password(password):
                return password
            QMessageBox.warning(self, "密码格式错误", "密码必须是 6 位，只能包含数字、大小写字母")

    def previous_page(self, scope: str) -> None:
        if self.current_pages[scope] > 1:
            self.current_pages[scope] -= 1
            self.render_file_scope(scope)

    def next_page(self, scope: str) -> None:
        if self.current_pages[scope] < self.total_pages(self.file_pages[scope]["files"]):
            self.current_pages[scope] += 1
            self.render_file_scope(scope)

    def set_actions_enabled(self, enabled: bool) -> None:
        for widgets in self.file_pages.values():
            for key in ["upload_button", "download_button", "delete_button", "refresh_button", "search_button", "search_type_box"]:
                widgets[key].setEnabled(enabled)
        if enabled:
            for scope in self.file_pages:
                self.render_file_scope(scope)

    def render_account_policy(self) -> None:
        if not hasattr(self, "role_box"):
            return
        self.role_box.clear()
        self.role_box.addItem("普通用户", "user")
        if self.current_user_is_initial_admin():
            self.role_box.addItem("管理员", "admin")
            self.account_subtitle.setText("初始 admin 可创建/管理管理员账号，管理员总数最多 3 个；删除账号时其文件按既有逻辑转移。")
        else:
            self.account_subtitle.setText("非初始管理员只能管理普通用户账号，无权管理管理员账号。")

    def refresh_users(self) -> None:
        if not self.current_user_is_admin():
            return
        try:
            self.users = self.api_client.list_users()
        except ApiError as exc:
            self.handle_api_error(exc)
            return
        self.render_users()

    def create_user(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()
        role = self.role_box.currentData()
        if not username:
            QMessageBox.warning(self, "创建失败", "用户名不能为空")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "创建失败", "密码至少 6 位")
            return
        try:
            self.api_client.create_user(username, password, role)
        except ApiError as exc:
            QMessageBox.warning(self, "创建失败", exc.message)
            return
        self.username_input.clear()
        self.password_input.clear()
        QMessageBox.information(self, "创建成功", "账号已创建")
        self.refresh_users()

    def update_selected_user(self, enabled: bool) -> None:
        user = self.selected_user()
        if user is None or not self.can_manage_user(user):
            return
        action = "启用" if enabled else "停用"
        reply = QMessageBox.question(
            self,
            "确认操作",
            f"确定要{action}账号 {user['username']} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api_client.set_user_enabled(user["id"], enabled)
        except ApiError as exc:
            QMessageBox.warning(self, "操作失败", exc.message)
            return
        self.refresh_users()

    def delete_selected_user(self) -> None:
        user = self.selected_user()
        if user is None or not self.can_manage_user(user, delete=True):
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除账号 {user['username']} 吗？该操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.api_client.delete_user(user["id"])
        except ApiError as exc:
            QMessageBox.warning(self, "删除失败", exc.message)
            return
        QMessageBox.information(self, "删除成功", "账号已删除")
        self.refresh_users()
        self.refresh_files()

    def selected_user(self) -> dict | None:
        row = self.account_table.currentRow()
        if row < 0 or row >= len(self.users):
            QMessageBox.information(self, "请选择账号", "请先选择一个账号")
            return None
        return self.users[row]

    def can_manage_user(self, user: dict, delete: bool = False) -> bool:
        current_user = self.api_client.current_user or {}
        if user["id"] == current_user.get("id"):
            message = "不能删除当前登录账号" if delete else "不能停用/启用当前登录账号"
            QMessageBox.warning(self, "操作不可用", message)
            return False
        if user["role"] == "admin" and user["username"] == INITIAL_ADMIN_USERNAME:
            QMessageBox.warning(self, "操作不可用", "初始 admin 账号不可删除或停用")
            return False
        if user["role"] == "admin" and not self.current_user_is_initial_admin():
            QMessageBox.warning(self, "权限不足", "只有初始 admin 可以管理管理员账号")
            return False
        return True

    def render_users(self) -> None:
        self.account_table.setRowCount(len(self.users))
        for row, user in enumerate(self.users):
            values = [
                user["id"],
                user["username"],
                "管理员" if user["role"] == "admin" else "普通用户",
                "启用" if user["enabled"] else "已停用",
                self.format_time(user["created_at"]),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column in {0, 2, 3}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.account_table.setItem(row, column, item)
        self.account_table.resizeColumnsToContents()

    def handle_api_error(self, exc: ApiError) -> None:
        if exc.status_code == 401:
            QMessageBox.warning(self, "登录已失效", exc.message)
            self.logout_requested.emit()
            return
        QMessageBox.warning(self, "请求失败", exc.message)

    def total_pages(self, files: list[dict]) -> int:
        return max(1, (len(files) + self.page_size - 1) // self.page_size)

    @staticmethod
    def format_size(size: int) -> str:
        value = float(size)
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
            value /= 1024
        return f"{size} B"

    @staticmethod
    def format_time(value: str) -> str:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            return str(value)
