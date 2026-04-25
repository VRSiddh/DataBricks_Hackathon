# Nyaya-Sahayak (न्याय सहायक)

**AI-powered legal assistant for India's Bharatiya Nyaya Sanhita (BNS), 2023** — built on Databricks for the Bharat Bricks Hacks 2026 hackathon.

Upload legal documents → OCR → Indic translation → **RAG via Vector Search** → **LLM via Model Serving** → Audio TTS → Government scheme recommendations.

## ✨ Key Features

| Feature | Tech |
|---------|------|
| 📄 **Document Analysis** | OCR (PyMuPDF + Tesseract) → RAG-grounded legal advice |
| 🗣️ **Voice Input (STT)** | Sarvam Saaras v3 — 22+ Indian languages with auto-detection |
| 🔊 **Audio Output (TTS)** | Sarvam Bulbul v3 — listen to legal advice in your language |
| 🌐 **Multilingual** | 10+ Indic languages via Sarvam translation |
| 🏛️ **IPC→BNS Mapping** | 150+ section mappings (old code → new code cross-reference) |
| 🛡️ **Scheme Eligibility** | 4,600+ government schemes with profile-based matching |
| 📊 **RAG Evaluation** | 30-question BhashaBench-Legal benchmark with MLflow |
| 🎨 **Rich Markdown** | BNS/IPC section badges, formatted legal text |
| ⚖️ **Constitution** | Fundamental rights and constitutional provisions in RAG |

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     User (Browser)                       │
│   Next.js 14 + Voice Input + Markdown Renderer           │
└───────────────┬───────────────────────┬──────────────────┘
                │                       │
         Upload/Chat/STT         Scheme Check
                │                       │
┌───────────────▼───────────────────────▼──────────────────┐
│               FastAPI (Databricks App)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐│
│  │ analyze  │ │  chat    │ │ schemes  │ │     stt      ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘│
│       │             │            │               │        │
│  ┌────▼─────────────▼────┐ ┌────▼─────┐  ┌──────▼──────┐│
│  │  RAG (Vector Search)  │ │ CSV 4.6K │  │ Sarvam STT  ││
│  │  + IPC Mapping        │ │ Schemes  │  │ (Saaras v3) ││
│  └────┬──────────────────┘ └──────────┘  └─────────────┘│
│       │                                                   │
│  ┌────▼──────────────────┐  ┌──────────────────────────┐ │
│  │  LLM (Model Serving)  │  │ Sarvam TTS (Bulbul v3)  │ │
│  │  Llama 3.3 70B        │  │ Translation API          │ │
│  └───────────────────────┘  └──────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Repo Layout

```
nyaya-sahayak/
├── data/
│   ├── bns_sections.csv          # BNS legal code (358 sections)
│   ├── ipc_bns_mapping.csv       # 150+ IPC→BNS cross-reference
│   ├── gov_schemes.csv           # 35 curated schemes (seed)
│   ├── gov_schemes_full.csv      # 4,600+ schemes (MyScheme.gov.in)
│   ├── prepare_schemes.py        # Dataset merger script
│   ├── elchemist/                # Kaggle: Elchemist dataset
│   └── bilingual/                # Kaggle: Hindi+English dataset
│
├── databricks/
│   ├── app/                      # FastAPI application
│   │   ├── app.py                # Entrypoint + static file mount
│   │   ├── settings.py           # Runtime config (env vars)
│   │   ├── routers/
│   │   │   ├── analyze.py        # Document upload → OCR → RAG → LLM
│   │   │   ├── chat.py           # Follow-up chat with session TTL
│   │   │   ├── schemes.py        # Scheme eligibility API (search, filter)
│   │   │   ├── stt.py            # Speech-to-text (Sarvam Saaras)
│   │   │   └── health.py         # Health check
│   │   ├── services/
│   │   │   ├── rag_service.py    # Databricks Vector Search retrieval
│   │   │   ├── llm_service.py    # Model Serving (OpenAI-compatible)
│   │   │   ├── ipc_mapping.py    # IPC↔BNS bidirectional mapping
│   │   │   ├── scheme_service.py # 4600+ scheme matching engine
│   │   │   ├── stt_service.py    # Sarvam speech-to-text
│   │   │   ├── tts_service.py    # Sarvam text-to-speech
│   │   │   ├── ocr_service.py    # PDF/image text extraction
│   │   │   └── translation_service.py
│   │   └── prompts/
│   │       └── system_prompt.py  # Constitution+scheme-aware prompt
│   │
│   └── notebooks/
│       ├── 01_data_ingestion.py      # CSV → Delta Lake
│       ├── 02_chunking_pipeline.py   # Sentence-aware chunking
│       ├── 03_vector_search_index.py # Create Vector Search index
│       ├── 04_evaluation.py          # BhashaBench-Legal (30 questions)
│       ├── 05_ipc_bns_mapping.py     # IPC→BNS Delta table
│       ├── 06_scheme_ingestion.py    # 4600+ schemes → Delta + RAG
│       └── 07_constitution_ingestion.py
│
└── web/                          # Next.js 14 (App Router, static export)
    ├── app/
    │   ├── page.tsx              # Landing page
    │   └── chat/page.tsx         # Chat interface
    └── components/
        ├── VoiceInput.tsx        # MediaRecorder → Sarvam STT
        ├── AudioPlayer.tsx       # Base64 audio playback
        └── MarkdownRenderer.tsx  # BNS/IPC badge highlighting
```

