from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BoxChatResultPopup(QWidget):
    def __init__(self, title: str = "Translate Box Chat"):
        super().__init__()
        self.dragging = False
        self.offset = QPoint()

        self.setWindowTitle(title)
        flags = (
            Qt.Tool
            | Qt.CustomizeWindowHint
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )

        self.setWindowFlags(flags)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(320, 140)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)

        self.text_label = QLabel("Translated text")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet(
            "font-size: 20px; font-weight: 600; color: white; background: rgba(0, 0, 0, 90); border: 1px solid rgba(255,255,255,60); border-radius: 12px; padding: 12px;"
        )
        self.layout.addWidget(self.text_label)

    def set_text(self, text: str):
        self.text_label.setText(text)

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
