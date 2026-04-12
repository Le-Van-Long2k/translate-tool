from enum import Enum
from typing import Union

from translator.translator import ITranslator
from translator.gemma_4_e2b_translator import (
    Gemma4E2BClientTranslator,
    Gemma4E2BLlamaCppPythonTranslator,
)


class TranslatorType(Enum):
    GEMMA_4_E2B_CLIENT = "gemma_4_e2b_client"
    GEMMA_4_E2B_LLAMACPP_PYTHON = "gemma_4_e2b_llamacpp_python"


MODEL_REGISTRY = {
    TranslatorType.GEMMA_4_E2B_CLIENT: Gemma4E2BClientTranslator,
    TranslatorType.GEMMA_4_E2B_LLAMACPP_PYTHON: Gemma4E2BLlamaCppPythonTranslator,
}


class TranslatorFactory:
    @staticmethod
    def create(model_type: Union[str, TranslatorType]) -> ITranslator:
        if isinstance(model_type, str):
            model_type = TranslatorType(model_type)

        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        return MODEL_REGISTRY[model_type]()
