import io

import requests
from PySide6.QtCore import QBuffer, QIODevice, QByteArray, QPoint, QRect, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from utils.ScreenSelector import ScreenSelector
from ui.ui_box_chat_popup import Ui_box_chat_translate_form


class BoxChatOCRWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, image):
        super().__init__()
        self.image = image

    def run(self):
        try:
            if self.image is None or self.image.isNull() or self.image.width() <= 1 or self.image.height() <= 1:
                self.error.emit("screen capture image is empty")
                return

            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            self.image.save(buffer, "PNG")
            buffer.close()

            files = {"file": ("box_chat_ocr.png", byte_array.data(), "image/png")}
            response = requests.post(
                "http://127.0.0.1:8052/translate_one_box_chat",
                files=files,
                timeout=30,
            )
            response.raise_for_status()

            payload = response.json() if response.headers.get("Content-Type", "").lower().startswith("application/json") else {"text": response.text}
            if isinstance(payload, dict):
                text = payload.get("translated") or payload.get("text") or payload.get("original")
            else:
                text = str(payload)

            if text:
                self.finished.emit(str(text))
            else:
                self.error.emit("backend returned empty OCR result")
        except Exception as exc:
            self.error.emit(str(exc))


class BoxChatModeController(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.offset = QPoint()
        self._box_chat_selector = None
        self._selected_ocr_rect = None
        self._last_box_chat_text = ""
        self._ocr_worker = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(5000)
        self._refresh_timer.timeout.connect(self._refresh_box_chat_region)

        self.popup = QWidget()
        self.popup.setWindowTitle("Dịch chat game")
        self.popup.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.popup.resize(320, 140)

        self.ui = Ui_box_chat_translate_form()
        self.ui.setupUi(self.popup)
        self.ui.result_label.setText("Đang chờ kết quả...")
        self.popup.closeEvent = self._handle_popup_close
        self.popup.hide()

    def _handle_popup_close(self, event):
        self._refresh_timer.stop()
        if self.main_window is not None and hasattr(self.main_window, "reset_to_default_mode"):
            self.main_window.reset_to_default_mode()
        event.accept()

    def show(self):
        self.popup.show()
        self.popup.raise_()

    def hide(self):
        self._refresh_timer.stop()
        self.popup.hide()

    def _capture_selected_region(self):
        if self._selected_ocr_rect is None:
            return None

        rect = self._selected_ocr_rect
        if rect.isEmpty() or rect.width() <= 1 or rect.height() <= 1:
            return None

        screen = QApplication.screenAt(rect.center())
        if screen is None:
            return None

        screen_rect = screen.geometry()
        local_rect = QRect(rect.topLeft() - screen_rect.topLeft(), rect.size())
        pixmap = screen.grabWindow(0, screen_rect.x(), screen_rect.y(), screen_rect.width(), screen_rect.height())
        if pixmap.isNull():
            return None

        image = pixmap.toImage()
        if image.isNull():
            return None

        dpr = pixmap.devicePixelRatio()
        pixel_rect = QRect(
            round(local_rect.x() * dpr),
            round(local_rect.y() * dpr),
            round(local_rect.width() * dpr),
            round(local_rect.height() * dpr),
        ).intersected(image.rect())

        if pixel_rect.isEmpty():
            return None

        return image.copy(pixel_rect)

    def _refresh_box_chat_region(self):
        if self._selected_ocr_rect is None:
            self._refresh_timer.stop()
            return
        if self._ocr_worker is not None and self._ocr_worker.isRunning():
            return

        image = self._capture_selected_region()
        if image is None or image.isNull() or image.width() <= 1 or image.height() <= 1:
            self.ui.result_label.setText("Lỗi OCR: không capture được màn hình")
            return

        self.ui.result_label.setText("Đang dịch...")
        self._start_box_chat_ocr(image)

    def start_box_chat_selection(self):
        self._refresh_timer.stop()
        if self._box_chat_selector is None:
            self._box_chat_selector = ScreenSelector()
            self._box_chat_selector.area_selected.connect(self._on_box_chat_region_selected)

        self._box_chat_selector.start_capture()

    def _on_box_chat_region_selected(self, rect, image):
        self._selected_ocr_rect = rect
        if image is None or image.isNull() or image.width() <= 1 or image.height() <= 1:
            self.ui.result_label.setText("Lỗi OCR: không capture được màn hình")
            QMessageBox.warning(
                self,
                "Lỗi capture",
                "Không thể capture vùng màn hình. Vui lòng thử lại.",
            )
            self._refresh_timer.stop()
            return

        self.ui.result_label.setText("Đang dịch...")
        self._start_box_chat_ocr(image)
        self._refresh_timer.start(5000)

    def _start_box_chat_ocr(self, image):
        if self._ocr_worker is not None and self._ocr_worker.isRunning():
            return

        self._ocr_worker = BoxChatOCRWorker(image)
        self._ocr_worker.finished.connect(self._on_box_chat_ocr_finished)
        self._ocr_worker.error.connect(self._on_box_chat_ocr_error)
        self._ocr_worker.start()

    def _on_box_chat_ocr_finished(self, text):
        try:
            if self._ocr_worker is not None and self._ocr_worker.isFinished():
                self._ocr_worker = None
        finally:
            if text:
                self._last_box_chat_text = text
                self.ui.result_label.setText(text)

    def _on_box_chat_ocr_error(self, error_message):
        try:
            if self._ocr_worker is not None and self._ocr_worker.isFinished():
                self._ocr_worker = None
        finally:
            message = str(error_message or "")
            lowered = message.lower()

            if "screen capture image is empty" in lowered or "capture" in lowered:
                self.ui.result_label.setText("Lỗi OCR: không capture được màn hình")
            elif "empty" in lowered or "rỗng" in lowered:
                self.ui.result_label.setText("Lỗi OCR: backend trả về dữ liệu rỗng")
            elif "timeout" in lowered or "read timed out" in lowered:
                self.ui.result_label.setText("Lỗi: thời gian chờ OCR đã hết")
            else:
                self.ui.result_label.setText("Lỗi OCR: không thể dịch vùng đang chọn")

            QMessageBox.warning(
                self,
                "Lỗi OCR",
                "Không thể dịch vùng đang chọn. Vui lòng thử lại.",
            )
