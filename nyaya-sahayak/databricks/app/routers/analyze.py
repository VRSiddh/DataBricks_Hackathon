"""Document upload → OCR → RAG → LLM → optional translate + TTS."""

from __future__ import annotations

import base64
import re
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

try:
    import mlflow
except ImportError:  # local dev without full Databricks stack
    mlflow = None  # type: ignore
from pydantic import BaseModel, Field

from prompts.system_prompt import SYSTEM_PROMPT, build_user_prompt
from services import ipc_mapping
from services.llm_service import chat_complete
from services.ocr_service import extract_text
from services.persona_router import style_addon
from services.rag_service import retrieve_context
from services.translation_service import to_english_for_rag, to_user_language
from services.tts_service import synthesize_speech_base64

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeJsonBody(BaseModel):
    file_base64: str = Field(..., description="Base64-encoded file bytes")
    file_type: str = Field("application/pdf", description="MIME type")
    language: str = Field("en-IN", description="Preferred response language (BCP-47)")
    query: Optional[str] = None


def _decode_file(b64: str) -> bytes:
    try:
        return base64.b64decode(b64, validate=False)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid base64: {e}") from e


def _extract_steps(text: str) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    steps = []
    for ln in lines:
        if re.match(r"^\d+[\).\]]\s+", ln):
            steps.append(re.sub(r"^\d+[\).\]]\s+", "", ln))
    return steps[:10]


def _summary_from_answer(text: str) -> str:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paras[0][:800] if paras else text[:800]


@router.post("/analyze")
async def analyze_json(body: AnalyzeJsonBody):
    raw = _decode_file(body.file_base64)
    return await _run_pipeline(
        file_bytes=raw,
        content_type=body.file_type,
        language=body.language,
        query=body.query,
    )


@router.post("/analyze_upload")
async def analyze_multipart(
    file: UploadFile = File(...),
    language: str = Form("en-IN"),
    query: Optional[str] = Form(None),
):
    raw = await file.read()
    ct = file.content_type or "application/octet-stream"
    return await _run_pipeline(file_bytes=raw, content_type=ct, language=language, query=query)


async def _run_pipeline(*, file_bytes: bytes, content_type: str, language: str, query: Optional[str]):
    t0 = time.perf_counter()
    if len(file_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 8MB for this demo).")

    ocr_text, ocr_method = extract_text(file_bytes, content_type)
    if not ocr_text or len(ocr_text.strip()) < 20:
        raise HTTPException(
            status_code=422,
            detail="Could not extract enough text (blurry scan or empty PDF). Try a clearer image or text-based PDF.",
        )

    rag_query = await to_english_for_rag(f"{query or ''}\n\n{ocr_text}"[:8000], language)
    rag_context, hits = retrieve_context(rag_query)
    ipc_ctx = ipc_mapping.format_ipc_context(ocr_text)

    style = style_addon(query or "", ocr_text)
    user_prompt = build_user_prompt(
        ocr_text=ocr_text[:12000],
        rag_context=rag_context or "(no retrieval results — say you don't know if needed)",
        ipc_context=ipc_ctx,
        user_query=query,
        response_language=language,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + style},
        {"role": "user", "content": user_prompt},
    ]

    try:
        answer_en = chat_complete(messages)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"LLM error: {e}") from e

    answer_out = await to_user_language(answer_en, language)
    audio_b64 = await synthesize_speech_base64(answer_out, target_language_code=language)

    latency = time.perf_counter() - t0

    if mlflow is not None:
        try:
            with mlflow.start_run(run_name="analyze"):
                mlflow.log_param("ocr_method", ocr_method)
                mlflow.log_param("response_language", language)
                mlflow.log_metric("latency_sec", latency)
                mlflow.log_metric("ocr_chars", len(ocr_text))
                mlflow.log_metric("rag_hits", len(hits))
        except Exception:
            pass

    return {
        "analysis": {
            "document_summary": _summary_from_answer(answer_out),
            "relevant_sections": hits,
            "advice": answer_out,
            "action_steps": _extract_steps(answer_out),
            "ipc_mapping": ipc_mapping.ipc_hints_for_text(ocr_text),
            "ocr_method": ocr_method,
            "document_text_preview": ocr_text[:4000],
        },
        "audio_base64": audio_b64,
        "detected_language": language,
        "response_language": language,
        "session_id": str(uuid.uuid4()),
        "latency_sec": round(latency, 3),
    }
