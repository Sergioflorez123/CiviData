import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RAW_DIR = Path("datalake/raw/educacion")
CLEAN_DIR = Path("datalake/clean/educacion")
EXPORT_DIR = Path("datalake/export/educacion")
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

DEPARTAMENTO_NORMALIZE = {
    "amazonas": "Amazonas",
    "antioquia": "Antioquia",
    "arauca": "Arauca",
    "atlantico": "Atlántico",
    "bogota": "Bogotá D.C.",
    "bogota d.c.": "Bogotá D.C.",
    "bolivar": "Bolívar",
    "boyaca": "Boyacá",
    "caldas": "Caldas",
    "caquetá": "Caquetá",
    " Casanare": "Casanare",
    "cauca": "Cauca",
    "cesar": "Cesar",
    "choco": "Chocó",
    "cundinamarca": "Cundinamarca",
    "guainía": "Guainía",
    "guaviare": "Guaviare",
    "huila": "Huila",
    "la guajira": "La Guajira",
    "magdalena": "Magdalena",
    "meta": "Meta",
    "nariño": "Nariño",
    "norte de santander": "Norte de Santander",
    "putumayo": "Putumayo",
    "quindío": "Quindío",
    "risaralda": "Risaralda",
    "san andrés": "San Andrés",
    "santander": "Santander",
    "sucre": "Sucre",
    "tolima": "Tolima",
    "valle del cauca": "Valle del Cauca",
    "vaupés": "Vaupés",
    "vichada": "Vía",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas."""
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(" ", "_", regex=False)
    df.columns = df.columns.str.replace(r"[^a-z0-9_]", "", regex=True)
    return df


def normalize_departamento(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de departamentos."""
    depto_cols = [c for c in df.columns if "depto" in c or "departamento" in c]
    for col in depto_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()
            df[col] = df[col].map(lambda x: DEPARTAMENTO_NORMALIZE.get(x, x))
    return df


def clean_educacion(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia datos de educación."""
    df = df.copy()
    df = normalize_columns(df)
    df = normalize_departamento(df)

    text_cols = [c for c in df.columns if df[c].dtype == "object"]
    for col in text_cols[:15]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("nan", "")
            df[col] = df[col].replace("None", "")

    numeric_cols = [
        c
        for c in df.columns
        if any(x in c for x in ["matricula", "cantidad", "num", "total", "valor"])
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates()
    df = df.dropna(how="all")
    logger.info(f"Limpios: {len(df)} registros educación")
    return df


def transform_file(filepath: Path) -> Path:
    logger.info(f"Transformando: {filepath.name}")
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        logger.error(f"Error leyendo {filepath}: {e}")
        return None

    df = clean_educacion(df)

    clean_name = f"{filepath.stem}_clean.csv"
    clean_path = CLEAN_DIR / clean_name
    df.to_csv(clean_path, index=False)
    logger.info(f"Guardado limpio: {clean_path}")

    export_name = f"{filepath.stem}.csv"
    export_path = EXPORT_DIR / export_name
    df.to_csv(export_path, index=False)
    logger.info(f"Exportado: {export_path}")

    return clean_path


def transform_all():
    results = {}
    if not RAW_DIR.exists():
        logger.warning(f"Directorio no existe: {RAW_DIR}")
        return results

    for filepath in RAW_DIR.glob("*.csv"):
        if filepath.stat().st_size > 100:
            logger.info(f"Procesando: {filepath.name}")
            clean_path = transform_file(filepath)
            if clean_path:
                results[filepath.stem] = clean_path

    return results


if __name__ == "__main__":
    transform_all()
