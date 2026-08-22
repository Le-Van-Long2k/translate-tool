# -*- coding: utf-8 -*-
import sys
import subprocess
import time

import os
from io import BytesIO

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QScrollArea,
    QGraphicsScene,
    QGraphicsView,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtGui import QPixmap, QImage, QIcon, QPainter

from PySide6.QtCore import (
    QBuffer,
    QFile,
    QIODevice,
    QPoint,
    QSize,
    QThread,
    QTimer,
    Qt,
    Signal,
)

from ScreenSelector import ScreenSelector
from MainWindow import Ui_MainWindow

import requests


class TranslationModeRequestBuilder:
    @staticmethod
    def _mime_for(filename: str) -> str:
        name = (filename or "").lower()
        if name.endswith(".png"):
            return "image/png"
        if name.endswith(".jpg") or name.endswith(".jpeg"):
            return "image/jpeg"
        if name.endswith(".webp"):
            return "image/webp"
        if name.endswith(".bmp"):
            return "image/bmp"
        return "application/octet-stream"

    @classmethod
    def build(cls, image_bytes: bytes, mode_name: str, selected_paths=None, filename: str = "capture.png"):
        mode_name = (mode_name or "").strip()
        selected_paths = selected_paths or []

        if mode_name == "Translate Box Chat":
            return {
                "endpoint": "http://localhost:8052/translate_one_box_chat",
                "filename": filename,
                "files": {"file": (filename, image_bytes, cls._mime_for(filename))},
            }

        return {
            "endpoint": "http://localhost:8052/translate_comic",
            "filename": filename,
            "files": {"file": (filename, image_bytes, cls._mime_for(filename))},
        }


