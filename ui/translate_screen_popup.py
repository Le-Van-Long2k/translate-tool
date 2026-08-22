from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class ScreenResultPopup(QWidget):
    def __init__(self, title: str = "Translate Screen"):
        super().__init__()
        self.dragging = False
        self.offset = QPoint()

        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.Tool | Qt.CustomizeWindowHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(360, 220)

        self.container = QFrame(self)
        self.container.setObjectName("popup_container")
        self.container.setStyleSheet(
            """
            QFrame#popup_container {
                background: rgba(15, 20, 28, 180);
                border: 1px solid rgba(85, 170, 255, 110);
                border-radius: 12px;
            }
            QLabel { color: white; }
            """
        )

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.addWidget(self.container)

        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(12, 12, 12, 12)
        self.inner_layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: white;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background: rgba(255,255,255,10); border: 1px solid rgba(255,255,255,50); border-radius: 8px;"
        )

        self.inner_layout.addWidget(self.title_label)
        self.inner_layout.addWidget(self.image_label)

    def set_image(self, image: QImage):
        if image is None or image.isNull():
            return

        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
