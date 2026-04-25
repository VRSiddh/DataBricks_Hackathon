"""Multi-corpus offline RAG fallback.

Searches all bundled datasets in priority order:
1. BNS sections  (law corpus — always searched for legal queries)
2. Constitution of India articles  (constitutional questions)
3. Government schemes  (entitlement / scheme queries)
4. Scheme FAQs  (quick Q&A)

Used when Databricks Vector Search is unavailable or returns no text.
"""

from __future__ import annotations

import csv
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DATA = Path(__file__).resolve().parent.parent / "data"

# ── helpers ──────────────────────────────────────────────────────────────────

def _tokenize(q: str) -> set[str]:
    q = q.lower()
    return {t for t in re.split(r"[^\w\u0900-\u0dff]+", q) if len(t) > 2}


def _score(query_tokens: set[str], blob: str, bonus_tokens: set[str] = frozenset()) -> float:
    words = _tokenize(blob)
    s = float(len(query_tokens & words))
    s += float(len(bonus_tokens & words)) * 2.0
    return s


# ── BNS sections ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_bns() -> list[dict[str, str]]:
    f = _DATA / "bns_sections.csv"
    if not f.is_file():
        logger.warning("BNS CSV missing: %s", f)
        return []
    rows: list[dict[str, str]] = []
    try:
        with f.open(newline="", encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                norm = {(k or "").strip(): (v.strip() if isinstance(v, str) else "") for k, v in r.items()}
                sec = norm.get("Section") or norm.get("section") or ""
                desc = norm.get("Description") or norm.get("description") or ""
                if not sec or not desc:
                    continue
                rows.append({
                    "source": "bns",
                    "section": sec,
                    "section_name": norm.get("Section _name") or norm.get("section_name") or "",
                    "chapter": norm.get("Chapter") or "",
                    "chapter_name": norm.get("Chapter_name") or "",
                    "text": desc,
                })
    except OSError as e:
        logger.warning("Cannot read BNS CSV: %s", e)
    logger.info("Loaded %d BNS rows", len(rows))
    return rows


# ── Constitution ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_constitution() -> list[dict[str, str]]:
    f = _DATA / "constitution.csv"
    if not f.is_file():
        logger.warning("Constitution CSV missing: %s", f)
        return []
    rows: list[dict[str, str]] = []
    try:
        with f.open(newline="", encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                norm = {(k or "").strip(): (v.strip() if isinstance(v, str) else "") for k, v in r.items()}
                # Column is "Articles" for this CSV
                article_text = norm.get("Articles") or norm.get("article") or ""
                if not article_text or len(article_text) < 20:
                    continue
                rows.append({
                    "source": "constitution",
                    "section": "",
                    "section_name": article_text[:80],
                    "chapter": "",
                    "chapter_name": "Constitution of India",
                    "text": article_text,
                })
    except OSError as e:
        logger.warning("Cannot read Constitution CSV: %s", e)
    logger.info("Loaded %d Constitution rows", len(rows))
    return rows


# ── Schemes ───────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_schemes() -> list[dict[str, str]]:
    f = _DATA / "schemes.csv"
    if not f.is_file():
        logger.warning("Schemes CSV missing: %s", f)
        return []
    rows: list[dict[str, str]] = []
    try:
        with f.open(newline="", encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                slug = (r.get("slug") or "").strip()
                name = (r.get("scheme_name") or "").strip()
                desc = (r.get("brief_description") or r.get("detailed_description") or "").strip()
                benefits = (r.get("benefits") or "").strip()
                eligibility = (r.get("eligibility") or "").strip()
                state = (r.get("state") or "").strip()
                categories = (r.get("categories") or "").strip()
                beneficiary = (r.get("beneficiary_type") or r.get("target_beneficiaries") or "").strip()
                if not name:
                    continue
                blob = f"{name}. {desc} Benefits: {benefits} Eligibility: {eligibility} State: {state} Categories: {categories}"
                rows.append({
                    "source": "scheme",
                    "slug": slug,
                    "section": slug,
                    "section_name": name,
                    "chapter": categories,
                    "chapter_name": state,
                    "beneficiary": beneficiary,
                    "eligibility": eligibility,
                    "benefits": benefits,
                    "state": state,
                    "categories": categories,
                    "text": blob,
                })
    except OSError as e:
        logger.warning("Cannot read schemes CSV: %s", e)
    logger.info("Loaded %d scheme rows", len(rows))
    return rows


@lru_cache(maxsize=1)
def _load_faqs() -> list[dict[str, str]]:
    f = _DATA / "schemes_faqs.csv"
    if not f.is_file():
        return []
    rows: list[dict[str, str]] = []
    try:
        with f.open(newline="", encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                slug = (r.get("scheme_slug") or "").strip()
                name = (r.get("scheme_name") or "").strip()
                q = (r.get("question") or "").strip()
                a = (r.get("answer") or "").strip()
                if not q or not a:
                    continue
                rows.append({
                    "source": "faq",
                    "slug": slug,
                    "section": slug,
                    "section_name": name,
                    "chapter_name": "Scheme FAQ",
                    "text": f"Q: {q}\nA: {a}",
                })
    except OSError as e:
        logger.warning("Cannot read FAQs CSV: %s", e)
    logger.info("Loaded %d FAQ rows", len(rows))
    return rows


# ── Profile-based scheme matching ─────────────────────────────────────────────

def match_schemes_for_profile(
    *,
    age: int | None = None,
    gender: str | None = None,
    state: str | None = None,
    caste: str | None = None,
    occupation: str | None = None,
    income: str | None = None,
    num_results: int = 8,
) -> list[dict[str, Any]]:
    """Return scheme rows best matching a user profile."""
    rows = _load_schemes()
    if not rows:
        return []

    profile_tokens = set()
    if state:
        profile_tokens |= _tokenize(state)
    if gender:
        profile_tokens.add(gender.lower())
        if gender.lower() in ("female", "woman", "women", "girl"):
            profile_tokens |= {"women", "woman", "female", "girl", "mahila"}
    if caste:
        profile_tokens |= _tokenize(caste)
    if occupation:
        profile_tokens |= _tokenize(occupation)
    if income:
        profile_tokens |= _tokenize(income)

    scored: list[tuple[float, dict[str, str]]] = []
    for row in rows:
        s = _score(profile_tokens, row["text"])
        # Age-based bonus — heuristic
        if age is not None:
            if age < 18 and any(w in row["text"].lower() for w in ("student", "youth", "child", "minor", "school")):
                s += 3
            if age >= 60 and any(w in row["text"].lower() for w in ("senior", "elderly", "old age", "pension")):
                s += 3
            if 18 <= age <= 35 and any(w in row["text"].lower() for w in ("youth", "startup", "employment", "skill")):
                s += 2
        # National-level schemes match everyone
        if "central" in row["text"].lower() or "national" in row["text"].lower():
            s += 0.5
        if s > 0:
            scored.append((s, row))

    scored.sort(key=lambda x: -x[0])
    out: list[dict[str, Any]] = []
    for _, row in scored[:num_results]:
        out.append({
            "name": row["section_name"],
            "slug": row.get("slug", ""),
            "state": row.get("state", ""),
            "categories": row.get("chapter", ""),
            "benefits": row.get("benefits", ""),
            "eligibility": row.get("eligibility", ""),
        })
    return out


# ── Detect query intent ───────────────────────────────────────────────────────

_SCHEME_KW = {
    "scheme", "schemes", "yojana", "benefit", "benefits", "subsidy", "grant",
    "entitlement", "government scheme", "welfare", "stipend", "pension",
    "scholarship", "loan", "apply", "application", "eligible", "eligibility",
    "pradhan mantri", "central govt", "state govt", "pm ", "pmay", "pmjdy",
}
_CONSTITUTION_KW = {
    "constitution", "article", "fundamental right", "directive principle",
    "parliament", "president", "governor", "supreme court", "high court",
    "amendment", "preamble", "citizen", "constitutional", "article 14",
    "article 21", "article 19", "freedom",
}


def _query_intent(q: str) -> tuple[bool, bool, bool]:
    """Returns (want_bns, want_constitution, want_schemes)."""
    ql = q.lower()
    want_schemes = any(kw in ql for kw in _SCHEME_KW)
    want_constitution = any(kw in ql for kw in _CONSTITUTION_KW)
    # Default to BNS unless clearly off-topic
    want_bns = not (want_schemes and not want_constitution)
    return want_bns, want_constitution, want_schemes


# ── Main entry point ──────────────────────────────────────────────────────────

def fallback_retrieve(
    query_text: str,
    *,
    num_results: int = 8,
    force_all: bool = False,
) -> tuple[str, list[dict[str, Any]]]:
    """Return (context_string, structured_hits) from bundled CSVs."""
    qt = _tokenize(query_text)
    if not qt:
        qt = _tokenize("bharatiya nyaya sanhita criminal offence bns")

    # Section-number bonus
    section_mentions = {m.group(1) for m in re.finditer(r"\b(?:section|sec\.?|article)\s*(\d{1,4})\b", query_text, re.I)}
    section_mentions |= {m.group(1) for m in re.finditer(r"\b(?:bns|art)\s*(\d{1,4})\b", query_text, re.I)}
    bonus = {s for s in section_mentions}

    want_bns, want_constitution, want_schemes = _query_intent(query_text)
    if force_all:
        want_bns = want_constitution = want_schemes = True

    per_corpus = max(2, num_results // (sum([want_bns, want_constitution, want_schemes]) or 1))

    def _top(rows: list[dict[str, str]], n: int) -> list[tuple[float, dict[str, str]]]:
        scored: list[tuple[float, dict[str, str]]] = []
        for row in rows:
            s = _score(qt, row["text"], bonus)
            # Exact section match bonus
            if row.get("section") and row["section"] in section_mentions:
                s += 10
            if s > 0:
                scored.append((s, row))
        if not scored:
            scored = [(0.01, r) for r in rows[:n]]
        scored.sort(key=lambda x: -x[0])
        return scored[:n]

    all_top: list[tuple[float, dict[str, str]]] = []
    if want_bns:
        all_top.extend(_top(_load_bns(), per_corpus))
    if want_constitution:
        all_top.extend(_top(_load_constitution(), per_corpus))
    if want_schemes:
        all_top.extend(_top(_load_schemes(), per_corpus))
        all_top.extend(_top(_load_faqs(), 2))

    all_top.sort(key=lambda x: -x[0])
    top = all_top[:num_results]

    if not top:
        return "", []

    source_labels = {"bns": "BNS", "constitution": "Constitution of India", "scheme": "Govt Scheme", "faq": "Scheme FAQ"}

    chunks: list[str] = []
    hits: list[dict[str, Any]] = []
    for rank, (sc, row) in enumerate(top, start=1):
        src = source_labels.get(row.get("source", ""), "")
        sec = row.get("section", "")
        name = row.get("section_name", "")
        label = f"[{src}] Section {sec}: {name}" if sec else f"[{src}] {name}"
        body = row["text"][:3000]
        chunks.append(f"--- {label.strip()} ---\n{body}")
        try:
            sec_int = int(sec)
        except (ValueError, TypeError):
            sec_int = sec
        hits.append({
            "section": sec_int,
            "name": name,
            "source": row.get("source"),
            "relevance": float(sc),
        })

    intro = (
        "[RAG note: Databricks Vector Search unavailable — using bundled BNS/Constitution/Scheme text.]\n\n"
    )
    return intro + "\n\n".join(chunks), hits
