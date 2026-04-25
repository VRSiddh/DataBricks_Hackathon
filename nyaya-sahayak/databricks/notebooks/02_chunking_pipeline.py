# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Sentence-aware chunking pipeline (BNS sections → `bns_chunks`)
# MAGIC Builds RAG-ready rows with metadata prefix + description.
# MAGIC **Improvement:** Sentence-aware splitting instead of arbitrary character boundary.
# MAGIC Splits at sentence boundaries (`.`, `।`) for better semantic coherence.

# COMMAND ----------

catalog = "main"
schema = "nyaya_sahayak"
source_table = f"{catalog}.{schema}.bns_sections"
chunks_table = f"{catalog}.{schema}.bns_chunks"

max_chars = 2000  # ~500 tokens heuristic
overlap_chars = 200

# COMMAND ----------

import hashlib
import re


def sentence_split(text: str) -> list[str]:
    """Split text into sentences (handles both English and Hindi)."""
    # Split on English period, Hindi purna viram, semicolon, or newline
    raw = re.split(r'(?<=[.।;])\s+|\n+', text)
    return [s.strip() for s in raw if s.strip()]


def chunk_text_sentence_aware(text: str, max_c: int, overlap: int) -> list[str]:
    """Chunk text at sentence boundaries with overlap."""
    if text is None:
        return []
    text = text.strip()
    if len(text) <= max_c:
        return [text]

    sentences = sentence_split(text)
    if not sentences:
        return [text[:max_c]]

    chunks = []
    current_chunk = ""
    overlap_buffer = []  # sentences to prepend to next chunk

    for sent in sentences:
        candidate = (current_chunk + " " + sent).strip() if current_chunk else sent

        if len(candidate) <= max_c:
            current_chunk = candidate
            overlap_buffer.append(sent)
            # Keep only last few sentences for overlap
            while sum(len(s) + 1 for s in overlap_buffer) > overlap and len(overlap_buffer) > 1:
                overlap_buffer.pop(0)
        else:
            # Current chunk is full, save it
            if current_chunk:
                chunks.append(current_chunk)

            # Start new chunk with overlap sentences + current sentence
            overlap_text = " ".join(overlap_buffer)
            if len(overlap_text) + len(sent) + 1 <= max_c:
                current_chunk = (overlap_text + " " + sent).strip()
            else:
                current_chunk = sent
            # Handle very long sentences (longer than max_c)
            if len(current_chunk) > max_c:
                # Fall back to character-based splitting for this sentence
                while len(current_chunk) > max_c:
                    chunks.append(current_chunk[:max_c])
                    current_chunk = current_chunk[max_c - overlap:]

            overlap_buffer = [sent]

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def stable_chunk_id(section: int, chapter: int, idx: int) -> str:
    raw = f"{chapter}:{section}:{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def chunk_rows(chapter, chapter_name, chapter_subtype, section, section_name, description):
    prefix = f"BNS Section {section}: {section_name or ''} | Chapter {chapter}: {chapter_name or ''} | Subtype: {chapter_subtype or ''}\n\n"
    base = (description or "").strip()
    pieces = chunk_text_sentence_aware(base, max_chars - len(prefix), overlap_chars)
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
