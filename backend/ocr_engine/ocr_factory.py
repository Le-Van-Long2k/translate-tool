from enum import Enum
from typing import Union

from ocr_engine.ocr_engine import OCREngine
from ocr_engine.paddle_ocr_engine import PaddleOCREngine


class OCREngineType(Enum):
    PADDLE_OCR = "paddle_ocr"


MODEL_REGISTRY = {
    OCREngineType.PADDLE_OCR: PaddleOCREngine,
}


class OCREngineFactory:
    @staticmethod
    def create(model_type: Union[str, OCREngineType]) -> OCREngine:
        if isinstance(model_type, str):
            model_type = OCREngineType(model_type)

        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        return MODEL_REGISTRY[model_type]()
