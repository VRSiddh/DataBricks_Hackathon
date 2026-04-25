# Databricks notebook source
# MAGIC %md
# MAGIC # 05 — IPC → BNS mapping table (Complete)
# MAGIC Loads **150+ curated** mappings from `ipc_bns_mapping.csv` into `workspace.nyaya_sahayak.ipc_bns_mapping`.
# MAGIC Sources: BPR&D correspondence table, UP Police ready reference, official Gazette of India.
# MAGIC
# MAGIC **Note:** IPC sections marked `0` are new BNS provisions with no IPC equivalent (e.g., organised crime, terrorism).

# COMMAND ----------

catalog = "workspace"
schema = "nyaya_sahayak"
table = f"{catalog}.{schema}.ipc_bns_mapping"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

# Load the expanded CSV from volume (upload ipc_bns_mapping.csv to your UC volume first)
csv_path = dbutils.widgets.text("csv_path", "/Volumes/main/nyaya_sahayak/raw_files/ipc_bns_mapping.csv")

df = (
    spark.read.option("header", True)
    .option("multiLine", True)
    .option("escape", '"')
    .csv(csv_path)
)

# Cast section columns to integer (filter out non-numeric like "120A" — handled separately)
df = df.withColumn("ipc_section", F.col("ipc_section").cast(IntegerType()))
df = df.withColumn("bns_section", F.col("bns_section").cast(IntegerType()))

# Clean up
df = df.filter(F.col("ipc_section").isNotNull() & F.col("bns_section").isNotNull())
df = df.select(
    "ipc_section",
    "bns_section",
    F.trim(F.col("offense_description")).alias("offense_description"),
    F.trim(F.col("mapping_note")).alias("mapping_note"),
)

# COMMAND ----------

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(table)
)

spark.sql(f"ALTER TABLE {table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# COMMAND ----------

display(spark.table(table).orderBy("ipc_section"))

# COMMAND ----------

total = spark.table(table).count()
new_bns = spark.table(table).filter(F.col("ipc_section") == 0).count()
print(f"Loaded {total} IPC→BNS mappings ({new_bns} are new BNS-only provisions) into {table}")

