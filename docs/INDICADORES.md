# Indicadores CiviData - Documentación

## Estado de Datos

| Dataset | Estado | Registros |
|---------|--------|----------|
| SECOP II | ✅ Completo | 48,311 en marts |
| SECOP Integrado | ✅ Completo | Consolidado en marts |
| SECOP I | ✅ Completo | Consolidado en marts |
| SECOP II 2025 | ✅ Completo | Consolidado en marts |
| Educación | ⚠️ Incompleto | 14 (prueba) |
| Catálogo CKAN | ❌ No disponible | API 404 |

---

## Fuentes de Datos

| Dataset | Tabla Raw | Tabla Marts | Registros |
|---------|----------|-------------|----------|
| SECOP II | clean.secop_ii_20260423_clean | marts.contratacion | 48,311 |
| SECOP Integrado | clean.secop_integrado_20260423_clean | (consolidado) | - |
| SECOP I | clean.secop_i_20260423_clean | (consolidado) | - |
| SECOP II 2025 | clean.secop_ii_2025_20260423_clean | (consolidado) | - |
| Educación | clean.datos_educacion_20260423_clean | - | 14 |

---

## Indicadores E-02 a E-09

### E-02 · Exploración de dataset: distribución de valores, fechas y tipos
**Fuente**: `marts.contratacion`
**Estado**: ✅ Implementado
**Fórmula**:
```sql
SELECT 
    MIN(valor_contrato), MAX(valor_contrato), AVG(valor_contrato),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_contrato),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_contrato)
FROM marts.contratacion;
```
**Limitaciones**: No incluye contratos sin valor reportado.

---

### E-03 · Valor total contratado por departamento 2024–2025
**Fuente**: `marts.resumen_departamento`
**Estado**: ✅ Implementado
**Fórmula**:
```sql
SELECT 
    depto,
    num_contratos,
    valor_total,
    valor_promedio,
    num_entidades
FROM marts.resumen_departamento
ORDER BY valor_total DESC;
```
**Limitaciones**: Algunos registros sin departamento definido.

---

### E-04 · Top 10 entidades por volumen de contratos
**Fuente**: `marts.resumen_entidad`
**Estado**: ✅ Implementado
**Fórmula**:
```sql
SELECT * FROM marts.resumen_entidad LIMIT 10;
```
**Limitaciones**: Consolidado solo de SECOP II.

---

### E-05 · Distribución de contratos por sector
**Fuente**: `marts.resumen_sector`
**Estado**: ✅ Implementado
**Fórmula**:
```sql
SELECT * FROM marts.resumen_sector ORDER BY valor_total DESC;
```
**Limitaciones**: Algunos contratos sin sector asignado.

---

### E-06 · Contratos por tipo de proceso
**Fuente**: `marts.resumen_tipo_proceso`
**Estado**: ✅ Implementado
**Fórmula**:
```sql
SELECT * FROM marts.resumen_tipo_proceso ORDER BY valor_total DESC;
```
**Limitaciones**: Categorización depende del catálogo SECOP.

---

### E-07 · Metadatos CKAN y cobertura por entidad
**Fuente**: API CKAN
**Estado**: ❌ No disponible - API datos.gov.co devuelve 404
**Alternativa**: Usar SECOP como proxy de actividad institucional.

---

### E-08 · Exportar tablas de indicadores para dashboard
**Fuente**: Esquema `marts`
**Estado**: ✅ Implementado
**Tablas disponibles**:
- `marts.contratacion` - Tabla maestra (48,311)
- `marts.resumen_departamento` - Por departamento (34)
- `marts.resumen_entidad` - Top 100 entidades (100)
- `marts.resumen_sector` - Por sector (25)
- `marts.resumen_tipo_proceso` - Por proceso

**Exportar a CSV**:
```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d cividata \
  -c "\COPY marts.resumen_departamento TO STDOUT CSV HEADER" > deptos.csv
```

---

### E-09 · Documentar cada indicador
**Estado**: ✅ Implementado - Este archivo

---

## Consultas de Detección de Anomalías

### Contratos con un solo proponente (competencia)
```sql
SELECT 
    nombre_entidad,
    proveedor,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total
FROM marts.contratacion
GROUP BY nombre_entidad, proveedor
HAVING COUNT(*) > 5
ORDER BY valor_total DESC;
```

### Valores atípicos (IQR method)
```sql
WITH percentiles AS (
    SELECT 
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_contrato) AS p25,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_contrato) AS p75
    FROM marts.contratacion
),
iqr_calc AS (
    SELECT p25, p75, (p75 - p25) * 1.5 AS iqr
    FROM percentiles
)
SELECT 
    id_contrato,
    nombre_entidad,
    valor_contrato,
    fecha_inicio
FROM marts.contratacion, iqr_calc
WHERE valor_contrato < (p25 - iqr) 
   OR valor_contrato > (p75 + iqr)
ORDER BY valor_contrato DESC
LIMIT 50;
```

---

## Validaciones (S-09)

```sql
-- Nulos en columnas críticas
SELECT 'valor_contrato nulos' AS validacion, COUNT(*) AS conteo 
FROM marts.contratacion WHERE valor_contrato IS NULL OR valor_contrato = 0;

-- Duplicados
SELECT 'id_contrato duplicados' AS validacion, COUNT(*) AS conteo FROM (
    SELECT id_contrato FROM marts.contratacion GROUP BY id_contrato HAVING COUNT(*) > 1
) dup;

-- Rangos de fechas
SELECT MIN(fecha_inicio), MAX(fecha_inicio) FROM marts.contratacion;

-- Valores fuera de rango
SELECT COUNT(*) FROM marts.contratacion 
WHERE valor_contrato < 0 OR valor_contrato > 1000000000000;
```

---

## Próximos Indicadores (al obtener más datos)

### Educación
- E-E1: Tasa de deserción por universidad/departamento
- E-E2: Programas con más graduados vs matriculados
- E-E3: Correlación nivel educativo y empleo

### Catálogo
- E-C1: Datasets por entidad pública
- E-C2: Actualización de datasets por sector
- E-C3: Brecha de datos por región