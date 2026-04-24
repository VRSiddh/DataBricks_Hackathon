"""Seed IPC → BNS mappings (extend via Delta table / official concordance)."""

from __future__ import annotations

import re
from typing import List

_SEED: list[tuple[int, int, str]] = [
    (302, 101, "Murder (illustrative — verify)"),
    (304, 103, "Attempt to murder"),
    (376, 63, "Sexual offences cluster — verify BNSS/BNS"),
    (420, 316, "Cheating / criminal breach cluster"),
    (499, 356, "Defamation"),
]


def find_ipc_mentions(text: str) -> list[int]:
    if not text:
        return []
    hits: set[int] = set()
    for m in re.finditer(r"\bIPC\b[^0-9]{0,40}Section\s*(\d{1,4})", text, flags=re.I):
        hits.add(int(m.group(1)))
    for m in re.finditer(r"\bIPC\s*[§s]*\s*(\d{1,4})\b", text, flags=re.I):
        hits.add(int(m.group(1)))
    for m in re.finditer(r"\bsections?\s*(\d{1,4})\b.*\bIPC\b", text, flags=re.I):
        hits.add(int(m.group(1)))
    return sorted(hits)


def ipc_hints_for_text(text: str) -> List[dict]:
    mentions = find_ipc_mentions(text)
    out: list[dict] = []
    for ipc in mentions:
        for ipc_sec, bns_sec, note in _SEED:
            if ipc_sec == ipc:
                out.append({"ipc_section": ipc_sec, "bns_section": bns_sec, "note": note})
                break
    return out


def format_ipc_context(text: str) -> str:
    hints = ipc_hints_for_text(text)
    if not hints:
        return "(none detected)"
    lines = [f"IPC {h['ipc_section']} → BNS {h['bns_section']}: {h['note']}" for h in hints]
    return "\n".join(lines)
