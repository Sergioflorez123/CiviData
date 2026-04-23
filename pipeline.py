#!/usr/bin/env python3
"""
Pipeline ETL Central - CiviData
Orquestación completa: Extract → Transform → Load
"""

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_extract_contratacion(dataset: str = "secop_ii", limit: int = 50000):
    """Extrae datos de contratación desde SODA API."""
    from src.extract.extract_contratacion import extract_all

    logger.info(f"[EXTRACT] Extrayendo {dataset} (límite: {limit})")
    results = extract_all(max_rows=limit)
    logger.info(f"[EXTRACT] Completado: {len(results)} archivos")
    return results


def run_extract_educacion():
    """Extrae datos de educación."""
    from src.extract.extract_educacion import extract_all

    logger.info("[EXTRACT] Extrayendo educación")
    extract_all(max_rows=10000)
    logger.info("[EXTRACT] Educación completado")


def run_clean_contratacion():
    """Limpia datos de contratación."""
    from src.transform.clean_contratacion import transform_all

    logger.info("[TRANSFORM] Limpiando contratación")
    results = transform_all()
    logger.info(f"[TRANSFORM] Completado: {len(results)} archivos")
    return results


def run_clean_educacion():
    """Limpia datos de educación."""
    from src.transform.clean_educacion import transform_all

    logger.info("[TRANSFORM] Limpiando educación")
    results = transform_all()
    logger.info(f"[TRANSFORM] Completado: {len(results)} archivos")
    return results


def run_clean_spark():
    """Limpia con PySpark (para grandes volúmenes)."""
    from src.transform.clean_spark import extract_and_clean_all

    logger.info("[TRANSFORM] Limpiando con PySpark")
    results = extract_and_clean_all()
    logger.info(f"[TRANSFORM] PySpark completado: {len(results)} archivos")
    return results


def run_load_postgres():
    """Carga datos limpios a PostgreSQL."""
    from src.load.load_to_postgres import (
        init_schemas,
        load_contratacion_to_db,
        load_educacion_to_db,
    )
    from sqlalchemy import create_engine

    logger.info("[LOAD] Iniciando carga a PostgreSQL")

    DB_URL = "postgresql://postgres:postgres@localhost:5432/cividata"
    engine = create_engine(DB_URL)

    try:
        init_schemas(engine)
        load_contratacion_to_db(clean_dir="datalake/clean/contratacion")
        load_educacion_to_db(clean_dir="datalake/clean/educacion")
        logger.info("[LOAD] Carga completada")
    except Exception as e:
        logger.error(f"[LOAD] Error: {e}")
        raise


def run_full_pipeline(dataset: str = "secop_ii", limit: int = 50000):
    """Ejecuta el pipeline completo."""
    logger.info("=" * 50)
    logger.info("INICIANDO PIPELINE ETL - CIVIDATA")
    logger.info("=" * 50)

    # 1. Extract
    logger.info("[1/3] FASE: EXTRACT")
    run_extract_contratacion(dataset, limit)
    run_extract_educacion()

    # 2. Transform
    logger.info("[2/3] FASE: TRANSFORM")
    run_clean_contratacion()

    # 3. Load
    logger.info("[3/3] FASE: LOAD")
    try:
        run_load_postgres()
    except Exception as e:
        logger.warning(f"[LOAD] PostgreSQL no disponible: {e}")

    logger.info("=" * 50)
    logger.info("PIPELINE COMPLETADO")
    logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL CiviData")
    parser.add_argument(
        "--dataset",
        "-d",
        default="secop_ii",
        choices=["secop_ii", "secop_integrado", "secop_i", "secop_ii_2025"],
        help="Dataset a extraer",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=50000, help="Límite de registros"
    )
    parser.add_argument(
        "--phase",
        "-p",
        choices=["extract", "transform", "load", "all"],
        default="all",
        help="Fase a ejecutar",
    )
    parser.add_argument(
        "--spark", action="store_true", help="Usar PySpark para transformación"
    )

    args = parser.parse_args()

    if args.phase == "all":
        run_full_pipeline(args.dataset, args.limit)
    elif args.phase == "extract":
        run_extract_contratacion(args.dataset, args.limit)
        run_extract_educacion()
    elif args.phase == "transform":
        if args.spark:
            run_clean_spark()
        else:
            run_clean_contratacion()
            run_clean_educacion()
    elif args.phase == "load":
        run_load_postgres()


if __name__ == "__main__":
    main()
