import pandas as pd
import logging
import re
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

RAW_DIR = Path("datalake/raw/contratacion")
CLEAN_DIR = Path("datalake/clean/contratacion")
EXPORT_DIR = Path("datalake/export/contratacion")
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

DATE_FORMAT = "%Y-%m-%d"


def normalize_text(val):
    """Normaliza texto: strip, title case, limpia caracteres extraños."""
    if pd.isna(val) or val is None:
        return ""
    val = str(val).strip()
    if not val or val.lower() in ["nan", "none", "null", ""]:
        return ""
    # Convertir a title case pero mantener siglas
    val = val.title()
    # Limpiar caracteres múltiples
    val = re.sub(r"\s+", " ", val)
    return val


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas."""
    df.columns = df.columns.str.lower()
    df.columns = df.columns.str.replace(" ", "_", regex=False)
    df.columns = df.columns.str.replace(r"[^a-z0-9_]", "", regex=True)
    return df


def clean_date(val):
    """Limpia y normaliza fechas."""
    if pd.isna(val) or val == "" or val is None:
        return None
    try:
        val_str = str(val).strip()
        # Remover horas si existen
        val_str = re.sub(r"\s+\d{1,2}:\d{2}.*$", "", val_str)

        for fmt in [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%Y-%m-%d %H:%M:%S",
        ]:
            try:
                return datetime.strptime(val_str, fmt).strftime(DATE_FORMAT)
            except:
                continue
        return None
    except:
        return None


def clean_valor(val):
    """Limpia valores numéricos."""
    if pd.isna(val) or val == "" or val is None:
        return 0
    try:
        val_str = str(val).strip()
        # Remover símbolos de moneda y separadores de miles
        val_str = re.sub(r"[$.,\s]", "", val_str)
        # Manejar formato colombiano (1.234.567)
        val_str = val_str.replace(".", "").replace(",", ".")
        return float(val_str) if val_str else 0
    except:
        return 0


def clean_nit(val):
    """Limpia NIT/identificaciones."""
    if pd.isna(val) or val == "" or val is None:
        return None
    val = str(val).strip()
    # Solo dejar números y guión
    val = re.sub(r"[^0-9\-]", "", val)
    return val if val else None


def normalize_departamento(val):
    """Normaliza nombres de departamentos."""
    if pd.isna(val) or val == "" or val is None:
        return None

    depto_map = {
        "bogota d.c.": "Bogotá D.C.",
        "bogota": "Bogotá D.C.",
        "cundinamarca": "Cundinamarca",
        "antioquia": "Antioquia",
        "valle del cauca": "Valle del Cauca",
        "atlantico": "Atlántico",
        "santander": "Santander",
        "norte de santander": "Norte de Santander",
        "tolima": "Tolima",
        "boyaca": "Boyacá",
        "cauca": "Cauca",
        "nariño": "Nariño",
        "huila": "Huila",
        "magdalena": "Magdalena",
        "bolivar": "Bolívar",
        "caldas": "Caldas",
        "risaralda": "Risaralda",
        "quindio": "Quindío",
        "meta": "Meta",
        "cesar": "Cesar",
        "la guajira": "La Guajira",
        "arauca": "Arauca",
        "putumayo": "Putumayo",
        "amazonas": "Amazonas",
        "guainia": "Guainía",
        "guaviare": "Guaviare",
        "vaupes": "Vaupés",
        "vichada": "Vichada",
        "choco": "Chocó",
        "caqueta": "Caquetá",
        "casanare": "Casanare",
        "sucre": "Sucre",
        "cordoba": "Córdoba",
    }

    val_normalized = str(val).strip().lower()
    return depto_map.get(val_normalized, val.title())


def clean_contratacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = normalize_column_names(df)

    # Limpiar valores numéricos
    valor_cols = [c for c in df.columns if "valor" in c and c != "valor_contrato"]
    for col in valor_cols + ["valor_contrato"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_valor)

    # Limpiar fechas
    date_cols = [c for c in df.columns if "fecha" in c]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_date)

    # Normalizar NIT
    nit_cols = [c for c in df.columns if "nit" in c]
    for col in nit_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_nit)

    # Normalizar departamento
    depto_cols = [c for c in df.columns if "departamento" in c]
    for col in depto_cols:
        if col in df.columns:
            df[col] = df[col].apply(normalize_departamento)

    # Normalizar texto
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
        "modalidad",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)

    # Eliminar filas con ID vacío
    id_cols = [c for c in df.columns if "id" in c and "contrato" in c or c == "uid"]
    for col in id_cols:
        if col in df.columns:
            df = df[df[col].notna() & (df[col] != "")]

    # Eliminar duplicados
    df = df.drop_duplicates()

    # Filtrar valores mayores a 0
    before = len(df)
    if "valor_del_contrato" in df.columns:
        df = df[df["valor_del_contrato"] > 0]
    elif "valor_contrato" in df.columns:
        df = df[df["valor_contrato"] > 0]

    logger.info(f"Limpios: {len(df)} registros (eliminados {before - len(df)})")
    return df


def transform_file(filepath: Path) -> Path:
    logger.info(f"Transformando: {filepath.name}")
    df = pd.read_csv(filepath, low_memory=False)
    df = clean_contratacion(df)

    clean_name = f"{filepath.stem}_clean.csv"
    clean_path = CLEAN_DIR / clean_name
    df.to_csv(clean_path, index=False)
    logger.info(f"Guardado limpio: {clean_path} ({len(df)} filas)")

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
        logger.info(f"Procesando: {filepath.name}")
        clean_path = transform_file(filepath)
        results[filepath.stem] = clean_path

    return results


if __name__ == "__main__":
    transform_all()