## Quick Start

### 1. Build the static site

```powershell
cd web
npm install
npm run build
```

### 2. Run locally (API + UI on :8000)

```powershell
cd databricks\app
pip install -r requirements.txt
$env:PORT="8000"
python app.py
```

- UI: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- Next dev server: `npm run dev` in `web/` (set `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000`)

### 3. Deploy to Databricks

From `databricks\app` run `databricks sync` to your workspace, then `databricks apps deploy`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABRICKS_HOST` | — | Workspace URL for Vector Search + LLM |
| `DATABRICKS_TOKEN` | — | PAT or SP credentials |
| `SARVAM_API_KEY` | — | Translation + TTS + STT (via Databricks secret scope) |
| `NYAYA_VECTOR_ENDPOINT` | `nyaya-sahayak-vs` | Vector Search endpoint name |
| `NYAYA_VECTOR_INDEX` | `main.nyaya_sahayak.bns_chunks_index` | Vector Search index name |
| `NYAYA_LLM_ENDPOINT` | (auto-detect) | Comma-separated Model Serving endpoints |
| `NYAYA_RAG_K` | `5` | Number of RAG results |
| `NYAYA_SCHEMES_CSV` | (auto) | Path override for schemes CSV |

## Data Pipeline

1. Upload `data/*.csv` to UC volume `/Volumes/main/nyaya_sahayak/raw_files/`
2. Run notebooks `01` → `02` → `03` → `04` → `05` → `06` → `07`
3. Deploy app from `databricks/app` via Databricks Apps

### Preparing the Schemes Dataset (4,600+)

```bash
# Download datasets from Kaggle into data/elchemist/ and data/bilingual/
# Then merge:
cd data
python prepare_schemes.py
# Output: data/gov_schemes_full.csv
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Document upload → OCR → RAG → LLM analysis |
| `POST` | `/api/analyze_upload` | Multipart file upload variant |
| `POST` | `/api/chat` | Follow-up chat with session memory |
| `POST` | `/api/stt` | Speech-to-text (Sarvam, 22+ languages) |
| `POST` | `/api/scheme_check` | Match schemes to user profile |
| `GET` | `/api/schemes` | List all schemes (paginated) |
| `GET` | `/api/schemes/search?q=...` | Full-text scheme search |
| `GET` | `/api/schemes/categories` | List scheme categories |
| `GET` | `/api/schemes/stats` | Dataset statistics |
| `GET` | `/api/schemes/{id}` | Single scheme details |

## Evaluation

The BhashaBench-Legal benchmark (`04_evaluation.py`) tests:
- **30 questions** across 10 categories (murder, property, sexual offences, IPC mapping, schemes, constitution)
- **Metrics:** Hit Rate, Precision, Recall, Keyword Relevance, P50/P90 Latency
- **Targets:** Hit Rate ≥ 80%, P90 Latency ≤ 2s
- All results logged to **MLflow** for reproducible comparison

## Disclaimer

Educational / hackathon prototype — **not legal advice**. Always consult a qualified advocate.
