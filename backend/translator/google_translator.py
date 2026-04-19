from typing import List
from translator.translator import ITranslator
from googletrans import Translator
import time
import logging

logger = logging.getLogger("TRANSLATOR")


class GoogleTranslatorEngine(ITranslator):
    def __init__(self):
        self.translator = Translator()

    def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str
    ) -> List[str]:
        if not texts:
            return []
        start_time = time.perf_counter()

        # Chọn delimiter hiếm để tránh bị trùng trong text
        delimiter = "<<<SEP>>>"

        # Nếu text có chứa delimiter thì escape trước
        escaped_texts = [t.replace(delimiter, " ") for t in texts]

        # Join thành 1 chuỗi
        combined_text = delimiter.join(escaped_texts)

        # Translate 1 lần
        translated_combined = self.translator.translate(
            combined_text, src=from_lang, dest=to_lang
        )

        # Split lại
        translated_list = str(translated_combined.text).split(delimiter)
        end_time = time.perf_counter()
        print(f"Translation completed in {end_time - start_time:.3f} seconds")
        return translated_list

    def translate(self, texts: str, from_lang: str, to_lang: str) -> str:
        start_time = time.perf_counter()
        result = self.translator.translate(texts, src=from_lang, dest=to_lang)
        end_time = time.perf_counter()
        print(f"Translation completed in {end_time - start_time:.3f} seconds")
        return result.text
