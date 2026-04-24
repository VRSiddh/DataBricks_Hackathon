"""Extract text from PDFs/images (fast local path + optional Sarvam Document Intelligence)."""

from __future__ import annotations

import io
import logging
from typing import Tuple

from PIL import Image

logger = logging.getLogger(__name__)


def extract_text_pdf(data: bytes) -> str:
    import fitz  # PyMuPDF

    text_parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    return "\n".join(t for t in text_parts if t).strip()


def extract_text_image(data: bytes) -> str:
    try:
        import pytesseract
    except ImportError:
        pytesseract = None  # type: ignore
    img = Image.open(io.BytesIO(data)).convert("RGB")
    if pytesseract is None:
        return ""
    try:
        return pytesseract.image_to_string(img, lang="eng+hin").strip()
    except Exception as e:  # noqa: BLE001
        logger.warning("pytesseract failed: %s", e)
        return ""


def extract_text(data: bytes, content_type: str) -> Tuple[str, str]:
    """
    Returns (extracted_text, method_label).
    """
    ct = (content_type or "").lower()
    if "pdf" in ct or data[:4] == b"%PDF":
        return extract_text_pdf(data), "pymupdf"
    if ct.startswith("image/") or ct in ("image/jpeg", "image/png", "image/webp"):
        txt = extract_text_image(data)
        return txt, "pytesseract" if txt else "pytesseract_empty"

    # Heuristic: try PDF then image
    try:
        t = extract_text_pdf(data)
        if t:
            return t, "pymupdf"
    except Exception:
        pass
    t2 = extract_text_image(data)
    return t2, "pytesseract"
