"""
Consolida los CSVs de SECOP (I, II, Integrado) en una tabla unificada.
No modifica los CSVs originales, solo crea uno nuevo consolidado.
Incluye normalización robusta de todos los campos.
"""

import pandas as pd
import logging
import re
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

EXPORT_DIR = Path("datalake/export/contratacion")
CONSOLIDATED_DIR = Path("datalake/export/consolidated")
CONSOLIDATED_DIR.mkdir(parents=True, exist_ok=True)


def normalize_text(val):
    """Normaliza texto: strip, title case, limpia caracteres."""
    if pd.isna(val) or val is None:
        return ""
    val = str(val).strip()
    if not val or val.lower() in ["nan", "none", "null", ""]:
        return ""
    val = val.title()
    val = re.sub(r"\s+", " ", val)
    return val


def normalize_departamento(val):
    """Normaliza nombres de departamentos."""
    if pd.isna(val) or val == "" or val is None:
        return ""

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


def clean_valor(val):
    """Limpia valores numéricos."""
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
        val_str = str(val).strip()
        val_str = re.sub(r"[$.,\s]", "", val_str)
        val_str = val_str.replace(".", "").replace(",", ".")
        return float(val_str) if val_str else 0.0
    except:
        return 0.0


def clean_nit(val):
    """Limpia NIT."""
    if pd.isna(val) or val == "" or val is None:
        return ""
    val = str(val).strip()
    val = re.sub(r"[^0-9\-]", "", val)
    return val if val else ""


