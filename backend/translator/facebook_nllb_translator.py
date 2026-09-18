import logging
import time
from pathlib import Path
from typing import List, Optional

import ctranslate2
from transformers import AutoTokenizer

from translator.translator import ITranslator
from utils.languages import SourceLang, TargetLang

logger = logging.getLogger("TRANSLATOR")

# Mapping nội bộ → mã NLLB
NLLB_LANG_MAP = {
    SourceLang.auto: None,          # sẽ dùng lingua detect
    SourceLang.en: "eng_Latn",
    SourceLang.zh: "zho_Hans",
    SourceLang.ja: "jpn_Jpan",
    SourceLang.ko: "kor_Hang",
    TargetLang.vi: "vie_Latn",
}


class FacebookNLLBTranslator(ITranslator):
    def __init__(
        self,
        model_path: str = str(Path(__file__).resolve().parent / "models" / "nllb-600m-ct2"),
        device: str = "cpu",          # "cuda" hoặc "cpu"
        compute_type: str = "auto",    # "int8", "float16", "auto"...
        inter_threads: int = 1,
        intra_threads: int = 4,
    ):
        self.model_path = str(Path(model_path).expanduser())
        self.device = device
        self.compute_type = compute_type
        self.inter_threads = inter_threads
        self.intra_threads = intra_threads

        self.translator: Optional[ctranslate2.Translator] = None
        self.tokenizer = None
        self.detector = None

    def _ensure_loaded(self):
        if self.translator is not None:
            return

        logger.info(f"Loading NLLB model from {self.model_path} ({self.device})...")
        self.translator = ctranslate2.Translator(
            self.model_path,
            device=self.device,
            compute_type=self.compute_type,
            inter_threads=self.inter_threads,
            intra_threads=self.intra_threads,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "facebook/nllb-200-distilled-600M"
        )

        # Chỉ load khi cần auto-detect
        try:
            from lingua import Language, LanguageDetectorBuilder

            self.detector = (
                LanguageDetectorBuilder.from_languages(
                    Language.ENGLISH,
                    Language.CHINESE,
                    Language.JAPANESE,
                    Language.KOREAN,
                    Language.VIETNAMESE,
                )
                .build()
            )
            self._lingua_map = {
                Language.ENGLISH: "eng_Latn",
                Language.CHINESE: "zho_Hans",
                Language.JAPANESE: "jpn_Jpan",
                Language.KOREAN: "kor_Hang",
                Language.VIETNAMESE: "vie_Latn",
            }
        except ImportError:
            logger.warning("lingua not installed, auto-detect will fallback to eng_Latn")
            self.detector = None

        logger.info("NLLB model loaded")

    def _detect_lang(self, text: str) -> str:
        if self.detector is None:
            return "eng_Latn"
        lang = self.detector.detect_language_of(text)
        if lang is None:
            return "eng_Latn"
        return self._lingua_map.get(lang, "eng_Latn")

    def _resolve_src_lang(self, from_lang: str, text: str) -> str:
        # Nếu truyền auto hoặc không có trong map → detect
        mapped = NLLB_LANG_MAP.get(SourceLang(from_lang), None)
        if mapped is None or from_lang == "auto":
            return self._detect_lang(text)
        return mapped

    async def translate_batch(
        self,
        texts: List[str],
        from_lang: str = "auto",
        to_lang: str = "vi",
        context: str = "",
    ) -> List[str]:
        if not texts:
            return []

        start_time = time.perf_counter()
        to_lang_code = NLLB_LANG_MAP.get(TargetLang(to_lang), "vie_Latn")

        try:
            self._ensure_loaded()

            # Xử lý từng câu (vì src_lang có thể khác nhau khi auto)
            translated_texts = []
            for text in texts:
                src_lang = self._resolve_src_lang(from_lang, text)

                self.tokenizer.src_lang = src_lang
                tokens = self.tokenizer.convert_ids_to_tokens(
                    self.tokenizer.encode(text)
                )

                results = self.translator.translate_batch(
                    [tokens],
                    target_prefix=[[to_lang_code]],
                    beam_size=1,
                    max_decoding_length=256,
                )

                translated = self.tokenizer.decode(
                    self.tokenizer.convert_tokens_to_ids(results[0].hypotheses[0]),
                    skip_special_tokens=True,
                )
                translated_texts.append(translated)

                logger.info(
                    f"NLLB: [{src_lang}→{to_lang_code}] "
                    f"original={text!r} -> translated={translated!r}"
                )

            logger.info(
                f"NLLB Translate: {len(texts)} texts, "
                f"{time.perf_counter() - start_time:.2f}s"
            )
            return translated_texts

        except Exception:
            logger.exception("NLLB Translate failed")
            return texts

    async def close(self):
        self.translator = None
        self.tokenizer = None
        self.detector = None