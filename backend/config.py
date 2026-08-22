import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

from bubble_detector.bubble_detector_factory import BubbleDetectorType
from inpainting.inpainter_factory import InpainterType
from ocr_engine.ocr_factory import OCREngineType
from translator.translator_factory import TranslatorType
from utils.languages import SourceLang, TargetLang


def _load_env_file() -> None:
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]

    for env_path in candidates:
        if not env_path.exists():
            continue

        if load_dotenv is not None:
            load_dotenv(env_path, override=False)
            continue

        with env_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)


def _coerce_enum(enum_cls, env_name: str, default):
    value = os.getenv(env_name)
    if value is None:
        return default

    normalized = value.strip()
    for member in enum_cls:
        if normalized.lower() in {member.name.lower(), member.value.lower()}:
            return member

    try:
        return enum_cls(normalized)
    except ValueError:
        return default


def get_default_config() -> dict:
    _load_env_file()

    return {
        "font_size_ratio": float(os.getenv("FONT_SIZE_RATIO", "1.0")),
        "detect_model": _coerce_enum(
            BubbleDetectorType,
            "DETECT_MODEL",
            BubbleDetectorType.RTDETR_COMIC_DETECTOR,
        ),
        "ocr_model": _coerce_enum(
            OCREngineType,
            "OCR_MODEL",
            OCREngineType.TURBO_OCR,
        ),
        "inpaint_model": _coerce_enum(
            InpainterType,
            "INPAINTER_MODEL",
            InpainterType.OPENCV,
        ),
        "translate_model": _coerce_enum(
            TranslatorType,
            "TRANSLATE_MODEL",
            TranslatorType.TENCENT_HY_MT,
        ),
        "source_lang": _coerce_enum(
            SourceLang,
            "SOURCE_LANG",
            SourceLang.auto,
        ),
        "target_lang": _coerce_enum(
            TargetLang,
            "TARGET_LANG",
            TargetLang.vi,
        ),
    }
