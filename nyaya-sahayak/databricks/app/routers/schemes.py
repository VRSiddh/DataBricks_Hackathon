"""Government scheme eligibility API — 4600+ schemes with search, categories & matching."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from services.scheme_service import (
    format_scheme_context_for_llm,
    get_all_schemes,
    get_categories,
    get_scheme_by_id,
    get_scheme_count,
    match_schemes,
    search_schemes,
)

router = APIRouter(prefix="/api", tags=["schemes"])


class SchemeCheckBody(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    gender: Optional[str] = Field(None, description="Male / Female / Other")
    income: Optional[float] = Field(None, ge=0, description="Annual household income in INR")
    caste: Optional[str] = Field(None, description="General / OBC / SC / ST / EWS")
    state: Optional[str] = Field(None, description="State name")
    category: Optional[str] = Field(None, description="Interest area: Health, Education, Legal Aid, etc.")
    query: Optional[str] = Field(None, description="Free-text query for keyword matching")


@router.post("/scheme_check")
async def check_scheme_eligibility(body: SchemeCheckBody):
    """Match government schemes to user profile."""
    matches = match_schemes(
        age=body.age,
        gender=body.gender,
        income=body.income,
        caste=body.caste,
        state=body.state,
        category=body.category,
        query=body.query,
    )
    # Remove internal score from response
    clean = [{k: v for k, v in m.items() if k != "_score"} for m in matches]
    return {
        "matched_schemes": clean,
        "total_matches": len(clean),
        "total_schemes_in_db": get_scheme_count(),
        "llm_context": format_scheme_context_for_llm(matches),
    }


@router.get("/schemes")
async def list_schemes(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """List available government schemes (paginated)."""
    all_schemes = get_all_schemes()
    total = len(all_schemes)
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "schemes": all_schemes[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/schemes/search")
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
):
    """Full-text search across scheme names, descriptions, and benefits."""
    results = search_schemes(q, limit=limit)
    clean = [{k: v for k, v in m.items() if k != "_score"} for m in results]
    return {
        "results": clean,
        "total_results": len(clean),
        "query": q,
        "total_schemes_in_db": get_scheme_count(),
    }


@router.get("/schemes/categories")
async def categories():
    """List all distinct scheme categories."""
    cats = get_categories()
    return {"categories": cats, "total": len(cats)}


@router.get("/schemes/stats")
async def scheme_stats():
    """Summary statistics about loaded scheme data."""
    all_schemes = get_all_schemes()
    cats = get_categories()
    levels = set(s.get("level", "") for s in all_schemes if s.get("level"))
    states = set(s.get("state_ut", "") for s in all_schemes if s.get("state_ut") and s["state_ut"] != "All")
    return {
        "total_schemes": len(all_schemes),
        "total_categories": len(cats),
        "categories": cats,
        "levels": sorted(levels),
        "states_covered": len(states),
        "hindi_available": sum(1 for s in all_schemes if s.get("description_hi")),
    }


@router.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: int):
    """Get details of a specific scheme."""
    scheme = get_scheme_by_id(scheme_id)
    if scheme is None:
        return {"error": f"Scheme {scheme_id} not found"}
    return scheme
