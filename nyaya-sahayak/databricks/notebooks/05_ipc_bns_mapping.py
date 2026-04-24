# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — IPC → BNS mapping table
# MAGIC Seeds `main.nyaya_sahayak.ipc_bns_mapping` with **curated high-signal** mappings (illustrative; verify against official concordance for production).
# MAGIC Extend with LLM-assisted rows in a governed pipeline if needed.

# COMMAND ----------

catalog = "main"
schema = "nyaya_sahayak"
table = f"{catalog}.{schema}.ipc_bns_mapping"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------

# Curated examples (IPC section → BNS section + note). Add full official mapping separately.
mapping_rows = [
    (302, 101, "Murder — illustrative mapping; verify with BNSS/BNS official tables"),
    (304, 103, "Attempt to commit murder"),
    (376, 63, "Rape — subject to BNSS/BNS split; verify"),
    (420, 316, "Cheating and dishonestly inducing delivery of property → criminal breach / cheating clusters"),
    (499, 356, "Defamation"),
]

cols = ["ipc_section", "bns_section", "mapping_note"]

df = spark.createDataFrame(mapping_rows, cols)

# COMMAND ----------

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(table)
)

# COMMAND ----------

display(spark.table(table))
