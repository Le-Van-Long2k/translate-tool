import os

import requests
from PySide6.QtCore import QPoint, Qt, QThread, Signal
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import QFileDialog, QGraphicsScene, QMessageBox, QWidget

from ui.ui_comic_popup import Ui_form_comic


class DownloadComicWorker(QThread):
    progress = Signal(int, int)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, entries, save_dir):
        super().__init__()
        self.entries = entries or []
        self.save_dir = save_dir

    def run(self):
        try:
            valid_count = 0
            total = len(self.entries)
            for index, (filename, image) in enumerate(self.entries, start=1):
                if image is None or image.isNull():
                    self.progress.emit(index, total)
                    continue
                out_path = os.path.join(self.save_dir, filename)
                image.save(out_path)
                valid_count += 1
                self.progress.emit(index, total)
            self.finished.emit(valid_count)
        except Exception as exc:
            self.error.emit(str(exc))


class ComicSelectionWorker(QThread):
    progress = Signal(int, int)
    image_processed = Signal(str, QImage)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, selected_paths):
        super().__init__()
        self.selected_paths = selected_paths or []

    def run(self):
        try:
            if not self.selected_paths:
                self.finished.emit([])
                return

            entries = []
            total = len(self.selected_paths)
            for index, path in enumerate(self.selected_paths, start=1):
                if not os.path.isfile(path):
                    continue

                filename = os.path.basename(path)
                fallback_image = QImage(path)

                try:
                    with open(path, "rb") as image_file:
                        image_bytes = image_file.read()

                    response = requests.post(
                        "http://127.0.0.1:8052/translate_comic",
                        files={"file": (filename, image_bytes, "application/octet-stream")},
                        timeout=300,
                    )
                    response.raise_for_status()

                    image = QImage.fromData(response.content)
                    if image.isNull():
                        image = fallback_image
                except Exception:
                    image = fallback_image

                if image is None or image.isNull():
                    self.progress.emit(index, total)
                    continue

                entries.append((filename, image))
                self.image_processed.emit(filename, image)
                self.progress.emit(index, total)

            self.finished.emit(entries)
        except Exception as exc:
            self.error.emit(str(exc))


