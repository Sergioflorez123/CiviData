from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, trim, regexp_replace, to_date
from pyspark.sql.types import DoubleType
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_spark(app_name: str = "CiviData") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )


def normalize_columns(df):
    for c in df.columns:
        new_name = c.lower().replace(" ", "_").replace("-", "_")
        df = df.withColumnRenamed(c, new_name)
    return df


def clean_contratacion(df):
    df = normalize_columns(df)

    if "valor_contrato" in df.columns:
        df = df.withColumn(
            "valor_contrato",
            regexp_replace(col("valor_contrato"), "[^0-9.]", "").cast(DoubleType()),
        )

    date_cols = ["fecha_inicio", "fecha_firma", "fecha_fin", "fecha_adjudicacion"]
    for c in date_cols:
        if c in df.columns:
            df = df.withColumn(c, to_date(col(c), "yyyy-MM-dd"))

    text_cols = [
        "nombre_entidad",
        "departamento",
        "municipio",
        "objeto_contrato",
        "proveedor",
    ]
    for c in text_cols:
        if c in df.columns:
            df = df.withColumn(c, trim(lower(col(c))))

    df = df.dropDuplicates()
    logger.info(f"Limpios: {df.count()} registros")
    return df


def process_file(input_path: str, output_path: str, category: str = "contratacion"):
    spark = create_spark()

    logger.info(f"Leyendo: {input_path}")
    df = spark.read.option("header", "true").json(input_path)

    if category == "contratacion":
        df = clean_contratacion(df)

    df.write.mode("overwrite").parquet(output_path)
    logger.info(f"Guardado: {output_path}")

    spark.stop()


def extract_and_clean_all():
    raw_dir = Path("datalake/raw")
    clean_dir = Path("datalake/clean")
    clean_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for json_file in raw_dir.rglob("*.json"):
        category = json_file.parent.name
        output = clean_dir / category / json_file.stem

        logger.info(f"Procesando: {json_file}")
        process_file(str(json_file), str(output), category)
        results[json_file.name] = str(output)

    return results


if __name__ == "__main__":
    extract_and_clean_all()
