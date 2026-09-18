from PySide6.QtCore import QPoint, QRect
from PySide6.QtWidgets import QApplication

from utils.ScreenSelector import ScreenSelector


def test_clamp_point_to_screen_rect():
    app = QApplication.instance() or QApplication([])
    selector = ScreenSelector()

    screen_rect = QRect(1920, 100, 1280, 1024)
    clamped = selector._clamp_point_to_rect(QPoint(2500, 1200), screen_rect)

    assert clamped == QPoint(2500, 1123)
    app.processEvents()


def test_screen_local_rect_uses_screen_origin_offset():
    app = QApplication.instance() or QApplication([])
    selector = ScreenSelector()

    screen_rect = QRect(1920, 100, 1280, 1024)
    global_rect = QRect(2000, 150, 200, 120)

    local_rect = selector._to_screen_local_rect(global_rect, screen_rect)

    assert local_rect == QRect(80, 50, 200, 120)
    app.processEvents()
