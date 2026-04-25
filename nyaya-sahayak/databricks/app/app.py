"""Nyaya-Sahayak FastAPI entrypoint for Databricks Apps.

Serves the Next.js static export from ``web_static/`` (same Databricks App URL) when present.
Build: ``cd web && npm install && npm run build`` (copy step writes to ``databricks/app/web_static``).
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from routers import analyze, chat, health, schemes, stt

app = FastAPI(title="Nyaya-Sahayak API", version="0.1.0")

_HERE = Path(__file__).resolve().parent
_WEB_STATIC = _HERE / "web_static"


def _web_static_ok() -> bool:
    if not _WEB_STATIC.is_dir():
        return False
    return any(_WEB_STATIC.iterdir())


if not _web_static_ok():

    @app.get("/", response_class=HTMLResponse)
    def root_placeholder():
        return """<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>Nyaya-Sahayak</title></head>
<body style="font-family:system-ui;max-width:40rem;margin:2rem auto;padding:0 1rem">
  <h1>Next.js UI not bundled</h1>
  <p>Run <code>cd web && npm install && npm run build</code> then re-sync <code>databricks/app</code> to the workspace and redeploy.</p>
  <p><a href="/docs">OpenAPI /docs</a> · <a href="/api/health">/api/health</a></p>
</body></html>"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("NYAYA_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(chat.router)
app.include_router(schemes.router)
app.include_router(stt.router)

# mount Next.js static export last (catch-all for HTML); /api, /docs stay on FastAPI
if _web_static_ok():
    app.mount("/", StaticFiles(directory=str(_WEB_STATIC), html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
