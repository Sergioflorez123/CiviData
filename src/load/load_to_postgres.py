from sqlalchemy import create_engine, text
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_URL = "postgresql://postgres:postgres@localhost:5432/cividata"


def get_engine():
    return create_engine(DB_URL)


def init_schemas(engine):
    schemas = ["raw", "staging", "clean", "marts"]
    with engine.connect() as conn:
        for schema in schemas:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()
    logger.info("Esquemas inicializados")


def load_csv_to_db(filepath: str, table_name: str, schema: str = "raw"):
    df = pd.read_csv(filepath)
    logger.info(f"Cargando {len(df)} filas a {schema}.{table_name}")
    df.to_sql(table_name, get_engine(), schema=schema, if_exists="replace", index=False)
    logger.info(f"Cargado: {schema}.{table_name}")
    return True


def load_contratacion_to_db(clean_dir: str = "datalake/clean/contratacion"):
    from pathlib import Path

    init_schemas(get_engine())
    clean_path = Path(clean_dir)
    for filepath in clean_path.glob("*.csv"):
        table_name = filepath.stem
        load_csv_to_db(str(filepath), table_name, schema="clean")


def load_educacion_to_db(clean_dir: str = "datalake/clean/educacion"):
    from pathlib import Path

    init_schemas(get_engine())
    clean_path = Path(clean_dir)
    for filepath in clean_path.glob("*.csv"):
        if filepath.stat().st_size > 100:
            table_name = filepath.stem
            load_csv_to_db(str(filepath), table_name, schema="clean")


def load_catalogo_to_db(catalogo_file: str):
    init_schemas(get_engine())
    load_csv_to_db(catalogo_file, "catalogo", schema="raw")


if __name__ == "__main__":
    engine = get_engine()
    init_schemas(engine)
    logger.info("Base de datos lista")
