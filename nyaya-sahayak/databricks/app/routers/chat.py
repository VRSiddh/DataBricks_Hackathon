"""Follow-up chat with lightweight in-memory sessions + TTL eviction."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prompts.system_prompt import SYSTEM_PROMPT, build_user_prompt
from services import ipc_mapping
from services.llm_service import chat_complete
from services.persona_router import style_addon
from services.rag_service import retrieve_context
from services.scheme_service import format_scheme_context_for_llm, match_schemes
from services.translation_service import to_english_for_rag, to_user_language
from services.tts_service import synthesize_speech_base64

router = APIRouter(prefix="/api", tags=["chat"])

# ─── Session store with TTL ──────────────────────────────────────────────────

SESSION_TTL_SEC = 3600  # 1 hour
MAX_SESSIONS = 200

_SESSIONS: Dict[str, Dict] = {}  # session_id → {"history": [...], "last_access": float}


def _get_session(session_id: str) -> List[dict]:
    """Get or create session history; evict stale sessions."""
    now = time.time()
    # Evict expired sessions periodically
    if len(_SESSIONS) > MAX_SESSIONS:
        expired = [sid for sid, s in _SESSIONS.items() if now - s["last_access"] > SESSION_TTL_SEC]
        for sid in expired:
            del _SESSIONS[sid]

    entry = _SESSIONS.setdefault(session_id, {"history": [], "last_access": now})
    entry["last_access"] = now
    return entry["history"]


class ChatBody(BaseModel):
    session_id: str
    message: str
    language: str = Field("en-IN")
    document_context: Optional[str] = Field(
        None,
        description="OCR / prior doc text to keep grounded (client should resend short excerpt).",
    )


@router.post("/chat")
async def chat_turn(body: ChatBody):
    hist = _get_session(body.session_id)
    rag_query = await to_english_for_rag(f"{body.message}\n{body.document_context or ''}"[:8000], body.language)
    rag_context, hits = retrieve_context(rag_query)
    ipc_ctx = ipc_mapping.format_ipc_context(body.document_context or body.message)

    style = style_addon(body.message, body.document_context or "")
    # Scheme context — auto-match based on message keywords
    scheme_matches = match_schemes(query=body.message)
    scheme_ctx = format_scheme_context_for_llm(scheme_matches)

    user_prompt = build_user_prompt(
        ocr_text=(body.document_context or "")[:12000],
        rag_context=rag_context or "(none)",
        ipc_context=ipc_ctx,
        user_query=body.message,
        response_language=body.language,
        scheme_context=scheme_ctx,
    )

    messages: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + style}]
    messages.extend(hist[-8:])
    messages.append({"role": "user", "content": user_prompt})

    try:
        answer_en = chat_complete(messages)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"LLM error: {e}") from e

    answer_out = await to_user_language(answer_en, body.language)
    audio_b64 = await synthesize_speech_base64(answer_out, target_language_code=body.language)

    hist.append({"role": "user", "content": body.message})
    hist.append({"role": "assistant", "content": answer_out})

    return {
        "reply": answer_out,
        "relevant_sections": hits,
        "ipc_mapping": ipc_mapping.ipc_hints_for_text(body.document_context or ""),
        "audio_base64": audio_b64,
    }
