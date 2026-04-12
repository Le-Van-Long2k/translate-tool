from pathlib import Path
import ctranslate2
import transformers
import time
from typing import List

from translator.translator import ITranslator

model_path_default = Path(__file__).parent / "nllb-600M-ct2-float16"


class NLLBTranslator(ITranslator):
    def __init__(
        self,
        model_path: str = str(model_path_default),
        device: str = "cuda",
    ):
        print(f"Đang tải model CTranslate2 từ: {model_path}")
        start_load = time.time()

        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            "facebook/nllb-200-distilled-600M"
        )

        self.translator = ctranslate2.Translator(
            model_path,
            device=device,
            device_index=0,
            compute_type="float16",  # Tối ưu cho RTX 3060
        )

        load_time = time.time() - start_load
        print(f"✅ Tải model hoàn tất trong {load_time:.3f} giây\n")

        # Mapping ngôn ngữ ngắn gọn
        self.lang_map = {
            "en": "eng_Latn",
            "vi": "vie_Latn",
            "zh": "zho_Hans",  # Trung Giản thể
            # "zh": "zho_Hant"  # Dùng nếu cần Phồn thể
        }

    def translate_batch(
        self, texts: List[str], from_lang: str, to_lang: str
    ) -> List[str]:
        if not texts:
            return []

        start_time = time.perf_counter()

        # Chuyển ngôn ngữ ngắn thành mã NLLB
        src_code = self.lang_map.get(from_lang, from_lang)
        tgt_code = self.lang_map.get(to_lang, to_lang)

        # Chuẩn bị target prefix
        target_prefix = [[tgt_code]] * len(texts)

        # Tokenize input
        batch_tokens = []
        for text in texts:
            tokenized = self.tokenizer(text, truncation=True, max_length=512).input_ids
            tokens = self.tokenizer.convert_ids_to_tokens(tokenized)
            batch_tokens.append(tokens)

        # Dịch batch với tham số tối ưu cho RTX 3060
        results = self.translator.translate_batch(
            batch_tokens,
            target_prefix=target_prefix,
            beam_size=1,
            max_decoding_length=512,
            batch_type="tokens",
            max_batch_size=512,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,
            sampling_temperature=0.7,
            sampling_topk=10,
        )

        # Decode kết quả
        translated = []
        total_tgt_tokens = 0

        for result in results:
            tokens = result.hypotheses[0]
            if tokens and tokens[0] == tgt_code:
                tokens = tokens[1:]

            total_tgt_tokens += len(tokens)

            text_out = self.tokenizer.decode(
                self.tokenizer.convert_tokens_to_ids(tokens), skip_special_tokens=True
            )
            translated.append(text_out)

        # Tính thời gian xử lý
        total_time = time.perf_counter() - start_time
        tokens_per_sec = total_tgt_tokens / total_time if total_time > 0 else 0

        # Print thông tin hiệu suất
        # print(
        #     f"📊 Dịch {len(texts)} câu | Thời gian: {total_time:.3f}s | "
        #     f"Tốc độ: {tokens_per_sec:.1f} tokens/s | "
        #     f"{from_lang} → {to_lang}"
        # )

        return translated