class PopupWindow(QWidget):
    def __init__(self, ui_file_name, title, popup_type, parent_window=None):
        super().__init__()
        self.popup_type = popup_type
        self.parent_window = parent_window
        self.dragging = False
        self.offset = QPoint()
        self._selected_paths = []
        self._current_image = None
        self._translated_images = []
        self._translated_entries = []
        self._navigation_images = []
        self._navigation_index = -1
        self._is_translating = False
        self._zoom_factor = 1.0
        self.image_scroll_area = None
        self.graphics_view = None
        self.graphics_scene = None
        self._popup_size = {"screen": (360, 220), "chat": (320, 140), "comic": (1101, 891)}.get(popup_type, (360, 220))

        ui_path = os.path.join(os.path.dirname(__file__), ui_file_name)
        loader = QUiLoader()
        ui_file = QFile(ui_path)
        self._ui = None
        if ui_file.exists():
            ui_file.open(QFile.ReadOnly)
            loaded_widget = loader.load(ui_file)
            ui_file.close()
            if loaded_widget is not None:
                self._ui = loaded_widget
                self._ui.hide()
                self._ui.setParent(None)
                self._ui.deleteLater()
                self._ui = None

        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(*self._popup_size)
        self.setMinimumSize(*self._popup_size)
        self.setMaximumSize(*self._popup_size)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #F8FAFC;")
        self.main_layout.addWidget(self.title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(0, 0)
        self.image_label.setStyleSheet(
            "background: rgba(15,23,42,0.8); border: 1px solid rgba(251,191,36,0.9); border-radius: 8px;"
        )
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMouseTracking(True)
        self.image_label.installEventFilter(self)

        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("color: #F8FAFC;")
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.select_btn = QPushButton("Select image(s)" if self.popup_type == "comic" else "Select area")
        self.download_btn = QPushButton("Download")
        self.select_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.select_btn.setMinimumHeight(36)
        self.download_btn.setMinimumHeight(36)

        if self.popup_type == "comic":
            self.graphics_scene = QGraphicsScene(self)
            self.graphics_view = QGraphicsView(self)
            self.graphics_view.setScene(self.graphics_scene)
            self.graphics_view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.graphics_view.setFrameShape(self.graphics_view.Shape.NoFrame)
            self.graphics_view.setBackgroundBrush(Qt.transparent)
            self.graphics_view.setStyleSheet("QGraphicsView { background: transparent; border: none; }")
            self.graphics_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.graphics_view.setMinimumHeight(220)
            self.graphics_view.setDragMode(self.graphics_view.DragMode.ScrollHandDrag)
            self.graphics_view.setTransformationAnchor(self.graphics_view.ViewportAnchor.AnchorUnderMouse)
            self.graphics_view.setResizeAnchor(self.graphics_view.ViewportAnchor.AnchorUnderMouse)
            self.graphics_view.setViewportUpdateMode(self.graphics_view.ViewportUpdateMode.FullViewportUpdate)
            self.graphics_view.installEventFilter(self)
            self.main_layout.addWidget(self.graphics_view)

            self.text_label.setText("0 file selected")
            self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.main_layout.addWidget(self.text_label)

            self.select_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.select_btn.setMinimumHeight(36)
            self.main_layout.addWidget(self.select_btn)

            self.download_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.download_btn.setMinimumHeight(36)
            self.main_layout.addWidget(self.download_btn)
        elif self.popup_type == "chat":
            self.text_label.setStyleSheet(
                "font-size: 20px; font-weight: 600; color: white; background: #0F172A; border: 1px solid rgba(148,163,184,0.7); border-radius: 12px; padding: 12px;"
            )
            self.main_layout.addWidget(self.text_label)
        else:
            self.main_layout.addWidget(self.image_label)

        self.select_btn.clicked.connect(self.open_file_dialog)
        self.download_btn.clicked.connect(self.download_selected_images)

        self._apply_mode_style()

    def _apply_mode_style(self):
        base_bg = "#0F172A"
        panel_bg = "#111827"
        accent_screen = "#3B82F6"
        accent_comic = "#FBBF24"
        border = "rgba(148, 163, 184, 0.7)"

        if self.popup_type == "screen":
            self.setStyleSheet(
                f"QWidget {{ background: {base_bg}; border: 1px solid {accent_screen}; border-radius: 12px; }} "
                "QLabel { color: #E2E8F0; } "
                f"QPushButton {{ background: {panel_bg}; color: #F8FAFC; border: 1px solid {border}; border-radius: 8px; padding: 6px 12px; }} "
                "QPushButton:hover { background: #334155; }"
            )
        elif self.popup_type == "chat":
            self.setStyleSheet(
                f"QWidget {{ background: {base_bg}; border: 1px solid {border}; border-radius: 12px; }} "
                "QLabel { color: #F8FAFC; } "
                f"QPushButton {{ background: {panel_bg}; color: #F8FAFC; border: 1px solid {border}; border-radius: 8px; padding: 6px 12px; }} "
                "QPushButton:hover { background: #334155; }"
            )
        else:
            self.setStyleSheet(
                f"QWidget {{ background: {base_bg}; border: 1px solid {accent_comic}; border-radius: 12px; }} "
                "QLabel { color: #F8FAFC; } "
                f"QPushButton {{ background: {panel_bg}; color: #F8FAFC; border: 1px solid {accent_comic}; border-radius: 8px; padding: 6px 12px; }} "
                "QPushButton:hover { background: #334155; }"
            )

    def set_text(self, text: str):
        if self.text_label is not None:
            self.text_label.setText(text)

    def set_download_state(self, is_translating: bool, current: int = 0, total: int = 0):
        if self.download_btn is None:
            return
        self._is_translating = is_translating
        if is_translating:
            if total > 0:
                label = f"Đang xử lý {current}/{total}"
                if hasattr(self, "_download_mode") and self._download_mode:
                    label = f"Đang download {current}/{total} ảnh"
                self.download_btn.setText(label)
            else:
                self.download_btn.setText("Đang download..." if getattr(self, "_download_mode", False) else "Đang dịch...")
            self.download_btn.setEnabled(False)
            self.download_btn.setStyleSheet(
                "background: #F59E0B; color: #0F172A; border: 1px solid #F59E0B; border-radius: 8px; padding: 6px 12px;"
            )
        else:
            self.download_btn.setText("Download")
            self.download_btn.setEnabled(True)
            self.download_btn.setStyleSheet(
                "background: #1E293B; color: #F8FAFC; border: 1px solid rgba(148, 163, 184, 0.8); border-radius: 8px; padding: 6px 12px;"
            )

    def _sync_navigation_buttons(self):
        if self.popup_type != "comic":
            return

        total = len(self._navigation_images)
        if self.text_label is not None:
            if total > 0 and self._navigation_index >= 0:
                self.text_label.setText(f"Ảnh {self._navigation_index + 1}/{total}")
            elif total > 0:
                self.text_label.setText(f"{total} file(s) translated")
            else:
                self.text_label.setText("0 file(s) translated")

    def set_preview_images(self, images):
        self._translated_images = list(images or [])
        self._navigation_images = self._translated_images
        if self._navigation_index < 0 and self._navigation_images:
            self._navigation_index = 0
        self._sync_navigation_buttons()
        if self.popup_type == "comic" and self._navigation_images and self._navigation_index >= 0:
            if self._current_image is None:
                self.set_image(self._navigation_images[self._navigation_index])
        elif self.text_label is not None:
            self.text_label.setText(f"{len(self._translated_images)} file(s) translated")
        self.set_download_state(False)

    def go_to_previous_image(self):
        if self.popup_type != "comic" or not self._navigation_images:
            return
        if self._navigation_index <= 0:
            return
        self._navigation_index -= 1
        self.set_image(self._navigation_images[self._navigation_index])
        self._sync_navigation_buttons()

    def go_to_next_image(self):
        if self.popup_type != "comic" or not self._navigation_images:
            return
        if self._navigation_index >= len(self._navigation_images) - 1:
            return
        self._navigation_index += 1
        self.set_image(self._navigation_images[self._navigation_index])
        self._sync_navigation_buttons()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress and self.popup_type == "comic":
            if event.key() == Qt.Key_Left:
                self.go_to_previous_image()
                return True
            if event.key() == Qt.Key_Right:
                self.go_to_next_image()
                return True

        if event.type() == event.Type.Wheel and obj is self.graphics_view:
            if not event.modifiers() & Qt.ControlModifier:
                return False

            delta = event.angleDelta().y()
            if delta == 0:
                return False

            factor = 1.1 if delta > 0 else 1.0 / 1.1
            self._zoom_factor = max(0.25, min(5.0, self._zoom_factor * factor))

            pos = event.position()
            self.graphics_view.setTransformationAnchor(self.graphics_view.ViewportAnchor.AnchorUnderMouse)
            self.graphics_view.scale(factor, factor)
            self.graphics_view.centerOn(self.graphics_view.mapToScene(int(pos.x()), int(pos.y())))
            return True

        return super().eventFilter(obj, event)

    def _refresh_image_view(self):
        if self._current_image is None:
            return

        if self.popup_type == "comic":
            if self.graphics_view is None or self.graphics_scene is None:
                return

            pixmap = QPixmap.fromImage(self._current_image)
            self.graphics_scene.clear()
            item = self.graphics_scene.addPixmap(pixmap)
            item.setPos(0, 0)
            self.graphics_scene.setSceneRect(self.graphics_scene.itemsBoundingRect())
            self.graphics_view.setSceneRect(self.graphics_scene.sceneRect())
            self.graphics_view.resetTransform()
            self.graphics_view.setDragMode(self.graphics_view.DragMode.ScrollHandDrag)
            self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)
            self.graphics_view.centerOn(item)
            return

        if self.image_label is None:
            return

        pixmap = QPixmap.fromImage(self._current_image)
        new_w = max(1, int(pixmap.width() * self._zoom_factor))
        new_h = max(1, int(pixmap.height() * self._zoom_factor))

        fit_pixmap = pixmap.scaled(
            QSize(new_w, new_h),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(fit_pixmap)
        self.image_label.setFixedSize(fit_pixmap.size())
        self.image_label.setMinimumSize(0, 0)

    def set_image(self, image: QImage):
        if image is None or image.isNull():
            return

        self._current_image = image.copy()
        self._zoom_factor = 1.0

        if self.popup_type == "comic":
            self._refresh_image_view()
            return

        if self.image_label is None:
            return

        self._refresh_image_view()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._ui is not None:
            self._ui.resize(self.size())
            self._ui.move(0, 0)
        if self._current_image is not None and self.image_label is not None:
            self.set_image(self._current_image)

    def showEvent(self, event):
        super().showEvent(event)
        self.resize(*self._popup_size)
        self.setMinimumSize(*self._popup_size)
        self.setMaximumSize(*self._popup_size)
        if self.parent_window is not None and hasattr(self.parent_window, "_position_popup"):
            self.parent_window._position_popup(self)
        else:
            self.setGeometry(self.x(), self.y(), self.width(), self.height())

    def open_file_dialog(self):
        if self.popup_type != "comic":
            return

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select comic image(s)",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not paths:
            return

        self._selected_paths = paths
        self._translated_images = []
        self._translated_entries = []
        self._navigation_images = []
        self._navigation_index = -1
        if self.text_label is not None:
            self.text_label.setText(f"{len(paths)} file(s) selected")
        if self.title_label is not None:
            self.title_label.setText(f"Translate Comic ({len(paths)} file(s))")
        self._sync_navigation_buttons()

        self.set_download_state(True, 0, len(paths))
        if self.parent_window is not None and hasattr(self.parent_window, "process_comic_selection"):
            self.parent_window.process_comic_selection(paths)

        first_image = QImage(paths[0])
        if not first_image.isNull():
            self.set_image(first_image)

    def download_selected_images(self):
        if self.popup_type != "comic":
            return

        entries = self._translated_entries if self._translated_entries else []
        if not entries:
            QMessageBox.information(self, "Download", "Chưa có ảnh đã xử lý để tải xuống.")
            return

        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Select folder to save",
            os.path.dirname(self._selected_paths[0]) if self._selected_paths else "",
        )
        if not save_dir:
            return

        self._download_mode = True
        self.set_download_state(True, 0, len(entries))
        self.download_btn.setEnabled(False)

        self.download_worker = DownloadComicWorker(entries, save_dir)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()

    def on_download_progress(self, current: int, total: int):
        if self.popup_type != "comic":
            return
        self.set_download_state(True, current, total)

    def on_download_finished(self, count: int):
        if self.popup_type != "comic":
            return
        self._download_mode = False
        self.set_download_state(False)
        QMessageBox.information(self, "Download", f"Đã tải xuống {count} ảnh.")

    def on_download_error(self, msg: str):
        if self.popup_type != "comic":
            return
        self._download_mode = False
        self.set_download_state(False)
        QMessageBox.critical(self, "Download", f"Không thể tải xuống ảnh:\n{msg}")

    def closeEvent(self, event):
        super().closeEvent(event)


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


