"""Sarvam Saaras v3 Speech-to-Text — multilingual STT for 22+ Indian languages."""

from __future__ import annotations

import base64
import logging
from typing import Optional

import httpx

from settings import get_settings

logger = logging.getLogger(__name__)

SARVAM_STT = "https://api.sarvam.ai/speech-to-text"


async def transcribe_audio(
    audio_bytes: bytes,
    language_code: str = "auto",
    model: str = "saaras:v3",
) -> Optional[str]:
    """
    Transcribe audio using Sarvam STT API.

    Args:
        audio_bytes: Raw audio data (WAV, MP3, WebM, OGG, etc.)
        language_code: BCP-47 code like "hi-IN", "en-IN", or "auto" for auto-detect
        model: Sarvam model name (saaras:v3 recommended)

    Returns:
        Transcribed text, or None on failure.
    """
    s = get_settings()
    if not s.sarvam_api_key:
        logger.warning("Sarvam API key not set; STT unavailable.")
        return None

    if not audio_bytes:
        return None

    headers = {"api-subscription-key": s.sarvam_api_key}

    # Sarvam STT uses multipart form-data
    files = {"file": ("recording.webm", audio_bytes, "audio/webm")}
    data = {
        "model": model,
        "language_code": language_code if language_code != "auto" else "unknown",
    }

    try:
        async with httpx.AsyncClient(timeout=s.request_timeout_sec) as client:
            r = await client.post(SARVAM_STT, files=files, data=data, headers=headers)
            r.raise_for_status()
            result = r.json()

            # Extract transcript from response
            if isinstance(result, dict):
                transcript = (
                    result.get("transcript")
                    or result.get("text")
                    or result.get("transcription")
                    or ""
                )
                lang_detected = result.get("language_code", language_code)
                logger.info("STT success: %d chars, lang=%s", len(transcript), lang_detected)
                return transcript.strip() if transcript else None

            return None

    except httpx.HTTPStatusError as e:
        logger.warning("Sarvam STT HTTP error %d: %s", e.response.status_code, e.response.text[:200])
        return None
    except Exception as e:  # noqa: BLE001
        logger.warning("Sarvam STT failed: %s", e)
        return None


async def transcribe_base64(
    audio_base64: str,
    language_code: str = "auto",
) -> Optional[str]:
    """Convenience wrapper: transcribe base64-encoded audio."""
    try:
        audio_bytes = base64.b64decode(audio_base64)
    except Exception:
        return None
    return await transcribe_audio(audio_bytes, language_code)
