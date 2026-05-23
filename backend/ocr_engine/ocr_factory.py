from enum import Enum
from functools import partial
from typing import Union

from ocr_engine.ocr_engine import OCREngine
from ocr_engine.paddle_ocr_engine import PaddleOCREngine
from ocr_engine.turbo_ocr_engine import TurboOCREngine


class OCREngineType(str, Enum):
    PP_OCR_V5_SERVER = "pp_ocr_v5_server"
    PP_OCR_V5_MOBILE = "pp_ocr_v5_mobile"
    PP_OCR_V4_SERVER = "pp_ocr_v4_server"
    PP_OCR_V4_MOBILE = "pp_ocr_v4_mobile"
    EN_PP_OCR_V5_MOBILE_REC = "en_PP-OCRv5_mobile"
    KOREAN_PP_OCR_V5_MOBILE_REC = "korean_PP-OCRv5_mobile"
    TURBO_OCR = "turbo_ocr "


MODEL_REGISTRY = {
    OCREngineType.PP_OCR_V5_SERVER: partial(PaddleOCREngine, model_name="PP-OCRv5_server"),
    OCREngineType.PP_OCR_V5_MOBILE: partial(PaddleOCREngine, model_name="PP-OCRv5_mobile"),
    OCREngineType.PP_OCR_V4_SERVER: partial(PaddleOCREngine, model_name="PP-OCRv4_server"),
    OCREngineType.PP_OCR_V4_MOBILE: partial(PaddleOCREngine, model_name="PP-OCRv4_mobile"),
    OCREngineType.EN_PP_OCR_V5_MOBILE_REC: partial(
        PaddleOCREngine, model_name="en_PP-OCRv5_mobile"
    ),
    OCREngineType.KOREAN_PP_OCR_V5_MOBILE_REC: partial(
        PaddleOCREngine, model_name="korean_PP-OCRv5_mobile"
    ),
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
