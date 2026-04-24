# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — RAG evaluation + MLflow
# MAGIC Logs retrieval/answer quality metrics to MLflow. Replace `golden_questions` with **BhashaBench-Legal** (or your own) eval set when available.

# COMMAND ----------

import mlflow
import time
import json

catalog = "main"
schema = "nyaya_sahayak"
experiment_name = "/Shared/nyaya-sahayak-rag-eval"

# Use workspace tracking when running inside Databricks
try:
    mlflow.set_tracking_uri("databricks")
except Exception:
    pass

mlflow.set_experiment(experiment_name)
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------

# Golden questions: English queries + expected section numbers (weak supervision)
golden_questions = [
    {"q": "What is the punishment for murder under BNS?", "min_section": 100, "max_section": 120},
    {"q": "Defamation and punishment Bharatiya Nyaya Sanhita", "min_section": 350, "max_section": 360},
    {"q": "Criminal breach of trust provisions", "min_section": 300, "max_section": 330},
]

# COMMAND ----------

def mock_retrieve_top_section(query: str) -> int:
    """Replace with VectorSearchClient similarity_search in production."""
    # Simple keyword stub for CI/local without VS
    q = query.lower()
    if "murder" in q:
        return 101
    if "defamation" in q:
        return 356
    if "trust" in q:
        return 316
    return 1


def score_hit(predicted_section: int, row: dict) -> float:
    lo, hi = row["min_section"], row["max_section"]
    return 1.0 if lo <= predicted_section <= hi else 0.0


# COMMAND ----------

with mlflow.start_run(run_name="bhashabench_stub_eval"):
    mlflow.log_param("eval_set", "golden_stub")
    mlflow.log_param("prompt_version", "v1")

    hits = []
    latencies = []
    for row in golden_questions:
        t0 = time.perf_counter()
        pred = mock_retrieve_top_section(row["q"])
        latencies.append(time.perf_counter() - t0)
        hits.append(score_hit(pred, row))

    mlflow.log_metric("retrieval_hit_rate", sum(hits) / len(hits))
    mlflow.log_metric("mean_latency_sec", sum(latencies) / len(latencies))
    mlflow.log_dict({"items": golden_questions, "hits": hits}, "eval_detail.json")

print("MLflow run complete. Open Experiments →", experiment_name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optional: live Vector Search eval
# MAGIC Uncomment when index is ready:
# MAGIC ```python
# MAGIC from databricks.vector_search.client import VectorSearchClient
# MAGIC client = VectorSearchClient(disable_notice=True)
# MAGIC index = client.get_index("nyaya-sahayak-vs", "main.nyaya_sahayak.bns_chunks_index")
# MAGIC index.similarity_search(columns=["chunk_text", "section"], query_text="murder punishment", num_results=5)
# MAGIC ```
