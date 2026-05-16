import asyncio
import logging
import time
from typing import List

import httpx

from translator.translator import ITranslator

logger = logging.getLogger("TRANSLATOR")


class TencentTranslatorEngine(ITranslator):
    def __init__(
        self,
        model: str = "/models/HY-MT1.5-1.8B-Q4_K_M.gguf",
        url: str = "http://llama-server:8080/v1/chat/completions",
        timeout: float = 60.0,
        max_concurrency: int = 10,
    ):
        self.model = model
        self.url = url
        self.timeout = timeout
        self.max_concurrency = max_concurrency

    # =========================
    # SINGLE TRANSLATE
    # =========================
    async def _translate_one(
        self,
        client: httpx.AsyncClient,
        text: str,
        idx: int,
        from_lang: str,
        to_lang: str,
        context: str,
    ):
        if not text:
            return idx, ""
        
        if from_lang == "en":
            from_lang = "English"
        
        if to_lang == "vi":
            to_lang = "Vietnamess"

        prompt = f"""
Translate the following text from {from_lang} to {to_lang}.

Only return the translated text.
Do not explain.
Do not add notes.

Text:
{text}
""".strip()

        if context:
            prompt = f"""
Context:
{context}

{prompt}
""".strip()

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.2,
        }

        try:
            response = await client.post(
                self.url,
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            content = (
                data
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            logger.info(f"[{idx}] Original: {text}")
            logger.info(f"[{idx}] Translate: {content}")
            logger.info(f"[{idx}] Translate success")

            return idx, content

        except Exception as e:
            logger.exception(
                f"[{idx}] Translate error: {e}"
            )

            return idx, ""

    # =========================
    # BATCH TRANSLATE
    # =========================
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

        semaphore = asyncio.Semaphore(
            self.max_concurrency
        )

        async with httpx.AsyncClient(
            timeout=self.timeout
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

            tasks = [
                run_task(text, idx)
                for idx, text in enumerate(texts)
            ]

            results = await asyncio.gather(
                *tasks,
                return_exceptions=False,
            )

        outputs = [""] * len(texts)

        for idx, content in results:
            outputs[idx] = content

        end = time.perf_counter()

        logger.info(
            f"Tencent async batch time: "
            f"{end - start:.3f}s"
        )

        return outputs

    # =========================
    # PUBLIC API
    # =========================
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