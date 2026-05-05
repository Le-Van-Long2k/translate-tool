import asyncio
from translator.tencent_translator import TencentTranslatorEngine


def test_tencent_translator():
    """Test dịch Anh → Việt (ổn định với llama.cpp)"""

    # ⚠️ CHỌN ĐÚNG URL THEO ENV

    # 👉 Nếu chạy trong Docker container:
    url = "http://llama-server:8080/v1/chat/completions"

    # 👉 Nếu chạy ngoài host thì dùng:
    # url = "http://localhost:8121/v1/chat/completions"

    translator = TencentTranslatorEngine(
        model="/models/HY-MT1.5-1.8B-Q4_K_M.gguf",
        url=url,
        timeout=60.0,
        max_concurrency=3,  # 🔥 quan trọng: giảm để tránh refused
    )

    test_texts = [
        "Hello, how are you today?",
        "Artificial intelligence is transforming the world rapidly.",
        "The weather is very nice today, I want to go for a walk.",
        "Machine learning and deep learning are important fields in computer science.",
        "Please help me translate this sentence accurately and naturally.",
        "I love programming and learning new technologies every day.",
        "This is a test to check if the translator maintains the correct order and length.",
    ]

    print("🚀 Đang test Tencent Translator (EN → VI)...\n")

    try:
        results = translator.translate_batch(
            texts=test_texts,
            from_lang="English",
            to_lang="Vietnamese",
            context="Dịch tự nhiên, mượt mà, phù hợp văn phong tiếng Việt.",
        )

        print("=" * 80)
        print("KẾT QUẢ DỊCH:\n")

        for i, (original, translated) in enumerate(zip(test_texts, results)):
            print(f"{i + 1}. English : {original}")
            print(f"   Vietnamese: {translated}")
            print("-" * 70)

        print(f"✅ Hoàn thành! Dịch {len(results)} đoạn văn bản thành công.")

    except Exception as e:
        print(f"❌ Lỗi khi test: {e}")


# =========================
# Test async trực tiếp
# =========================
async def test_async():
    url = "http://llama-server:8080/v1/chat/completions"

    translator = TencentTranslatorEngine(
        url=url,
        max_concurrency=3,
    )

    texts = ["Good morning!", "How was your day?"]

    results = await translator._translate_batch_async(
        texts, "English", "Vietnamese", ""
    )

    for en, vi in zip(texts, results):
        print(f"{en} → {vi}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    test_tencent_translator()

    # asyncio.run(test_async())
