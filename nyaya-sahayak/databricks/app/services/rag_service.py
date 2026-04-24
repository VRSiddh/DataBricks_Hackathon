"""Databricks Mosaic AI Vector Search retrieval."""

from __future__ import annotations

import logging
from typing import Any, List

from credentials import get_databricks_host_and_token
from settings import get_settings

logger = logging.getLogger(__name__)


def _format_hits(hits: Any) -> tuple[str, list[dict]]:
    """Turn SDK response into (context_str, structured_hits)."""
    rows: list[dict] = []
    chunks: list[str] = []

    def consume_item(item: Any) -> None:
        if isinstance(item, dict):
            meta = item.get("metadata") or item
            text = (
                meta.get("chunk_text")
                or meta.get("text")
                or item.get("chunk_text")
                or item.get("page_content")
                or ""
            )
            sec = meta.get("section") or item.get("section")
            name = meta.get("section_name") or item.get("section_name")
            score = item.get("score") or item.get("similarity") or item.get("distance")
            rows.append(
                {
                    "section": int(sec) if str(sec).isdigit() else sec,
                    "name": name,
                    "relevance": float(score) if score is not None else None,
                }
            )
            if text:
                label = f"Section {sec}: {name}" if sec else "Chunk"
                chunks.append(f"--- {label} ---\n{text}")

    if hits is None:
        return "", rows

    if isinstance(hits, dict):
        data = hits.get("result") or hits.get("manifest") or hits.get("data") or hits
        if isinstance(data, dict) and "data_array" in data:
            for row in data.get("data_array", []):
                consume_item(row)
        elif isinstance(data, list):
            for row in data:
                consume_item(row)
        else:
            consume_item(hits)
    elif isinstance(hits, list):
        for row in hits:
            consume_item(row)

    return "\n\n".join(chunks), rows


def retrieve_context(query_text: str) -> tuple[str, list[dict]]:
    s = get_settings()
    host, token = get_databricks_host_and_token()
    if not host:
        logger.warning("Databricks host missing; RAG disabled.")
        return "", []

    try:
        from databricks.vector_search.client import VectorSearchClient

        import os

        cid = os.environ.get("DATABRICKS_CLIENT_ID")
        csec = os.environ.get("DATABRICKS_CLIENT_SECRET")
        # Databricks Apps: prefer SP client credentials for Vector Search when injected.
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
        return _format_hits(raw)
    except Exception as e:  # noqa: BLE001
        logger.exception("Vector search failed: %s", e)
        return "", []
