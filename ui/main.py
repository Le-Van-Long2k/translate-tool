import sys
from pathlib import Path

import resources_rc
from PySide6.QtWidgets import QApplication

from controller.MainWindow_controller import MainWindowController
from controller.splash_screen_controller import SplashScreenController

def load_qss_theme():
    qss_path = Path(__file__).resolve().parent / "styles.qss"
    if qss_path.exists():
        return qss_path.read_text(encoding="utf-8")
    return ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(load_qss_theme())

    window = MainWindowController()
    window.setEnabled(False)

    splash = SplashScreenController(main_window=window)
    splash.show()

    sys.exit(app.exec())