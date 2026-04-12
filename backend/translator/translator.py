from abc import ABC, abstractmethod
from typing import List


class ITranslator(ABC):
    @abstractmethod
    def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str
    ) -> List[str]:
        pass

    # @abstractmethod
    # def translate(self, text: str, from_lang: str, to_lang: str) -> str:
    #     pass
