# Nyaya-Sahayak (न्याय सहायक)

Access-to-justice assistant for **Bharatiya Nyaya Sanhita (BNS), 2023**: document upload → OCR → (optional Indic translation) → **Databricks Vector Search** RAG → **Databricks Model Serving** LLM → optional **Sarvam** TTS.

## Repo layout

- [`databricks/notebooks/`](databricks/notebooks/) — Delta ingest, chunking, Vector Search index, MLflow eval stub, IPC→BNS seed table.
- [`databricks/app/`](databricks/app/) — **FastAPI** Databricks App; also serves the **Next.js** static export from `web_static/` (same public URL as the API).
- [`web/`](web/) — **Next.js 14 (App Router)** front end (`output: "export"`). Build copies assets into `databricks/app/web_static/`.
- [`flutter_app/`](flutter_app/) — legacy Flutter UI (optional; not required for deployment).

## Front end (Next.js) + API on one Databricks App

1. Build the static site (writes `databricks/app/web_static/`):

```powershell
cd web
npm install
npm run build
```

2. Run locally (API + UI on :8000):

```powershell
cd databricks\app
pip install -r requirements.txt
$env:PORT="8000"
python app.py
```

Open `http://127.0.0.1:8000/` for the **Next.js UI**; `http://127.0.0.1:8000/docs` for OpenAPI.  
Use a separate terminal for `npm run dev` in `web/` if you only want the Next dev server (set `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000`).

3. **Deploy to Databricks**: from `databricks\app` run `databricks sync` to your workspace path, then `databricks apps deploy` (see Databricks *Deploy a Databricks app* in the product docs).

If `web_static/` is missing, `GET /` shows a small placeholder HTML with links to `/docs` and `/api/health`.

## Quickstart (API only)

```powershell
cd databricks/app
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:PORT="8000"
python app.py
```

- `GET /api/health`
- `POST /api/analyze_upload` (multipart) — `file`, `language`, optional `query`
- `POST /api/chat` — JSON

Configure:

- `DATABRICKS_HOST`, `DATABRICKS_TOKEN` (for Vector Search + LLM from the app)
- `NYAYA_VECTOR_ENDPOINT`, `NYAYA_VECTOR_INDEX`
- `NYAYA_LLM_ENDPOINT` (optional; comma-separated **exact** names from **Compute → Model Serving**. If unset, the app tries common pay-per-token endpoints such as `databricks-meta-llama-3-3-70b-instruct` until one exists in your workspace.)
- `SARVAM_API_KEY` (optional; translation + TTS) via Databricks secret scope

## Databricks data pipeline

1. Upload [`data/bns_sections.csv`](data/bns_sections.csv) to a UC volume, e.g. `/Volumes/main/nyaya_sahayak/raw_files/`.
2. Run notebooks `01` → `02` → `03` (Vector Search) → `05` (IPC seed). Use `04` for MLflow metrics / eval stubs.
3. Deploy the app from [`databricks/app`](databricks/app) via **Databricks Apps** (include `web_static` after `npm run build`).

## Disclaimer

Educational / hackathon prototype — **not legal advice**. Always consult a qualified advocate for your situation.
