from enum import Enum
from functools import partial
from typing import Union

from ocr_engine.ocr_engine import OCREngine
from ocr_engine.turbo_ocr_engine import TurboOCREngine


class OCREngineType(str, Enum):
    TURBO_OCR = "turbo_ocr "


MODEL_REGISTRY = {
    OCREngineType.TURBO_OCR: partial(TurboOCREngine, model_name="turbo_ocr"),
}


class OCREngineFactory:
    @staticmethod
    def create(model_type: Union[str, OCREngineType]) -> OCREngine:
        if isinstance(model_type, str):
            model_type = OCREngineType(model_type)

        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        return MODEL_REGISTRY[model_type]()
