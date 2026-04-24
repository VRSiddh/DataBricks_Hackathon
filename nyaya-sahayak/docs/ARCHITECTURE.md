# Nyaya-Sahayak architecture

## Single Databricks App (FastAPI + Next static)

```mermaid
flowchart LR
  subgraph databricksApp [Databricks_App]
    N[Next_static_web_static]
    A[FastAPI_routers]
    N -->|"/" "/chat/"| A
  end
  U[User_browser] -->|same_origin| databricksApp
  A --> VS[Vector_Search]
  A --> LLM[Model_Serving]
  A --> Sarvam[Sarvam_APIs]
```

- **`web/`** — `next build` with `output: "export"` → **`databricks/app/web_static/`**
- **`app.py`** — registers `/api/*` and `/docs` first, then `StaticFiles` for the Next build so the **public app URL** serves both UI and API.

Export a PNG for the hackathon from your preferred Mermaid renderer if needed.
