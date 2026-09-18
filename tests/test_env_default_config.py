from bubble_detector.bubble_detector_factory import BubbleDetectorType
from inpainting.inpainter_factory import InpainterType
from ocr_engine.ocr_factory import OCREngineType
from translator.translator_factory import TranslatorType
from utils.languages import SourceLang, TargetLang


def test_get_default_config_reads_env(monkeypatch):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

    from config import get_default_config

    monkeypatch.setenv("DETECT_MODEL", "yolov8")
    monkeypatch.setenv("OCR_MODEL", "turbo_ocr")
    monkeypatch.setenv("INPAINTER_MODEL", "lama")
    monkeypatch.setenv("TRANSLATE_MODEL", "google_translator")
    monkeypatch.setenv("SOURCE_LANG", "ko")
    monkeypatch.setenv("TARGET_LANG", "vi")
    monkeypatch.setenv("FONT_SIZE_RATIO", "1.5")

    cfg = get_default_config()

    assert cfg["detect_model"] == BubbleDetectorType.YOLOV8
    assert cfg["ocr_model"] == OCREngineType.TURBO_OCR
    assert cfg["inpaint_model"] == InpainterType.LAMA
    assert cfg["translate_model"] == TranslatorType.GoogleTranslator
    assert cfg["source_lang"] == SourceLang.ko
    assert cfg["target_lang"] == TargetLang.vi
    assert cfg["font_size_ratio"] == 1.5
