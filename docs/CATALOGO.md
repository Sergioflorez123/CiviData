# Análisis de Catálogo de Datos Abiertos - Colombia

> ⚠️ **Estado**: API CKAN no disponible (404) - Datos simulados desde SECOP
> 
> **Necesario**: Extraer metadatos manualmente o esperar que la API se restore

## E-07 · Metadatos CKAN y Cobertura por Entidad

**Estado**: La API CKAN de datos.gov.co devuelve 404.

---

## Fuentes de Metadatos

### API Socrata (funciona)
```python
# Listar datasets disponibles en un recurso
url = "https://www.datos.gov.co/api/3/action/package_list"
```

### Endpoints probados:
| Endpoint | Estado | Notas |
|----------|--------|-------|
| `/api/3/action/package_list` | ❌ 404 | No disponible |
| `/api/3/action/organization_list` | ❌ 404 | No disponible |
| `/api/3/action/package_search` | ❌ 404 | No disponible |

---

## Alternativas para Obtener Metadatos

### 1. Extraer manualmente desde el portal
- Visitar datos.gov.co
- Buscar por organización/entidad
- Documentar manualmente

### 2. Usar datos del dataset SECOP
```sql
-- Analizar qué entidades publican más en SECOP
SELECT 
    nombre_entidad,
    COUNT(*) AS num_contratos,
    COUNT(DISTINCT proceso_de_compra) AS num_tipos_proceso,
    MIN(fecha_inicio) AS primera_publicacion,
    MAX(fecha_inicio) AS ultima_publicacion
FROM marts.contratacion
GROUP BY nombre_entidad
ORDER BY num_contratos DESC
LIMIT 50;
```

### 3. Crear tabla de cobertura desde SECOP
```sql
-- Simular catálogo basado en SECOP
SELECT 
    nombre_entidad AS organizacion,
    departamento AS region,
    COUNT(*) AS num_datasets_simulado,
    COUNT(DISTINCT proceso_de_compra) AS num_tipos_datos,
    SUM(valor_contrato) AS tamano_simulado
FROM marts.contratacion
GROUP BY nombre_entidad, departamento
ORDER BY num_datasets_simulado DESC;
```

---

## Consultas de Análisis de Cobertura

### P-C1 · ¿Qué sectores tienen más datos publicados en Colombia?

Basado en SECOP (proxy de actividad de datos abiertos):
```sql
SELECT 
    sector,
    COUNT(*) AS num_registros,
    COUNT(DISTINCT nombre_entidad) AS num_entidades,
    SUM(valor_contrato) AS valor_total
FROM marts.contratacion
GROUP BY sector
ORDER BY num_entidades DESC;
```

### P-C2 · ¿Qu�� tan actualizados están los datasets por entidad?

```sql
SELECT 
    nombre_entidad,
    departamento,
    COUNT(*) AS num_contratos,
    MIN(fecha_inicio) AS desde,
    MAX(fecha_inicio) AS hasta,
    MAX(fecha_inicio) - MIN(fecha_inicio) AS rango_dias,
    CASE 
        WHEN MAX(fecha_inicio) >= CURRENT_DATE - INTERVAL '30 days' THEN 'Actualizado'
        WHEN MAX(fecha_inicio) >= CURRENT_DATE - INTERVAL '90 days' THEN 'Reciente'
        WHEN MAX(fecha_inicio) >= CURRENT_DATE - INTERVAL '365 days' THEN 'Anual'
        ELSE 'Desactualizado'
    END AS estado_actualizacion
FROM marts.contratacion
WHERE fecha_inicio IS NOT NULL
GROUP BY nombre_entidad, departamento
ORDER BY num_contratos DESC
LIMIT 20;
```

### P-C3 · ¿Qué regiones tienen menos datos disponibles?

```sql
-- Departamentos con menos actividad en SECOP
SELECT 
    COALESCE(departamento, 'Sin información') AS region,
    COUNT(*) AS num_contratos,
    COUNT(DISTINCT nombre_entidad) AS num_entidades,
    SUM(valor_contrato) AS valor_total,
    ROW_NUMBER() OVER (ORDER BY COUNT(*)) AS ranking_disponibilidad
FROM marts.contratacion
GROUP BY departamento
ORDER BY COUNT(*) ASC
LIMIT 10;
```

### Brecha de datos abiertos (por investigar)
```sql
-- Entidades que deberían publicar pero no tienen datos
SELECT 
    'Posible brecha' AS nota,
    departamento,
    COUNT(*) AS num_contratos,
    CASE 
        WHEN COUNT(*) < 100 THEN 'Baja cobertura'
        WHEN COUNT(*) < 500 THEN 'Cobertura media'
        ELSE 'Buena cobertura'
    END AS clasificacion
FROM marts.contratacion
GROUP BY departamento
ORDER BY COUNT(*) ASC;
```

---

## Estructura Ideal del Catálogo (para futura implementación)

### Tabla propuesta: `raw.catalogo_datasets`
```sql
CREATE TABLE raw.catalogo_datasets (
    id VARCHAR(100),
    title VARCHAR(500),
    organization VARCHAR(200),
    num_resources INTEGER,
    tags TEXT[],
    created_at DATE,
    last_modified_at DATE,
    url VARCHAR(500),
    format VARCHAR(50),
    frecuencia_actualizacion VARCHAR(50),
    owner_org VARCHAR(100)
);
```

### Tabla propuesta: `marts.resumen_catalogo`
```sql
CREATE TABLE marts.resumen_catalogo AS
SELECT 
    organization,
    COUNT(*) AS num_datasets,
    COUNT(DISTINCT tags) AS num_tags,
    MIN(created_at) AS primer_dataset,
    MAX(last_modified_at) AS ultimo_update,
    COUNT(CASE WHEN last_modified_at >= CURRENT_DATE - INTERVAL '30 days' END) AS datasets_activos
FROM raw.catalogo_datasets
GROUP BY organization;
```

---

## Cómo Extraer Catálogo Manualmente

### Paso 1: Buscar recursos en datos.gov.co
```python
import requests

# Buscar por categoría
categorias = ['educacion', 'salud', 'transporte', 'ambiente', 'seguridad']

for cat in categorias:
    url = f"https://www.datos.gov.co/resource/9bqa-vc8t.json"  # Ejemplo
    # Implementar búsqueda por cada categoría
```

### Paso 2: Documentar en CSV
```csv
organizacion,cantidad_datasets,ultima_actualizacion,sector
Alcaldía de Pasto,25,2024-03-15,Educación
Gobernación de Nariño,18,2024-02-20,Salud
...
```

### Paso 3: Cargar a PostgreSQL
```python
# En src/load/load_to_postgres.py
def load_catalogo():
    df = pd.read_csv('catalogo_organizaciones.csv')
    df.to_sql('catalogo_organizaciones', engine, schema='raw')
```

---

## Limitaciones

1. **API CKAN caída**: No se pueden obtener metadatos automáticos
2. **SECOP como proxy**: Usamos SECOP como indicador de publicación de datos
3. **Catálogo manual**: Requiere investigación manual para completar
4. **Frecuencia desconocida**: No sabemos cuándo se actualizan los datasets