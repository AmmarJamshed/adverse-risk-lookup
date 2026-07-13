"""Groq LLM client with JSON helpers and modular provider boundary."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.prompts import load_prompt

logger = get_logger("groq")


class GroqService:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.translation_model = settings.groq_translation_model
        self._client: Optional[Groq] = None

    @property
    def client(self) -> Groq:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    def chat(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        response = self.client.chat.completions.create(
            model=model or self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""

    def chat_json(
        self,
        system: str,
        user: str,
        *,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        raw = self.chat(system, user, model=model, temperature=temperature)
        return parse_json_response(raw)

    def analyze_article(self, title: str, content: str) -> dict[str, Any]:
        system = load_prompt("analyze_article")
        user = f"TITLE:\n{title}\n\nBODY:\n{content[:12000]}"
        logger.info("ai_analysis_start", title=title[:120])
        result = self.chat_json(system, user)
        logger.info(
            "ai_analysis_done",
            relevant=result.get("is_relevant"),
            severity=result.get("severity"),
        )
        return result

    def translate_to_english(self, text: str, source_lang: str) -> str:
        if not text or source_lang.lower() in ("en", "english"):
            return text
        system = load_prompt("translate")
        user = f"Source language code: {source_lang}\n\nText:\n{text[:10000]}"
        logger.info("translation_start", source_lang=source_lang)
        return self.chat(
            system,
            user,
            model=self.translation_model,
            temperature=0.0,
            max_tokens=4096,
        ).strip()

    def explain_match(
        self,
        article_summary: str,
        risk_name: str,
        risk_description: str,
        similarity: float,
    ) -> dict[str, Any]:
        system = load_prompt("explain_match")
        user = (
            f"SIMILARITY: {similarity:.4f}\n\n"
            f"ARTICLE:\n{article_summary[:4000]}\n\n"
            f"RISK NAME: {risk_name}\n"
            f"RISK DESCRIPTION: {risk_description or ''}\n"
        )
        return self.chat_json(system, user)

    def suggest_emerging_risk(self, theme_context: str) -> dict[str, Any]:
        system = load_prompt("emerging_risk")
        return self.chat_json(system, theme_context[:8000])

    def assistant_reply(self, question: str, context: str) -> str:
        system = load_prompt("assistant")
        user = f"CONTEXT:\n{context[:12000]}\n\nQUESTION:\n{question}"
        return self.chat(system, user, temperature=0.3, max_tokens=2048)


def parse_json_response(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            logger.warning("json_parse_failed", preview=text[:200])
    return {"raw": raw, "parse_error": True}


_groq: Optional[GroqService] = None


def get_groq() -> GroqService:
    global _groq
    if _groq is None:
        _groq = GroqService()
    return _groq
