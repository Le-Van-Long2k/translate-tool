import threading

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QSizePolicy, QWidget

from controller.MainWindow_controller import MainWindowController
from ui.ui_MainWindow import Ui_Form
from ui.ui_box_chat_popup import Ui_box_chat_translate_form
from utils.backend_url import (
    build_backend_url,
    normalize_backend_host,
    normalize_backend_url,
    resolve_backend_base_url,
)


def test_backend_url_normalization_uses_single_canonical_host():
    assert normalize_backend_host("localhost") == "127.0.0.1"
    assert normalize_backend_host("127.0.0.0") == "127.0.0.1"
    assert normalize_backend_host("http://127.0.0.0:8052") == "127.0.0.1"
    assert normalize_backend_url("http://localhost:8052/health_check") == "http://127.0.0.1:8052/health_check"
    assert normalize_backend_url("http://127.0.0.0:8052/health_check") == "http://127.0.0.1:8052/health_check"
    assert build_backend_url("/health_check") == "http://127.0.0.1:8052/health_check"
    assert build_backend_url("translate_one_box_chat") == "http://127.0.0.1:8052/translate_one_box_chat"


def test_backend_url_uses_first_working_localhost_candidate():
    attempts = []

    def fake_get(url, timeout):
        attempts.append(url)
        if url == "http://127.0.0.1:8052/health_check":
            raise ConnectionError("down")
        if url == "http://localhost:8052/health_check":
            class _Response:
                status_code = 200
                headers = {"Content-Type": "application/json"}

                def json(self):
                    return {"status": "ok"}

            return _Response()
        raise AssertionError(f"unexpected url: {url}")

    assert resolve_backend_base_url(request_getter=fake_get) == "http://localhost:8052"
    assert attempts == [
        "http://127.0.0.1:8052/health_check",
        "http://localhost:8052/health_check",
    ]


def test_backend_health_payload_ok():
    payload = {"status": "ok", "models_loaded": True}
    assert MainWindowController.is_backend_healthy_payload(payload) is True


def test_main_window_does_not_start_docker_in_background_thread():
    app = QApplication.instance() or QApplication([])
    controller = MainWindowController()

    assert not hasattr(controller, "docker")
    assert not hasattr(controller, "_docker_start_thread")


def test_backend_health_payload_not_ok():
    payload = {"status": "error", "models_loaded": False}
    assert MainWindowController.is_backend_healthy_payload(payload) is False


def test_backend_ui_controls_disable_when_backend_down():
    app = QApplication.instance() or QApplication([])
    parent = QWidget()
    ui = Ui_Form()
    ui.setupUi(parent)

    controller = MainWindowController.__new__(MainWindowController)
    controller.ui = ui

    controller._set_backend_status(False)
    assert ui.comboBox_translate_engine.isEnabled() is False
    assert ui.comboBox_mode.isEnabled() is False

    controller._set_backend_status(True)
    assert ui.comboBox_translate_engine.isEnabled() is True
    assert ui.comboBox_mode.isEnabled() is True


def test_box_chat_result_label_fills_widget():
    app = QApplication.instance() or QApplication([])
    widget = app.activeWindow() or QWidget() if False else None

    parent = __import__("PySide6.QtWidgets", fromlist=["QWidget"]).QWidget()
    ui = Ui_box_chat_translate_form()
    ui.setupUi(parent)

    policy = ui.result_label.sizePolicy()
    assert policy.horizontalPolicy() == QSizePolicy.Policy.Expanding
    assert policy.verticalPolicy() == QSizePolicy.Policy.Expanding
    assert ui.result_label.width() >= parent.width() - 40
    assert ui.result_label.height() >= parent.height() - 40


def test_splash_screen_is_frameless_and_has_no_title():
    from controller.splash_screen_controller import SplashScreenController

    app = QApplication.instance() or QApplication([])
    splash = SplashScreenController()

    flags = splash.windowFlags()
    assert "FramelessWindowHint" in str(flags)
    assert splash.windowTitle() == ""
    assert splash.isModal() is False


def test_close_event_shows_busy_closing_dialog():
    app = QApplication.instance() or QApplication([])

    controller = MainWindowController.__new__(MainWindowController)
    controller.ui = Ui_Form()
    controller.ui.setupUi(QWidget())
    controller.docker = type(
        "DummyDocker",
        (),
        {
            "stop": lambda self, callback=None, finished_callback=None: (
                finished_callback and finished_callback(0), None
            )
        },
    )()
    controller._closing_dialog = None
    controller._closing = False
    controller._on_docker_stopped = lambda code: None

    event = QCloseEvent()
    controller.closeEvent(event)

    assert controller._closing is True
    assert controller._closing_dialog is None
    assert event.isAccepted() is True


def test_close_event_does_not_stop_backend_services():
    app = QApplication.instance() or QApplication([])

    controller = MainWindowController.__new__(MainWindowController)
    controller.ui = Ui_Form()
    controller.ui.setupUi(QWidget())

    calls = []

    class DummyDocker:
        def stop_sync(self, callback=None):
            calls.append("stop")
            return 0

        def shutdown_wsl(self, callback=None):
            calls.append("shutdown")
            return 0

    controller.docker = DummyDocker()
    controller._closing_dialog = None
    controller._closing = False

    event = QCloseEvent()
    controller.closeEvent(event)

    assert calls == []
    assert event.isAccepted() is True
