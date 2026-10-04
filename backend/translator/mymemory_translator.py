import asyncio
import os
from typing import List

import requests

from lingua import (
    Language,
    LanguageDetectorBuilder,
)

from translator.translator import ITranslator


# ============================================================
# LANGUAGE DETECTOR
# ============================================================

detector = LanguageDetectorBuilder.from_languages(
    Language.ENGLISH,
    Language.JAPANESE,
    Language.KOREAN,
    Language.CHINESE,
    Language.VIETNAMESE,
).build()


# ============================================================
# LANGUAGE NORMALIZATION
# ============================================================

def normalize_lang_code(lang: object) -> str:
    if lang is None:
        return ""

    value = getattr(lang, "value", lang)
    text = str(value).strip()

    if not text:
        return ""

    normalized = text.lower().replace("_", "-")

    mapping = {
        "auto": "auto",
        "detect": "auto",

        "english": "en",
        "en": "en",

        "japanese": "ja",
        "ja": "ja",

        "korean": "ko",
        "ko": "ko",

        "chinese": "zh",
        "zh": "zh",
        "zh-cn": "zh-cn",
        "zh-tw": "zh-tw",
        "zh-hans": "zh-cn",
        "zh-hant": "zh-tw",

        "vietnamese": "vi",
        "vi": "vi",
        "viet": "vi",
    }

    return mapping.get(normalized, normalized)


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(text: str) -> str:
    language = detector.detect_language_of(text)

    if language is None:
        return "en"

    mapping = {
        Language.ENGLISH: "en",
        Language.JAPANESE: "ja",
        Language.KOREAN: "ko",
        Language.CHINESE: "zh",
        Language.VIETNAMESE: "vi",
    }

    return mapping.get(language, "en")


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_SOURCE_LANGS = {
    "auto",
    "detect",
    "en",
    "ja",
    "ko",
    "zh",
    "zh-cn",
    "zh-tw",
    "vi",
}


def resolve_source_lang(
    text: str,
    from_lang: str,
) -> str:

    resolved = normalize_lang_code(from_lang)

    if (
        not resolved
        or resolved in {"auto", "detect"}
    ):
        detected = detect_language(text)

        return (
            detected
            if detected in SUPPORTED_SOURCE_LANGS
            else "en"
        )

    if resolved not in SUPPORTED_SOURCE_LANGS:
        detected = detect_language(text)

        return (
            detected
            if detected in SUPPORTED_SOURCE_LANGS
            else "en"
        )

    return resolved


# ============================================================
# MYMEMORY TRANSLATOR
# ============================================================

