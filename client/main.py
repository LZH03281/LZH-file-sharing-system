import sys

from PyQt6.QtWidgets import QApplication

from api_client.client import ApiClient
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    api_client = ApiClient()

    login_window = LoginWindow(api_client)
    main_window = MainWindow(api_client)

    def open_main_window() -> None:
        main_window.refresh_files()
        main_window.show()
        login_window.hide()

    def logout() -> None:
        api_client.logout()
        main_window.hide()
        login_window.show()

    login_window.login_success.connect(open_main_window)
    main_window.logout_requested.connect(logout)

    login_window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
