"""Offline BNS RAG fallback when Vector Search returns no rows or is unavailable.

Uses bundled ``data/bns_sections.csv`` (same source as Delta ingest) with simple
token overlap scoring so the LLM always receives *some* BNS text for in-scope questions.
"""

from __future__ import annotations

import csv
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_APP_ROOT = Path(__file__).resolve().parent.parent
_BNS_CSV = _APP_ROOT / "data" / "bns_sections.csv"


@lru_cache(maxsize=1)
def _load_bns_rows() -> tuple[list[dict[str, str]], bool]:
    if not _BNS_CSV.is_file():
        logger.warning("BNS fallback CSV missing at %s", _BNS_CSV)
        return [], False
    rows: list[dict[str, str]] = []
    try:
        with _BNS_CSV.open(newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for raw in reader:
                norm = {(k or "").strip(): (v.strip() if isinstance(v, str) else "") for k, v in raw.items()}
                sec = norm.get("Section") or norm.get("section") or ""
                desc = norm.get("Description") or norm.get("description") or ""
                if not sec or not desc:
                    continue
                rows.append(
                    {
                        "chapter": norm.get("Chapter") or norm.get("chapter") or "",
                        "chapter_name": norm.get("Chapter_name") or norm.get("chapter_name") or "",
                        "section": sec,
                        "section_name": norm.get("Section _name")
                        or norm.get("Section_name")
                        or norm.get("section_name")
                        or "",
                        "description": desc,
                    }
                )
    except OSError as e:
        logger.warning("Could not read BNS fallback CSV: %s", e)
        return [], False
    logger.info("Loaded %d BNS rows for offline RAG fallback", len(rows))
    return rows, True


def _tokenize(q: str) -> set[str]:
    q = q.lower()
    return {t for t in re.split(r"[^\w\u0900-\u0dff]+", q) if len(t) > 1}


def _score_row(query_tokens: set[str], section_nums: set[str], row: dict[str, str]) -> float:
    blob = " ".join(row.values()).lower()
    words = _tokenize(blob)
    overlap = len(query_tokens & words)
    bonus = 0.0
    if row["section"] in section_nums:
        bonus += 8.0
    for kw in ("ipc", "bns", "murder", "theft", "cheating", "bail", "fir", "cognizable"):
        if kw in " ".join(query_tokens) and kw in blob:
            bonus += 1.5
    return overlap + bonus


def fallback_retrieve(query_text: str, *, num_results: int = 8) -> tuple[str, list[dict[str, Any]]]:
    """Return (context_string, structured_hits) from local CSV."""
    rows, ok = _load_bns_rows()
    if not ok or not rows:
        return "", []

    qt = _tokenize(query_text)
    if not qt:
        qt = _tokenize("bharatiya nyaya sanhita criminal offence section")

    section_mentions = {m.group(1) for m in re.finditer(r"\b(?:section|sec\.?)\s*(\d{1,4})\b", query_text, re.I)}
    section_mentions |= {m.group(1) for m in re.finditer(r"\bbns\s*(\d{1,4})\b", query_text, re.I)}

    scored: list[tuple[float, dict[str, str]]] = []
    for row in rows:
        s = _score_row(qt, section_mentions, row)
        if s > 0:
            scored.append((s, row))

    scored.sort(key=lambda x: -x[0])
    if not scored:
        # Broad fallback: first N sections so the model is never fully blind
        scored = [(0.01, r) for r in rows[:num_results]]

    top = scored[: max(1, num_results)]

    chunks: list[str] = []
    hits: list[dict[str, Any]] = []
    for rank, (sc, row) in enumerate(top, start=1):
        sec = row["section"]
        name = row["section_name"]
        body = row["description"][:3500]
        label = f"Section {sec}: {name}".strip()
        chunks.append(f"--- {label} (offline fallback rank {rank}) ---\n{body}")
        try:
            sec_int = int(sec)
        except ValueError:
            sec_int = sec
        hits.append({"section": sec_int, "name": name, "relevance": float(sc)})

    intro = (
        "[Retrieval note: Databricks Vector Search returned no rows or is unavailable — "
        "using bundled BNS section text for grounding.]\n\n"
    )
    return intro + "\n\n".join(chunks), hits
