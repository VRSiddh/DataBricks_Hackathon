"""Sarvam Mayura translation (optional) + identity fallback."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from settings import get_settings

logger = logging.getLogger(__name__)

SARVAM_TRANSLATE = "https://api.sarvam.ai/translate"


async def translate_text(
    text: str,
    *,
    source_language_code: str,
    target_language_code: str,
    timeout: Optional[float] = None,
) -> str:
    if not text.strip():
        return text
    s = get_settings()
    if not s.sarvam_api_key:
        return text
    timeout = timeout or s.request_timeout_sec
    payload = {
        "input": text,
        "source_language_code": source_language_code,
        "target_language_code": target_language_code,
        "model": "mayura:v1",
    }
    headers = {"api-subscription-key": s.sarvam_api_key, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(SARVAM_TRANSLATE, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            # Sarvam may return translated_text or similar — handle common shapes
            if isinstance(data, dict):
                for key in ("translated_text", "output", "translation", "text"):
                    if key in data and isinstance(data[key], str):
                        return data[key]
            if isinstance(data, str):
                return data
    except Exception as e:  # noqa: BLE001
        logger.warning("Sarvam translate failed, returning original: %s", e)
    return text


async def to_english_for_rag(text: str, user_lang: str) -> str:
    if user_lang.lower().startswith("en"):
        return text
    return await translate_text(text, source_language_code=user_lang, target_language_code="en-IN")


async def to_user_language(text: str, user_lang: str) -> str:
    if user_lang.lower().startswith("en"):
        return text
    return await translate_text(text, source_language_code="en-IN", target_language_code=user_lang)
