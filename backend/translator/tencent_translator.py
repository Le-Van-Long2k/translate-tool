import asyncio
import logging
import time
from typing import List

import httpx

from translator.translator import ITranslator

logger = logging.getLogger("TRANSLATOR")


class TencentTranslator(ITranslator):
    def __init__(
        self,
        model: str = "/models/Hy-MT2-1.8B-Q8_0.gguf",
        url: str = "http://llama-server:8080/v1/chat/completions",
        timeout: float = 60.0,
        max_concurrency: int = 3,
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
        from_lang: str,
        to_lang: str,
        context: str = "",
    ):

        if not text or not text.strip():
            return idx, ""

        from_lang = self._normalize_lang(from_lang)
        to_lang = self._normalize_lang(to_lang)

        # -----------------------------
        # SYSTEM PROMPT
        # -----------------------------

        system_prompt = (
            f"Bạn là một biên dịch viên chuyên nghiệp.\n"
            f"Tự động nhận biết ngôn ngữ của văn bản đầu vào.\n"
            f"Dịch sang {to_lang}.\n"
            f"Sử dụng văn phong tự nhiên, phù hợp với hội thoại trong manga/comic.\n"
            f"Nếu văn bản đầu vào có lỗi chính tả, ký tự bị nhận dạng sai, thiếu chữ hoặc câu bị dính chữ, hãy tự động khôi phục và sửa lại nội dung dựa trên ngữ cảnh trước khi dịch.\n"
            f"Chỉ xuất ra nội dung đã dịch.\n"
            f"Không giải thích.\n"
            f"Không thêm ghi chú.\n"
            f"Không lặp lại nội dung đầu vào.\n"
        )

        if context:
            system_prompt += f"\n\nContext:\n{context}"

        # -----------------------------
        # PAYLOAD
        # -----------------------------

        payload = {
            "model": self.model,
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

            content = (
                content.replace("<|im_end|>", "")
                .replace("<|file_separator|>", "")
                .replace("<end_of_turn>", "")
                .replace("</s>", "")
                .replace("<|im_start|>", "")
                .strip()
            )

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
