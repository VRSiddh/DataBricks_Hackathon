"""Runtime configuration (env + Databricks defaults)."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    databricks_host: str = os.environ.get("DATABRICKS_HOST", "").rstrip("/")
    databricks_token: str = os.environ.get("DATABRICKS_TOKEN", "")
    sarvam_api_key: str = os.environ.get("SARVAM_API_KEY", "sk_jpqtipyn_SS4oYlXZgjr9ZlBTPZMPyXWq")

    vector_endpoint: str = os.environ.get("NYAYA_VECTOR_ENDPOINT", "nyaya-sahayak-vs")
    vector_index: str = os.environ.get("NYAYA_VECTOR_INDEX", "main.nyaya_sahayak.bns_chunks_index")

    # Comma-separated Model Serving endpoint names (first match wins). Empty = use built-in fallbacks in llm_service.
    llm_serving_endpoint: str = os.environ.get("NYAYA_LLM_ENDPOINT", "")

    rag_num_results: int = int(os.environ.get("NYAYA_RAG_K", "5"))
    request_timeout_sec: float = float(os.environ.get("NYAYA_HTTP_TIMEOUT", "120"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
