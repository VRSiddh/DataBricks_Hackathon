# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Chunking pipeline (BNS sections → `bns_chunks`)
# MAGIC Builds RAG-ready rows: metadata prefix + description; splits very long text into overlapping windows (~512 tokens ≈ 2000 chars heuristic).

# COMMAND ----------

catalog = "main"
schema = "nyaya_sahayak"
source_table = f"{catalog}.{schema}.bns_sections"
chunks_table = f"{catalog}.{schema}.bns_chunks"

max_chars = 2000  # ~500 tokens heuristic
overlap_chars = 200

# COMMAND ----------

import hashlib


def chunk_text(text: str, max_c: int, overlap: int):
    if text is None:
        return []
    text = text.strip()
    if len(text) <= max_c:
        return [text]
    out = []
    start = 0
    while start < len(text):
        end = min(start + max_c, len(text))
        piece = text[start:end]
        out.append(piece)
        if end >= len(text):
            break
        start = end - overlap
        if start < 0:
            start = 0
    return out


def stable_chunk_id(section: int, chapter: int, idx: int) -> str:
    raw = f"{chapter}:{section}:{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def chunk_rows(chapter, chapter_name, chapter_subtype, section, section_name, description):
    prefix = f"BNS Section {section}: {section_name or ''} | Chapter {chapter}: {chapter_name or ''} | Subtype: {chapter_subtype or ''}\n\n"
    base = (description or "").strip()
    pieces = chunk_text(base, max_chars, overlap_chars)
    rows = []
    for i, p in enumerate(pieces):
        chunk_text_full = prefix + p
        cid = stable_chunk_id(int(section) if section is not None else 0, int(chapter) if chapter is not None else 0, i)
        rows.append((cid, int(chapter), chapter_name, chapter_subtype, int(section), section_name, chunk_text_full, i))
    return rows


src = spark.table(source_table).collect()
all_rows = []
for r in src:
    all_rows.extend(
        chunk_rows(
            r.chapter,
            r.chapter_name,
            r.chapter_subtype,
            r.section,
            r.section_name,
            r.description,
        )
    )

from pyspark.sql.types import StructType, StructField, IntegerType, StringType

chunk_struct = StructType(
    [
        StructField("chunk_id", StringType(), False),
        StructField("chapter", IntegerType(), True),
        StructField("chapter_name", StringType(), True),
        StructField("chapter_subtype", StringType(), True),
        StructField("section", IntegerType(), True),
        StructField("section_name", StringType(), True),
        StructField("chunk_text", StringType(), True),
        StructField("chunk_index", IntegerType(), True),
    ]
)
chunks_df = spark.createDataFrame(all_rows, chunk_struct)

# COMMAND ----------

(
    chunks_df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(chunks_table)
)

spark.sql(f"ALTER TABLE {chunks_table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# COMMAND ----------

display(spark.table(chunks_table).orderBy("section", "chunk_index").limit(20))

# COMMAND ----------

print("Chunks written:", spark.table(chunks_table).count(), "→", chunks_table)
