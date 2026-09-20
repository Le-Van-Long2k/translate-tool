import sys
import types


class _FakeLanguage:
    ENGLISH = "ENGLISH"
    JAPANESE = "JAPANESE"
    KOREAN = "KOREAN"
    CHINESE = "CHINESE"
    VIETNAMESE = "VIETNAMESE"


class _FakeDetector:
    def detect_language_of(self, text):
        return None


fake_lingua = types.ModuleType("lingua")
fake_lingua.Language = _FakeLanguage
fake_lingua.LanguageDetectorBuilder = type(
    "LanguageDetectorBuilder",
    (),
    {
        "from_languages": staticmethod(lambda *args, **kwargs: type("Builder", (), {"build": staticmethod(lambda: _FakeDetector())})()),
    },
)

sys.modules.setdefault("lingua", fake_lingua)

from backend.translator.mymemory_translator import MyMemoryTranslator


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_mymemory_invalid_source_lang_falls_back_to_en(monkeypatch):
    translator = MyMemoryTranslator(timeout=5)

    captured = {}

    def fake_get(url, params, timeout):
        captured["params"] = params
        return _FakeResponse({"responseData": {"translatedText": "Xin chào"}})

    monkeypatch.setattr("backend.translator.mymemory_translator.requests.get", fake_get)
    monkeypatch.setattr("backend.translator.mymemory_translator.detect_language", lambda text: "xx")

    result = translator._translate_one("hello", "unknown-language", "vi")

    assert result == "Xin chào"
    assert captured["params"]["langpair"].startswith("en|")
