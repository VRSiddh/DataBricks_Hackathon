"""Databricks Mosaic AI Vector Search retrieval + offline BNS CSV fallback."""

from __future__ import annotations

import logging
from typing import Any

from credentials import get_databricks_host_and_token
from services.rag_fallback import fallback_retrieve
from settings import get_settings

logger = logging.getLogger(__name__)


def _manifest_column_names(manifest: Any) -> list[str]:
    if not manifest or not isinstance(manifest, dict):
        return []
    cols = manifest.get("columns") or []
    out: list[str] = []
    for c in cols:
        if isinstance(c, dict) and c.get("name"):
            out.append(str(c["name"]))
        elif isinstance(c, str):
            out.append(c)
    return out


def _row_list_to_dict(column_names: list[str], row: list[Any]) -> dict[str, Any]:
    """Vector Search ``data_array`` rows are positional lists aligned with ``manifest.columns``."""
    if not column_names or not row:
        return {}
    n = min(len(column_names), len(row))
    d: dict[str, Any] = {column_names[i]: row[i] for i in range(n)}
    if len(row) == len(column_names) + 1:
        d["_score"] = row[-1]
    elif len(row) > len(column_names):
        d["_score"] = row[-1]
    return d


def _format_hits(hits: Any) -> tuple[str, list[dict]]:
    """Turn SDK response into (context_str, structured_hits).

    Databricks returns ``{"manifest": {"columns": [...]}, "result": {"data_array": [[...], ...]}}``
    where each row is a **list** (not a dict). Older paths may still return dict rows.
    """
    rows: list[dict] = []
    chunks: list[str] = []

    def consume_dict(item: dict) -> None:
        meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else item
        text = (
            (meta.get("chunk_text") if isinstance(meta, dict) else None)
            or (meta.get("text") if isinstance(meta, dict) else None)
            or item.get("chunk_text")
            or item.get("text")
            or item.get("page_content")
            or ""
        )
        sec = meta.get("section") if isinstance(meta, dict) else item.get("section")
        name = (meta.get("section_name") if isinstance(meta, dict) else None) or item.get("section_name")
        score = item.get("score") or item.get("similarity") or item.get("distance") or item.get("_score")
        rows.append(
            {
                "section": int(sec) if sec is not None and str(sec).isdigit() else sec,
                "name": name,
                "relevance": float(score) if score is not None else None,
            }
        )
        if text:
            label = f"Section {sec}: {name}" if sec else "Chunk"
            chunks.append(f"--- {label} ---\n{text}")

    def consume_any(item: Any, column_names: list[str] | None) -> None:
        if isinstance(item, dict):
            consume_dict(item)
            return
        if isinstance(item, (list, tuple)) and column_names:
            consume_dict(_row_list_to_dict(column_names, list(item)))
            return
        if isinstance(item, (list, tuple)) and not column_names:
            # Best-effort: first long string is probably chunk text
            parts = [str(x) for x in item if isinstance(x, str) and len(str(x)) > 50]
            if parts:
                rows.append({"section": None, "name": None, "relevance": None})
                chunks.append(f"--- Chunk ---\n{parts[0]}")

    if hits is None:
        return "", rows

    manifest_cols: list[str] = []
    if isinstance(hits, dict):
        manifest = hits.get("manifest")
        manifest_cols = _manifest_column_names(manifest)
        res = hits.get("result")
        if isinstance(res, dict) and "data_array" in res:
            for row in res.get("data_array") or []:
                consume_any(row, manifest_cols)
            return "\n\n".join(chunks), rows
        data = hits.get("result") or hits.get("data") or hits
        if isinstance(data, dict) and "data_array" in data:
            for row in data.get("data_array") or []:
                consume_any(row, manifest_cols)
            return "\n\n".join(chunks), rows
        if isinstance(data, list):
            for row in data:
                consume_any(row, manifest_cols)
            return "\n\n".join(chunks), rows
        consume_any(hits, manifest_cols)
        return "\n\n".join(chunks), rows

    if isinstance(hits, list):
        for row in hits:
            consume_any(row, manifest_cols)

    return "\n\n".join(chunks), rows


def retrieve_context(query_text: str) -> tuple[str, list[dict]]:
    s = get_settings()
    host, token = get_databricks_host_and_token()
    if not host:
        logger.warning("Databricks host missing; using offline BNS fallback only.")
        return fallback_retrieve(query_text, num_results=s.rag_num_results)

    try:
        from databricks.vector_search.client import VectorSearchClient

        import os

        cid = os.environ.get("DATABRICKS_CLIENT_ID")
        csec = os.environ.get("DATABRICKS_CLIENT_SECRET")
        if cid and csec:
            vsc = VectorSearchClient(
                disable_notice=True,
                workspace_url=host,
                service_principal_client_id=cid,
                service_principal_client_secret=csec,
            )
        elif token:
            vsc = VectorSearchClient(disable_notice=True, workspace_url=host, personal_access_token=token)
        else:
            vsc = VectorSearchClient(disable_notice=True)
        index = vsc.get_index(s.vector_endpoint, s.vector_index)
        raw = index.similarity_search(
            columns=["chunk_text", "section", "section_name", "chapter_name"],
            query_text=query_text,
            num_results=s.rag_num_results,
        )
        text, hits = _format_hits(raw)
        if text.strip():
            logger.info("Vector Search returned %d chunk(s) for RAG", len(hits))
            return text, hits
        logger.warning(
            "Vector Search returned empty context (index may be empty or still syncing). "
            "Endpoint=%s index=%s — using CSV fallback.",
            s.vector_endpoint,
            s.vector_index,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Vector search failed; using CSV fallback: %s", e)

    fb_text, fb_hits = fallback_retrieve(query_text, num_results=s.rag_num_results)
    return fb_text, fb_hits
