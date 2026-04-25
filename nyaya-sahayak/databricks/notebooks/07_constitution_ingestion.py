# Databricks notebook source
# MAGIC %md
# MAGIC # 07 — Constitution of India Ingestion
# MAGIC Loads the Constitution of India articles into Delta Lake for RAG retrieval.
# MAGIC Creates `main.nyaya_sahayak.constitution_articles` and `main.nyaya_sahayak.constitution_chunks`.
# MAGIC
# MAGIC **Source:** civictech-India/constitution-of-india (public domain Indian government text).
# MAGIC **Prerequisite:** Upload `data/constitution_articles.csv` to `/Volumes/main/nyaya_sahayak/raw_files/`.

# COMMAND ----------

catalog = "main"
schema = "nyaya_sahayak"
raw_table = f"{catalog}.{schema}.constitution_articles"
chunks_table = f"{catalog}.{schema}.constitution_chunks"

max_chars = 2000
overlap_chars = 200

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

csv_path = dbutils.widgets.text("csv_path", "/Volumes/main/nyaya_sahayak/raw_files/constitution_articles.csv")

df = (
    spark.read.option("header", True)
    .option("multiLine", True)
    .option("escape", '"')
    .csv(csv_path)
)

# Clean columns
text_cols = ["part", "article_number", "article_title", "article_text"]
for c in text_cols:
    if c in df.columns:
        df = df.withColumn(c, F.trim(F.col(c)))

df = df.filter(F.col("article_number").isNotNull())

# COMMAND ----------

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(raw_table)
)

spark.sql(f"ALTER TABLE {raw_table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
print(f"Constitution articles ingested: {spark.table(raw_table).count()} rows → {raw_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chunking for Vector Search

# COMMAND ----------

import hashlib


def chunk_text(text, max_c, overlap):
    if text is None:
        return []
    text = text.strip()
    if len(text) <= max_c:
        return [text]
    out, start = [], 0
    while start < len(text):
        end = min(start + max_c, len(text))
        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start, end)
            if last_period > start + max_c // 2:
                end = last_period + 1
        out.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return out


def const_chunk_id(article, idx):
    raw = f"constitution:{article}:{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def constitution_chunk_rows(row):
    part = row.part or ""
    article_num = row.article_number or ""
    title = row.article_title or ""
    text = row.article_text or ""

    prefix = (
        f"Constitution of India — {part}\n"
        f"Article {article_num}: {title}\n\n"
    )

    pieces = chunk_text(text, max_chars - len(prefix), overlap_chars)
    if not pieces:
        pieces = [""]

    rows = []
    for i, p in enumerate(pieces):
        chunk_full = prefix + p
        cid = const_chunk_id(article_num, i)
        rows.append((cid, part, article_num, title, chunk_full, i))
    return rows


src = spark.table(raw_table).collect()
all_rows = []
for r in src:
    all_rows.extend(constitution_chunk_rows(r))

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType

chunk_struct = StructType([
    StructField("chunk_id", StringType(), False),
    StructField("part", StringType(), True),
    StructField("article_number", StringType(), True),
    StructField("article_title", StringType(), True),
    StructField("chunk_text", StringType(), True),
    StructField("chunk_index", IntegerType(), True),
])

chunks_df = spark.createDataFrame(all_rows, chunk_struct)

(
    chunks_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(chunks_table)
)

spark.sql(f"ALTER TABLE {chunks_table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# COMMAND ----------

display(spark.table(chunks_table).orderBy("article_number", "chunk_index").limit(20))

# COMMAND ----------

total = spark.table(chunks_table).count()
print(f"Constitution chunks: {total} → {chunks_table}")
print("Next: Create Vector Search index or union with BNS chunks for a combined index.")
