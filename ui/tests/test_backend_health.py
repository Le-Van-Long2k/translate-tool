from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QSizePolicy, QWidget

from controller.MainWindow_controller import MainWindowController
from ui.ui_MainWindow import Ui_Form
from ui.ui_box_chat_popup import Ui_box_chat_translate_form


def test_backend_health_payload_ok():
    payload = {"status": "ok", "models_loaded": True}
    assert MainWindowController.is_backend_healthy_payload(payload) is True


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
