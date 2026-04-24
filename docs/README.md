# CiviData - Documentación

## Índice

| Documento | Descripción |
|-----------|-------------|
| [DATABASE.md](DATABASE.md) | Esquema completo: tablas, columnas, tipos, relaciones |
| [CONTRATACION.md](CONTRATACION.md) | Consultas SQL para análisis de contratación |
| [EDUCACION.md](EDUCACION.md) | Consultas SQL para análisis de educación |
| [CATALOGO.md](CATALOGO.md) | Análisis de catálogo de datos abiertos |
| [POWERBI_GUIDE.md](POWERBI_GUIDE.md) | Guía de conexión Power BI → PostgreSQL |
| [INDICADORES.md](INDICADORES.md) | Resumen de indicadores E-02 a E-09 |

---

## Estado de Datos

### ✅ Completos
- **Contratación SECOP**: ~196k registros extraídos, 48k en marts
- **Dashboard de contratación**: Listo para implementar

### ⚠️ Datos Incompletos
- **Educación**: Solo 14 registros (dataset de prueba)
- **Catálogo CKAN**: API no disponible (404)

### 📋 Por Extraer
- Directorio establecimientos educativos (9bqa-vc8t)
- Estadísticas deserción SNIES
- GEIH DANE (mercado laboral)
- Datos SISBEN
- Datos salud

---

## Arquitectura Extensible para Frontend/Dashboard

El proyecto está diseñado para añadir nuevas categorías y dashboards con facilidad.

### Estructura de Categorías
```
PostgreSQL: cividata
├── clean                    # Datos normalizados
│   ├── contratacion         # ✅ Listo
│   ├── educacion            # ⚠️ Datos limitados
│   ├── salud                # 📋 Por crear
│   ├── catalogo             # ⚠️ API no disponible
│   └── sisben               # 📋 Por crear
│
└── marts                    # Tablas analíticas
    ��── contratacion         # ✅ Tabla maestra
    ├── resumen_departamento # ✅
    ├── resumen_entidad      # ✅
    ├── resumen_sector       # ✅
    ├── resumen_tipo_proceso # ✅
    ├── educacion_stats      # 📋 Por crear
    ├── salud_resumen        # 📋 Por crear
    └── catalogo_cobertura   # 📋 Por crear
```

### Cómo Añadir Nueva Categoría

1. **Extraer datos** → `src/extract/extract_{categoria}.py`
2. **Limpiar datos** → `src/transform/clean_{categoria}.py`
3. **Cargar a PostgreSQL** → `src/load/load_to_postgres.py`
4. **Crear marts** → `sql/migrations/003_{categoria}_mart.sql`
5. **Documentar** → `docs/{CATEGORIA}.md`
6. **Dashboard Power BI** → Nueva página/widget

### Pipeline para Nueva Categoría
```bash
# Añadir en pipeline.py
# 1. Extract
run_extract_{categoria}()

# 2. Transform  
run_clean_{categoria}()

# 3. Load
load_{categoria}_to_db()

# 4. Migrate marts
PGPASSWORD=postgres psql -h localhost -U postgres -d cividata \
  -f sql/migrations/003_{categoria}_mart.sql
```

### Power BI: Preparación para Nuevos Datos

El modelo de datos Power BI debe tener:
```
Dashboard Principal
├── Página: Contratación    # ✅ Implementada
├── Página: Educación        # 📋 Estructura lista, esperar datos
├── Página: Salud            # 📋 Estructura lista
├── Página: Catálogo         # 📋 Estructura lista
└── Página: SISBEN           # 📋 Estructura lista
```

### Tablas Base Recomendadas por Categoría

| Categoría | Tabla Hechos | Dimensiones | Indicadores Clave |
|-----------|-------------|-------------|-------------------|
| Contratación | `marts.contratacion` | depto, entidad, sector, proceso | E-02 a E-06 |
| Educación | `clean.educacion` | institucion, programa, depto | Tasa deserción, graduación |
| Salud | `clean.salud` | eps, ips, municipio | Cobertura, gasto per cápita |
| Catálogo | `clean.catalogo` | organizacion, sector | Datasets por entidad |

### Queries Preparedas para Nuevas Categorías
Ver archivos correspondientes:
- `docs/CONTRATACION.md` → 20+ queries
- `docs/EDUCACION.md` → Queries placeholder
- `docs/CATALOGO.md` → Queries cobertura

---

## Estructura del Proyecto

```
CiviData/
├── docs/                    # Documentación
│   ├── DATABASE.md         # Esquema base de datos
│   ├── CONTRATACION.md     # Análisis contratación
│   ├── EDUCACION.md       # Análisis educación
│   ├── CATALOGO.md        # Análisis catálogo
│   ├── POWERBI_GUIDE.md   # Conexión Power BI
│   └── INDICADORES.md     # Resumen indicadores
├── datalake/
│   ├── raw/                # Datos extraídos
│   ├── clean/              # Datos normalizados
│   └── marts/             # (en PostgreSQL)
├── sql/migrations/         # Scripts SQL
├── src/                    # Código ETL
├── docker-compose.yml      # PostgreSQL
└── pipeline.py             # Pipeline principal
```

---

## Inicio Rápido

### 1. Iniciar PostgreSQL
```bash
docker-compose up -d
```

### 2. Ejecutar Pipeline
```bash
uv run python pipeline.py
```

### 3. Crear marts
```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d cividata -f sql/migrations/001_create_marts.sql
PGPASSWORD=postgres psql -h localhost -U postgres -d cividata -f sql/migrations/002_resumenes.sql
```

### 4. Conectar Power BI
Ver [POWERBI_GUIDE.md](POWERBI_GUIDE.md)

---

## Datos Disponibles

| Categoría | Tablas | Registros |
|-----------|--------|----------|
| Contratación | 5 (clean) + 5 (marts) | ~196k raw / ~48k marts |
| Educación | 1 (prueba) | 14 |

---

## Consultas Principales

### Contratación
```sql
-- Resumen por departamento
SELECT * FROM marts.resumen_departamento LIMIT 10;

-- Top entidades
SELECT * FROM marts.resumen_entidad LIMIT 10;

-- Por sector
SELECT * FROM marts.resumen_sector;

-- Educación vs Salud
-- Ver CONTRATACION.md → E-05
```

### Ver todas las tablas
```sql
SELECT table_schema, table_name 
FROM information_schema.tables 
WHERE table_schema IN ('marts', 'clean')
ORDER BY table_schema, table_name;
```

---

## Conexión Base de Datos

```
Host: localhost
Port: 5432
Database: cividata
User: postgres
Password: postgres
```

### DBeaver / pgAdmin
Conectar con las credenciales anteriores.

### Power BI
Ver [POWERBI_GUIDE.md](POWERBI_GUIDE.md) sección 1-3.