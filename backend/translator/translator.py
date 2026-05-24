from abc import ABC, abstractmethod
from typing import List


class ITranslator(ABC):
    @abstractmethod
    async def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str, context: str = ""
    ) -> List[str]:
        pass

    async def translate(
        self, text: str, from_lang: str, to_lang: str, context: str = ""
    ) -> str:
        return (await self.translate_batch([text], from_lang, to_lang, context))[0]

from abc import ABC, abstractmethod
from typing import List, Optional


# class ITranslator(ABC):
#     def __init__(
#         self,
#         source_lang: Optional[str] = None,
#         target_lang: Optional[str] = None,
#     ):
#         self.source_lang = source_lang
#         self.target_lang = target_lang

#     def set_languages(self, source_lang: str, target_lang: str):
#         self.source_lang = source_lang
#         self.target_lang = target_lang

#     @abstractmethod
#     async def translate_batch(
#         self,
#         texts: List[str],
#         context: str = "",
#     ) -> List[str]:
#         pass

#     async def translate(
#         self,
#         text: str,
#         context: str = "",
#     ) -> str:
#         return (await self.translate_batch([text], context))[0]

# Ví dụ implement:

# class GoogleTranslator(ITranslator):
#     async def translate_batch(
#         self,
#         texts: List[str],
#         context: str = "",
#     ) -> List[str]:
#         if not self.source_lang or not self.target_lang:
#             raise ValueError("Source and target languages must be set")

#         # call api
#         return [
#             f"{text} ({self.source_lang} -> {self.target_lang})"
#             for text in texts
#         ]

# Cách dùng:

# translator = GoogleTranslator()
# translator.set_languages("en", "vi")

# result = await translator.translate("Hello")
# print(result)