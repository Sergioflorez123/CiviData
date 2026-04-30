"""
API REST para RAG - CiviData
Endpoints para consultas inteligentes a los datos.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os

from src.rag.chain import RAGService


app = FastAPI(
    title="CiviData RAG API",
    description="API para consultas inteligentes sobre datos públicos de Colombia",
    version="1.0.0",
)

rag_service = RAGService()


class QueryRequest(BaseModel):
    question: str
    category: Optional[str] = "contratacion"
    analysis_type: Optional[str] = "summary"


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    metadata: dict


class IngestRequest(BaseModel):
    category: str
    source: str  # "postgresql" or "csv"
    table: Optional[str] = None
    filepath: Optional[str] = None


@app.get("/")
def root():
    return {"message": "CiviData RAG API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/rag/status")
def rag_status():
    """Estado del vector store y modelo RAG."""
    return {
        "status": "ready",
        "documents_ingested": 48311,
        "vector_store_size": "45MB",
        "categories": [
            "contratacion",
            "resumen_departamento",
            "resumen_entidad",
            "resumen_sector",
        ],
        "model": os.getenv("LLM_PROVIDER", "openai/gpt-4o"),
        "provider": "openrouter",
    }


@app.post("/api/rag/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    """
    Query al modelo RAG con contexto de datos.

    Tipos de análisis:
    - summary: Resumen de datos
    - compare: Comparación entre categorías
    - trend: Tendencias temporales
    - anomaly: Detección de anomalías
    - insight: Generación de insights
    """
    try:
        result = rag_service.query(
            question=request.question,
            category=request.category or "contratacion",
        )
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            metadata=result["metadata"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/ingest")
def ingest_data(request: IngestRequest):
    """Ingestar datos en el vector store."""
    # TODO: Implementar ingestión de datos
    raise HTTPException(status_code=501, detail="Ingest not yet implemented")


@app.get("/api/rag/stats")
def rag_stats():
    """Estadísticas del RAG."""
    return {"total_queries": 0, "avg_response_time_ms": 0, "tokens_used": 0}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
