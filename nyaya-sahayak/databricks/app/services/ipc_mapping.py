"""IPC → BNS mapping: loads full correspondence from CSV at startup, falls back to seed."""

from __future__ import annotations

import csv
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent
_CSV_CANDIDATES = [
    _HERE.parent.parent.parent / "data" / "ipc_bns_mapping.csv",   # repo root: nyaya-sahayak/data/
    _HERE.parent / "data" / "ipc_bns_mapping.csv",
    Path(os.environ.get("NYAYA_IPC_CSV", "")) if os.environ.get("NYAYA_IPC_CSV") else None,
]

# {ipc_section: (bns_section, offense_description, mapping_note)}
_MAPPING: Dict[int, Tuple[int, str, str]] = {}


def _load_mapping() -> None:
    """Load CSV once at import time; populate _MAPPING."""
    for p in _CSV_CANDIDATES:
        if p is None:
            continue
        try:
            if p.is_file():
                with open(p, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ipc = row.get("ipc_section", "").strip()
                        bns = row.get("bns_section", "").strip()
                        desc = row.get("offense_description", "").strip()
                        note = row.get("mapping_note", "").strip()
                        if ipc and bns and ipc != "0":
                            try:
                                _MAPPING[int(ipc)] = (int(bns), desc, note)
                            except ValueError:
                                pass  # skip non-numeric (e.g. "120A")
                                # Try to handle sections like "120A"
                                cleaned = re.sub(r"[A-Za-z]+", "", ipc)
                                if cleaned:
                                    try:
                                        _MAPPING[int(cleaned)] = (int(bns), desc, note)
                                    except ValueError:
                                        pass
                logger.info("Loaded %d IPC→BNS mappings from %s", len(_MAPPING), p)
                return
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to load IPC mapping from %s: %s", p, e)

    # Fallback: seed data
    _SEED: list[tuple[int, int, str]] = [
        (302, 103, "Murder"),
        (304, 105, "Culpable homicide not amounting to murder"),
        (304, 106, "Causing death by negligence (304A)"),
        (307, 109, "Attempt to murder"),
        (376, 64, "Rape"),
        (420, 316, "Cheating"),
        (498, 85, "Cruelty by husband or relative"),
        (499, 356, "Defamation"),
        (354, 74, "Assault to outrage modesty"),
        (506, 351, "Criminal intimidation"),
        (379, 303, "Theft"),
        (384, 308, "Extortion"),
        (392, 307, "Robbery"),
        (406, 316, "Criminal breach of trust"),
        (463, 335, "Forgery"),
        (323, 115, "Voluntarily causing hurt"),
        (325, 117, "Voluntarily causing grievous hurt"),
        (339, 126, "Wrongful restraint"),
        (340, 127, "Wrongful confinement"),
        (299, 100, "Culpable homicide"),
        (300, 101, "Murder"),
        (319, 114, "Hurt"),
        (326, 124, "Acid attack"),
        (363, 141, "Kidnapping"),
        (370, 147, "Trafficking"),
        (375, 63, "Rape — definition"),
        (494, 82, "Bigamy"),
        (503, 349, "Criminal intimidation"),
    ]
    for ipc, bns, desc in _SEED:
        _MAPPING[ipc] = (bns, desc, "Seed mapping — verify with official concordance")
    logger.info("Using %d seed IPC→BNS mappings (CSV not found)", len(_MAPPING))


_load_mapping()


# ─── Public helpers ───────────────────────────────────────────────────────────


def find_ipc_mentions(text: str) -> list[int]:
    """Extract IPC section numbers mentioned in text."""
    if not text:
        return []
    hits: set[int] = set()
    # "IPC Section 302", "IPC 302", "section 302 IPC"
    for m in re.finditer(r"\bIPC\b[^0-9]{0,40}(?:Section|Sec\.?|§)?\s*(\d{1,4})", text, flags=re.I):
        hits.add(int(m.group(1)))
    for m in re.finditer(r"\bIPC\s*[§s]*\s*(\d{1,4})\b", text, flags=re.I):
        hits.add(int(m.group(1)))
    for m in re.finditer(r"\bsections?\s*(\d{1,4})\b.*\bIPC\b", text, flags=re.I):
        hits.add(int(m.group(1)))
    # Also catch standalone "Section 302" when context is criminal law
    for m in re.finditer(r"(?:u/?s|under\s+section)\s*(\d{1,4})", text, flags=re.I):
        sec = int(m.group(1))
        if sec in _MAPPING:
            hits.add(sec)
    return sorted(hits)


def ipc_hints_for_text(text: str) -> List[dict]:
    """Return structured IPC→BNS hints found in text."""
    mentions = find_ipc_mentions(text)
    out: list[dict] = []
    for ipc in mentions:
        if ipc in _MAPPING:
            bns, desc, note = _MAPPING[ipc]
            out.append({
                "ipc_section": ipc,
                "bns_section": bns,
                "offense": desc,
                "note": note,
            })
    return out


def format_ipc_context(text: str) -> str:
    """Format IPC→BNS hints for the LLM system prompt."""
    hints = ipc_hints_for_text(text)
    if not hints:
        return "(none detected)"
    lines = [
        f"IPC {h['ipc_section']} → BNS {h['bns_section']}: {h['offense']} ({h['note']})"
        for h in hints
    ]
    return "\n".join(lines)


def lookup_ipc(ipc_section: int) -> dict | None:
    """Lookup a single IPC section."""
    if ipc_section in _MAPPING:
        bns, desc, note = _MAPPING[ipc_section]
        return {
            "ipc_section": ipc_section,
            "bns_section": bns,
            "offense": desc,
            "note": note,
        }
    return None


def lookup_bns(bns_section: int) -> list[dict]:
    """Reverse lookup: find all IPC sections that map to a given BNS section."""
    results = []
    for ipc, (bns, desc, note) in _MAPPING.items():
        if bns == bns_section:
            results.append({
                "ipc_section": ipc,
                "bns_section": bns,
                "offense": desc,
                "note": note,
            })
    return sorted(results, key=lambda x: x["ipc_section"])


def get_all_mappings() -> list[dict]:
    """Return all IPC→BNS mappings."""
    return [
        {"ipc_section": ipc, "bns_section": bns, "offense": desc, "note": note}
        for ipc, (bns, desc, note) in sorted(_MAPPING.items())
    ]
