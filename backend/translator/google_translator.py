
import logging
import time
from typing import List

from googletrans import Translator

from translator.translator import ITranslator
from utils.languages import SourceLang, TargetLang

logger = logging.getLogger("TRANSLATOR")


LANG_MAP = {
    SourceLang.auto: "auto",
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
            self.translator = Translator(transport="curl")
            await self.translator.__aenter__()

        return self.translator

    async def translate_batch(
        self,
        texts: List[str],
        from_lang: SourceLang,
        to_lang: TargetLang,
        context: str = "",
    ) -> List[str]:

        if not texts:
            return []

        start_time = time.perf_counter()

        src = LANG_MAP.get(from_lang, "auto")
        dest = LANG_MAP.get(to_lang, "vi")

        try:
            translator = await self._get_translator()

            results = await translator.translate(
                texts,
                src=src,
                dest=dest,
            )

            if not isinstance(results, list):
                results = [results]

            translated_texts = [result.text for result in results]

            # Bảo đảm số lượng kết quả tương ứng đầu vào
            if len(translated_texts) != len(texts):
                raise ValueError(
                    f"Expected {len(texts)} translations, "
                    f"got {len(translated_texts)}"
                )

            for original, translated in zip(texts, translated_texts):
                logger.info(
                    "Google Translate: "
                    f"original={original!r} -> translated={translated!r}"
                )

            elapsed = time.perf_counter() - start_time

            logger.info(
                f"Google Translate: {len(texts)} texts, {elapsed:.2f}s"
            )

            return translated_texts

        except Exception:
            logger.exception("Google Translate failed")
            return texts

    async def close(self):
        if self.translator is not None:
            try:
                await self.translator.__aexit__(None, None, None)
            finally:
                self.translator = None
