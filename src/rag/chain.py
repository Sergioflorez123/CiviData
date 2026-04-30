from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()


class RAGService:
    """RAG Service que responde preguntas usando datos de PostgreSQL."""

    def __init__(
        self,
        db_url: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
    ):
        self.db_url = db_url or os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cividata"
        )
        self.model = model

    def get_context(
        self, question: str = "", category: str = "contratacion", limit: int = 50
    ) -> str:
        """Obtiene contexto desde PostgreSQL."""
        engine = create_engine(self.db_url)

        # Siempre usar la tabla completa de contratos
        table = "contratos_universales"
        schema = "clean"

        # Detectar departamentos en la pregunta
        departamentos = [
            "amazonas",
            "antioquia",
            "arauca",
            "atlantico",
            "bogota",
            "bogotá",
            "bolivar",
            "boyaca",
            "caldas",
            "caqueta",
            "casanare",
            "cauca",
            "cesar",
            "choco",
            "cordoba",
            "cundinamarca",
            "guainia",
            "guaviare",
            "huila",
            "la guajira",
            "magdalena",
            "meta",
            "nariño",
            "norte de santander",
            "putumayo",
            "quindio",
            "risaralda",
            "santander",
            "sucre",
            "tolima",
            "valle",
            "vaupes",
            "vichada",
        ]

        pregunta_lower = question.lower()
        filtros = []
        for depto in departamentos:
            if depto in pregunta_lower:
                filtros.append(f"departamento ILIKE '%{depto}%'")

        if filtros and schema == "marts":
            where_clause = " OR ".join(filtros)
            query = (
                f"SELECT * FROM {schema}.{table} WHERE ({where_clause}) LIMIT {limit}"
            )
        elif filtros and schema == "clean":
            where_clause = " OR ".join(filtros)
            query = (
                f"SELECT * FROM {schema}.{table} WHERE ({where_clause}) LIMIT {limit}"
            )
        else:
            query = f"SELECT * FROM {schema}.{table} LIMIT {limit}"

        with engine.connect() as conn:
            import pandas as pd
            from sqlalchemy import text

            result = conn.execute(text(query))
            columns = list(result.keys())
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=columns)

        if df.empty:
            # Si no hay datos con filtro, intentar sin filtro
            query = f"SELECT * FROM {schema}.{table} LIMIT {limit}"
            with engine.connect() as conn:
                import pandas as pd
                from sqlalchemy import text

                result = conn.execute(text(query))
                columns = list(result.keys())
                rows = result.fetchall()
                df = pd.DataFrame(rows, columns=columns)

        if df.empty:
            return "No hay datos disponibles."

        context_parts = []
        for _, row in df.head(30).iterrows():
            row_text = " | ".join([f"{k}: {v}" for k, v in row.items() if pd.notna(v)])
            context_parts.append(row_text)

        return "\n".join(context_parts)

    def build_prompt(self, question: str, context: str) -> str:
        """Construye el prompt con contexto."""
        return f"""Eres un asistente de análisis de datos de contratación pública de Colombia.

Tienes acceso a datos de la base de datos de contratos públicos (SECOP) y educación.
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

    def query(self, question: str, category: str = "contratos") -> Dict[str, Any]:
        """Ejecuta una query y retorna la respuesta."""
        from src.rag.llm import OpenRouterLLM

        context = self.get_context(question=question, category=category)
        prompt = self.build_prompt(question, context)

        llm = OpenRouterLLM(model=self.model)
        answer = llm.invoke(prompt)

        return {
            "answer": answer,
            "sources": [
                "clean.contratos_universales (133,371 contratos SECOP I, II e Integrado)"
            ],
            "metadata": {
                "model": self.model,
                "category": "contratos",
            },
        }
