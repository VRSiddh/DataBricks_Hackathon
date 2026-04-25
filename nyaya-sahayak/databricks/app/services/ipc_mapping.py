"""IPC → BNS mappings (bundled CSV + small seed for regex-detected sections)."""

from __future__ import annotations

import csv
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

_APP_ROOT = Path(__file__).resolve().parent.parent
_IPC_CSV = _APP_ROOT / "data" / "ipc_bns_mapping.csv"

_SEED: list[tuple[int, int, str]] = [
    (302, 101, "Murder (illustrative — verify)"),
    (304, 103, "Attempt to murder"),
    (376, 63, "Sexual offences cluster — verify BNSS/BNS"),
    (420, 316, "Cheating / criminal breach cluster"),
    (499, 356, "Defamation"),
]


@lru_cache(maxsize=1)
def _csv_mappings() -> list[tuple[int, int, str]]:
    rows: list[tuple[int, int, str]] = []
    if not _IPC_CSV.is_file():
        return rows
    try:
        with _IPC_CSV.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                try:
                    ipc = int((r.get("ipc_section") or r.get("ipc") or "").strip())
                    bns = int((r.get("bns_section") or r.get("bns") or "").strip())
                    note = (r.get("mapping_note") or r.get("note") or "").strip() or "See official concordance"
                    rows.append((ipc, bns, note))
                except (TypeError, ValueError):
                    continue
    except OSError as e:
        logger.warning("Could not read IPC mapping CSV: %s", e)
    if rows:
        logger.info("Loaded %d IPC→BNS rows from %s", len(rows), _IPC_CSV)
    return rows


def _all_mappings() -> list[tuple[int, int, str]]:
    merged: dict[int, tuple[int, int, str]] = {}
    for ipc, bns, note in _SEED:
        merged[ipc] = (ipc, bns, note)
    for ipc, bns, note in _csv_mappings():
        merged[ipc] = (ipc, bns, note)
    return list(merged.values())


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
    for m in re.finditer(r"\bsection\s*(\d{1,4})\b.*\bIPC\b", text, flags=re.I):
        hits.add(int(m.group(1)))
    return sorted(hits)


def ipc_hints_for_text(text: str) -> List[dict]:
    mentions = find_ipc_mentions(text)
    out: list[dict] = []
    table = _all_mappings()
    for ipc in mentions:
        for ipc_sec, bns_sec, note in table:
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
