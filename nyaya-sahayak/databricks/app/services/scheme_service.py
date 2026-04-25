"""Government scheme eligibility matching — supports both 35-scheme and 4600+ scheme datasets."""

from __future__ import annotations

import csv
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_HERE = Path(__file__).resolve().parent

# Priority order: full merged dataset → original hand-crafted → env override
_CSV_CANDIDATES = [
    _HERE.parent.parent.parent / "data" / "gov_schemes_full.csv",
    _HERE.parent.parent.parent / "data" / "gov_schemes.csv",
    _HERE.parent / "data" / "gov_schemes_full.csv",
    _HERE.parent / "data" / "gov_schemes.csv",
    Path(os.environ.get("NYAYA_SCHEMES_CSV", "")) if os.environ.get("NYAYA_SCHEMES_CSV") else None,
]

_SCHEMES: List[Dict[str, Any]] = []

# ─── Keyword index for fast text search ──────────────────────────────────────
_SEARCH_INDEX: Dict[str, List[int]] = {}  # keyword → list of scheme indices


def _load_schemes() -> None:
    """Load schemes from CSV at startup (auto-detects column format)."""
    for p in _CSV_CANDIDATES:
        if p is None:
            continue
        try:
            if p.is_file():
                with open(p, encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    cols = set(reader.fieldnames or [])
                    # Detect whether this is the full or legacy format
                    is_full = "eligibility_criteria" in cols or "target_beneficiaries" in cols

                    for row in reader:
                        scheme = _parse_row(row, is_full)
                        if scheme["scheme_name"]:
                            _SCHEMES.append(scheme)

                logger.info("Loaded %d government schemes from %s", len(_SCHEMES), p)
                _build_search_index()
                return
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to load schemes from %s: %s", p, e)

    logger.warning("No scheme CSV found; scheme eligibility will be unavailable.")


def _parse_row(row: dict, is_full: bool) -> Dict[str, Any]:
    """Parse a CSV row into a normalised scheme dict (handles both formats)."""

    def g(key: str, default: str = "") -> str:
        return (row.get(key) or default).strip()

    def gi(key: str, default: int = 0) -> int:
        v = row.get(key, "")
        try:
            return int(float(v)) if v else default
        except (ValueError, TypeError):
            return default

    def gf(key: str, default: float = 0.0) -> float:
        v = row.get(key, "")
        try:
            return float(v) if v else default
        except (ValueError, TypeError):
            return default

    return {
        "scheme_id": gi("scheme_id"),
        "scheme_name": g("scheme_name"),
        "short_title": g("short_title"),
        "ministry": g("ministry") or g("department"),
        "category": g("category") or g("categories"),
        "sub_category": g("sub_category") or g("sub_categories"),
        "level": g("level"),
        "state_ut": g("state_ut") or g("eligibility_state", "All"),
        "target_beneficiaries": g("target_beneficiaries"),
        "eligibility_criteria": g("eligibility_criteria"),
        "eligibility_gender": g("eligibility_gender", "All"),
        "eligibility_min_age": gi("eligibility_min_age", 0),
        "eligibility_max_age": gi("eligibility_max_age", 99),
        "eligibility_income_limit": gf("eligibility_income_limit"),
        "eligibility_caste": g("eligibility_caste", "All"),
        "benefits": g("benefits"),
        "application_process": g("application_process"),
        "documents_required": g("documents_required"),
        "description_en": g("description_en") or g("brief_description") or g("detailed_description"),
        "description_hi": g("description_hi"),
        "source_url": g("source_url"),
    }


def _build_search_index() -> None:
    """Build inverted keyword index for fast query matching."""
    _SEARCH_INDEX.clear()
    stop_words = {"the", "a", "an", "is", "are", "for", "and", "or", "of", "to", "in", "on", "at", "by", "with", "from"}

    for idx, scheme in enumerate(_SCHEMES):
        searchable = " ".join([
            scheme["scheme_name"],
            scheme["category"],
            scheme["sub_category"],
            scheme["benefits"],
            scheme["description_en"],
            scheme["target_beneficiaries"],
            scheme["eligibility_criteria"],
        ]).lower()

        words = set(re.findall(r'\b[a-z]{3,}\b', searchable)) - stop_words
        for word in words:
            _SEARCH_INDEX.setdefault(word, []).append(idx)

    logger.info("Built search index: %d keywords across %d schemes", len(_SEARCH_INDEX), len(_SCHEMES))


_load_schemes()


# ─── Profile-based matching ──────────────────────────────────────────────────


def match_schemes(
    *,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    income: Optional[float] = None,
    caste: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filter schemes by user profile. Returns matching schemes sorted by relevance.
    Optimised with keyword index for 4000+ scheme datasets.
    """
    query_lower = (query or "").lower()

    # If we have a query, use the keyword index to narrow candidates
    if query_lower and _SEARCH_INDEX:
        query_words = set(re.findall(r'\b[a-z]{3,}\b', query_lower))
        candidate_indices: set[int] = set()
        for w in query_words:
            if w in _SEARCH_INDEX:
                candidate_indices.update(_SEARCH_INDEX[w])

        # If keyword search found candidates, score only those
        if candidate_indices:
            candidates = [(idx, _SCHEMES[idx]) for idx in candidate_indices]
        else:
            # Fall back to full scan
            candidates = list(enumerate(_SCHEMES))
    else:
        candidates = list(enumerate(_SCHEMES))

    results = []

    for _idx, scheme in candidates:
        score = 0
        eligible = True

        # Age check
        if age is not None:
            if age < scheme["eligibility_min_age"] or age > scheme["eligibility_max_age"]:
                eligible = False
            else:
                score += 1

        # Gender check
        if gender and scheme["eligibility_gender"] != "All":
            if gender.lower() not in scheme["eligibility_gender"].lower():
                eligible = False
            else:
                score += 2

        # Income check
        if income is not None and scheme["eligibility_income_limit"] > 0:
            if income > scheme["eligibility_income_limit"]:
                eligible = False
            else:
                score += 1

        # Caste/category check
        if caste and scheme["eligibility_caste"] != "All":
            caste_lower = caste.lower()
            elig_caste = scheme["eligibility_caste"].lower()
            if caste_lower not in elig_caste and "all" not in elig_caste:
                eligible = False
            else:
                score += 2

        # State check
        if state and scheme["state_ut"] and scheme["state_ut"] != "All":
            if state.lower() not in scheme["state_ut"].lower():
                eligible = False
            else:
                score += 2

        # Category interest check
        if category:
            cat_lower = category.lower()
            if cat_lower in scheme["category"].lower() or cat_lower in scheme["sub_category"].lower():
                score += 3

        # Query keyword matching
        if query_lower:
            words = re.findall(r'\b[a-z]{3,}\b', query_lower)
            searchable = (
                scheme["scheme_name"].lower() + " " +
                scheme["description_en"].lower() + " " +
                scheme["benefits"].lower() + " " +
                scheme["category"].lower() + " " +
                scheme["eligibility_criteria"].lower()
            )
            matched_words = sum(1 for w in words if w in searchable)
            if matched_words > 0:
                score += matched_words * 2

            # Boost legal-aid schemes for legal queries
            legal_keywords = {"legal", "law", "court", "victim", "aid", "compensation", "fir", "police",
                              "crime", "arrest", "bail", "advocate", "lawyer", "justice"}
            if bool(legal_keywords & set(words)):
                cat_lower = scheme["category"].lower()
                if any(kw in cat_lower for kw in ["legal", "safety", "justice", "law"]):
                    score += 5

        if eligible and score > 0:
            results.append({**scheme, "_score": score})

    # Sort by relevance score
    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:20]  # top 20


def search_schemes(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Simple text search without profile-based filtering."""
    if not query:
        return _SCHEMES[:limit]

    words = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))
    if not words:
        return _SCHEMES[:limit]

    scored = []
    candidate_indices: set[int] = set()
    for w in words:
        if w in _SEARCH_INDEX:
            candidate_indices.update(_SEARCH_INDEX[w])

    for idx in candidate_indices:
        scheme = _SCHEMES[idx]
        searchable = (
            scheme["scheme_name"].lower() + " " +
            scheme["description_en"].lower() + " " +
            scheme["benefits"].lower()
        )
        score = sum(1 for w in words if w in searchable)
        if score > 0:
            scored.append({**scheme, "_score": score})

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:limit]


