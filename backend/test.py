import asyncio
import logging

from translator.tencent_translator import TencentTranslator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


async def main():
    translator = TencentTranslator()

    tests = [
        # =========================================================
        # Japanese - OCR lỗi / manga
        # =========================================================
        ("ja", "こん にちは、元気ですか？"),
        ("ja", "今日はいい天気で すね。"),
        ("ja", "どうしてここにいる  の？"),
        ("ja", "まさ力……そんなはず ない！"),
        ("ja", "お前はいったい何者な んだ？"),

        # =========================================================
        # English - OCR lỗi / game
        # =========================================================
        ("en", "I can't be lieve you came back."),
        ("en", "What are you do ing here?"),
        ("en", "Th1s place doesn't feel r1ght..."),
        ("en", "We have to f1nd the key before it's too late!"),
        ("en", "I-I didn't mean to d0 that..."),

        # =========================================================
        # Chinese - OCR lỗi
        # =========================================================
        ("zh", "你怎么会在这 里？"),
        ("zh", "我不知 道你在说什么。"),
        ("zh", "这不可能……你明明已 经死了！"),
        ("zh", "快 点离开这里！"),
        ("zh", "你到底想 要什么？"),

        # =========================================================
        # Korean - OCR lỗi / game
        # =========================================================
        ("ko", "왜 여기에 있 는 거야?"),
        ("ko", "이건 말도 안 돼..."),
        ("ko", "빨리 여기 서 나가야 해!"),
        ("ko", "도대체 무슨 일이 일어 난 거야?"),
        ("ko", "나를 믿 어 줘. 부탁이야."),
    ]

    # -------------------------------------------------
    # Test từng ngôn ngữ → Vietnamese
    # -------------------------------------------------

    for from_lang in ["ja", "en", "zh", "ko"]:
        texts = [
            text
            for lang, text in tests
            if lang == from_lang
        ]

        print(f"\n{'=' * 60}")
        print(f"TEST: {from_lang} → vi")
        print(f"{'=' * 60}")

        results = await translator.translate_batch(
            texts=texts,
            from_lang=from_lang,
            to_lang="vi",
        )

        for i, (original, translated) in enumerate(
            zip(texts, results),
            1,
        ):
            print(f"\n[{i}]")
            print(f"IN : {original}")
            print(f"OUT: {translated}")


if __name__ == "__main__":
    asyncio.run(main())