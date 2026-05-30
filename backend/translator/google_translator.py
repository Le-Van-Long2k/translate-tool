import logging
import time
from typing import List

from googletrans import Translator

from translator.translator import ITranslator
from utils.languages import SourceLang, TargetLang

logger = logging.getLogger("TRANSLATOR")

LANG_MAP = {
    SourceLang.en: "en",
    SourceLang.zh: "zh-cn",
    SourceLang.ja: "ja",
    SourceLang.ko: "ko",
    TargetLang.vi: "vi",
}


class GoogleTranslator(ITranslator):
    def __init__(self):
        self.translator: Translator | None = None

    async def _get_translator(self) -> Translator:
        if self.translator is None:
            self.translator = Translator()
            await self.translator.__aenter__()
        return self.translator

    async def translate_batch(
        self,
        texts: List[str],
        from_lang: str,
        to_lang: str,
        context: str = "",
    ) -> List[str]:
        if not texts:
            return []

        start_time = time.perf_counter()
        from_lang = LANG_MAP.get(SourceLang(from_lang), from_lang)
        to_lang = LANG_MAP.get(TargetLang(to_lang), to_lang)

        try:
            translator = await self._get_translator()

            results = await translator.translate(
                texts,
                src=from_lang,
                dest=to_lang,
            )

            if not isinstance(results, list):
                results = [results]

            translated_texts = [r.text for r in results]

            logger.info(
                f"Google Translate: {len(texts)} texts, {time.perf_counter() - start_time:.2f}s"
            )

            return translated_texts

        except Exception:
            logger.exception("Google Translate failed")
            return texts

    async def close(self):
        if self.translator:
            await self.translator.__aexit__(None, None, None)
            self.translator = None
