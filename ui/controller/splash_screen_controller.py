# -*- coding: utf-8 -*-

import requests

from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget

from ui.ui_splash_screen import Ui_SplashScreen


class BackendHealthWorker(QThread):
    """Check backend health without blocking the Qt UI thread."""

    backend_ready = Signal(bool)

    def __init__(self, backend_url: str, parent=None):
        super().__init__(parent)
        self.backend_url = backend_url

    def run(self):
        try:
            response = requests.get(
                self.backend_url,
                timeout=1.5,
            )

            response.raise_for_status()

            content_type = response.headers.get(
                "Content-Type",
                "",
            )

            if "application/json" not in content_type.lower():
                self.backend_ready.emit(False)
                return

            payload = response.json()

            self.backend_ready.emit(
                payload.get("status") == "ok"
            )

        except Exception:
            self.backend_ready.emit(False)


class SplashScreenController(QWidget):
    """
    Frameless splash window shown until backend health is ready.

    The progress bar uses Qt's indeterminate mode:
        setRange(0, 0)

    Backend health checks run in a worker thread so the
    progress bar animation never gets blocked by requests.get().
    """

    def __init__(
        self,
        main_window=None,
        backend_url="http://127.0.0.1:8052/health_check",
    ):
        super().__init__()

        self.main_window = main_window
        self.backend_url = backend_url

        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)
        self.ui.backgroundWidget.lower()
        self.ui.darkOverlay.raise_()
        self.ui.contentWidget.raise_()
        self._backend_worker = None
        self._status_timer = None
        self._closing = False

        self._configure_window()
        self._start_backend_check()

    # =========================================================
    # Window configuration
    # =========================================================

    def _configure_window(self):
        self.setWindowTitle("")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setWindowModality(
            Qt.WindowModality.ApplicationModal
        )

        self.setFixedSize(self.size())

        # -----------------------------------------------------
        # Indeterminate progress bar
        #
        # min == max == 0
        # => Qt automatically displays a busy/loading animation.
        # -----------------------------------------------------

        self.ui.progressBar.setRange(0, 0)
        self.ui.progressBar.setTextVisible(False)
        self.ui.progressBar.setFormat("")

        self.ui.labelStatus.setText(
            "Đang khởi động ứng dụng..."
        )

        self._center_on_screen()

    # =========================================================
    # Center window
    # =========================================================

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()

        if screen is None:
            return

        geometry = screen.availableGeometry()

        x = geometry.x() + (
            geometry.width() - self.width()
        ) // 2

        y = geometry.y() + (
            geometry.height() - self.height()
        ) // 2

        self.move(x, y)

    # =========================================================
    # Backend health check
    # =========================================================

    def _start_backend_check(self):
        self._status_timer = QTimer(self)

        # Check every 1.5 seconds
        self._status_timer.setInterval(1500)

        self._status_timer.timeout.connect(
            self._check_backend_status
        )

        # Check immediately
        self._check_backend_status()

        self._status_timer.start()

    def _check_backend_status(self):
        # Don't start another request if the previous
        # request is still running.
        if (
            self._backend_worker is not None
            and self._backend_worker.isRunning()
        ):
            return

        self._backend_worker = BackendHealthWorker(
            self.backend_url,
            self,
        )

        self._backend_worker.backend_ready.connect(
            self._on_backend_status
        )

        self._backend_worker.finished.connect(
            self._on_worker_finished
        )

        self._backend_worker.start()

    def _on_backend_status(self, ready: bool):
        if self._closing:
            return

        if not ready:
            self.ui.labelStatus.setText(
                "Đang khởi động dịch vụ..."
            )
            return

        # Backend is ready
        self.ui.labelStatus.setText(
            "Đã sẵn sàng..."
        )

        # Let Qt repaint the final status before closing.
        QTimer.singleShot(
            150,
            self._close_splash,
        )

    def _on_worker_finished(self):
        worker = self.sender()

        if worker is not None:
            worker.deleteLater()

        self._backend_worker = None

    # =========================================================
    # Close splash
    # =========================================================

    def _close_splash(self):
        if self._closing:
            return

        self._closing = True

        # Stop health-check timer
        if (
            self._status_timer is not None
            and self._status_timer.isActive()
        ):
            self._status_timer.stop()

        # Show main window
        if self.main_window is not None:
            self.main_window.setEnabled(True)
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

        self.close()

    # =========================================================
    # Close event
    # =========================================================

    def closeEvent(self, event):
        self._closing = True

        # Stop timer
        if (
            self._status_timer is not None
            and self._status_timer.isActive()
        ):
            self._status_timer.stop()

        # Stop worker if still running
        if (
            self._backend_worker is not None
            and self._backend_worker.isRunning()
        ):
            self._backend_worker.requestInterruption()

            # Wait only a short time.
            self._backend_worker.wait(300)

        event.accept()