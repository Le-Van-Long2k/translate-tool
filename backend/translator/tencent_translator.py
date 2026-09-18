import asyncio
import logging
import os
import time
from typing import List

import httpx

from translator.translator import ITranslator

logger = logging.getLogger("TRANSLATOR")

DEFAULT_SYSTEM_PROMPT = (
    "Dịch sang Tiếng Việt.\n"
    "Tự xác định ý nghĩa và dịch theo ngữ cảnh phù hợp nhất.\n"
    "Không tự thêm tên riêng hoặc nội dung.\n"
    "Chỉ trả về bản dịch.\n"
    "Không dịch được → trả nguyên văn bản gốc.\n"
    "Không giải thích.\n"
    "Không thêm ghi chú.\n"
)

class TencentTranslator(ITranslator):
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
    # NORMALIZE LANGUAGE
    # =====================================================

    def _normalize_lang(self, lang: str) -> str:

        mapping = {
            "en": "English",
            "vi": "Tiếng Việt",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean",
            "auto": "Auto",
        }

        return mapping.get(lang.lower(), lang)

    # =====================================================
    # SINGLE TRANSLATE
    # =====================================================

    async def _translate_one(
        self,
        client: httpx.AsyncClient,
        text: str,
        idx: int,
        from_lang: str, # not used because llm server can detect language automatically
        to_lang: str,
        context: str = "",
    ):

        if not text or not text.strip():
            return idx, ""

        to_lang = self._normalize_lang(to_lang)

        # -----------------------------
        # SYSTEM PROMPT
        # -----------------------------

        system_prompt = os.getenv(
            "TRANSLATE_SYSTEM_PROMPT",
            DEFAULT_SYSTEM_PROMPT,
        )

        if context:
            system_prompt += f"\n\nContext:\n{context}"

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
            "repeat_penalty": 1.1,
            "max_tokens": 256,
        }

        # -----------------------------
        # REQUEST
        # -----------------------------

        try:
            response = await client.post(
                self.url,
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            # Kiểm tra model có đang giải thích hay không
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

            logger.debug(f"[{idx}] Original: {text}")
            logger.debug(f"[{idx}] Translate: {content}")
            logger.debug(f"[{idx}] Translate success")

            return idx, content

        except Exception as e:
            logger.exception(f"[{idx}] Translate error: {e}")

            return idx, ""

    # =====================================================
    # BATCH TRANSLATE
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

        logger.info(f"Tencent async batch time: {end - start:.3f}s")

        return outputs

    # =====================================================
    # PUBLIC API
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
