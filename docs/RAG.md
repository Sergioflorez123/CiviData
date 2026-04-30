# RAG - Retrieval Augmented Generation

## Visión General

El módulo RAG de CiviData proporciona capacidades de análisis inteligente sobre los datos extraídos, utilizando LangChain para permitir consultas en lenguaje natural sobre la base de datos.

## Arquitectura

```
                    ┌─────────────────┐
                    │   Cliente       │
                    │ (Frontend/UI)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   API FastAPI   │
                    │  /api/rag/*     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐        ┌─────▼─────┐      ┌─────▼─────┐
    │  Loader │        │  Chain    │      │ Vector DB │
    │ (CSV/PG)│        │ (LangChain│      │ (Chroma)  │
    └─────────┘        └───────────┘      └───────────┘
```

## Componentes

### 1. Loader (`src/rag/loader.py`)

Carga datos desde PostgreSQL o CSV y los convierte en documentos.

```python
from src.rag.loader import DataLoader

loader = DataLoader()
docs = loader.load_from_postgres(
    table="marts.contratacion",
    schema="marts"
)

docs = loader.load_from_csv(
    filepath="datalake/export/contratacion/secop_i.csv"
)
```

### 2. Splitter (`src/rag/splitter.py`)

Divide documentos en chunks para embeddings.

```python
from src.rag.splitter import TextSplitter

splitter = TextSplitter(
    chunk_size=1000,
    chunk_overlap=100
)
chunks = splitter.split_documents(docs)
```

### 3. Vector Store (`src/rag/vector_store.py`)

Almacena embeddings para búsqueda semántica.

```python
from src.rag.vector_store import VectorStore

vs = VectorStore(provider="chroma")
vs.ingest(chunks)

results = vs.similarity_search(
    query="contratos de educación",
    k=5
)
```

### 4. Chain (`src/rag/chain.py`)

Configura la cadena RAG completa.

```python
from src.rag.chain import RAGChain

chain = RAGChain(
    llm_provider="openai",
    model="gpt-4",
    vector_store=vs
)

response = chain.invoke(
    "Cuál es el sector con más contratos en 2024?"
)
```

## API Endpoints

### Query RAG

```bash
POST /api/rag/query

{
    "question": "¿Cuántos contratos hay en educación?",
    "category": "contratacion",
    "analysis_type": "summary"
}
```

**Respuesta:**
```json
{
    "answer": "Hay 1,245 contratos en el sector educación...",
    "sources": [
        "marts.contratacion (fila 123)",
        "marts.resumen_sector (sector: Educación)"
    ],
    "metadata": {
        "tokens_used": 1500,
        "model": "gpt-4"
    }
}
```

### Ingestar Datos

```bash
POST /api/rag/ingest

{
    "category": "contratacion",
    "source": "postgresql",
    "table": "marts.contratacion"
}
```

### Estado del Sistema

```bash
GET /api/rag/status
```

**Respuesta:**
```json
{
    "status": "ready",
    "documents_ingested": 48311,
    "vector_store_size": "45MB",
    "categories": ["contratacion", "educacion"]
}
```

## Tipos de Análisis

### Summary
Resumen de datos con estadísticas básicas.

```json
{
    "question": "Resume los datos de contratos",
    "analysis_type": "summary"
}
```

### Compare
Comparación entre categorías o períodos.

```json
{
    "question": "Compara educación vs salud",
    "analysis_type": "compare"
}
```

### Trend
Análisis de tendencias temporales.

```json
{
    "question": "Cuál es la tendencia de contratos por año?",
    "analysis_type": "trend"
}
```

### Anomaly
Detección de valores atípicos.

```json
{
    "question": "Hay valores atípicos en los contratos?",
    "analysis_type": "anomaly"
}
```

### Insight
Generación automática de insights.

```json
{
    "question": "Dame insights de los datos",
    "analysis_type": "insight"
}
```

## Configuración

### Variables de Entorno

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic (alternativo)
ANTHROPIC_API_KEY=sk-...

# Vector Store
CHROMA_PERSIST_DIR=./vector_store
PINECONE_API_KEY=...

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### pyproject.toml

```toml
[project.optional-dependencies]
rag = [
    "langchain>=0.1.0",
    "langchain-openai>=0.0.2",
    "langchain-anthropic>=0.1.0",
    "chromadb>=0.4.0",
    "faiss-cpu>=1.7.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pydantic>=2.0.0",
]
```

## Uso

### Iniciar API

```bash
cd CiviData
uv pip install -e ".[rag]"
uv run python -m uvicorn src.api.main:app --reload
```

### Consultar desde Frontend

```javascript
const response = await fetch('http://localhost:8000/api/rag/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: '¿Cuántos contratos hay en Nariño?',
    category: 'contratacion'
  })
});
const data = await response.json();
console.log(data.answer);
```

### Endpoints para Frontend

#### Chat/Query

```bash
POST http://localhost:8000/api/rag/query
Content-Type: application/json

{
    "question": "¿Cuántos contratos hay en Nariño?",
    "category": "contratacion"
}
```

**Respuesta:**
```json
{
    "answer": "Hay aproximadamente X contratos en el departamento de Nariño...",
    "sources": ["marts.contratacion"],
    "metadata": {
        "model": "openai/gpt-4o",
        "category": "contratacion"
    }
}
```

#### Estado

```bash
GET http://localhost:8000/api/rag/status
```

#### Salud

```bash
GET http://localhost:8000/health
```

### Categorías disponibles

| Category | Descripción |
|----------|-------------|
| `contratacion` | Datos de contratos (48,311 registros) |
| `resumen_departamento` | Resumen por departamento (34 filas) |
| `resumen_entidad` | Resumen por entidad (100 filas) |
| `resumen_sector` | Resumen por sector (25 filas) |

### Notas

- El modelo **NO hace predicciones** - solo responde basadas en datos
- Usa `category` para filtrar qué tipo de datos buscar

## Métricas y Monitoreo

- **Latencia**: Tiempo de respuesta de queries
- **Tokens**: Uso de tokens por запрос
- **Hits**: Relevancia de retrieved documents
- **Errores**: Logging de fallos

---

## Roadmap

- [ ] Implementar loader para PostgreSQL
- [ ] Configurar Chroma como vector store
- [ ] Crear endpoints API básicos
- [ ] Integrar OpenAI GPT-4
- [ ] Añadir Anthropic Claude como alternativa
- [ ] Implementar caching de respuestas
- [ ] Dashboard de administración
- [ ] Tests de integración