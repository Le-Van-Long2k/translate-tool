import asyncio
import html
import logging
import re
from enum import Enum
from typing import Dict, List

import requests

from translator.translator import ITranslator
from utils.languages import SourceLang, TargetLang

logger = logging.getLogger("TRANSLATOR")


class LibreTranslateTranslator(ITranslator):
    """
    LibreTranslate local API translator.

    - Gộp toàn bộ texts thành 1 HTTP request.
    - Mỗi text được bọc trong <seg id="N">...</seg>.
    - Dùng format="html" để LibreTranslate giữ markup.
    - Giữ nguyên thứ tự bằng id.
    - Text rỗng không gửi lên API.
    - requests chạy trong asyncio.to_thread().
    - Tự động convert SourceLang / TargetLang
      sang mã ngôn ngữ LibreTranslate.
    """

    SEGMENT_RE = re.compile(
        r'<seg\s+id=["\'](\d+)["\']\s*>(.*?)</seg\s*>',
        re.IGNORECASE | re.DOTALL,
    )

    LANG_MAP = {
        SourceLang.en: "en",
        SourceLang.zh: "zh",
        SourceLang.ja: "ja",
        SourceLang.ko: "ko",
        SourceLang.auto: "auto",

        TargetLang.vi: "vi",
    }

    STRING_LANG_MAP = {
        "en": "en",
        "english": "en",

        "zh": "zh",
        "chinese": "zh",
        "zh-cn": "zh",
        "zh_cn": "zh",

        "ja": "ja",
        "japanese": "ja",

        "ko": "ko",
        "korean": "ko",

        "vi": "vi",
        "vietnamese": "vi",

        "auto": "auto",
    }

    def __init__(
        self,
        base_url: str = "http://libretranslate:5000",
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.url = f"{self.base_url}/translate"
        self.timeout = timeout

    # ------------------------------------------------------------------
    # LANGUAGE MAPPING
    # ------------------------------------------------------------------

    def _get_lang_code(self, lang) -> str:
        """
        Convert internal language enum/value to LibreTranslate code.

        SourceLang.en   -> "en"
        SourceLang.zh   -> "zh"
        SourceLang.ja   -> "ja"
        SourceLang.ko   -> "ko"
        SourceLang.auto -> "auto"

        TargetLang.vi   -> "vi"
        """

        if lang in self.LANG_MAP:
            return self.LANG_MAP[lang]

        if isinstance(lang, str):
            value = lang.strip().lower()

            if value in self.STRING_LANG_MAP:
                return self.STRING_LANG_MAP[value]

        if isinstance(lang, Enum):
            value = str(lang.value).strip().lower()

            if value in self.STRING_LANG_MAP:
                return self.STRING_LANG_MAP[value]

        raise ValueError(
            f"Unsupported language for LibreTranslate: {lang!r}"
        )

    # ------------------------------------------------------------------
    # TRANSLATE BATCH
    # ------------------------------------------------------------------

    async def translate_batch(
        self,
        texts: List[str],
        from_lang: SourceLang,
        to_lang: TargetLang,
        context: str = "",
    ) -> List[str]:

        if not texts:
            return []

        results: List[str] = [""] * len(texts)

        try:
            source_lang = self._get_lang_code(from_lang)
            target_lang = self._get_lang_code(to_lang)

        except Exception:
            logger.exception(
                "LibreTranslate language mapping failed"
            )
            return results

        segments: List[str] = []
        non_empty_count = 0

        for index, text in enumerate(texts):

            if not text or not text.strip():
                continue

            escaped_text = html.escape(
                text,
                quote=False,
            )

            segments.append(
                f'<seg id="{index}">{escaped_text}</seg>'
            )

            non_empty_count += 1

        if not segments:
            logger.info(
                "LibreTranslate: all texts are empty"
            )
            return results

        combined_text = "\n".join(segments)

        logger.info(
            "LibreTranslate: %d texts -> 1 request, "
            "source=%s, target=%s, input chars=%d",
            non_empty_count,
            source_lang,
            target_lang,
            len(combined_text),
        )

        try:
            translated = await asyncio.to_thread(
                self._translate_combined,
                combined_text,
                source_lang,
                target_lang,
            )

        except Exception:
            logger.exception(
                "LibreTranslate batch request failed"
            )
            return results

        extracted = self._extract_segments(
            translated,
            len(texts),
        )

        for index, value in extracted.items():
            value = html.unescape(value)
            value = value.strip()
            results[index] = value

        missing = [
            index
            for index, original in enumerate(texts)
            if (
                original
                and original.strip()
                and index not in extracted
            )
        ]

        if missing:
            logger.warning(
                "LibreTranslate: missing segments: %s",
                missing,
            )

        logger.info(
            "LibreTranslate: extracted %d/%d segments",
            len(extracted),
            non_empty_count,
        )

        return results

    # ------------------------------------------------------------------
    # HTTP REQUEST
    # ------------------------------------------------------------------

    def _translate_combined(
        self,
        text: str,
        from_lang: str,
        to_lang: str,
    ) -> str:

        payload = {
            "q": text,
            "source": from_lang,
            "target": to_lang,
            "format": "html",
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                timeout=self.timeout,
            )

        except requests.RequestException:
            logger.exception(
                "LibreTranslate HTTP request failed"
            )
            raise

        if not response.ok:
            logger.error(
                "LibreTranslate HTTP %d: %s",
                response.status_code,
                response.text[:5000],
            )

        response.raise_for_status()

        try:
            data = response.json()

        except ValueError as exc:
            logger.error(
                "LibreTranslate returned invalid JSON: %s",
                response.text[:5000],
            )

            raise RuntimeError(
                "LibreTranslate returned invalid JSON"
            ) from exc

        translated_text = data.get("translatedText")

        if translated_text is None:
            raise RuntimeError(
                "LibreTranslate returned invalid response: "
                f"{data}"
            )

        return translated_text

    # ------------------------------------------------------------------
    # EXTRACT SEGMENTS
    # ------------------------------------------------------------------

    def _extract_segments(
        self,
        translated: str,
        count: int,
    ) -> Dict[int, str]:

        results: Dict[int, str] = {}

        matches = list(
            self.SEGMENT_RE.finditer(translated)
        )

        if not matches:
            logger.error(
                "LibreTranslate: no <seg> markers found "
                "in translated response: %r",
                translated[:2000],
            )

            return results

        for match in matches:

            raw_id = match.group(1)
            value = match.group(2)

            try:
                index = int(raw_id)

            except ValueError:
                continue

            if index < 0 or index >= count:
                logger.warning(
                    "LibreTranslate: invalid segment id=%s",
                    raw_id,
                )
                continue

            if index in results:
                logger.warning(
                    "LibreTranslate: duplicate segment id=%d",
                    index,
                )
                continue

            results[index] = value

        return results