def normalize_columns_secop1(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas de SECOP I."""
    df = df.copy()

    rename_map = {
        "nombre_entidad": "nombre_entidad",
        "nit_de_la_entidad": "nit_entidad",
        "departamento_entidad": "departamento",
        "modalidad_de_contratacion": "modalidad",
        "tipo_de_contrato": "tipo_contrato",
        "cuantia_proceso": "valor_contrato",
        "fecha_de_firma_del_contrato": "fecha_firma",
        "proponentes_seleccionados": "proveedor",
        "anno_firma_contrato": "anno",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df["origen"] = "SECOP_I"
    if "uid" not in df.columns:
        numero_col = "numero_de_contrato"
        if numero_col in df.columns:
            df["uid"] = df[numero_col].astype(str) + "_" + df["nit_entidad"].astype(str)
        else:
            df["uid"] = "SECOP_I_" + df.index.astype(str)

    return df


def normalize_columns_secop2(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas de SECOP II."""
    df = df.copy()

    rename_map = {
        "nombre_entidad": "nombre_entidad",
        "nit_entidad": "nit_entidad",
        "departamento": "departamento",
        "modalidad_de_contratacion": "modalidad",
        "tipo_de_contrato": "tipo_contrato",
        "valor_del_contrato": "valor_contrato",
        "fecha_de_firma": "fecha_firma",
        "proveedor_adjudicado": "proveedor",
        "proceso_de_compra": "proceso",
        "sector": "sector",
        "id_contrato": "uid",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df["origen"] = "SECOP_II"
    return df


def normalize_columns_integrado(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas de SECOP Integrado."""
    df = df.copy()

    rename_map = {
        "nombre_de_la_entidad": "nombre_entidad",
        "nit_de_la_entidad": "nit_entidad",
        "departamento_entidad": "departamento",
        "modalidad_de_contrataci_n": "modalidad",
        "tipo_de_contrato": "tipo_contrato",
        "valor_contrato": "valor_contrato",
        "fecha_de_firma_del_contrato": "fecha_firma",
        "nom_raz_social_contratista": "proveedor",
        "numero_del_contrato": "uid",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df["origen"] = "SECOP_INTEGRADO"
    return df


def find_latest_files():
    """Busca los archivos más recientes en export/contratacion (excluye 2025)."""
    pattern_map = {
        "secop_i": "secop_i_*.csv",
        "secop_ii": "secop_ii_*.csv",
        "secop_integrado": "secop_integrado_*.csv",
    }

    files = {}
    for key, pattern in pattern_map.items():
        matches = sorted(
            EXPORT_DIR.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True
        )
        # Excluir archivos de 2025 (contienen metadata diferente)
        matches = [m for m in matches if "2025" not in m.name]

        if matches:
            files[key] = matches[0].name
            logger.info(f"Último {key}: {matches[0].name}")
        else:
            logger.warning(f"No encontrado: {pattern}")

    return files


def consolidate_secop():
    """Consolida los CSVs de SECOP más recientes."""
    files = find_latest_files()

    if not files:
        logger.error("No se encontraron archivos para consolidar")
        return None

    normalize_funcs = {
        "secop_i": normalize_columns_secop1,
        "secop_ii": normalize_columns_secop2,
        "secop_integrado": normalize_columns_integrado,
    }

    common_columns = [
        "uid",
        "nombre_entidad",
        "nit_entidad",
        "departamento",
        "modalidad",
        "tipo_contrato",
        "valor_contrato",
        "fecha_firma",
        "proveedor",
        "origen",
    ]

    all_dfs = []

    for name, filename in files.items():
        filepath = EXPORT_DIR / filename
        if not filepath.exists():
            logger.warning(f"Archivo no encontrado: {filepath}")
            continue

        logger.info(f"Cargando: {filename}")
        df = pd.read_csv(filepath, low_memory=False)

        df = normalize_funcs[name](df)

        available_cols = [c for c in common_columns if c in df.columns]
        df = df[available_cols]

        for col in common_columns:
            if col not in df.columns:
                df[col] = ""

        logger.info(f"  - {len(df)} registros de {name}")
        all_dfs.append(df)

    if not all_dfs:
        logger.error("No se cargó ningún archivo")
        return None

    consolidated = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"Total consolidado: {len(consolidated)} registros")

    # Normalizar todos los campos de texto
    text_cols = [
        "nombre_entidad",
        "departamento",
        "modalidad",
        "tipo_contrato",
        "proveedor",
    ]
    for col in text_cols:
        if col in consolidated.columns:
            consolidated[col] = consolidated[col].apply(normalize_text)

    if "departamento" in consolidated.columns:
        consolidated["departamento"] = consolidated["departamento"].apply(
            normalize_departamento
        )

    if "nit_entidad" in consolidated.columns:
        consolidated["nit_entidad"] = consolidated["nit_entidad"].apply(clean_nit)

    if "valor_contrato" in consolidated.columns:
        consolidated["valor_contrato"] = consolidated["valor_contrato"].apply(
            clean_valor
        )

    # Reemplazar valores vacíos con "No Definido"
    no_definido_cols = [
        "nit_entidad",
        "departamento",
        "proveedor",
        "modalidad",
        "tipo_contrato",
        "fecha_firma",
    ]
    for col in no_definido_cols:
        if col in consolidated.columns:
            consolidated[col] = consolidated[col].replace("", "No Definido")
            consolidated[col] = consolidated[col].fillna("No Definido")

    if "nombre_entidad" in consolidated.columns:
        consolidated["nombre_entidad"] = consolidated["nombre_entidad"].replace(
            "", "No Definido"
        )
        consolidated["nombre_entidad"] = consolidated["nombre_entidad"].fillna(
            "No Definido"
        )

    # FILTROS: Eliminar registros que no pasen calidad mínima
    before = len(consolidated)

    # Filter 1: Eliminar si valor es 0 o negativo
    consolidated = consolidated[consolidated["valor_contrato"] > 0]
    logger.info(f"Filtrados valor 0: {before - len(consolidated)}")

    before = len(consolidated)
    # Filter 2: Eliminar si nombre_entidad es "No Definido" o vacío
    consolidated = consolidated[consolidated["nombre_entidad"] != "No Definido"]
    logger.info(f"Filtrados nombre_entidad vacío: {before - len(consolidated)}")

    before = len(consolidated)
    # Filter 3: Eliminar si nit es "No Definido" (NIT inválido)
    consolidated = consolidated[consolidated["nit_entidad"] != "No Definido"]
    logger.info(f"Filtrados nit vacío: {before - len(consolidated)}")

    before = len(consolidated)
    # Filter 4: Eliminar si departamento es "No Definido" o vacío
    consolidated = consolidated[consolidated["departamento"] != "No Definido"]
    logger.info(f"Filtrados departamento vacío: {before - len(consolidated)}")

    # Guardar
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"secop_consolidado_{date_str}.csv"
    filepath = CONSOLIDATED_DIR / filename
    consolidated.to_csv(filepath, index=False)
    logger.info(f"Guardado: {filepath}")

    latest_path = CONSOLIDATED_DIR / "secop_consolidado_latest.csv"
    consolidated.to_csv(latest_path, index=False)
    logger.info(f"Guardado latest: {latest_path}")

    # Resumen
    logger.info("=== RESUMEN CONSOLIDACIÓN ===")
    logger.info(f"Total registros: {len(consolidated)}")
    for origen in list(consolidated["origen"].unique()):
        count = len(consolidated[consolidated["origen"] == origen])
        logger.info(f"  {origen}: {count}")

    return filepath


if __name__ == "__main__":
    consolidate_secop()
