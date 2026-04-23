import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RAW_DIR = Path("datalake/raw/contratacion")
CLEAN_DIR = Path("datalake/clean/contratacion")
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

DATE_FORMAT = "%Y-%m-%d"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(" ", "_", regex=False)
    df.columns = df.columns.str.replace(r"[^a-z0-9_]", "", regex=True)
    return df


def clean_date(val):
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(str(val), fmt).strftime(DATE_FORMAT)
            except:
                continue
        return None
    except:
        return None


def clean_contratacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = normalize_columns(df)

    valor_cols = ["valor_del_contrato", "valor_contrato", "valor_pagado"]
    for col in valor_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    date_cols = [
        "fecha_de_firma",
        "fecha_de_inicio_del_contrato",
        "fecha_de_fin_del_contrato",
        "fecha_inicio",
        "fecha_firma",
        "fecha_fin",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_date)

    text_cols = [
        "nombre_entidad",
        "departamento",
        "ciudad",
        "proveedor_adjudicado",
        "proveedor",
        "proceso_de_compra",
        "tipo_de_contrato",
        "modalidad_de_contratacion",
        "estado_contrato",
        "sector",
        "rama",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
            df[col] = df[col].replace("nan", "").replace("None", "")

    if "id_contrato" in df.columns:
        df = df[
            df["id_contrato"].notna()
            & (df["id_contrato"] != "")
            & (df["id_contrato"] != "nan")
        ]

    df = df.drop_duplicates()

    before = len(df)
    if "valor_del_contrato" in df.columns:
        df = df[df["valor_del_contrato"] > 0]
    elif "valor_contrato" in df.columns:
        df = df[df["valor_contrato"] > 0]

    logger.info(
        f"Limpios: {len(df)} registros (eliminados {before - len(df)} con valor 0)"
    )
    return df


def transform_file(filepath: Path) -> Path:
    logger.info(f"Transformando: {filepath.name}")
    df = pd.read_csv(filepath, low_memory=False)
    df = clean_contratacion(df)

    clean_name = f"{filepath.stem}_clean.csv"
    clean_path = CLEAN_DIR / clean_name
    df.to_csv(clean_path, index=False)
    logger.info(f"Guardado limpio: {clean_path} ({len(df)} filas)")
    return clean_path


def transform_all():
    results = {}
    if not RAW_DIR.exists():
        logger.warning(f"Directorio no existe: {RAW_DIR}")
        return results

    for filepath in RAW_DIR.glob("*.csv"):
        logger.info(f"Procesando: {filepath.name}")
        clean_path = transform_file(filepath)
        results[filepath.stem] = clean_path

    return results


if __name__ == "__main__":
    transform_all()
