from abc import ABC, abstractmethod
from typing import List


class ITranslator(ABC):
    @abstractmethod
    async def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str, context: str = ""
    ) -> List[str]:
        pass

    async def translate(self, text: str, from_lang: str, to_lang: str, context: str = "") -> str:
        return (await self.translate_batch([text], from_lang, to_lang, context))[0]
