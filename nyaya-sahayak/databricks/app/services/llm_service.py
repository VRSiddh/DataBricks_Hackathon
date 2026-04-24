"""Databricks Model Serving (OpenAI-compatible) chat completions."""

from __future__ import annotations

import logging
from typing import List

from openai import OpenAI

from credentials import get_databricks_host_and_token
from settings import get_settings

logger = logging.getLogger(__name__)

# Pay-per-token foundation endpoints (see Databricks “Foundation Model APIs”); first that exists wins.
_DEFAULT_ENDPOINT_CANDIDATES = [
    "databricks-meta-llama-3-3-70b-instruct",
    "databricks-meta-llama-3-1-8b-instruct",
    "databricks-meta-llama-3-1-70b-instruct",
    "databricks-meta-llama-3-1-405b-instruct",
    "databricks-llama-4-maverick",
]


def _endpoint_not_found(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "endpoint_not_found" in msg or ("404" in msg and "endpoint" in msg)


def _model_candidates(preferred: str) -> list[str]:
    user = [x.strip() for x in (preferred or "").split(",") if x.strip()]
    seen: set[str] = set()
    out: list[str] = []
    for m in user + _DEFAULT_ENDPOINT_CANDIDATES:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out if out else list(_DEFAULT_ENDPOINT_CANDIDATES)


def chat_complete(messages: List[dict], *, max_tokens: int = 2048, temperature: float = 0.2) -> str:
    s = get_settings()
    host, token = get_databricks_host_and_token()
    if not host or not token:
        raise RuntimeError(
            "Could not resolve Databricks credentials for LLM calls. "
            "On Databricks Apps the SDK usually picks up OAuth automatically; "
            "otherwise set DATABRICKS_HOST and DATABRICKS_TOKEN (PAT) in the app environment / secret scope."
        )

    base = host.rstrip("/")
    client = OpenAI(api_key=token, base_url=f"{base}/serving-endpoints")
    models = _model_candidates(s.llm_serving_endpoint)

    last_err: BaseException | None = None
    for model in models:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if model != models[0]:
                logger.info("LLM using fallback serving endpoint: %s", model)
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            last_err = e
            if _endpoint_not_found(e):
                logger.warning("Serving endpoint not found: %s — trying next candidate", model)
                continue
            logger.exception("LLM call failed on %s: %s", model, e)
            raise

    raise RuntimeError(
        "No model serving endpoint responded. Tried: "
        + ", ".join(models)
        + ". In Databricks open **Compute → Model Serving**, copy the exact **Endpoint name** "
        "for a chat model and set **NYAYA_LLM_ENDPOINT** on this app (comma-separated to prefer order). "
        "Docs: https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models"
    ) from last_err
