# -*- coding: utf-8 -*-

import ctypes
import sys

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget


class ScreenSelector(QWidget):
    """Overlay toàn bộ desktop, chọn vùng trong 1 monitor (tối ưu Win11)."""

    area_selected = Signal(QRect, QImage)

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.start = None               # local của overlay
        self.end = None
        self.selected_screen = None
        self.selected_screen_geo = QRect()
        self.virtual_geo = QRect()

    # ------------------------------------------------------------------
    def _apply_win11_style(self):
        if sys.platform != "win32":
            return
        hwnd = int(self.winId())
        if not hwnd:
            return

        user32 = ctypes.windll.user32
        GWL_EXSTYLE = -20
        style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style |= (
            0x00080000   # WS_EX_LAYERED
            | 0x00000008 # WS_EX_TOPMOST
            | 0x08000000 # WS_EX_NOACTIVATE
            | 0x00000080 # WS_EX_TOOLWINDOW
        )
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)

    def _desktop_union(self) -> QRect:
        rect = QRect()
        for s in QApplication.screens():
            rect = rect.united(s.geometry())
        return rect

    # ------------------------------------------------------------------
    def start_capture(self):
        self.virtual_geo = self._desktop_union()
        self.start = None
        self.end = None
        self.selected_screen = None
        self.selected_screen_geo = QRect()

        self.setGeometry(self.virtual_geo)
        self.show()
        self.raise_()
        self._apply_win11_style()
        self.setFocus()
        self.setCursor(Qt.CrossCursor)
        self.update()

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.cancel()
            return
        if event.button() != Qt.LeftButton:
            return

        global_pos = QCursor.pos()
        screen = QApplication.screenAt(global_pos)
        if screen is None:
            return

        self.selected_screen = screen
        self.selected_screen_geo = screen.geometry()

        # local của overlay
        self.start = self.mapFromGlobal(global_pos)
        self.end = self.start
        self.update()

    def mouseMoveEvent(self, event):
        if self.start is None:
            return

        # Giới hạn trong monitor đã chọn
        global_pos = QCursor.pos()
        geo = self.selected_screen_geo
        clamped = QPoint(
            max(geo.left(), min(global_pos.x(), geo.right())),
            max(geo.top(), min(global_pos.y(), geo.bottom())),
        )
        self.end = self.mapFromGlobal(clamped)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self.start is None:
            return

        rect_local = QRect(self.start, self.end).normalized()
        if rect_local.width() < 2 or rect_local.height() < 2:
            self.cancel()
            return

        # Global rect
        global_rect = QRect(
            self.mapToGlobal(rect_local.topLeft()),
            rect_local.size(),
        ).intersected(self.selected_screen_geo)

        if global_rect.isEmpty():
            self.cancel()
            return

        # Ẩn overlay
        self.hide()
        QApplication.processEvents()

        # Capture toàn bộ monitor đã chọn
        pixmap = self.selected_screen.grabWindow(0)
        if pixmap.isNull():
            self.cancel()
            return

        image = pixmap.toImage()
        if image.isNull():
            self.cancel()
            return

        # Chuyển global → local của monitor
        local_on_screen = QRect(
            global_rect.topLeft() - self.selected_screen_geo.topLeft(),
            global_rect.size(),
        )

        # DPI
        dpr = pixmap.devicePixelRatio()
        pixel_rect = QRect(
            round(local_on_screen.x() * dpr),
            round(local_on_screen.y() * dpr),
            round(local_on_screen.width() * dpr),
            round(local_on_screen.height() * dpr),
        ).intersected(image.rect())

        if pixel_rect.isEmpty():
            self.cancel()
            return

        cropped = image.copy(pixel_rect)

        self.close()
        self.area_selected.emit(global_rect, cropped)

    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Nền mờ toàn desktop
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

        if self.start is not None and self.end is not None:
            rect = QRect(self.start, self.end).normalized()

            # Đục lỗ
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Viền
            painter.setPen(QPen(QColor(255, 60, 60), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

            # Size
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                rect.adjusted(6, 6, -6, -6),
                Qt.AlignTop | Qt.AlignLeft,
                f"{rect.width()} × {rect.height()}",
            )

        painter.end()

    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.cancel()

    def cancel(self):
        self.start = None
        self.end = None
        self.selected_screen = None
        self.close()