class MyMemoryTranslator(ITranslator):
    """
    Translation flow:

        1. MyMemory
           - Gộp toàn bộ texts thành 1 request.

        Nếu MyMemory lỗi:

        2. LibreTranslate
           - Không merge.
           - Mỗi text = 1 request riêng.

    Ví dụ:

        texts = [
            "你好",
            "你好吗？",
            "我想回家。"
        ]

    MyMemory:

        你好\\r\\n你好吗？\\r\\n我想回家。

    Nếu MyMemory lỗi:

        LibreTranslate #1 -> 你好
        LibreTranslate #2 -> 你好吗？
        LibreTranslate #3 -> 我想回家。
    """

    MYMEMORY_URL = (
        "https://api.mymemory.translated.net/get"
    )

    LIBRETRANSLATE_URL = (
        "http://libretranslate:5000/translate"
    )

    SEPARATOR = "\r\n"

    def __init__(
        self,
        timeout: float = 30.0,
        libretranslate_url: str = (
            "http://libretranslate:5000"
        ),
    ):
        self.timeout = timeout

        self.email = os.getenv(
            "MYMEMORY_EMAIL",
            "",
        )

        self.libretranslate_url = (
            libretranslate_url.rstrip("/")
            + "/translate"
        )

    # ========================================================
    # TRANSLATE BATCH
    # ========================================================

    async def translate_batch(
        self,
        texts: List[str],
        from_lang: str,
        to_lang: str,
        context: str = "",
    ) -> List[str]:

        if not texts:
            return []

        # ----------------------------------------------------
        # Giữ nguyên vị trí text rỗng
        # ----------------------------------------------------

        results: List[str] = [""] * len(texts)

        # ----------------------------------------------------
        # Chỉ xử lý text có nội dung
        # ----------------------------------------------------

        valid_items = [
            (index, text)
            for index, text in enumerate(texts)
            if text and text.strip()
        ]

        if not valid_items:
            return results

        # ----------------------------------------------------
        # Resolve source language
        # ----------------------------------------------------

        normalized_from = normalize_lang_code(
            from_lang
        )

        if (
            not normalized_from
            or normalized_from in {"auto", "detect"}
        ):
            resolved_from_lang = resolve_source_lang(
                valid_items[0][1],
                from_lang,
            )

        elif normalized_from not in SUPPORTED_SOURCE_LANGS:
            resolved_from_lang = resolve_source_lang(
                valid_items[0][1],
                from_lang,
            )

        else:
            resolved_from_lang = normalized_from

        # ----------------------------------------------------
        # Resolve target language
        # ----------------------------------------------------

        resolved_to_lang = normalize_lang_code(
            to_lang
        )

        if not resolved_to_lang:
            raise ValueError(
                "Target language is required."
            )

        # ----------------------------------------------------
        # Gộp toàn bộ text cho MyMemory
        # ----------------------------------------------------

        combined_text = self.SEPARATOR.join(
            text.strip()
            for _, text in valid_items
        )

        # ====================================================
        # MYMEMORY
        # ====================================================

        try:
            translated_text = await asyncio.to_thread(
                self._translate_mymemory,
                combined_text,
                resolved_from_lang,
                resolved_to_lang,
            )

            # ------------------------------------------------
            # Parse MyMemory response
            # ------------------------------------------------

            translated_parts = translated_text.split(
                self.SEPARATOR
            )

            if len(translated_parts) != len(valid_items):
                raise RuntimeError(
                    "MyMemory changed or removed "
                    "the separator.\n"
                    f"Expected parts : {len(valid_items)}\n"
                    f"Received parts : {len(translated_parts)}\n"
                    f"Response       : {translated_text}"
                )

            # ------------------------------------------------
            # Khôi phục vị trí ban đầu
            # ------------------------------------------------

            for (
                (index, _),
                translation,
            ) in zip(
                valid_items,
                translated_parts,
            ):
                results[index] = translation.strip()

            return results

        except Exception as e:
            print(
                "MyMemory failed. "
                "Falling back to LibreTranslate."
            )
            print(
                f"{type(e).__name__}: {e}"
            )

        # ====================================================
        # LIBRETRANSLATE FALLBACK
        #
        # Mỗi câu = 1 request
        # ====================================================

        for index, text in valid_items:
            try:
                translation = await asyncio.to_thread(
                    self._translate_libretranslate,
                    text.strip(),
                    resolved_from_lang,
                    resolved_to_lang,
                )

                results[index] = translation.strip()

            except Exception as e:
                print(
                    f"LibreTranslate failed for "
                    f"text #{index + 1}: "
                    f"{type(e).__name__}: {e}"
                )

                results[index] = ""

        return results

    # ========================================================
    # MYMEMORY
    # ========================================================

    def _translate_mymemory(
        self,
        text: str,
        from_lang: str,
        to_lang: str,
    ) -> str:

        params = {
            "q": text,
            "langpair": (
                f"{from_lang}|{to_lang}"
            ),
        }

        if self.email:
            params["de"] = self.email

        print("MyMemory request #1...")

        response = requests.get(
            self.MYMEMORY_URL,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        response_data = data.get(
            "responseData",
            {},
        )

        translated = response_data.get(
            "translatedText"
        )

        if not translated:
            raise RuntimeError(
                "MyMemory returned invalid response: "
                f"{data}"
            )

        print("MyMemory request #1 succeeded.")

        return translated

    # ========================================================
    # LIBRETRANSLATE
    # ========================================================

    def _translate_libretranslate(
        self,
        text: str,
        from_lang: str,
        to_lang: str,
    ) -> str:

        payload = {
            "q": text,
            "source": from_lang,
            "target": to_lang,
            "format": "text",
        }

        response = requests.post(
            self.libretranslate_url,
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        translated = data.get(
            "translatedText"
        )

        if not translated:
            raise RuntimeError(
                "LibreTranslate returned invalid "
                f"response: {data}"
            )

        return translated