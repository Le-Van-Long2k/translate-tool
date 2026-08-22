# -*- coding: utf-8 -*-
import sys

import os
import tempfile
import zipfile
from io import BytesIO

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from PySide6.QtGui import QPixmap, QImage, QIcon

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

    @staticmethod
    def _cleanup_temp_zip(path: str):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    @classmethod
    def build(cls, image_bytes: bytes, mode_name: str, selected_paths=None, filename: str = "capture.png"):
        mode_name = (mode_name or "").strip()
        selected_paths = selected_paths or []

        if mode_name == "Translate Box Chat":
            return {
                "endpoint": "http://localhost:8052/translate_one_box_chat",
                "files": {"file": (filename, image_bytes, cls._mime_for(filename))},
                "temp_zip_path": None,
            }

        if mode_name == "Translate Comic" and len(selected_paths) > 1:
            zip_path = os.path.join(tempfile.gettempdir(), "temp_ocr.zip")
            cls._cleanup_temp_zip(zip_path)

            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in selected_paths:
                    if not os.path.isfile(path):
                        continue
                    archive.write(path, os.path.basename(path))

            return {
                "endpoint": "http://localhost:8052/translate_comic_zip",
                "files": {"file": ("temp_ocr.zip", open(zip_path, "rb"), "application/zip")},
                "temp_zip_path": zip_path,
            }

        return {
            "endpoint": "http://localhost:8052/translate_comic",
            "files": {"file": (filename, image_bytes, cls._mime_for(filename))},
            "temp_zip_path": None,
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
        self._is_translating = False

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
                self._ui.setParent(self)
                self._ui.move(0, 0)
                self._ui.resize(self.size())

        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setMinimumSize(220, 120)

        root = self._ui if self._ui is not None else self
        self.title_label = root.findChild(QLabel, "title_label")
        self.text_label = root.findChild(QLabel, "text_label")
        self.image_label = root.findChild(QLabel, "image_label")
        self.select_btn = root.findChild(QPushButton, "select_btn")
        self.download_btn = root.findChild(QPushButton, "download_btn")

        self.preview_list = None
        if self.popup_type == "comic":
            if self.image_label is not None:
                self.image_label.hide()
            if self.text_label is not None:
                self.text_label.setText("0 file selected")

        if self.image_label is not None:
            self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.image_label.setMinimumSize(0, 0)
            self.image_label.setScaledContents(False)
        if self.text_label is not None:
            self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.text_label.setMinimumSize(0, 0)
            self.text_label.setWordWrap(True)
        if self.title_label is not None:
            self.title_label.setText(title)

        if self.select_btn is not None:
            self.select_btn.clicked.connect(self.open_file_dialog)

        if self.download_btn is not None:
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
                self.download_btn.setText(f"Đang xử lý {current}/{total}")
            else:
                self.download_btn.setText("Đang dịch...")
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

    def set_preview_images(self, images):
        self._translated_images = list(images or [])
        if self.text_label is not None:
            self.text_label.setText(f"{len(self._translated_images)} file(s) translated")
        self.set_download_state(False)

    def set_image(self, image: QImage):
        if image is None or image.isNull() or self.image_label is None:
            return

        self._current_image = image.copy()
        label_size = self.image_label.size()
        if label_size.width() <= 1 or label_size.height() <= 1:
            return

        pixmap = QPixmap.fromImage(self._current_image)
        scaled = pixmap.scaled(
            label_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._ui is not None:
            self._ui.resize(self.size())
            self._ui.move(0, 0)
        if self._current_image is not None and self.image_label is not None:
            self.set_image(self._current_image)

    def showEvent(self, event):
        super().showEvent(event)
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
        if self.text_label is not None:
            self.text_label.setText(f"{len(paths)} file(s) selected")
        if self.title_label is not None:
            self.title_label.setText(f"Translate Comic ({len(paths)} file(s))")

        self.set_download_state(True, 0, len(paths))
        if self.parent_window is not None and hasattr(self.parent_window, "process_comic_selection"):
            self.parent_window.process_comic_selection(paths)

        first_image = QImage(paths[0])
        if not first_image.isNull() and self.image_label is not None:
            self.image_label.show()
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

        valid_count = 0
        for filename, image in entries:
            if image is None or image.isNull():
                continue
            out_path = os.path.join(save_dir, filename)
            image.save(out_path)
            valid_count += 1

        QMessageBox.information(self, "Download", f"Đã tải xuống {valid_count} ảnh.")



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

            temp_zip_path = request.get("temp_zip_path")
            try:
                response = requests.post(
                    request["endpoint"],
                    files=request["files"],
                    timeout=300,
                )
                response.raise_for_status()
            finally:
                if temp_zip_path:
                    TranslationModeRequestBuilder._cleanup_temp_zip(temp_zip_path)
                    if request["files"].get("file") and hasattr(request["files"]["file"][1], "close"):
                        request["files"]["file"][1].close()

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._apply_main_window_position()

        self.setStyleSheet(
            "QMainWindow { background: #0F172A; color: #E2E8F0; } "
            "QWidget { color: #E2E8F0; } "
            "QPushButton { background: #1E293B; color: #F8FAFC; border: 1px solid rgba(148, 163, 184, 0.8); border-radius: 8px; padding: 6px 12px; } "
            "QPushButton:hover { background: #334155; } "
            "QComboBox { background: #111827; color: #F8FAFC; border: 1px solid rgba(148, 163, 184, 0.8); border-radius: 6px; padding: 4px 8px; }"
        )

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

        self.processing = False
        self.api_error_shown = False

    def _create_result_popups(self):
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

        popup = self.result_popups.get(mode_name)
        if popup is not None:
            popup.show()
            popup.raise_()
            self._position_popup(popup)

        self._sync_mode_controls()

    def show_selected_popup(self):
        mode_name = self.ui.mode_ocr.currentText()
        popup = self.result_popups.get(mode_name)
        if popup is not None:
            popup.show()
            popup.raise_()
            self._position_popup(popup)

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
        popup.set_image(image)
        if popup.text_label is not None:
            popup.text_label.setText(f"Đã dịch {len(popup._translated_images)}/{len(popup._selected_paths)}")

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

        chat_popup = self.result_popups.get("Translate Box Chat")
        if chat_popup is not None:
            chat_popup.set_text(msg)

        QMessageBox.critical(self, "Lỗi", f"API thất bại:\n{msg}")
        self.stop_capture()

        if QApplication.instance() is not None:
            QApplication.instance().quit()

    def show_image(self, image: QImage):
        if image is None or image.isNull():
            print("ERROR: Image is None/Null")
            return

        # Main window keeps only controls; result is displayed in the selected popup.
        return

    def closeEvent(self, event):
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