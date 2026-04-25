"""Speech-to-text API — Sarvam Saaras v3 for 22+ Indian languages."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from services.stt_service import transcribe_audio

router = APIRouter(prefix="/api", tags=["stt"])


@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file (WebM, WAV, MP3, OGG, etc.)"),
    language: Optional[str] = Form("auto", description="BCP-47 language code or 'auto' for detection"),
):
    """
    Transcribe speech to text using Sarvam AI.

    Accepts audio files from browser MediaRecorder (typically WebM/Opus).
    Returns the transcribed text and detected language.
    """
    audio_bytes = await file.read()

    if not audio_bytes:
        return {"transcript": "", "error": "Empty audio file"}

    if len(audio_bytes) > 10 * 1024 * 1024:  # 10MB limit
        return {"transcript": "", "error": "Audio file too large (max 10MB)"}

    transcript = await transcribe_audio(audio_bytes, language_code=language or "auto")

    if transcript:
        return {
            "transcript": transcript,
            "language": language,
            "audio_size_bytes": len(audio_bytes),
        }
    else:
        return {
            "transcript": "",
            "error": "Transcription failed — check Sarvam API key or try again",
            "fallback": "browser",  # Signal frontend to fall back to Web Speech API
        }
