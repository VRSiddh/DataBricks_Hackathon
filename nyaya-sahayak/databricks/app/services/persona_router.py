"""Lightweight style nudge (main adaptation lives in the LLM system prompt)."""

from __future__ import annotations

import re

from prompts.persona_templates import LAY_HINT, PRO_HINT


_PRO_MARKERS = re.compile(
    r"\b(mens rea|actus reus|bail|anticipatory|charge\s*sheet|FIR|summons|"
    r"complaint|ingredients|statute|section\s*\d+|BNS|IPC|evidence\s*act|CrPC|BNSS)\b",
    re.I,
)


def style_addon(user_text: str, ocr_sample: str) -> str:
    blob = f"{user_text}\n{ocr_sample[:2000]}"
    if _PRO_MARKERS.search(blob):
        return PRO_HINT
    return LAY_HINT
