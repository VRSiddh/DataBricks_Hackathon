"""Sarvam speech-to-text + user-profile scheme recommendation endpoints."""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.rag_fallback import match_schemes_for_profile
from settings import get_settings

router = APIRouter(prefix="/api", tags=["stt", "profile"])
logger = logging.getLogger(__name__)

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


# ── STT ──────────────────────────────────────────────────────────────────────

@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(..., description="WebM/WAV/OGG audio file from browser MediaRecorder"),
    language_code: str = Form("hi-IN", description="BCP-47 language code for transcription"),
):
    """Transcribe audio via Sarvam AI speech-to-text."""
    s = get_settings()
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    content_type = audio.content_type or "audio/webm"

    if s.sarvam_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    SARVAM_STT_URL,
                    headers={"api-subscription-key": s.sarvam_api_key},
                    files={"file": (audio.filename or "audio.webm", audio_bytes, content_type)},
                    data={"language_code": language_code, "model": "saarika:v2"},
                )
                if r.status_code == 200:
                    data = r.json()
                    transcript = (
                        data.get("transcript")
                        or data.get("text")
                        or data.get("transcription")
                        or ""
                    ).strip()
                    return {"transcript": transcript, "source": "sarvam"}
                logger.warning("Sarvam STT returned %d: %s", r.status_code, r.text[:300])
        except Exception as e:  # noqa: BLE001
            logger.warning("Sarvam STT call failed: %s", e)

    raise HTTPException(
        status_code=503,
        detail=(
            "Sarvam STT unavailable. "
            "Set SARVAM_API_KEY in the app environment or Databricks secret scope. "
            "Get a key at https://www.sarvam.ai"
        ),
    )


# ── Profile-based scheme recommendations ─────────────────────────────────────

class UserProfile(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    locality: Optional[str] = None
    caste: Optional[str] = None
    occupation: Optional[str] = None
    annual_income: Optional[str] = None
    education: Optional[str] = None


@router.post("/recommend-schemes")
async def recommend_schemes(profile: UserProfile):
    """Return government schemes personalised to a user profile."""
    schemes = match_schemes_for_profile(
        age=profile.age,
        gender=profile.gender,
        state=profile.state or profile.locality,
        caste=profile.caste,
        occupation=profile.occupation,
        income=profile.annual_income,
        num_results=10,
    )
    return {"schemes": schemes, "count": len(schemes)}
