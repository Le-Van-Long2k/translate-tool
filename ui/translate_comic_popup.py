from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget


class ComicResultPopup(QWidget):
    def __init__(self, title: str = "Translate Comic"):
        super().__init__()
        self.dragging = False
        self.offset = QPoint()
        self._selected_paths = []

        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.Tool | Qt.CustomizeWindowHint | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(360, 220)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: white;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background: rgba(255,255,255,10); border: 1px solid rgba(255,255,255,50); border-radius: 8px;"
        )

        self.select_btn = QPushButton("Select image(s)")
        self.select_btn.clicked.connect(self.open_file_dialog)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.image_label)
        self.layout.addWidget(self.select_btn)

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

    def open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select comic image(s)",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not paths:
            return

        self._selected_paths = paths
        self.title_label.setText(f"Translate Comic ({len(paths)} file(s))")
        first_image = QImage(paths[0])
        if not first_image.isNull():
            self.set_image(first_image)

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
