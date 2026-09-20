import io

import requests
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QWidget

from controller.box_chat_controller import BoxChatModeController
from controller.comic_controller import ComicModeController
from controller.screen_controller import ScreenModeController
from ui.ui_MainWindow import Ui_Form
from utils.backend_url import (
    DEFAULT_BACKEND_PORT,
    LOCALHOST_BACKEND_HOSTS,
    build_backend_url,
    update_backend_host,
)

from services.docker_manager import DockerManager

class MainWindowController(QWidget):
    """Main window controller for choosing a translate mode."""

    def __init__(self):
        super().__init__()

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setFixedSize(self.size())

        self.is_running = False
        self.backend_is_running = False
        self.backend_host_index = 0
        self.backend_host = LOCALHOST_BACKEND_HOSTS[self.backend_host_index]
        self._closing = False
        self._closing_dialog = None
        self.popup_map = {
            "Dịch màn hình": ScreenModeController(self),
            "Dịch chat game": BoxChatModeController(self),
            "Dịch truyện tranh": ComicModeController(self),
        }
        self.docker = DockerManager(project_dir="/mnt/c/Users/PC/translate-tool/backend")

        self._docker_start_thread = self.docker.start(
            callback=lambda line: print(line),
            finished_callback=lambda code: print("Docker start finished:", code),
        )

        self.ui.comboBox_mode.currentIndexChanged.connect(self.on_mode_changed)

        self.backend_status_timer = QTimer(self)
        self.backend_status_timer.setInterval(5000)
        self.backend_status_timer.timeout.connect(self.check_backend_status)
        self.check_backend_status()
        self.backend_status_timer.start()

        self.reset_to_default_mode()

    def _show_closing_dialog(self):
        if self._closing_dialog is not None:
            if self._closing_dialog.isVisible():
                return
            self._closing_dialog.deleteLater()

        self._closing_dialog = QProgressDialog(
            "Đang đóng ứng dụng...",
            "",
            0,
            0,
            self,
        )
        self._closing_dialog.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self._closing_dialog.setWindowFlag(Qt.WindowType.Tool, True)
        self._closing_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._closing_dialog.setAutoClose(False)
        self._closing_dialog.setAutoReset(False)
        self._closing_dialog.setCancelButton(None)
        self._closing_dialog.setMinimumDuration(0)
        self._closing_dialog.setValue(0)
        self._closing_dialog.show()
        self._closing_dialog.raise_()
        self._closing_dialog.activateWindow()
        QApplication.processEvents()

    def closeEvent(self, event):
        print("Closing application...")

        if self._closing:
            event.accept()
            return

        self._closing = True

        if self.backend_status_timer.isActive():
            self.backend_status_timer.stop()

        self._show_closing_dialog()

        try:
            return_code = self.docker.stop_sync(
                callback=lambda line: print(line)
            )
            print("Docker stop finished:", return_code)
        except Exception as exc:
            print("Docker stop failed:", exc)

        try:
            shutdown_code = self.docker.shutdown_wsl(
                callback=lambda line: print(line)
            )
            print("WSL shutdown finished:", shutdown_code)
        except Exception as exc:
            print("WSL shutdown unavailable:", exc)
        finally:
            if self._closing_dialog is not None:
                self._closing_dialog.close()
                self._closing_dialog.deleteLater()
                self._closing_dialog = None

        event.accept()
        
    @staticmethod
    def is_backend_healthy_payload(payload):
        if payload.get("status") == "ok":
            return True
        return False

    def _set_backend_status(self, is_running):
        self.backend_is_running = is_running
        color = "#22c55e" if is_running else "#dc2626"
        dot_text = "●"
        status_text = "Backend đang chạy" if is_running else "Backend không hoạt động"

        font = self.ui.label_radio_check_backend.font()
        font.setPointSize(18)
        font.setBold(True)
        self.ui.label_radio_check_backend.setFont(font)
        self.ui.label_radio_check_backend.setText(dot_text)
        self.ui.label_radio_check_backend.setStyleSheet(f"color: {color};")

        self.ui.label_check_status_backend.setText(status_text)
        self.ui.label_check_status_backend.setStyleSheet(f"color: {color};")

        self.ui.comboBox_translate_engine.setEnabled(is_running)
        self.ui.comboBox_mode.setEnabled(is_running)

        if not is_running:
            self.reset_to_default_mode()
            for popup in self.popup_map.values():
                popup.hide()
        else:
            self.refresh_mode_button_state()

    def check_backend_status(self):
        host = self.backend_host
        health_url = f"http://{host}:{DEFAULT_BACKEND_PORT}/health_check"

        try:
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            payload = response.json() if "application/json" in content_type.lower() else {}
        except Exception:
            payload = {}

        if self.is_backend_healthy_payload(payload):
            update_backend_host(host)
            self.backend_host = host
            self._set_backend_status(True)
            return

        next_index = (self.backend_host_index + 1) % len(LOCALHOST_BACKEND_HOSTS)
        self.backend_host_index = next_index
        self.backend_host = LOCALHOST_BACKEND_HOSTS[next_index]
        self._set_backend_status(False)

    def refresh_mode_button_state(self):
        mode_name = self.ui.comboBox_mode.currentText()

    def reset_to_default_mode(self):
        self.is_running = False
        self.ui.comboBox_mode.blockSignals(True)
        if self.ui.comboBox_mode.currentIndex() != 0:
            self.ui.comboBox_mode.setCurrentIndex(0)
        self.ui.comboBox_mode.blockSignals(False)
        self.refresh_mode_button_state()

        for popup in self.popup_map.values():
            popup.hide()

    def on_mode_changed(self, index):
        del index
        mode_name = self.ui.comboBox_mode.currentText()

        if mode_name == "Vui lòng chọn chế độ":
            self.refresh_mode_button_state()
            return

        if mode_name == "Dịch chat game":
            answer = QMessageBox.question(
                self,
                "Xác nhận",
                "Bạn muốn chọn vùng OCR để dịch chat game?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Ok:
                self.reset_to_default_mode()
                return

            box_chat_popup = self.popup_map.get(mode_name)
            if isinstance(box_chat_popup, BoxChatModeController):
                box_chat_popup.start_box_chat_selection()

        self.refresh_mode_button_state()

        for popup_name, popup in self.popup_map.items():
            popup.hide()

        popup = self.popup_map.get(mode_name)
        if popup is not None:
            popup.show()
            popup.raise_()

    def on_start_stop_clicked(self):
        mode_name = self.ui.comboBox_mode.currentText()
        if mode_name in ("", "Vui lòng chọn chế độ"):
            return

        self.is_running = not self.is_running
        action = "Dừng" if self.is_running else "Bắt đầu"

    def _update_mode_state(self):
        self.on_mode_changed(0)
