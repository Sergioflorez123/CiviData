"""
Loader para datos - Carga documentos desde PostgreSQL o CSV.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional
from sqlalchemy import create_engine, text


class DataLoader:
    """Carga datos desde PostgreSQL o CSV y los convierte en documentos."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or "postgresql://postgres:postgres@localhost:5432/cividata"

    def load_from_postgres(
        self, table: str, schema: str = "marts", limit: Optional[int] = None
    ) -> List[dict]:
        """Carga datos desde PostgreSQL."""
        engine = create_engine(self.db_url)

        query = f"SELECT * FROM {schema}.{table}"
        if limit:
            query += f" LIMIT {limit}"

        with engine.connect() as conn:
            df = pd.read_sql(query, conn)

        return df.to_dict("records")

    def load_from_csv(self, filepath: str) -> List[dict]:
        """Carga datos desde CSV."""
        df = pd.read_csv(filepath)
        return df.to_dict("records")

    def load_directory(self, directory: str, pattern: str = "*.csv") -> List[dict]:
        """Carga todos los CSV de un directorio."""
        path = Path(directory)
        all_data = []

        for filepath in path.glob(pattern):
            df = pd.read_csv(filepath)
            all_data.extend(df.to_dict("records"))

        return all_data

    def to_documents(self, data: List[dict], source_name: str) -> List[dict]:
        """Convierte datos en documentos para RAG."""
        documents = []

        for i, row in enumerate(data):
            text_content = " | ".join(
                [f"{k}: {v}" for k, v in row.items() if v is not None]
            )

            documents.append(
                {
                    "id": f"{source_name}_{i}",
                    "content": text_content,
                    "metadata": {"source": source_name, "index": i},
                }
            )

        return documents
