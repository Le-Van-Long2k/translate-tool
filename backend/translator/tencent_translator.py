import asyncio
import httpx
import time
from typing import List
import logging

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
    # CORE TASK (GIỐNG TEST CODE)
    # =========================
    async def _translate_one(self, client, text, idx, from_lang, to_lang, context):
        if not text:
            return idx, ""

        prompt = f"Translate to Vietnamese: {text}"
        if context:
            prompt = f"Context: {context}\n\n{prompt}"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        try:
            resp = await client.post(self.url, json=payload)
            resp.raise_for_status()

            data = resp.json()

            content = (
                data
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            return idx, content

        except Exception as e:
            logger.error(f"[{idx}] Translate error: {e}")
            return idx, ""

    # =========================
    # BATCH (PURE GATHER LIKE TEST)
    # =========================
    async def _translate_batch_async(self, texts, from_lang, to_lang, context):
        start = time.perf_counter()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [
                self._translate_one(client, text, idx, from_lang, to_lang, context)
                for idx, text in enumerate(texts)
            ]

            results = await asyncio.gather(*tasks)

        outputs = [""] * len(texts)
        for idx, content in results:
            outputs[idx] = content

        end = time.perf_counter()
        print(f"Tencent async batch time: {end - start:.3f}s")

        return outputs

    # =========================
    # SYNC WRAPPER
    # =========================
    def translate_batch(
        self,
        texts: List[str],
        from_lang: str,
        to_lang: str,
        context: str = "",
    ) -> List[str]:

        if not texts:
            return []

        try:
            return asyncio.run(
                self._translate_batch_async(texts, from_lang, to_lang, context)
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._translate_batch_async(texts, from_lang, to_lang, context)
            )
            loop.close()
            return result
