import asyncio
import logging
import os
import time
from typing import List

import httpx
from lingua import Language, LanguageDetectorBuilder

from translator.translator import ITranslator

logger = logging.getLogger("TRANSLATOR")

DETECTED_LANG_CODES = {
    Language.ENGLISH: "en",
    Language.CHINESE: "zh",
    Language.JAPANESE: "ja",
    Language.KOREAN: "ko",
    Language.VIETNAMESE: "vi",
}

detector = LanguageDetectorBuilder.from_languages(
    Language.ENGLISH,
    Language.CHINESE,
    Language.JAPANESE,
    Language.KOREAN,
    Language.VIETNAMESE,
).build()


class IndexTranslator(ITranslator):
    def __init__(
        self,
        model: str = "",
        url: str = "http://llama-server:8080/v1/chat/completions",
        timeout: float = 60.0,
        max_concurrency: int = 5,
    ):
        self.model = model
        self.url = url
        self.timeout = timeout
        self.max_concurrency = max_concurrency

    # =====================================================
    # CHUẨN HÓA NGÔN NGỮ
    # =====================================================

    def _detect_source_lang(self, text: str) -> str:
        detected_language = detector.detect_language_of(text)
        return DETECTED_LANG_CODES.get(detected_language, "auto")

    # =====================================================
    # DỊCH ĐƠN
    # =====================================================

    async def _translate_one(
        self,
        client: httpx.AsyncClient,
        text: str,
        idx: int,
        from_lang: str,
        to_lang: str,
        context: str = "",
    ):

        if not text or not text.strip():
            return idx, ""

        system_prompt = os.getenv(
            "TRANSLATE_SYSTEM_PROMPT",
            "Dịch sang Tiếng Việt.",
        )

        if context:
            system_prompt = f"{system_prompt}\n\nContext:\n{context}"

        # -----------------------------
        # PAYLOAD
        # -----------------------------

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
            "temperature": 0.0,
            "max_tokens": 256,
        }

        # -----------------------------
        # YÊU CẦU
        # -----------------------------

        try:
            response = await client.post(
                self.url,
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            # Kiểm tra mô hình có đang giải thích hay không
            bad_patterns = [
                "tôi không thể",
                "không thể dịch",
                "không thể hiểu",
                "không có nghĩa",
                "không có từ",
                "nếu bạn muốn",
                "nếu bạn cần",
                "có thể hiểu là",
                "điều này có nghĩa",
                "ngữ cảnh",
            ]

            lower_content = content.lower()

            if (
                not content
                or any(pattern in lower_content for pattern in bad_patterns)
            ):
                content = text

            logger.debug(f"[{idx}] Bản gốc: {text}")
            logger.debug(f"[{idx}] Dịch: {content}")
            logger.debug(f"[{idx}] Dịch thành công")

            return idx, content

        except Exception as e:
            logger.exception(f"[{idx}] Lỗi dịch: {e}")

            return idx, ""

    # =====================================================
    # DỊCH HÀNG LOẠT
    # =====================================================

    async def _translate_batch_async(
        self,
        texts: List[str],
        from_lang: str,
        to_lang: str,
        context: str = "",
    ) -> List[str]:

        if not texts:
            return []

        start = time.perf_counter()

        semaphore = asyncio.Semaphore(self.max_concurrency)

        limits = httpx.Limits(
            max_connections=self.max_concurrency,
            max_keepalive_connections=self.max_concurrency,
        )

        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=limits,
        ) as client:

            async def run_task(text, idx):

                async with semaphore:
                    return await self._translate_one(
                        client=client,
                        text=text,
                        idx=idx,
                        from_lang=from_lang,
                        to_lang=to_lang,
                        context=context,
                    )

            tasks = [run_task(text, idx) for idx, text in enumerate(texts)]

            results = await asyncio.gather(
                *tasks,
                return_exceptions=False,
            )

        outputs = [""] * len(texts)

        for idx, content in results:
            outputs[idx] = content

        end = time.perf_counter()

        logger.info(f"Thời gian batch bất đồng bộ: {end - start:.3f}s")

        return outputs

    # =====================================================
    # API CÔNG KHAI
    # =====================================================

    async def translate_batch(
        self,
        texts: List[str],
        from_lang: str,
        to_lang: str,
        context: str = "",
    ) -> List[str]:

        return await self._translate_batch_async(
            texts=texts,
            from_lang=from_lang,
            to_lang=to_lang,
            context=context,
        )
