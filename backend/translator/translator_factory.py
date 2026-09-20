from enum import Enum
from typing import Union

from translator.google_translator import GoogleTranslator
from translator.tencent_translator import TencentTranslator
from translator.facebook_nllb_translator import FacebookNLLBTranslator
from translator.mymemory_translator import MyMemoryTranslator
from translator.libretranslate_translator import LibreTranslateTranslator
from translator.translator import ITranslator


class TranslatorType(str, Enum):
    TENCENT_HY_MT = "hy-mt"
    GoogleTranslator = "google_translator"
    FacebookNLLBTranslator = "facebook_nllb_translator"
    MyMemoryTranslator = "mymemory_translator"
    LibreTranslateTranslator = "libretranslate_translator"


MODEL_REGISTRY = {
    TranslatorType.TENCENT_HY_MT: TencentTranslator,
    TranslatorType.GoogleTranslator: GoogleTranslator,
    TranslatorType.FacebookNLLBTranslator: FacebookNLLBTranslator,
    TranslatorType.MyMemoryTranslator: MyMemoryTranslator,
    TranslatorType.LibreTranslateTranslator: LibreTranslateTranslator,
}


class TranslatorFactory:
    @staticmethod
    def create(model_type: Union[str, TranslatorType]) -> ITranslator:
        if isinstance(model_type, str):
            model_type = TranslatorType(model_type)

        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        return MODEL_REGISTRY[model_type]()
