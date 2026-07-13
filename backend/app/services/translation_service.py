"""Language detection and modular translation layer."""

from __future__ import annotations

from typing import Protocol

from langdetect import DetectorFactory, detect, lang_detect_exception

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.groq_service import get_groq

DetectorFactory.seed = 0
logger = get_logger("translation")

LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "ar": "Arabic",
    "ur": "Urdu",
    "hi": "Hindi",
}


class TranslationProvider(Protocol):
    def translate(self, text: str, source_lang: str, target_lang: str = "en") -> str: ...


class GroqTranslationProvider:
    def translate(self, text: str, source_lang: str, target_lang: str = "en") -> str:
        if target_lang != "en":
            raise NotImplementedError("Only English target is currently supported")
        return get_groq().translate_to_english(text, source_lang)


class PassthroughTranslationProvider:
    def translate(self, text: str, source_lang: str, target_lang: str = "en") -> str:
        return text


def get_translation_provider() -> TranslationProvider:
    settings = get_settings()
    if settings.groq_api_key:
        return GroqTranslationProvider()
    return PassthroughTranslationProvider()


def detect_language(text: str) -> str:
    snippet = (text or "").strip()
    if len(snippet) < 20:
        return "en"
    try:
        lang = detect(snippet[:2000])
        return lang
    except lang_detect_exception.LangDetectException:
        return "en"


def ensure_english(title: str, content: str) -> tuple[str, str, str, str]:
    """Return (title_en, content_en, language, original_content_language)."""
    combined = f"{title}\n{content}"
    language = detect_language(combined)
    provider = get_translation_provider()
    if language in ("en", "english"):
        return title, content, "en", content
    try:
        title_en = provider.translate(title, language)
        content_en = provider.translate(content[:8000], language) if content else ""
        return title_en, content_en, language, content
    except Exception as exc:
        logger.warning("translation_failed", error=str(exc), language=language)
        return title, content, language, content
