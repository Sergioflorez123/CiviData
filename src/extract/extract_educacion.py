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

DATASETS = {
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


def save_raw(df: pd.DataFrame, name: str) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"{name}_{date_str}.csv"
    filepath = BASE_DIR / filename
    df.to_csv(filepath, index=False)
    logger.info(f"Guardado: {filepath} ({len(df)} filas)")
    return filepath


def extract_all(max_rows: int = 10000):
    for name, config in DATASETS.items():
        logger.info(f"Extrayendo: {name}")
        df = fetch_soda(name, max_rows)
        if not df.empty:
            save_raw(df, name)


if __name__ == "__main__":
    extract_all()