class TranslateCommicWorker(QThread):
    finished = Signal(QImage)
    text_result = Signal(str)
    error = Signal(str)

    def __init__(self, image, mode_name="Translate Screen", selected_paths=None):
        super().__init__()
        self.image = image
        self.mode_name = mode_name
        self.selected_paths = selected_paths or []

    def run(self):
        try:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            self.image.save(buffer, "PNG")
            image_bytes = bytes(buffer.data())
            buffer.close()

            request = TranslationModeRequestBuilder.build(
                image_bytes=image_bytes,
                mode_name=self.mode_name,
                selected_paths=self.selected_paths,
                filename="screenshot.png",
            )

            try:
                response = requests.post(
                    request["endpoint"],
                    files=request["files"],
                    timeout=300,
                )
                response.raise_for_status()
            finally:
                file_tuple = request["files"].get("file")
                if file_tuple and hasattr(file_tuple[1], "close"):
                    file_tuple[1].close()

            if self.mode_name == "Translate Box Chat":
                payload = response.json()
                translated_text = payload.get("translated") or payload.get("text") or ""
                self.text_result.emit(str(translated_text))
                return

            result = QImage.fromData(response.content)

            if result.isNull():
                raise Exception("API không trả về ảnh hợp lệ")

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))


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

                with open(path, "rb") as image_file:
                    image_bytes = image_file.read()

                filename = os.path.basename(path)
                response = requests.post(
                    "http://localhost:8052/translate_comic",
                    files={"file": (filename, image_bytes, "application/octet-stream")},
                    timeout=300,
                )
                response.raise_for_status()

                image = QImage.fromData(response.content)
                if image.isNull():
                    raise Exception(f"API không trả về ảnh hợp lệ cho {filename}")

                entries.append((filename, image))
                self.image_processed.emit(filename, image)
                self.progress.emit(index, total)

            if not entries:
                raise Exception("Không có ảnh hợp lệ nào được xử lý")

            self.finished.emit(entries)

        except Exception as e:
            self.error.emit(str(e))


class BackendStartupWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, backend_dir: str, backend_mode: str):
        super().__init__()
        self.backend_dir = backend_dir
        self.backend_mode = backend_mode

    def _health_ok(self) -> bool:
        try:
            response = requests.get("http://localhost:8052/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def run(self):
        try:
            target = "run_with_ai" if self.backend_mode == "ai" else "run_with_google_translate"
            subprocess.Popen(
                f"cd '{self.backend_dir}' && make {target}",
                cwd=self.backend_dir,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                if self._health_ok():
                    self.finished.emit(True, "Backend đã running")
                    return
                time.sleep(2)

            self.finished.emit(False, "Không thể khởi động backend bằng make run_with_*")
        except Exception as exc:
            self.finished.emit(False, str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR Translate")

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._apply_main_window_position()
        self.backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
        self.backend_mode = None
        self.startup_dialog = None
        self.startup_worker = None

        self.setStyleSheet(
            "QMainWindow { background: #0F172A; color: #E2E8F0; } "
            "QWidget { color: #E2E8F0; } "
            "QPushButton { background: #1E293B; color: #F8FAFC; border: 1px solid rgba(148, 163, 184, 0.8); border-radius: 8px; padding: 6px 12px; } "
            "QPushButton:hover { background: #334155; } "
            "QComboBox { background: #111827; color: #F8FAFC; border: 1px solid rgba(148, 163, 184, 0.8); border-radius: 6px; padding: 4px 8px; }"
        )

        self.backend_ready = False
        self.selector = None
        self.selected_rect = None
        self.selected_image = None
        self.worker = None

        self.result_popups = {}
        self._create_result_popups()

        self.ui.mode_ocr.currentIndexChanged.connect(self.on_mode_changed)

        self.ui.Select_area_btn.clicked.connect(self.open_screen_selector)
        self.is_capturing = False
        self.ui.start_stop_btn.clicked.connect(self.toggle_capture)
        self._sync_mode_controls()

        self.previous_image = None
        self.capture_timer = QTimer(self)
        self.capture_timer.setInterval(500)
        self.capture_timer.timeout.connect(self.check_capture)
        self.last_box_chat_text = None

        self.backend_status_timer = QTimer(self)
        self.backend_status_timer.setInterval(10000)
        self.backend_status_timer.timeout.connect(self.check_backend_status)
        self.check_backend_status()
        self.backend_status_timer.start()

        self.processing = False
        self.api_error_shown = False
        QTimer.singleShot(0, self._start_backend_sequence)

    def _start_backend_sequence(self):
        if self.backend_mode is None:
            self._prompt_backend_mode()

        self._show_startup_status("Đang khởi động backend...")
        self.startup_worker = BackendStartupWorker(self.backend_dir, self.backend_mode)
        self.startup_worker.finished.connect(self._on_backend_start_finished, Qt.QueuedConnection)
        self.startup_worker.start()

    def _on_backend_start_finished(self, ok: bool, msg: str):
        self._hide_startup_status()
        QApplication.processEvents()
        if ok:
            self.backend_ready = True
            return

        self.backend_ready = False
        QMessageBox.critical(self, "Backend", f"Không thể khởi động backend: {msg}")
        self.close()

    def _show_startup_status(self, text: str):
        if self.startup_dialog is not None:
            self.startup_dialog.close()
        self.startup_dialog = QMessageBox(self)
        self.startup_dialog.setWindowTitle("")
        self.startup_dialog.setText(text)
        self.startup_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.startup_dialog.setWindowModality(Qt.ApplicationModal)
        self.startup_dialog.setModal(False)
        self.startup_dialog.setWindowFlag(Qt.FramelessWindowHint, on=True)
        self.startup_dialog.setWindowFlag(Qt.WindowStaysOnTopHint, on=True)
        self.startup_dialog.setStyleSheet(
            """
            QMessageBox {
                background: #0F172A;
                color: #E2E8F0;
                border: 1px solid rgba(148, 163, 184, 0.5);
                border-radius: 12px;
                padding: 18px 22px;
            }
            QLabel {
                color: #E2E8F0;
                background: transparent;
                font-size: 14px;
                font-weight: 600;
                qproperty-alignment: AlignCenter;
            }
            """
        )
        self.startup_dialog.resize(320, 110)
        self.startup_dialog.show()
        self.startup_dialog.raise_()
        self.startup_dialog.activateWindow()
        QApplication.processEvents()

    def _hide_startup_status(self):
        if self.startup_dialog is not None:
            self.startup_dialog.hide()
            self.startup_dialog.close()
            self.startup_dialog.deleteLater()
            self.startup_dialog = None
            QApplication.processEvents()

    def _prompt_backend_mode(self):
        choice = QMessageBox.question(
            self,
            "Chọn backend",
            "Bạn có dùng AI để translate không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        self.backend_mode = "ai" if choice == QMessageBox.StandardButton.Yes else "google"
        return self.backend_mode

    def _backend_health_check(self) -> bool:
        try:
            response = requests.get("http://localhost:8052/health", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def _wait_for_backend(self, timeout_seconds: int = 300) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._backend_health_check():
                return True
            time.sleep(3)
        return self._backend_health_check()

    def _ensure_backend_ready(self) -> bool:
        if self.backend_mode is None:
            self._prompt_backend_mode()

        if self._backend_health_check():
            return True

        return False

    def _stop_backend_and_docker(self):
        self._run_shell_command(f"cd '{self.backend_dir}' && make stop || true", "Stop Backend")

    def _run_shell_command(self, command: str, label: str) -> bool:
        try:
            subprocess.Popen(
                command,
                cwd=self.backend_dir,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except Exception as exc:
            QMessageBox.critical(self, label, f"Không thể chạy lệnh: {command}\n\nLỗi: {exc}")
            return False

    def _create_result_popups(self):
        if self.result_popups:
            return

        self.result_popups = {
            "Translate Screen": PopupWindow("translate_screen_popup.ui", "Translate Screen", "screen", self),
            "Translate Box Chat": PopupWindow("translate_box_chat_popup.ui", "Translate Box Chat", "chat", self),
            "Translate Comic": PopupWindow("translate_comic_popup.ui", "Translate Comic", "comic", self),
        }
        for popup in self.result_popups.values():
            popup.hide()

    def _apply_main_window_position(self):
        screen = QApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.setGeometry(geo.left() + 20, geo.top() + 30, self.width(), self.height())
        else:
            self.setGeometry(20, 30, self.width(), self.height())

    def _position_popup(self, popup):
        if popup is None:
            return

        screen = QApplication.primaryScreen()
        if screen is None:
            popup.setGeometry(self.x() + self.width() + 18, self.y() + 18, popup.width(), popup.height())
            return

        geo = screen.availableGeometry()
        popup_x = self.x() + self.width() + 18
        popup_y = self.y() + 18

        if popup_x + popup.width() > geo.right():
            popup_x = max(geo.left(), self.x() - popup.width() - 18)
        if popup_y + popup.height() > geo.bottom():
            popup_y = max(geo.top(), self.y())

        popup.setGeometry(popup_x, popup_y, popup.width(), popup.height())

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_main_window_position()
        for popup in self.result_popups.values():
            if popup.isVisible():
                self._position_popup(popup)

    def _sync_mode_controls(self):
        mode_name = self.ui.mode_ocr.currentText()
        should_disable = mode_name in ("Please select mode", "Translate Comic")

        self.ui.Select_area_btn.setEnabled(not should_disable)
        self.ui.start_stop_btn.setEnabled(not should_disable)

        if should_disable:
            self.ui.Select_area_btn.setToolTip("Chọn mode khác để kích hoạt")
            self.ui.start_stop_btn.setToolTip("Chọn mode khác để kích hoạt")
        else:
            self.ui.Select_area_btn.setToolTip("Select area")
            self.ui.start_stop_btn.setToolTip("Start Capture" if not self.is_capturing else "Stop Capture")

    def _apply_capture_interval_for_mode(self):
        mode_name = self.ui.mode_ocr.currentText()
        self.capture_timer.setInterval(1000 if mode_name == "Translate Box Chat" else 500)

    def _set_backend_status(self, is_running: bool):
        dot_color = "#22C55E" if is_running else "#A63A1F"
        text = "Backend is running" if is_running else "Backend not running"

        if hasattr(self.ui, "label_indicator_backend_status"):
            self.ui.label_indicator_backend_status.setText(
                f'<span style="color:{dot_color}; font-size: 14px; font-weight: 700;">●</span>'
            )

        if hasattr(self.ui, "label_check_status_backend"):
            self.ui.label_check_status_backend.setText(text)
            self.ui.label_check_status_backend.setStyleSheet(
                "color: #F8FAFC; background: transparent; font-weight: 600;"
            )

    def check_backend_status(self):
        try:
            response = requests.get("http://localhost:8052/health", timeout=2)
            is_running = response.status_code == 200
        except Exception:
            is_running = False

        self._set_backend_status(is_running)

    def on_mode_changed(self, index):
        mode_name = self.ui.mode_ocr.currentText()
        self.last_box_chat_text = None

        if self.is_capturing:
            self.stop_capture()
            self.is_capturing = False
            self.ui.start_stop_btn.setIcon(QIcon("icons/start.svg"))
            self.ui.start_stop_btn.setToolTip("Start Capture")

        self._apply_capture_interval_for_mode()

        for name, popup in self.result_popups.items():
            popup.hide()

        if mode_name == "Please select mode":
            self._sync_mode_controls()
            return

        popup = self.result_popups.get(mode_name)
        if popup is not None:
            popup.show()
            popup.raise_()
            self._position_popup(popup)

        self._sync_mode_controls()

    def show_selected_popup(self):
        return

    def toggle_capture(self):
        mode_name = self.ui.mode_ocr.currentText()
        if mode_name in ("Please select mode", "Translate Comic"):
            return

        self._apply_capture_interval_for_mode()

        if self.is_capturing:
            self.stop_capture()
            self.is_capturing = False

            self.ui.start_stop_btn.setIcon(QIcon("icons/start.svg"))
            self.ui.start_stop_btn.setToolTip("Start Capture")
            self._sync_mode_controls()
        else:
            if self.start_capture():
                self.is_capturing = True
                self.ui.start_stop_btn.setIcon(QIcon("icons/stop.svg"))
                self.ui.start_stop_btn.setToolTip("Stop Capture")
                self._sync_mode_controls()

    def open_screen_selector(self):
        print("Opening screen selector...")
        if self.selector is None:
            self.selector = ScreenSelector()
            self.selector.area_selected.connect(self.on_area_selected)
            self.selector.region_captured.connect(self.on_region_captured)

        self.selector.start_capture()

    def on_area_selected(self, rect, image):
        print(f"Area selected: {rect.x()},{rect.y()} {rect.width()}x{rect.height()}")
        self.selected_rect = rect
        self.selected_image = image
        self.previous_image = None
        self.show_image(image)

    def start_capture(self):
        print("Start auto capture...")

        if self.selected_rect is None or self.selected_rect.isEmpty():
            QMessageBox.warning(self, "Lỗi", "Chưa chọn vùng. Hãy bấm Select area trước.")
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
        if self.processing:
            return
        if self.selector is None:
            return

        self.selector.capture_region(self.selected_rect)

    def images_equal(self, image1: QImage, image2: QImage) -> bool:
        if image1.size() != image2.size():
            return False

        img1 = image1.convertToFormat(QImage.Format_RGBA8888)
        img2 = image2.convertToFormat(QImage.Format_RGBA8888)

        return bytes(img1.bits()) == bytes(img2.bits())

    def on_region_captured(self, image: QImage):
        if image is None or image.isNull():
            print("Captured image invalid")
            return

        if self.previous_image is not None and self.images_equal(self.previous_image, image):
            return

        self.previous_image = image.copy()
        self.processing = True
        self.api_error_shown = False

        mode_name = self.ui.mode_ocr.currentText()
        selected_paths = []
        comic_popup = self.result_popups.get("Translate Comic")
        if comic_popup is not None:
            selected_paths = list(comic_popup._selected_paths)

        self.worker = TranslateCommicWorker(
            image,
            mode_name=mode_name,
            selected_paths=selected_paths,
        )
        self.worker.finished.connect(self.on_bubble_finished)
        self.worker.text_result.connect(self.on_box_chat_result)
        self.worker.error.connect(self.on_bubble_error)
        self.worker.start()

    def on_box_chat_result(self, translated_text: str):
        self.processing = False

        text_value = str(translated_text or "").strip()
        if not text_value:
            return

        if self.last_box_chat_text is not None and text_value == self.last_box_chat_text:
            return

        self.last_box_chat_text = text_value

        chat_popup = self.result_popups.get("Translate Box Chat")
        if chat_popup is not None:
            chat_popup.set_text(text_value)

    def process_comic_selection(self, paths):
        popup = self.result_popups.get("Translate Comic")
        if popup is not None:
            popup._translated_entries = []
            popup._translated_images = []
            popup.set_download_state(True, 0, len(paths))
            if popup.text_label is not None:
                popup.text_label.setText(f"Đang xử lý 0/{len(paths)}")

        self.comic_worker = ComicSelectionWorker(paths)
        self.comic_worker.progress.connect(self.on_comic_selection_progress)
        self.comic_worker.image_processed.connect(self.on_comic_selection_image_processed)
        self.comic_worker.finished.connect(self.on_comic_selection_finished)
        self.comic_worker.error.connect(self.on_comic_selection_error)
        self.comic_worker.start()

    def on_comic_selection_image_processed(self, filename: str, image: QImage):
        popup = self.result_popups.get("Translate Comic")
        if popup is None:
            return

        popup._translated_entries.append((filename, image))
        popup._translated_images.append(image)
        popup._navigation_images = list(popup._translated_images)
        if popup._navigation_index < 0 and popup._navigation_images:
            popup._navigation_index = 0
            popup.set_image(popup._navigation_images[popup._navigation_index])
        if popup.text_label is not None:
            popup.text_label.setText(f"Đã dịch {len(popup._translated_images)}/{len(popup._selected_paths)}")
        popup._sync_navigation_buttons()

    def on_comic_selection_progress(self, current: int, total: int):
        popup = self.result_popups.get("Translate Comic")
        if popup is not None:
            popup.set_download_state(True, current, total)
            if popup.text_label is not None:
                popup.text_label.setText(f"Đang xử lý {current}/{total}")

    def on_comic_selection_finished(self, entries):
        popup = self.result_popups.get("Translate Comic")
        if popup is not None:
            popup._translated_entries = list(entries)
            popup._translated_images = [img for _, img in entries]
            popup.set_preview_images(popup._translated_images)
            popup.set_download_state(False)

    def on_comic_selection_error(self, msg: str):
        popup = self.result_popups.get("Translate Comic")
        if popup is not None:
            popup._translated_entries = []
            popup._translated_images = []
            popup.set_download_state(False)
        self.on_bubble_error(msg)

    def on_bubble_finished(self, result_image: QImage):
        self.processing = False

        mode_name = self.ui.mode_ocr.currentText()
        if mode_name == "Translate Screen":
            screen_popup = self.result_popups.get("Translate Screen")
            if screen_popup is not None:
                screen_popup.set_image(result_image)
        elif mode_name == "Translate Comic":
            comic_popup = self.result_popups.get("Translate Comic")
            if comic_popup is not None:
                comic_popup.set_image(result_image)

        self.show_image(result_image)

    def on_bubble_error(self, msg: str):
        if self.api_error_shown:
            return
        self.api_error_shown = True

        print("Lỗi:", msg)
        self.processing = False
        self.previous_image = None

        chat_popup = self.result_popups.get("Translate Box Chat")
        if chat_popup is not None:
            chat_popup.set_text(msg)

        QMessageBox.warning(self, "Lỗi", f"API thất bại, đang tiếp tục xử lý ảnh tiếp theo:\n{msg}")
        if self.capture_timer.isActive():
            self.capture_timer.start()

        if self.selector is not None:
            self.selector.start_capture()

    def show_image(self, image: QImage):
        if image is None or image.isNull():
            print("ERROR: Image is None/Null")
            return

        # Main window keeps only controls; result is displayed in the selected popup.
        return

    def closeEvent(self, event):
        self._stop_backend_and_docker()
        for popup in self.result_popups.values():
            popup.close()
        if self.selector is not None:
            self.selector.stop_stream()
        if self.worker is not None and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(3000)
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("TranslateTool")
    app.setDesktopFileName("translate-tool")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())