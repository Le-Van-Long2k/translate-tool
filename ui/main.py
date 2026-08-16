# -*- coding: utf-8 -*-
import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QGraphicsScene,
)

from PySide6.QtGui import QPixmap, QImage

from PySide6.QtCore import Qt

from ScreenSelector import ScreenSelector
from MainWindow import Ui_MainWindow

import requests
from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QBuffer,
    QIODevice,
    QTimer,
)

from PySide6.QtGui import QIcon


class TranslateCommicWorker(QThread):
    finished = Signal(QImage)
    error = Signal(str)

    def __init__(self, image):
        super().__init__()
        self.image = image

    def run(self):
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            self.image.save(buffer, "PNG")
            image_bytes = bytes(buffer.data())
            buffer.close()

            response = requests.post(
                "http://localhost:8052/translate_comic",
                files={
                    "file": (
                        "screenshot.png",
                        image_bytes,
                        "image/png"
                    )
                },
                timeout=300
            )

            response.raise_for_status()

            result = QImage.fromData(response.content)

            if result.isNull():
                raise Exception("API không trả về ảnh hợp lệ")

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))

# ============================================================
# MainWindow
# ============================================================
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.selector = None
        self.selected_rect = None
        self.selected_image = None
        self.worker = None

        self.ui.Select_area_btn.clicked.connect(self.open_screen_selector)
        self.is_capturing = False
        self.ui.start_stop_btn.clicked.connect(self.toggle_capture)

        self.previous_image = None
        self.capture_timer = QTimer(self)
        self.capture_timer.setInterval(500)
        self.capture_timer.timeout.connect(self.check_capture)

        self.processing = False

    def toggle_capture(self):
        if self.is_capturing:
            self.stop_capture()
            self.is_capturing = False

            self.ui.start_stop_btn.setIcon(
                QIcon("icons/start.svg")
            )
            self.ui.start_stop_btn.setToolTip("Start Capture")

        else:
            if self.start_capture():
                self.is_capturing = True

                self.ui.start_stop_btn.setIcon(
                    QIcon("icons/stop.svg")
                )
                self.ui.start_stop_btn.setToolTip("Stop Capture")

    # =========================================================
    # CHỌN VÙNG
    # =========================================================
    def open_screen_selector(self):
        print("Opening screen selector...")

        if self.selector is None:
            self.selector = ScreenSelector()
            self.selector.area_selected.connect(self.on_area_selected)
            self.selector.region_captured.connect(self.on_region_captured)

        self.selector.start_capture()

    def on_area_selected(self, rect, image):
        print(
            f"Area selected: "
            f"{rect.x()},{rect.y()} "
            f"{rect.width()}x{rect.height()}"
        )

        self.selected_rect = rect
        self.selected_image = image

        self.previous_image = None

        self.show_image(image)

    # =========================================================
    # NÚT START → Capture + Bubble
    # =========================================================
    def start_capture(self):
        print("Start auto capture...")

        if self.selected_rect is None or self.selected_rect.isEmpty():
            QMessageBox.warning(
                self,
                "Lỗi",
                "Chưa chọn vùng. Hãy bấm Select area trước."
            )
            return False

        if not self.capture_timer.isActive():
            self.capture_timer.start()

        return True

    def stop_capture(self):
        if self.selector is not None:
            self.selector.stop_stream()
        if self.worker is not None and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(3000)
        if self.capture_timer.isActive():
            self.capture_timer.stop()

    def check_capture(self):
        if self.selected_rect is None:
            return

        # Nếu API trước đó vẫn đang xử lý thì bỏ qua frame này
        if self.processing:
            return

        if self.selector is None:
            return

        self.selector.capture_region(self.selected_rect)

    def images_equal(self, image1: QImage, image2: QImage) -> bool:
        if image1.size() != image2.size():
            return False

        img1 = image1.convertToFormat(
            QImage.Format_RGBA8888
        )

        img2 = image2.convertToFormat(
            QImage.Format_RGBA8888
        )

        ptr1 = img1.bits()
        ptr2 = img2.bits()

        data1 = bytes(ptr1)
        data2 = bytes(ptr2)

        return data1 == data2

    # =========================================================
    # NHẬN ẢNH SAU CAPTURE → CHẠY BUBBLE
    # =========================================================
    def on_region_captured(self, image: QImage):
        if image is None or image.isNull():
            print("Captured image invalid")
            return

        # =========================
        # So sánh ảnh
        # =========================
        if self.previous_image is not None:
            if self.images_equal(self.previous_image, image):
                # Không thay đổi → không làm gì
                return

        # Lưu frame hiện tại
        self.previous_image = image.copy()

        # print("Image changed → gọi API detect + OCR")

        self.processing = True

        self.worker = TranslateCommicWorker(image)

        self.worker.finished.connect(
            self.on_bubble_finished
        )

        self.worker.error.connect(
            self.on_bubble_error
        )

        self.worker.start()

    def on_bubble_finished(self, result_image: QImage):
        self.processing = False

        self.show_image(result_image)

    def on_bubble_error(self, msg: str):
        print("Lỗi:", msg)

        self.processing = False

        QMessageBox.critical(
            self,
            "Lỗi",
            f"Detect + OCR thất bại:\n{msg}"
        )

        self.stop_capture()

    # =========================================================
    # HIỂN THỊ
    # =========================================================
    def show_image(self, image: QImage):
        if image is None or image.isNull():
            print("ERROR: Image is None/Null")
            return

        # print(f"Displaying: {image.width()}x{image.height()}")
        pixmap = QPixmap.fromImage(image)
        scene = QGraphicsScene(self)
        scene.addPixmap(pixmap)
        self.ui.graphicsView.setScene(scene)
        self.ui.graphicsView.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)

    def closeEvent(self, event):
        if self.selector is not None:
            self.selector.stop_stream()
        if self.worker is not None and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(3000)
        # unload_models()
        super().closeEvent(event)


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("TranslateTool")
    app.setDesktopFileName("translate-tool")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())