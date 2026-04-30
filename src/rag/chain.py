from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine
import os


class RAGService:
    """RAG Service que responde preguntas usando datos de PostgreSQL."""

    def __init__(
        self,
        db_url: Optional[str] = None,
        model: str = "openai/gpt-4o",
    ):
        self.db_url = db_url or os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cividata"
        )
        self.model = model
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
        )

    def get_context(self, category: str = "contratacion", limit: int = 50) -> str:
        """Obtiene contexto desde PostgreSQL."""
        engine = create_engine(self.db_url)

        table_map = {
            "contratacion": "contratacion",
            "resumen": "resumen_departamento",
            "entidad": "resumen_entidad",
            "sector": "resumen_sector",
            "proceso": "resumen_tipo_proceso",
        }

        table = table_map.get(category, "contratacion")

        query = f"SELECT * FROM marts.{table} ORDER BY random() LIMIT {limit}"

        with engine.connect() as conn:
            import pandas as pd

            df = pd.read_sql(query, conn)

        if df.empty:
            return "No hay datos disponibles."

        context_parts = []
        for _, row in df.head(20).iterrows():
            row_text = " | ".join([f"{k}: {v}" for k, v in row.items() if pd.notna(v)])
            context_parts.append(row_text)

        return "\n".join(context_parts)

    def build_prompt(self, question: str, context: str) -> str:
        """Construye el prompt con contexto."""
        return f"""Eres un asistente de análisis de datos de contratación pública de Colombia.

Tienes acceso a datos de la base de datos de contratos públicos (SECOP). 
Responde preguntas sobre contratos, entidades, proveedores y sectores.

Datos disponibles:
{context}

Pregunta del usuario: {question}

Instrucciones:
1. Responde SOLO usando los datos proporcionados
2. Si no tienes suficiente información, dice "No tengo datos suficientes"
3. NO hagas predicciones ni especulaciones
4. Sé conciso y específico
5. Puedes agregar contexto adicional relevante

Respuesta:"""

    def query(self, question: str, category: str = "contratacion") -> Dict[str, Any]:
        """Ejecuta una query y retorna la respuesta."""
        from src.rag.llm import OpenRouterLLM

        context = self.get_context(category)
        prompt = self.build_prompt(question, context)

        llm = OpenRouterLLM(model=self.model)
        answer = llm.invoke(prompt)

        return {
            "answer": answer,
            "sources": [f"marts.{category}"],
            "metadata": {
                "model": self.model,
                "category": category,
            },
        }
