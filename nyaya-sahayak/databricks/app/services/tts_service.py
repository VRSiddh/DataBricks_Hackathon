"""Sarvam Bulbul TTS (optional) — returns base64 WAV/MP3 when available."""

from __future__ import annotations

import base64
import logging
from typing import Optional

import httpx

from settings import get_settings

logger = logging.getLogger(__name__)

SARVAM_TTS = "https://api.sarvam.ai/text-to-speech"


async def synthesize_speech_base64(text: str, target_language_code: str = "en-IN") -> Optional[str]:
    s = get_settings()
    if not s.sarvam_api_key or not text.strip():
        return None
    payload = {
        "text": text[:2500],
        "target_language_code": target_language_code,
        "model": "bulbul:v3",
        "speaker": "shubh",
    }
    headers = {"api-subscription-key": s.sarvam_api_key, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=s.request_timeout_sec) as client:
            r = await client.post(SARVAM_TTS, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            # Response may be base64 audio field
            if isinstance(data, dict):
                for key in ("audios", "audio", "speech", "output"):
                    val = data.get(key)
                    if isinstance(val, str):
                        return val
                    if isinstance(val, list) and val and isinstance(val[0], str):
                        return val[0]
            if isinstance(data, (bytes, bytearray)):
                return base64.b64encode(data).decode("ascii")
    except Exception as e:  # noqa: BLE001
        logger.warning("Sarvam TTS failed: %s", e)
    return None
