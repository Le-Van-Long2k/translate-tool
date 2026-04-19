from typing import List
import ollama
import time
import re
import logging

logger = logging.getLogger("TRANSLATOR")


class TencentTranslatorEngine:
    def __init__(self, model: str = "MedAIBase/Tencent-HY-MT1.5:7b"):
        self.model = model

    def _call_model(self, prompt: str) -> str:
        response = ollama.generate(
            model=self.model,
            prompt=prompt,
            options={
                "temperature": 0,
                "num_ctx": 256,
                "num_predict": 256,
                "top_k": 1,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        )
        return response["response"].strip()

    def translate(self, text: str, from_lang: str = "en", to_lang: str = "vi") -> str:
        if not text:
            return ""
        start_time = time.perf_counter()

        prompt = f"Translate to Vietnamese:\n{text}"

        start_time = time.perf_counter()
        result = self._call_model(prompt)
        end_time = time.perf_counter()

        # logger.info(f"Translate time: {end_time - start_time:.3f}s")
        end_time = time.perf_counter()
        print(f"Tencent translate time: {end_time - start_time:.3f}s")
        return result

    def translate_batch(
        self, texts: List[str], from_lang: str = "en", to_lang: str = "vi"
    ) -> List[str]:
        if not texts:
            return []

        start_time = time.perf_counter()

        delimiter = "<<<#>>>"

        # escape delimiter nếu có sẵn
        escaped_texts = [t.replace(delimiter, " ") for t in texts]

        # wrap delimiter
        wrapped_texts = [f"<sn>{t}<bn>" for t in escaped_texts]
        combined_text = "".join(wrapped_texts)

        # ✅ PROMPT
        prompt = f"""Translate the following segment into Vietnamese, without additional explanation.

{combined_text}
    """

        raw_output = self._call_model(prompt)

        # ==============================
        # 🧹 CLEAN OUTPUT
        # ==============================
        cleaned = raw_output.strip()
        # ==============================
        # ✂️ REMOVE HEADER (phần hướng dẫn)
        # ==============================
        parts = cleaned.split("\n\n", 1)

        if len(parts) == 2:
            cleaned = parts[1].strip()
            print("XXXXXXXXXX")
            print(cleaned)

        # ==============================
        # 🔪 EXTRACT ALL <sn>...<bn>
        # ==============================
        parts = re.findall(r"<sn>(.*?)<bn>", cleaned, flags=re.IGNORECASE | re.DOTALL)

        # cleanup
        results = [p.strip() for p in parts if p.strip()]

        end_time = time.perf_counter()
        print(f"Tencent translate time: {end_time - start_time:.3f}s")

        return results
