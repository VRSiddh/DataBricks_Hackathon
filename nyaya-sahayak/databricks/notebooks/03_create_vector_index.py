# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Mosaic AI Vector Search (Delta Sync)
# MAGIC Creates **one** Vector Search endpoint (Free Edition quota) and a **Delta Sync** index on `bns_chunks.chunk_text`.
# MAGIC
# MAGIC **Prerequisites:** `workspace.nyaya_sahayak.bns_chunks` exists with CDF enabled; workspace has Vector Search + embedding model access.

# COMMAND ----------

dbutils.widgets.text("endpoint_name", "nyaya-sahayak-vs")
endpoint_name = dbutils.widgets.get("endpoint_name")

catalog = "workspace"
schema = "nyaya_sahayak"
source_table = f"{catalog}.{schema}.bns_chunks"
index_name = f"{catalog}.{schema}.bns_chunks_index"

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient(disable_notice=True)

# COMMAND ----------

# List endpoints; create if missing (API shape varies slightly by SDK version)
try:
    resp = vsc.list_endpoints()
    endpoints = resp.get("endpoints", resp) if isinstance(resp, dict) else []
    existing = [e.get("name") for e in endpoints if isinstance(e, dict)]
except Exception:
    existing = []

if endpoint_name not in existing:
    vsc.create_endpoint(name=endpoint_name, endpoint_type="STANDARD")

print("Using endpoint:", endpoint_name)

# COMMAND ----------

# Create Delta Sync index (Databricks-managed embeddings)
# See: https://docs.databricks.com/generative-ai/create-query-vector-search.html

index = vsc.create_delta_sync_index(
    endpoint_name=endpoint_name,
    source_table_name=source_table,
    index_name=index_name,
    primary_key="chunk_id",
    embedding_source_column="chunk_text",
    embedding_model_endpoint_name="databricks-gte-large-en",
    pipeline_type="TRIGGERED",
    columns_to_sync=None,
)

print("Index creation initiated:", index_name)
print(index)

# COMMAND ----------

# MAGIC %md
# MAGIC Poll status in UI: **Compute → Vector Search** until index is **Ready**. Then query from the app with `VectorSearchClient().get_index(endpoint, index_name).similarity_search(...)`.

