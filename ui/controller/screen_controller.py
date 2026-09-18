from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QWidget

from ui.ui_screen_popup import Ui_screen_translate_form


class ScreenModeController(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.offset = QPoint()

        self.popup = QWidget()
        self.popup.setWindowTitle("Dịch màn hình")
        self.popup.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.popup.resize(360, 220)

        self.ui = Ui_screen_translate_form()
        self.ui.setupUi(self.popup)
        self.popup.closeEvent = self._handle_popup_close
        self.popup.hide()

    def _handle_popup_close(self, event):
        if self.main_window is not None and hasattr(self.main_window, "reset_to_default_mode"):
            self.main_window.reset_to_default_mode()
        event.accept()

    def show(self):
        self.popup.show()
        self.popup.raise_()

    def hide(self):
        self.popup.hide()
