# Indicadores CiviData - Documentación

## Fuentes de Datos

| Dataset | Tabla Raw | Registros | Descripción |
|---------|----------|----------|-------------|
| SECOP II | clean.secop_ii_20260423_clean | 10,000 | Contratos Electrónicos 2024 |
| SECOP Integrado | clean.secop_integrado_20260423_clean | 10,000 | I + II combinados |
| SECOP I | clean.secop_i_20260423_clean | 9,693 | Procesos de compra |
| SECOP II 2025 | clean.secop_ii_2025_20260423_clean | 9,998 | Desde 2025 |

## Indicadores E-02 a E-09

### E-02 · Distribución de valores, fechas y tipos
**Fuente**: `marts.contratacion`
**Fórmula**:
```sql
-- Distribución de valores
SELECT 
    MIN(valor_contrato), MAX(valor_contrato), AVG(valor_contrato),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_contrato),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_contrato)
FROM marts.contratacion;

-- Distribución por tipo de contrato
SELECT tipo_contrato, COUNT(*), SUM(valor_contrato)
FROM marts.contratacion GROUP BY tipo_contrato;
```
**Limitaciones**: No incluye contratos sin valor reportado.

---

### E-03 · Valor total contratado por departamento 2024-2025
**Fuente**: `marts.resumen_departamento`
**Fórmula**:
```sql
SELECT 
    departamento,
    num_contratos,
    valor_total,
    valor_promedio,
    num_entidades,
    num_proveedores
FROM marts.resumen_departamento
ORDER BY valor_total DESC;
```
**Limitaciones**: Algunos registros sin departamento definido.

---

### E-04 · Top 10 entidades por volumen de contratos
**Fuente**: `marts.resumen_entidad`
**Fórmula**:
```sql
SELECT * FROM marts.resumen_entidad LIMIT 10;
```
**Limitaciones**: Consolidado solo de SECOP II.

---

### E-05 · Distribución de contratos por sector
**Fuente**: `marts.resumen_sector`
**Fórmula**:
```sql
SELECT * FROM marts.resumen_sector ORDER BY valor_total DESC;
```
**Limitaciones**: Algunos contratos sin sector asignado.

---

### E-06 · Contratos por tipo de proceso
**Fuente**: `marts.resumen_tipo_proceso`
**Fórmula**:
```sql
SELECT * FROM marts.resumen_tipo_proceso ORDER BY valor_total DESC;
```
**Limitaciones**: Categorización depende del catálogo SECOP.

---

### E-07 · Metadatos CKAN y cobertura por entidad
**Estado**: ❌ No disponible - API CKAN de datos.gov.co devuelve 404
**Alternativa**: Usar metadatos manuales del portal.

---

### E-08 · Exportar tablas de indicadores
**Fuente**: Esquema `marts`
**Tablas disponibles**:
- `marts.contratacion` - Tabla maestra
- `marts.resumen_departamento` - Por departamento
- `marts.resumen_entidad` - Top 100 entidades
- `marts.resumen_sector` - Por sector
- `marts.resumen_tipo_proceso` - Por proceso

**Exportar a CSV**:
```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d cividata \
  -c "\COPY marts.resumen_departamento TO STDOUT CSV HEADER" > indicadores_departamento.csv
```

---

### E-09 · Documentación de cada indicador
Este archivo documenta cada indicador.

## Validaciones (S-09)

```sql
-- Nulos en columnas críticas
SELECT 'valor_contrato' AS col, COUNT(*) AS nulos 
FROM marts.contratacion WHERE valor_contrato IS NULL OR valor_contrato = 0;

-- Duplicados
SELECT id_contrato, COUNT(*) FROM marts.contratacion 
GROUP BY id_contrato HAVING COUNT(*) > 1;

-- Rangos de fechas
SELECT MIN(fecha_inicio), MAX(fecha_inicio) FROM marts.contratacion;

-- Valores fuera de rango (negativos o excesivamente altos)
SELECT COUNT(*) FROM marts.contratacion WHERE valor_contrato < 0 OR valor_contrato > 1000000000000;
```