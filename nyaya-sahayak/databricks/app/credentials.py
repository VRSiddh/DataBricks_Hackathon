"""Resolve workspace host + bearer token for REST calls (Apps OAuth, PAT, or env)."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_databricks_host_and_token() -> tuple[str, str]:
    """
    Returns ``(host, token)`` for OpenAI-compatible Databricks serving endpoints.

    1. ``DATABRICKS_HOST`` + ``DATABRICKS_TOKEN`` (or ``DATABRICKS_ACCESS_TOKEN``).
    2. Databricks SDK ``Config()`` — PAT from profile / env, or **OAuth** when the
       runtime injects ``DATABRICKS_CLIENT_ID`` + ``DATABRICKS_CLIENT_SECRET`` (Databricks Apps).
    """
    host = (os.environ.get("DATABRICKS_HOST") or os.environ.get("WORKSPACE_URL") or "").strip().rstrip("/")
    token = (
        os.environ.get("DATABRICKS_TOKEN")
        or os.environ.get("DATABRICKS_ACCESS_TOKEN")
        or ""
    ).strip()
    if host and token:
        return host, token

    try:
        from databricks.sdk.core import Config

        cfg = Config()
        ch = (cfg.host or host or "").strip().rstrip("/")
        ct = (getattr(cfg, "token", None) or "").strip()
        if ch and ct:
            return ch, ct

        auth_headers = cfg.authenticate()
        if isinstance(auth_headers, dict):
            auth = auth_headers.get("Authorization") or auth_headers.get("authorization")
            if isinstance(auth, str) and auth.lower().startswith("bearer "):
                ct = auth.split(" ", 1)[1].strip()
        if ch and ct:
            return ch, ct
    except Exception as e:  # noqa: BLE001
        logger.warning("Databricks SDK auth resolution failed: %s", e)

    return host, token
