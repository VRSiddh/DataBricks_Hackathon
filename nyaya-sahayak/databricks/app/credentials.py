"""Resolve workspace host + bearer token for REST calls (Apps OAuth, PAT, or env)."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _bearer_from_cfg(cfg: object) -> tuple[str, str]:
    """Extract (host, bearer_token) from a databricks.sdk Config instance."""
    ch = (getattr(cfg, "host", None) or "").strip().rstrip("/")
    ct = (getattr(cfg, "token", None) or "").strip()
    if ch and ct:
        return ch, ct
    auth_headers = getattr(cfg, "authenticate", lambda: None)()
    if isinstance(auth_headers, dict):
        auth = auth_headers.get("Authorization") or auth_headers.get("authorization")
        if isinstance(auth, str) and auth.lower().startswith("bearer "):
            ct = auth.split(" ", 1)[1].strip()
    return ch, ct


def get_databricks_host_and_token() -> tuple[str, str]:
    """
    Returns ``(host, token)`` for OpenAI-compatible serving endpoints and REST.

    **Not cached.** Databricks Apps OAuth tokens expire; ``@lru_cache`` on this
    function caused repeated ``Invalid Token`` errors after the first token TTL.

    Order:
    1. **Service principal / Apps OAuth** — ``DATABRICKS_CLIENT_ID`` +
       ``DATABRICKS_CLIENT_SECRET`` (or ``ARM_*``): call ``Config().authenticate()``
       every time so tokens stay fresh. Prefer this over a static ``DATABRICKS_TOKEN``
       when both exist.
    2. **Explicit PAT** — ``DATABRICKS_HOST`` + ``DATABRICKS_TOKEN`` /
       ``DATABRICKS_ACCESS_TOKEN`` (local dev, notebooks with PAT).
    3. **Default SDK** — ``Config()`` from profile / remaining env.
    """
    host = (os.environ.get("DATABRICKS_HOST") or os.environ.get("WORKSPACE_URL") or "").strip().rstrip("/")
    cid = (os.environ.get("DATABRICKS_CLIENT_ID") or os.environ.get("ARM_CLIENT_ID") or "").strip()
    csec = (os.environ.get("DATABRICKS_CLIENT_SECRET") or os.environ.get("ARM_CLIENT_SECRET") or "").strip()

    if cid and csec:
        try:
            from databricks.sdk.core import Config

            cfg = Config(
                host=host or None,
                client_id=cid,
                client_secret=csec,
            )
            ch, ct = _bearer_from_cfg(cfg)
            if ch and ct:
                return ch, ct
        except Exception as e:  # noqa: BLE001
            logger.warning("Databricks SP OAuth resolution failed: %s", e)

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
        ch, ct = _bearer_from_cfg(cfg)
        if ch and ct:
            return ch, ct
    except Exception as e:  # noqa: BLE001
        logger.warning("Databricks SDK auth resolution failed: %s", e)

    return host, token
