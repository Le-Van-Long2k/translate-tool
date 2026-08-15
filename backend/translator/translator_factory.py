from enum import Enum
from typing import Union

from translator.gemma_4_e2b_translator import Gemma4E2BTranslator
from translator.google_translator import GoogleTranslator
from translator.tencent_translator import TencentTranslator
from translator.translator import ITranslator


class TranslatorType(str, Enum):
    TENCENT_HY_MT = "hy-mt"
    TRANSLATEGEMMA_4B = "translategemma-4b"
    Gemma4E2B = "gemma_4_e2b"
    GoogleTranslator = "google_translator"


MODEL_REGISTRY = {
    TranslatorType.TENCENT_HY_MT: TencentTranslator,
    TranslatorType.Gemma4E2B: Gemma4E2BTranslator,
    TranslatorType.GoogleTranslator: GoogleTranslator,
}


class TranslatorFactory:
    @staticmethod
    def create(model_type: Union[str, TranslatorType]) -> ITranslator:
        if isinstance(model_type, str):
            model_type = TranslatorType(model_type)

        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        return MODEL_REGISTRY[model_type]()
