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
        model: str = "/models/HY-MT1.5-1.8B-Q8_0.gguf",
        url: str = "http://llama-server:8080/v1/chat/completions",
        timeout: float = 60.0,
        max_concurrency: int = 10,
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
            "vi": "Vietnamese",
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
            f"You are a professional translator.\n"
            f"Translate from {from_lang} to {to_lang}.\n"
            f"Use natural {to_lang} conversational style.\n"
            f"Only output the translated text.\n"
            f"Do not explain.\n"
            f"Do not add notes.\n"
            f"Do not repeat the input.\n"
            f"If the text is not actually written in {from_lang}, do not translate it.\n"
            f"Keep symbols, punctuation, emojis, and sound effects unchanged.\n"
            f"If translation is not possible or uncertain, return the original text unchanged."
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
            "max_tokens": 128,
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
            max_connections=100,
            max_keepalive_connections=20,
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
