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
CLEAN_DIR.mkdir(parents=True, exist_ok=True)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas."""
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(" ", "_", regex=False)
    df.columns = df.columns.str.replace(r"[^a-z0-9_]", "", regex=True)
    return df


def clean_educacion(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia datos de educación."""
    df = df.copy()
    df = normalize_columns(df)

    # Limpiar texto
    text_cols = [c for c in df.columns if df[c].dtype == "object"]
    for col in text_cols[:10]:  # primeras 10 columnas de texto
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Eliminar duplicados
    df = df.drop_duplicates()
    logger.info(f"Limpios: {len(df)} registros educación")
    return df


def transform_file(filepath: Path) -> Path:
    logger.info(f"Transformando: {filepath.name}")
    df = pd.read_csv(filepath)
    df = clean_educacion(df)

    clean_name = f"{filepath.stem}_clean.csv"
    clean_path = CLEAN_DIR / clean_name
    df.to_csv(clean_path, index=False)
    logger.info(f"Guardado limpio: {clean_path}")
    return clean_path


def transform_all():
    results = {}
    if not RAW_DIR.exists():
        logger.warning(f"Directorio no existe: {RAW_DIR}")
        return results

    for filepath in RAW_DIR.glob("*.csv"):
        if filepath.stat().st_size > 100:  # ignora archivos vacíos
            logger.info(f"Procesando: {filepath.name}")
            clean_path = transform_file(filepath)
            results[filepath.stem] = clean_path

    return results


if __name__ == "__main__":
    transform_all()
