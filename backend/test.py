import asyncio
import logging
import time

from translator.libretranslate_translator import LibreTranslateTranslator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


async def main():
    translator = LibreTranslateTranslator(
        timeout=120,
        base_url="http://localhost:5000",
    )
    texts = [
        "Hello, how are you today?",
        "What?! You really did that?",
        "No way... I can't believe it!",
        "Wait... what happened?!",
        "Are you okay? 😊",
        "That's amazing! 😂",
        "「Hello!」",
        "He said: \"Don't worry!\"",
        "It's 100% true.",
        "This is a test!!!",
        "Really???",
        "...and then everything changed.",
        "Well... I don't know.",
        "Okay, let's go!",
        "Please wait a moment.",
        "Can you hear me?",
        "I can't believe this...",
        "Oh my god!!!",
        "What the hell?!",
        "This is crazy! 🤯",
        "Hello\nHow are you?",
        "This is\nmultiple lines\nof text.",
        "Line one.\nLine two.\nLine three.",
        "A & B < C > D",
        "Don't worry — everything is fine.",
        "He said, 'Hello!'",
        "She asked: \"Are you ready?\"",
        "Email: test@example.com",
        "Price: $100.00",
        "#hashtag @username",
        "100% FREE!!!",
        "Chapter 1: The Beginning",
        "Chapter ① — A New Adventure",
        "★ This is important ★",
        "♡ Thank you ♡",
        "♪ La la la ♪",
        "(What?)",
        "(Really?!)",
        "😂 😂 😂",
        "😀 😃 😄 😁",
        "!!! ??? ... --- ___ ===",
        "Wait!!!\nWhat are you doing?!",
        "I... I don't know...",
        "YES!!! We did it!!! 🎉",
    ]

    texts.extend([
        "Ithoughtyouweresupposedtocomehereyesterday.",
        "Whatareyoudoinghere?!",
        "Idon'tknowwhatyou'retalkingabout.",
        "Pleasewaitforme!",
        "Canyouhearme?",
        "Dontworry,everythingwillbefine.",
        "Ican'tbelievethisishappeningrightnow.",
        "Wherehaveyoubeenallthis time?",
        "YouneedtogetoutofhereNOW!",
        "Ithoughtweweresafehere...",
        "Whatdoyoumeanbythat?",
        "Hurryupwe're runningoutoftime!",
        "Ireallydon'twanttodothisagain.",
        "Didyouactuallysaythat?!",
        "Thereisn'tanyoneelseinthebuilding.",
        "IwasjustabouttoleavewhenIsawhim.",
        "Whyareyoulookingatmelikethat?",
        "Thisisn'twhatIexpectedatall.",
        "Youcan'tjustwalkawaylikenothinghappened.",
        "Ineedtoknowthetruth.",
        "Waitaminute,whatdidyoujustsay?",
        "Idon'tthinkwehaveenoughtime.",
        "Somethingiswrongwiththisplace.",
        "Don'ttouchthat!Youhavenoideawhatitdoes!",
        "Ifyougointhere,youwon'tbeabletocomeback.",
        "Iknowthissoundscrazybutyouhavetotrustme.",
        "Hestoodthereforamomentbeforefinallyanswering.",
        "Shelookedaroundtheroomandrealizedthatsomethingwasmissing.",
        "Ican'trememberwhereIputthekey.",
        "Everythingwasfineuntilthatstrangesoundstarted.",
        "Whydidn'tyoutellmethisbeforewecamehere?",
        "Ithoughtyouweremyfriend!",
        "Therewasn'tenoughtimetothinkaboutit.",
        "Youshouldn'thavecomebackhere.",
        "Iknowyou'rehiding somethingfromme.",
        "Please,justlistentomeforaminute.",
        "Idon'tcarewhatyouheard,it'snottrue.",
        "Youhavetobelieveme!",
        "Iwasn'texpectingtofindyouhere.",
        "Thedoorwaslocked,buthemanagedtoopenit.",
        "Ican'ttellifthisisarealplaceorjustadream.",
        "Wehavetofindawayoutbeforeit'stoolate.",
    ])

    print("=" * 70)
    print("LibreTranslate Batch Test")
    print("=" * 70)
    print(f"Input texts: {len(texts)}")
    print("Source: auto")
    print("Target: vi")
    print("Batch: ALL TEXTS IN ONE REQUEST")
    print()

    print("INPUT")
    print("-" * 70)

    for i, text in enumerate(texts, 1):
        print(f"[{i:02d}] {text}")

    print()
    print("TRANSLATING...")
    print("-" * 70)

    start_time = time.perf_counter()

    try:
        results = await translator.translate_batch(
            texts=texts,
            from_lang="en",
            to_lang="vi",
        )
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        print()
        print(f"ERROR: {type(e).__name__}: {e}")
        print(f"Time: {elapsed:.3f} seconds")
        return

    elapsed = time.perf_counter() - start_time

    print()
    print("RESULT")
    print("-" * 70)

    for i, (src, dst) in enumerate(zip(texts, results), 1):
        print(f"[{i:02d}]")
        print(f"ZH: {src}")
        print(f"VI: {dst}")
        print()

    print("=" * 70)
    print(f"Input count : {len(texts)}")
    print(f"Output count: {len(results)}")
    print(f"Total time  : {elapsed:.3f} seconds")

    if texts:
        print(f"Time/text   : {elapsed / len(texts):.3f} seconds")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())