class ComicModeController(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.offset = QPoint()
        self._selected_paths = []
        self._translated_entries = []
        self._translated_images = []
        self._navigation_images = []
        self._navigation_index = -1
        self._current_image = None
        self._zoom_factor = 1.0
        self._download_mode = False

        self.popup = QWidget()
        self.popup.setWindowTitle("Dịch truyện tranh")
        self.popup.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        self.popup.resize(1101, 891)

        self.ui = Ui_form_comic()
        self.ui.setupUi(self.popup)

        self.graphics_scene = QGraphicsScene(self.popup)
        self.ui.graphicsView.setScene(self.graphics_scene)
        self.ui.graphicsView.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.ui.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.ui.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.ui.graphicsView.setFrameShape(self.ui.graphicsView.Shape.NoFrame)
        self.ui.graphicsView.setBackgroundBrush(Qt.transparent)
        self.ui.graphicsView.setStyleSheet("QGraphicsView { background: transparent; border: none; }")
        self.ui.graphicsView.setDragMode(self.ui.graphicsView.DragMode.ScrollHandDrag)
        self.ui.graphicsView.setTransformationAnchor(self.ui.graphicsView.ViewportAnchor.AnchorUnderMouse)
        self.ui.graphicsView.setResizeAnchor(self.ui.graphicsView.ViewportAnchor.AnchorUnderMouse)
        self.ui.graphicsView.setViewportUpdateMode(self.ui.graphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.ui.graphicsView.installEventFilter(self)

        self.ui.select_img_btn.clicked.connect(self.open_file_dialog)
        self.ui.download_btn.clicked.connect(self.download_selected_images)

        self.popup.closeEvent = self._handle_popup_close
        self.popup.hide()

    def _handle_popup_close(self, event):
        if self.main_window is not None and hasattr(self.main_window, "reset_to_default_mode"):
            self.main_window.reset_to_default_mode()
        event.accept()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress and obj is self.ui.graphicsView:
            if event.key() == Qt.Key_Left:
                self.go_to_previous_image()
                return True
            if event.key() == Qt.Key_Right:
                self.go_to_next_image()
                return True

        if event.type() == event.Type.Wheel and obj is self.ui.graphicsView:
            if not event.modifiers() & Qt.ControlModifier:
                return False

            delta = event.angleDelta().y()
            if delta == 0:
                return False

            factor = 1.1 if delta > 0 else 1.0 / 1.1
            self._zoom_factor = max(0.25, min(5.0, self._zoom_factor * factor))
            pos = event.position()
            self.ui.graphicsView.setTransformationAnchor(self.ui.graphicsView.ViewportAnchor.AnchorUnderMouse)
            self.ui.graphicsView.scale(factor, factor)
            self.ui.graphicsView.centerOn(self.ui.graphicsView.mapToScene(int(pos.x()), int(pos.y())))
            return True

        return super().eventFilter(obj, event)

    def _update_status_label(self, text: str):
        self.ui.status_label.setText(text)

    def _sync_navigation_buttons(self):
        total = len(self._navigation_images)
        if total > 0 and self._navigation_index >= 0:
            self._update_status_label(f"Ảnh {self._navigation_index + 1}/{total}")
        elif total > 0:
            self._update_status_label(f"{total} ảnh đã dịch")
        else:
            self._update_status_label("Chưa có ảnh nào")

    def _refresh_image_view(self):
        if self._current_image is None or self._current_image.isNull():
            return

        pixmap = QPixmap.fromImage(self._current_image)
        self.graphics_scene.clear()
        item = self.graphics_scene.addPixmap(pixmap)
        item.setPos(0, 0)
        self.graphics_scene.setSceneRect(self.graphics_scene.itemsBoundingRect())
        self.ui.graphicsView.setSceneRect(self.graphics_scene.sceneRect())
        self.ui.graphicsView.resetTransform()
        self.ui.graphicsView.setDragMode(self.ui.graphicsView.DragMode.ScrollHandDrag)
        self.ui.graphicsView.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
        self.ui.graphicsView.centerOn(item)

    def set_image(self, image: QImage):
        if image is None or image.isNull():
            return

        self._current_image = image.copy()
        self._zoom_factor = 1.0
        self._refresh_image_view()

    def go_to_previous_image(self):
        if not self._navigation_images:
            return
        if self._navigation_index <= 0:
            return
        self._navigation_index -= 1
        self.set_image(self._navigation_images[self._navigation_index])
        self._sync_navigation_buttons()

    def go_to_next_image(self):
        if not self._navigation_images:
            return
        if self._navigation_index >= len(self._navigation_images) - 1:
            return
        self._navigation_index += 1
        self.set_image(self._navigation_images[self._navigation_index])
        self._sync_navigation_buttons()

    def set_download_state(self, is_translating: bool, current: int = 0, total: int = 0):
        if is_translating:
            if total > 0:
                self._update_status_label(f"Đang xử lý {current}/{total}")
            else:
                self._update_status_label("Đang xử lý...")
            self.ui.download_btn.setEnabled(False)
        else:
            self.ui.download_btn.setEnabled(True)
            self.ui.download_btn.setText("Tải xuống")
            if self._navigation_images:
                self._sync_navigation_buttons()
            elif self._translated_images:
                self._update_status_label(f"{len(self._translated_images)} ảnh đã dịch")
            else:
                self._update_status_label("Chưa có ảnh nào")

    def set_preview_images(self, images):
        self._translated_images = list(images or [])
        self._navigation_images = self._translated_images
        if self._navigation_index < 0 and self._navigation_images:
            self._navigation_index = 0
        self._sync_navigation_buttons()
        if self._navigation_images and self._navigation_index >= 0:
            if self._current_image is None:
                self.set_image(self._navigation_images[self._navigation_index])
        else:
            self._update_status_label(f"{len(self._translated_images)} ảnh đã dịch")
        self.set_download_state(False)

    def open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self.popup,
            "Chọn ảnh truyện tranh",
            "",
            "Ảnh (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not paths:
            return

        self._selected_paths = paths
        self._translated_entries = []
        self._translated_images = []
        self._navigation_images = []
        self._navigation_index = -1
        self.popup.setWindowTitle(f"Dịch truyện tranh ({len(paths)} ảnh)")
        self._update_status_label(f"Đang xử lý 0/{len(paths)}")
        self.set_download_state(True, 0, len(paths))

        self.process_comic_selection(paths)

        first_image = QImage(paths[0])
        if not first_image.isNull():
            self.set_image(first_image)

    def process_comic_selection(self, paths):
        self._translated_entries = []
        self._translated_images = []
        self.set_download_state(True, 0, len(paths))
        self._update_status_label(f"Đang xử lý 0/{len(paths)}")

        self.comic_worker = ComicSelectionWorker(paths)
        self.comic_worker.progress.connect(self.on_comic_selection_progress)
        self.comic_worker.image_processed.connect(self.on_comic_selection_image_processed)
        self.comic_worker.finished.connect(self.on_comic_selection_finished)
        self.comic_worker.error.connect(self.on_comic_selection_error)
        self.comic_worker.start()

    def on_comic_selection_progress(self, current: int, total: int):
        self.set_download_state(True, current, total)
        self._update_status_label(f"Đang xử lý {current}/{total}")

    def on_comic_selection_image_processed(self, filename: str, image: QImage):
        self._translated_entries.append((filename, image))
        self._translated_images.append(image)
        self._navigation_images = list(self._translated_images)
        if self._navigation_index < 0 and self._navigation_images:
            self._navigation_index = 0
            self.set_image(self._navigation_images[self._navigation_index])
        self._update_status_label(f"Đã dịch {len(self._translated_images)}/{len(self._selected_paths)}")
        self._sync_navigation_buttons()

    def on_comic_selection_finished(self, entries):
        self._translated_entries = list(entries)
        self._translated_images = [img for _, img in entries]
        self.set_preview_images(self._translated_images)
        self.set_download_state(False)

    def on_comic_selection_error(self, msg: str):
        self._translated_entries = []
        self._translated_images = []
        self.set_download_state(False)
        self._update_status_label("Lỗi xử lý ảnh")
        QMessageBox.warning(self.popup, "Lỗi", f"API thất bại khi xử lý ảnh:\n{msg}")

    def download_selected_images(self):
        entries = self._translated_entries if self._translated_entries else []
        if not entries:
            QMessageBox.information(self.popup, "Tải xuống", "Chưa có ảnh đã xử lý để tải xuống.")
            return

        save_dir = QFileDialog.getExistingDirectory(
            self.popup,
            "Chọn thư mục lưu ảnh",
            os.path.dirname(self._selected_paths[0]) if self._selected_paths else "",
        )
        if not save_dir:
            return

        self._download_mode = True
        self.set_download_state(True, 0, len(entries))
        self._update_status_label(f"Đang tải xuống 0/{len(entries)}")
        self.ui.download_btn.setEnabled(False)

        self.download_worker = DownloadComicWorker(entries, save_dir)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()

    def on_download_progress(self, current: int, total: int):
        self.set_download_state(True, current, total)
        self._update_status_label(f"Đang tải xuống {current}/{total}")

    def on_download_finished(self, count: int):
        self._download_mode = False
        self.set_download_state(False)
        self._update_status_label(f"Đã tải xuống {count} ảnh")
        QMessageBox.information(self.popup, "Tải xuống", f"Đã tải xuống {count} ảnh.")

    def on_download_error(self, msg: str):
        self._download_mode = False
        self.set_download_state(False)
        self._update_status_label("Không thể tải xuống ảnh")
        QMessageBox.critical(self.popup, "Tải xuống", f"Không thể tải xuống ảnh:\n{msg}")

    def show(self):
        self.popup.show()
        self.popup.raise_()

    def hide(self):
        self.popup.hide()

    def closeEvent(self, event):
        self.popup.close()
        event.accept()
