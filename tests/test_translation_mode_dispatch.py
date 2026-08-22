import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.main import TranslationModeRequestBuilder


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


def test_comic_mode_with_multiple_files_uses_zip_endpoint():
    req = TranslationModeRequestBuilder.build(
        image_bytes=b"img",
        mode_name="Translate Comic",
        selected_paths=["/tmp/a.png", "/tmp/b.png"],
        filename="comic.png",
    )

    assert req["endpoint"] == "http://localhost:8052/translate_comic_zip"
    assert req["filename"].endswith("temp_ocr.zip")
