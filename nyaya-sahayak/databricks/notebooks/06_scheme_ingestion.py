# Databricks notebook source
# MAGIC %md
# MAGIC # 06 — Government Schemes Ingestion (4600+ MyScheme.gov.in scraped data)
# MAGIC Ingests the unified `gov_schemes_full.csv` (merged from Elchemist + Bilingual datasets)
# MAGIC into Delta Lake with RAG-optimised chunking for Vector Search.
# MAGIC
# MAGIC **Prerequisite:** Run `data/prepare_schemes.py` locally first, then upload
# MAGIC `data/gov_schemes_full.csv` to `/Volumes/main/nyaya_sahayak/raw_files/`.

# COMMAND ----------

catalog = "main"
schema = "nyaya_sahayak"
raw_table = f"{catalog}.{schema}.gov_schemes"
chunks_table = f"{catalog}.{schema}.scheme_chunks"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType

csv_path = dbutils.widgets.text("csv_path", "/Volumes/main/nyaya_sahayak/raw_files/gov_schemes_full.csv")

# Explicit schema for reliable parsing
scheme_schema = StructType([
    StructField("scheme_id", IntegerType(), True),
    StructField("scheme_name", StringType(), True),
    StructField("short_title", StringType(), True),
    StructField("ministry", StringType(), True),
    StructField("category", StringType(), True),
    StructField("sub_category", StringType(), True),
    StructField("level", StringType(), True),
    StructField("state_ut", StringType(), True),
    StructField("target_beneficiaries", StringType(), True),
    StructField("eligibility_criteria", StringType(), True),
    StructField("eligibility_gender", StringType(), True),
    StructField("eligibility_min_age", IntegerType(), True),
    StructField("eligibility_max_age", IntegerType(), True),
    StructField("eligibility_income_limit", FloatType(), True),
    StructField("eligibility_caste", StringType(), True),
    StructField("benefits", StringType(), True),
    StructField("application_process", StringType(), True),
    StructField("documents_required", StringType(), True),
    StructField("description_en", StringType(), True),
    StructField("description_hi", StringType(), True),
    StructField("source_url", StringType(), True),
])

df = (
    spark.read.option("header", True)
    .option("multiLine", True)
    .option("escape", '"')
    .schema(scheme_schema)
    .csv(csv_path)
)

df = df.filter(F.col("scheme_name").isNotNull())
print(f"Loaded {df.count()} schemes from CSV")

# COMMAND ----------

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(raw_table)
)
spark.sql(f"ALTER TABLE {raw_table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## RAG-optimised chunking
# MAGIC Each scheme becomes 1-3 chunks: main description + eligibility + benefits.
# MAGIC Metadata is prefixed so the LLM knows the scheme context.

# COMMAND ----------

import hashlib


def chunk_scheme(row):
    """Create RAG-optimised chunks from a scheme row."""
    sid = row.scheme_id or 0
    name = row.scheme_name or ""
    ministry = row.ministry or ""
    category = row.category or ""
    level = row.level or "Central"
    state = row.state_ut or "All"
    target = row.target_beneficiaries or ""
    elig = row.eligibility_criteria or ""
    gender = row.eligibility_gender or "All"
    benefits = row.benefits or ""
    apply_process = row.application_process or ""
    docs = row.documents_required or ""
    desc_en = row.description_en or ""
    desc_hi = row.description_hi or ""

    prefix = (
        f"Government Scheme: {name}\n"
        f"Ministry/Department: {ministry} | Category: {category}\n"
        f"Level: {level} | State: {state}\n"
        f"Target: {target} | Gender: {gender}\n\n"
    )

    chunks = []

    # Chunk 1: Description + eligibility
    text1 = prefix + f"Description:\n{desc_en}\n\nEligibility:\n{elig}"
    if desc_hi:
        text1 += f"\n\n(Hindi) विवरण:\n{desc_hi}"
    cid1 = hashlib.sha256(f"scheme:{sid}:desc".encode()).hexdigest()[:32]
    chunks.append((cid1, sid, name, category, "description", text1, 0))

    # Chunk 2: Benefits + application process
    if benefits or apply_process:
        text2 = prefix + f"Benefits:\n{benefits}\n\nHow to Apply:\n{apply_process}"
        if docs:
            text2 += f"\n\nDocuments Required:\n{docs}"
        cid2 = hashlib.sha256(f"scheme:{sid}:benefits".encode()).hexdigest()[:32]
        chunks.append((cid2, sid, name, category, "benefits", text2, 1))

    return chunks


src = spark.table(raw_table).collect()
all_chunks = []
for r in src:
    all_chunks.extend(chunk_scheme(r))

print(f"Generated {len(all_chunks)} chunks from {len(src)} schemes")

# COMMAND ----------

chunk_struct = StructType([
    StructField("chunk_id", StringType(), False),
    StructField("scheme_id", IntegerType(), True),
    StructField("scheme_name", StringType(), True),
    StructField("category", StringType(), True),
    StructField("chunk_type", StringType(), True),
    StructField("chunk_text", StringType(), True),
    StructField("chunk_index", IntegerType(), True),
])

chunks_df = spark.createDataFrame(all_chunks, chunk_struct)

(
    chunks_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(chunks_table)
)
spark.sql(f"ALTER TABLE {chunks_table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# COMMAND ----------

display(spark.table(chunks_table).orderBy("scheme_id", "chunk_index").limit(20))

# COMMAND ----------

total = spark.table(chunks_table).count()
print(f"Scheme chunks: {total} → {chunks_table}")
print("Next step: Create/sync Vector Search index on this table.")
display(spark.table(chunks_table).groupBy("chunk_type").count().orderBy("count", ascending=False))
