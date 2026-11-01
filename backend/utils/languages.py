from enum import Enum


class SourceLang(str, Enum):
    en = "English"
    zh = "Chinese"
    ja = "Japanese"
    ko = "Korean"
    auto = "auto"


class TargetLang(str, Enum):
    vi = "Vietnamese"
