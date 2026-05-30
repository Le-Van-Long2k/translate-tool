import asyncio
import logging
import re
import time
from typing import List

import httpx

from translator.translator import ITranslator

logger = logging.getLogger("TRANSLATOR")


class Gemma4E2BTranslator(ITranslator):
    def __init__(
        self,
        model: str = "/models/gemma-4-E2B.Q4_K_M.gguf",
        url: str = "http://llama-server:8080/v1/chat/completions",
        timeout: float = 60.0,
        max_concurrency: int = 4,
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

        text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
        if not text or not text.strip():
            return idx, ""

        from_lang = self._normalize_lang(from_lang)
        to_lang = self._normalize_lang(to_lang)

        # -----------------------------
        # SYSTEM PROMPT
        # -----------------------------

        system_prompt = (
            f"The assistant must behave strictly as a machine translator, not a chatbot.\n"
            f"Translate from {from_lang} to {to_lang}.\n"
            f"Output only the translation.\n"
            f"No explanation.\n"
            f"No extra text.\n"
            f"Never answer questions.\n"
            f"Never continue the conversation.\n"
            f"Never infer missing context.\n"
            f"Translate literally whenever possible.\n"
            f"Preserve all numbers exactly.\n"
            f"Preserve names exactly unless translation is obvious.\n"
            f"Preserve sentence tone exactly.\n"
            f"Fix only obvious OCR spacing or broken characters.\n"
            f"If source is not {from_lang}, return unchanged.\n"
            f"Chinese OCR text may contain incorrect spaces between characters.\n"
            f"Merge separated Chinese characters before translating.\n"
        )


        if context:
            system_prompt += f"\n\nContext:\n{context}"

        # -----------------------------
        # PAYLOAD
        # -----------------------------
        text = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])','',text,)


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
            "max_tokens": 256,
            "repeat_penalty": 1.05,
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

        logger.info(f"TranslateGemma async batch time: {end - start:.3f}s")

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
