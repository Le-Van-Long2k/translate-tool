from abc import ABC, abstractmethod
from typing import List


class ITranslator(ABC):
    @abstractmethod
    def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str, context: str = ""
    ) -> List[str]:
        pass

    def translate(
        self, text: str, from_lang: str, to_lang: str, context: str = ""
    ) -> str:
        translate_batch_result = self.translate_batch(
            [text], from_lang, to_lang, context
        )
        return translate_batch_result[0] if translate_batch_result else ""
