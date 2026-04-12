import re
from typing import List
import json
import requests
from translator.translator import ITranslator
from llama_cpp import Llama
import time
import logging

logger = logging.getLogger(__name__)


class Gemma4E2BClientTranslator(ITranslator):
    def __init__(self, url="http://localhost:8121/completion"):
        self.url = url
        logger.info(f"Gemma4E2B Client Translator initialized with URL: {self.url}")

    def _call(self, prompt: str) -> str:
        res = requests.post(
            self.url,
            json={
                "prompt": prompt,
                "n_predict": 512,
                "temperature": 0.1,
            },
            timeout=60,
        )

        res.raise_for_status()
        data = res.json()

        return data.get("content")

    def _build_prompt(self, texts: List[str]) -> str:

        texts = [self.clean_ocr_text(text) for text in texts]

        return f"""
        Bạn là hệ thống dịch tiếng Việt.

        QUY TẮC TUYỆT ĐỐI:
        - Output phải có đúng {len(texts)} phần tử, tương ứng với số lượng input
        - Mỗi phần tử tương ứng 1 input theo đúng thứ tự
        - KHÔNG được bỏ bất kỳ dòng nào
        - KHÔNG được gộp dòng
        - KHÔNG được thiếu phần tử
        - KHÔNG được coi dòng nào là rác hay bỏ qua
        - Dù là watermark / noise / ký tự lạ cũng phải giữ nguyên và chỉ dịch nếu có nghĩa
        - Neu trong cau da dich co ki tu khong phu hop voi tieng viet thi xoa no di
        - Chỉ trả về JSON array hợp lệ
        - Không chữ, không tiêu đề, không giải thích
        - Không được thêm "DỮ LIỆU", "INPUT", "OUTPUT"
        - Không markdown

        INPUT:
        {json.dumps(texts, ensure_ascii=False, indent=2)}

        OUTPUT:
        """

    def clean_ocr_text(self, text: str) -> str:
        pattern = r"[^\w\s\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\.\,\!\?\:\;\-\(\)\[\]\"\'\/\@\•\…❤]"

        text = re.sub(pattern, "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def parse_llm_json(self, output: str):
        try:
            start = output.rfind("[")
            end = output.rfind("]")
            if start == -1 or end == -1:
                return None

            data = output[start : end + 1]
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return None

    def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str, context: str = ""
    ) -> List[str]:
        if not texts:
            return []
        start_time = time.time()
        prompt = self._build_prompt(texts)
        output = self._call(prompt)

        parsed_output = self.parse_llm_json(output)
        if parsed_output is None:
            logger.warning(
                "⚠️ Cảnh báo: Không tìm thấy JSON hợp lệ trong output. Trả về input gốc."
            )
            logger.info("Input nhận được: %s", texts)
            logger.info("Output nhận được: %s", output)
            return texts
        if len(parsed_output) != len(texts):
            logger.warning(
                "⚠️ Cảnh báo: Số lượng output không khớp với input. Trả về input gốc."
            )
            logger.info("Input nhận được: %s", texts)
            logger.info("Output nhận được: %s", output)
            return texts

        end_time = time.time()
        logger.info(f"Translation time: {end_time - start_time:.3f} seconds")

        return parsed_output


class Gemma4E2BLlamaCppPythonTranslator(ITranslator):
    def __init__(
        self, model_path="/home/test/llama.cpp/custom-models/gemma-4-e2b-it-Q8_0.gguf"
    ):

        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=30,
            n_batch=512,
            n_ubatch=512,
            n_ctx=2048,
            verbose=False,
            flash_attn=True,
            logits_all=False,
            embedding=False,
        )
        logger.info(
            f"Gemma4E2B Llama.cpp Translator initialized with model: {model_path}"
        )

    def _build_prompt(self, texts: List[str]) -> str:

        texts = [self.clean_ocr_text(text) for text in texts]

        return f"""
        Bạn là hệ thống dịch tiếng Việt.

        QUY TẮC TUYỆT ĐỐI:
        - Output phải có đúng {len(texts)} phần tử, tương ứng với số lượng input
        - Mỗi phần tử tương ứng 1 input theo đúng thứ tự
        - KHÔNG được bỏ bất kỳ dòng nào
        - KHÔNG được gộp dòng
        - KHÔNG được thiếu phần tử
        - KHÔNG được coi dòng nào là rác hay bỏ qua
        - Dù là watermark / noise / ký tự lạ cũng phải giữ nguyên và chỉ dịch nếu có nghĩa
        - Neu trong cau da dich co ki tu khong phu hop voi tieng viet thi xoa no di
        - Chỉ trả về JSON array hợp lệ
        - Không chữ, không tiêu đề, không giải thích
        - Không được thêm "DỮ LIỆU", "INPUT", "OUTPUT"
        - Không markdown

        INPUT:
        {json.dumps(texts, ensure_ascii=False, indent=2)}

        OUTPUT:
        """

    def clean_ocr_text(self, text: str) -> str:
        pattern = r"[^\w\s\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\.\,\!\?\:\;\-\(\)\[\]\"\'\/\@\•\…❤]"

        text = re.sub(pattern, "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def parse_llm_json(self, output: str):
        try:
            start = output.rfind("[")
            end = output.rfind("]")
            if start == -1 or end == -1:
                return None

            data = output[start : end + 1]
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return None

    def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str, context: str = ""
    ) -> List[str]:
        if not texts:
            return []
        start_time = time.time()
        prompt = self._build_prompt(texts)

        res = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional English to Vietnamese translator.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=512,
        )

        output_text = res["choices"][0]["message"]["content"]
        parsed_output = self.parse_llm_json(output_text)
        if parsed_output is None:
            logger.warning(
                "⚠️ Cảnh báo: Không tìm thấy JSON hợp lệ trong output. Trả về input gốc."
            )
            logger.info("Input nhận được: %s", texts)
            logger.info("Output nhận được: %s", output_text)
            return texts
        if len(parsed_output) != len(texts):
            logger.warning(
                "⚠️ Cảnh báo: Số lượng output không khớp với input. Trả về input gốc."
            )
            logger.info("Input nhận được: %s", texts)
            logger.info("Output nhận được: %s", output_text)
            return texts
        end_time = time.time()
        logger.info(f"Translation time: {end_time - start_time:.3f} seconds")
        return parsed_output
