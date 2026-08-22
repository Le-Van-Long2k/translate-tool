import os

from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.main import MainWindow, TranslationModeRequestBuilder


def test_screen_mode_uses_translate_comic():
    req = TranslationModeRequestBuilder.build(
        image_bytes=b"img",
        mode_name="Translate Screen",
        selected_paths=[],
        filename="screenshot.png",
    )

    assert req["endpoint"] == "http://localhost:8052/translate_comic"
    assert req["filename"] == "screenshot.png"


def test_box_chat_mode_uses_translate_one_box_chat():
    req = TranslationModeRequestBuilder.build(
        image_bytes=b"img",
        mode_name="Translate Box Chat",
        selected_paths=[],
        filename="box.png",
    )

    assert req["endpoint"] == "http://localhost:8052/translate_one_box_chat"
    assert req["filename"] == "box.png"


def test_comic_mode_uses_direct_image_uploads_for_multiple_files():
    req = TranslationModeRequestBuilder.build(
        image_bytes=b"img",
        mode_name="Translate Comic",
        selected_paths=["/tmp/a.png", "/tmp/b.png"],
        filename="comic.png",
    )

    assert req["endpoint"] == "http://localhost:8052/translate_comic"
    assert req["filename"] == "comic.png"
    assert req.get("temp_zip_path") is None


def test_on_bubble_error_keeps_app_running_and_allows_next_frame(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.api_error_shown = False
    window.processing = True
    window.previous_image = object()
    window.capture_timer.start = lambda: None
    window.selector = type("Selector", (), {"start_capture": lambda self: None})()

    quit_calls = {"count": 0}
    original_quit = app.quit
    app.quit = lambda: quit_calls.__setitem__("count", quit_calls["count"] + 1)

    try:
        window.on_bubble_error("backend down")
    finally:
        app.quit = original_quit
        window.close()

    assert window.processing is False
    assert window.previous_image is None
    assert quit_calls["count"] == 0
