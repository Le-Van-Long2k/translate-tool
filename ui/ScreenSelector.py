# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, Signal, QTimer, Slot
from PySide6.QtGui import QPainter, QPen, QColor, QImage
from PySide6.QtMultimedia import QScreenCapture, QMediaCaptureSession, QVideoSink


class ScreenSelector(QWidget):

    area_selected = Signal(QRect, QImage)
    region_captured = Signal(QImage)

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)
        self.hide()

        self.start = None
        self.end = None
        self.selected_rect = None
        self.screen_image = None

        self.mode = "select"          # "select" | "recapture"
        self.target_rect = None
        self.waiting_frame = False    # đang chờ 1 frame mới
        self.latest_frame = None

        # =====================================================
        # CAPTURE - giữ sống sau lần đầu
        # =====================================================
        self.screen_capture = QScreenCapture(self)
        self.session = QMediaCaptureSession(self)
        self.video_sink = QVideoSink(self)

        self.session.setScreenCapture(self.screen_capture)
        self.session.setVideoSink(self.video_sink)

        self.video_sink.videoFrameChanged.connect(self.on_frame)
        self.screen_capture.errorOccurred.connect(self.on_capture_error)

        self._stream_running = False

    # =========================================================
    # 1. CHỌN VÙNG MỚI
    # =========================================================
    def start_capture(self):
        self.mode = "select"
        self.waiting_frame = True
        self.start = None
        self.end = None
        self.target_rect = None

        if not self._stream_running:
            print("→ Lần đầu: Chọn Entire Screen → Share/Allow")
            self.screen_capture.setActive(True)
        else:
            print("→ Stream đang chạy, chờ frame mới nhất...")

        QTimer.singleShot(20000, self._timeout)

    # =========================================================
    # 2. CHỤP LẠI VÙNG ĐÃ LƯU (không hỏi quyền)
    # =========================================================
    def capture_region(self, rect: QRect):
        if rect is None or rect.isEmpty():
            print("ERROR: rect rỗng")
            return

        # LUÔN dùng frame mới nhất
        if self.latest_frame is None or self.latest_frame.isNull():
            print("ERROR: chưa có frame màn hình")
            return

        self.mode = "recapture"
        self.target_rect = QRect(rect)

        image = self.latest_frame

        # print(
        #     f"→ Lấy frame mới nhất: "
        #     f"{rect.x()},{rect.y()} "
        #     f"{rect.width()}x{rect.height()}"
        # )

        crop_rect = self.target_rect.intersected(
            QRect(
                0,
                0,
                image.width(),
                image.height()
            )
        )

        if crop_rect.isEmpty():
            print("ERROR: Crop rỗng")
            return

        cropped = image.copy(crop_rect)

        # cropped.save("ocr_input.png")

        # print(
        #     f"Saved: ocr_input.png "
        #     f"{cropped.width()}x{cropped.height()}"
        # )

        self.region_captured.emit(cropped)

    def _timeout(self):
        if self.waiting_frame:
            print("Timeout: không nhận được frame")
            self.waiting_frame = False
            if self.mode == "select":
                self.close()

    # =========================================================
    # NHẬN FRAME
    # =========================================================
    @Slot(object)
    def on_frame(self, frame):
        if not frame.isValid():
            return

        image = frame.toImage()

        if image.isNull():
            return

        # =====================================================
        # KHI SELECTOR ĐANG HIỂN THỊ
        # KHÔNG cập nhật frame nữa
        #
        # Vì frame lúc này đã chứa chính ScreenSelector
        # =====================================================
        if self.mode == "select" and self.isVisible():
            return

        # Frame mới nhất của màn hình thật
        self.latest_frame = image.copy()
        self._stream_running = True

        # Đang chờ frame để mở selector
        if not self.waiting_frame:
            return

        self.waiting_frame = False

        # Đóng băng frame này làm background cho selector
        self.screen_image = self.latest_frame.copy()

        print(
            f"Frame: "
            f"{self.screen_image.width()}x"
            f"{self.screen_image.height()}"
        )

        if self.mode == "select":

            self.setGeometry(
                0,
                0,
                self.screen_image.width(),
                self.screen_image.height()
            )

            self.setWindowState(Qt.WindowFullScreen)
            self.show()
            self.raise_()
            self.activateWindow()
            self.update()

    def on_capture_error(self, error, msg):
        print(f"Capture error: {error} - {msg}")
        self._stream_running = False
        self.waiting_frame = False
        if self.mode == "select":
            self.close()

    # =========================================================
    # MOUSE
    # =========================================================
    def mousePressEvent(self, event):
        if self.mode != "select" or event.button() != Qt.LeftButton:
            return
        self.start = event.position().toPoint()
        self.end = self.start
        self.update()

    def mouseMoveEvent(self, event):
        if self.mode != "select" or self.start is None:
            return
        self.end = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event):
        if self.mode != "select" or event.button() != Qt.LeftButton or self.start is None:
            return

        self.end = event.position().toPoint()
        self.selected_rect = QRect(self.start, self.end).normalized()

        print(f"Selected: {self.selected_rect.width()}x{self.selected_rect.height()}")

        if self.screen_image is None:
            return

        crop_rect = self.selected_rect.intersected(
            QRect(0, 0, self.screen_image.width(), self.screen_image.height())
        )
        if crop_rect.isEmpty():
            return

        cropped = self.screen_image.copy(crop_rect)
        # cropped.save("ocr_input.png")
        # print("Saved: ocr_input.png")

        # Đóng selector trước khi emit
        self.mode = "idle"
        self.close()

        self.area_selected.emit(crop_rect, cropped)

    # =========================================================
    # PAINT
    # =========================================================
    def paintEvent(self, event):
        if not self.screen_image or self.mode != "select":
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawImage(self.rect(), self.screen_image)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if self.start is not None and self.end is not None:
            rect = QRect(self.start, self.end).normalized()
            painter.drawImage(rect, self.screen_image, rect)

            painter.setPen(QPen(QColor(255, 50, 50), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                rect.adjusted(4, 4, -4, -4),
                Qt.AlignTop | Qt.AlignLeft,
                f"{rect.width()} × {rect.height()}"
            )

    def closeEvent(self, event):
        # Quan trọng: KHÔNG tắt screen_capture ở đây
        # để lần sau không bị hỏi quyền lại
        super().closeEvent(event)

    def stop_stream(self):
        if self.screen_capture.isActive():
            self.screen_capture.setActive(False)

        self._stream_running = False
        self.screen_image = None