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

BASE_DIR = Path("datalake/raw/contratacion")
BASE_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = {
    "secop_ii": {
        "resource_id": "jbjy-vk9h",
        "url": "https://www.datos.gov.co/resource/jbjy-vk9h.json",
        "limit": 50000,
    },
    "secop_integrado": {
        "resource_id": "rpmr-utcd",
        "url": "https://www.datos.gov.co/resource/rpmr-utcd.json",
        "limit": 50000,
    },
    "secop_i": {
        "resource_id": "f789-7hwg",
        "url": "https://www.datos.gov.co/resource/f789-7hwg.json",
        "limit": 50000,
    },
    "secop_ii_2025": {
        "resource_id": "dmgg-8hin",
        "url": "https://www.datos.gov.co/resource/dmgg-8hin.json",
        "limit": 50000,
    },
}


def fetch_soda(
    dataset_key: str, max_rows: int = 50000, chunk_size: int = 10000
) -> pd.DataFrame:
    """Descarga datos desde Socrata SODA API paginando si es necesario."""
    config = DATASETS[dataset_key]
    url = config["url"]
    limit = min(config["limit"], max_rows)

    all_data = []
    offset = 0

    while offset < limit:
        params = {
            "$limit": chunk_size,
            "$offset": offset,
        }

        logger.info(f"Descargando {dataset_key}: offset={offset}, limit={chunk_size}")

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error descargando {dataset_key}: {e}")
            break

        df = pd.read_json(StringIO(response.text), orient="records")

        if df.empty:
            break

        all_data.append(df)
        offset += chunk_size

        if len(df) < chunk_size:
            break

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Descargados {len(final_df)} filas de {dataset_key}")
        return final_df
    else:
        return pd.DataFrame()


def save_raw(df: pd.DataFrame, dataset_key: str) -> Path:
    """Guarda el DataFrame en CSV con fecha."""
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{dataset_key}_{date_str}.csv"
    filepath = BASE_DIR / filename
    df.to_csv(filepath, index=False)
    logger.info(f"Guardado: {filepath}")
    return filepath


def extract_all(max_rows: int = 50000):
    """Extrae todos los datasets de contratacion."""
    results = {}

    for dataset_key in DATASETS.keys():
        logger.info(f"Iniciando extraccion: {dataset_key}")
        df = fetch_soda(dataset_key, max_rows)
        if not df.empty:
            path = save_raw(df, dataset_key)
            results[dataset_key] = path
        else:
            logger.warning(f"Sin datos para {dataset_key}")

    return results


if __name__ == "__main__":
    extract_all()
