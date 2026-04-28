import requests
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from io import StringIO

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = Path("datalake/raw/educacion")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Datasets de Educación - MEN y DANE
# Ref: docs/EDUCACION.md
DATASETS = {
    # MEN - Datos Abiertos (datos.gov.co - redirección desde mineducacion.gov.co)
    "men_establecimientos": {
        "resource_id": "9bqa-vc8t",
        "url": "https://www.datos.gov.co/resource/9bqa-vc8t.json",
        "descripcion": "Directorio de establecimientos educativos",
    },
    "men_matricula_preescolar": {
        "resource_id": "yq23-98uj",
        "url": "https://www.datos.gov.co/resource/yq23-98uj.json",
        "descripcion": "Matrícula preescolar por departamento",
    },
    "men_matricula_primaria": {
        "resource_id": "43rp-p3xh",
        "url": "https://www.datos.gov.co/resource/43rp-p3xh.json",
        "descripcion": "Matrícula primaria por departamento",
    },
    "men_matricula_secundaria": {
        "resource_id": "53kw-8w94",
        "url": "https://www.datos.gov.co/resource/53kw-8w94.json",
        "descripcion": "Matrícula secundaria por departamento",
    },
    "men_tasa_desercion": {
        "resource_id": "46xr-3wpi",
        "url": "https://www.datos.gov.co/resource/46xr-3wpi.json",
        "descripcion": "Tasa de deserción educativa",
    },
    "men_graduados_superior": {
        "resource_id": "4p5n-8qix",
        "url": "https://www.datos.gov.co/resource/4p5n-8qix.json",
        "descripcion": "Graduados educación superior",
    },
    "men_saber11_resultados": {
        "resource_id": "pjs3-8v9p",
        "url": "https://www.datos.gov.co/resource/pjs3-8v9p.json",
        "descripcion": "Resultados Saber 11 por departamento",
    },
    # DANE - GEIH (Gran Encuesta Integrada de Hogares) - Mercado laboral
    "dane_geih_empleo": {
        "url": "https://microdatos.dane.gov.co/api/v2/",
        "catalog_id": "819",
        "type": "catalog",
        "descripcion": "GEIH 2024 - Mercado laboral",
    },
    # DANE - Estadísticas de educación
    "dane_educacion_formal": {
        "url": "https://www.dane.gov.co/files/infografias/educacion/01_educacion_formal.xlsx",
        "type": "direct_excel",
        "descripcion": "Estadísticas de educación formal",
    },
    "dane_educacion_formal_csv": {
        "url": "https://www.dane.gov.co/files/infografias/educacion/01_educacion_formal.csv",
        "type": "direct_csv",
        "descripcion": "Estadísticas de educación formal (CSV)",
    },
    # Dataset legacy (prueba)
    "datos_educacion": {
        "resource_id": "2a76-5evx",
        "url": "https://www.datos.gov.co/resource/2a76-5evx.json",
    },
}


def fetch_soda(
    dataset_key: str, max_rows: int = 10000, chunk_size: int = 5000
) -> pd.DataFrame:
    config = DATASETS[dataset_key]
    url = config["url"]

    all_data = []
    offset = 0

    while offset < max_rows:
        params = {"$limit": chunk_size, "$offset": offset}
        logger.info(f"Descargando {dataset_key}: offset={offset}")

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error: {e}")
            break

        df = pd.read_json(StringIO(response.text), orient="records")
        if df.empty:
            break
        all_data.append(df)
        offset += chunk_size

        if len(df) < chunk_size:
            break

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def fetch_direct_csv(url: str, name: str) -> pd.DataFrame:
    """Descarga CSV directamente desde URL."""
    logger.info(f"Descargando CSV directo: {name}")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        content = response.text
        df = pd.read_csv(StringIO(content), encoding="utf-8")
        logger.info(f"Descargado: {len(df)} filas")
        return df
    except Exception as e:
        logger.error(f"Error descargando {name}: {e}")
        return pd.DataFrame()


def fetch_dane_catalog(catalog_id: str, dataset_key: str) -> pd.DataFrame:
    """Descarga datos del catálogo DANE microdatos."""
    base_url = DATASETS[dataset_key]["url"]
    logger.info(f"Consultando catálogo DANE: {catalog_id}")

    try:
        url = f"{base_url}catalogs/{catalog_id}/datasets"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()

        datasets = data.get("datasets", [])
        if datasets:
            first_ds = datasets[0]
            download_url = first_ds.get("download_url")
            if download_url:
                logger.info(f"Descargando: {download_url}")
                resp = requests.get(download_url, timeout=180)
                resp.raise_for_status()
                content = resp.text
                df = pd.read_csv(StringIO(content), encoding="utf-8")
                return df
    except Exception as e:
        logger.error(f"Error catálogo DANE: {e}")

    return pd.DataFrame()


def fetch_excel_dane(url: str, name: str) -> pd.DataFrame:
    """Descarga Excel desde DANE."""
    logger.info(f"Descargando Excel DANE: {name}")
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        df = pd.read_excel(response.content)
        logger.info(f"Descargado: {len(df)} filas")
        return df
    except Exception as e:
        logger.error(f"Error descargando Excel {name}: {e}")
        return pd.DataFrame()


def save_raw(df: pd.DataFrame, name: str) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{name}_{date_str}.csv"
    filepath = BASE_DIR / filename
    df.to_csv(filepath, index=False)
    logger.info(f"Guardado: {filepath} ({len(df)} filas)")
    return filepath


def extract_all(max_rows: int = 10000):
    results = {}

    for name, config in DATASETS.items():
        df = pd.DataFrame()

        if config.get("type") == "direct_csv":
            df = fetch_direct_csv(config["url"], name)
        elif config.get("type") == "direct_excel":
            df = fetch_excel_dane(config["url"], name)
        elif config.get("type") == "catalog":
            df = fetch_dane_catalog(config["catalog_id"], name)
        elif config.get("resource_id"):
            df = fetch_soda(name, max_rows)

        if not df.empty:
            save_raw(df, name)
            results[name] = len(df)
        else:
            logger.warning(f"Sin datos para: {name}")

    logger.info(f"Extracción completada: {len(results)} datasets")
    return results


if __name__ == "__main__":
    extract_all()