def get_all_schemes() -> List[Dict[str, Any]]:
    """Return all schemes (for browsing). Paginate if needed."""
    return list(_SCHEMES)


def get_scheme_count() -> int:
    """Return total number of loaded schemes."""
    return len(_SCHEMES)


def get_scheme_by_id(scheme_id: int) -> Optional[Dict[str, Any]]:
    """Lookup a single scheme by ID."""
    for s in _SCHEMES:
        if s["scheme_id"] == scheme_id:
            return s
    return None


def get_categories() -> List[str]:
    """Return distinct categories."""
    cats = sorted(set(s["category"] for s in _SCHEMES if s["category"]))
    return cats


def format_scheme_context_for_llm(schemes: List[Dict[str, Any]], max_schemes: int = 5) -> str:
    """Format matched schemes as context for the LLM prompt."""
    if not schemes:
        return "(No matching government schemes found)"
    lines = []
    for s in schemes[:max_schemes]:
        elig_parts = []
        if s.get("eligibility_gender") and s["eligibility_gender"] != "All":
            elig_parts.append(f"Gender: {s['eligibility_gender']}")
        if s.get("eligibility_min_age", 0) > 0 or s.get("eligibility_max_age", 99) < 99:
            elig_parts.append(f"Age {s['eligibility_min_age']}-{s['eligibility_max_age']}")
        if s.get("eligibility_caste") and s["eligibility_caste"] != "All":
            elig_parts.append(f"Category: {s['eligibility_caste']}")
        if s.get("eligibility_criteria"):
            elig_parts.append(s["eligibility_criteria"][:200])

        elig_str = ", ".join(elig_parts) if elig_parts else "Open to all"

        lines.append(
            f"• {s['scheme_name']} ({s['ministry']})\n"
            f"  Eligibility: {elig_str}\n"
            f"  Benefits: {s['benefits'][:300]}\n"
            f"  How to apply: {s['application_process'][:200]}"
        )
    return "\n\n".join(lines)
