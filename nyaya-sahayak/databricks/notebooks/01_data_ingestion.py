# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Data Ingestion (BNS → Delta)
# MAGIC Loads `bns_sections.csv` from a Unity Catalog volume, cleans with PySpark, writes `workspace.nyaya_sahayak.bns_sections` with **Change Data Feed** enabled.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration
# MAGIC Set `RAW_CSV_PATH` to your volume path, e.g. `/Volumes/main/nyaya_sahayak/raw_files/bns_sections.csv`

# COMMAND ----------

catalog = "workspace"
schema = "nyaya_sahayak"
table = f"{catalog}.{schema}.bns_sections"
raw_csv_path = dbutils.widgets.text("raw_csv_path", "/Volumes/main/nyaya_sahayak/raw_files/bns_sections.csv")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType

df = (
    spark.read.option("header", True)
    .option("multiLine", True)
    .option("escape", '"')
    .csv(raw_csv_path)
)

# Normalize column names (source CSV: Chapter, Section, Section _name, Description)
rename_map = {
    "Chapter": "chapter",
    "Chapter_name": "chapter_name",
    "Chapter_subtype": "chapter_subtype",
    "Section": "section",
    "Section _name": "section_name",
    "Description": "description",
}
for old, new in rename_map.items():
    if old in df.columns:
        df = df.withColumnRenamed(old, new)

df = df.withColumn("chapter", F.col("chapter").cast(IntegerType()))
df = df.withColumn("section", F.col("section").cast(IntegerType()))

df = df.select(
    "chapter",
    F.trim(F.col("chapter_name")).alias("chapter_name"),
    F.trim(F.col("chapter_subtype")).alias("chapter_subtype"),
    "section",
    F.trim(F.col("section_name")).alias("section_name"),
    F.trim(F.regexp_replace(F.col("description"), r"\s+", " ")).alias("description"),
)

df = df.filter(F.col("section").isNotNull() & F.col("description").isNotNull())
df = df.dropDuplicates(["section"])

# COMMAND ----------

(
    df.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(table)
)

# COMMAND ----------

spark.sql(f"ALTER TABLE {table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

# COMMAND ----------

display(spark.table(table).limit(10))

# COMMAND ----------

print(f"Ingested into {table}; row count:", spark.table(table).count())

