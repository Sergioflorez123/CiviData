# Análisis de Contratación Pública - Consultas SQL

> **Estado**: ✅ Dataset completo - 48,311 registros en marts

## Indicadores E-02 a E-09

---

## E-02 · Exploración de Dataset: Distribución de Valores, Fechas y Tipos

### Distribución de valores de contratos
```sql
SELECT 
    MIN(valor_contrato) AS valor_minimo,
    MAX(valor_contrato) AS valor_maximo,
    AVG(valor_contrato) AS valor_promedio,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_contrato) AS q25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY valor_contrato) AS mediana,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_contrato) AS q75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY valor_contrato) AS p95,
    STDDEV(valor_contrato) AS desviacion_estandar
FROM marts.contratacion;
```

### Distribución por tipo de contrato
```sql
SELECT 
    tipo_contrato,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS porcentaje
FROM marts.contratacion
GROUP BY tipo_contrato
ORDER BY valor_total DESC;
```

### Distribución temporal (por mes/año)
```sql
SELECT 
    EXTRACT(YEAR FROM fecha_inicio) AS anno,
    EXTRACT(MONTH FROM fecha_inicio) AS mes,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total
FROM marts.contratacion
WHERE fecha_inicio IS NOT NULL
GROUP BY EXTRACT(YEAR FROM fecha_inicio), EXTRACT(MONTH FROM fecha_inicio)
ORDER BY anno, mes;
```

### Distribución por modalidad
```sql
SELECT 
    modalidad,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio
FROM marts.contratacion
GROUP BY modalidad
ORDER BY valor_total DESC;
```

---

## E-03 · Valor Total Contratado por Departamento 2024-2025

### Tabla ya disponible: `marts.resumen_departamento`
```sql
SELECT * FROM marts.resumen_departamento ORDER BY valor_total DESC;
```

### Consulta personalizada por año
```sql
SELECT 
    COALESCE(departamento, 'Sin información') AS departamento,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio,
    EXTRACT(YEAR FROM fecha_inicio) AS anno
FROM marts.contratacion
WHERE EXTRACT(YEAR FROM fecha_inicio) IN (2024, 2025)
GROUP BY departamento, EXTRACT(YEAR FROM fecha_inicio)
ORDER BY valor_total DESC;
```

### Top 10 departamentos por valor
```sql
SELECT 
    departamento,
    num_contratos,
    valor_total,
    valor_promedio,
    num_entidades,
    num_proveedores
FROM marts.resumen_departamento
LIMIT 10;
```

### Filtrar por departamento específico (ej: Nariño)
```sql
SELECT 
    nombre_entidad,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio
FROM marts.contratacion
WHERE departamento = 'Nariño'
GROUP BY nombre_entidad
ORDER BY valor_total DESC
LIMIT 20;
```

---

## E-04 · Top 10 Entidades por Volumen de Contratos

### Tabla ya disponible: `marts.resumen_entidad`
```sql
SELECT * FROM marts.resumen_entidad LIMIT 10;
```

### Top entidades por departamento
```sql
SELECT 
    nombre_entidad,
    departamento,
    num_contratos,
    valor_total,
    valor_promedio,
    ROW_NUMBER() OVER (PARTITION BY departamento ORDER BY valor_total DESC) AS ranking
FROM marts.resumen_entidad
WHERE departamento IN ('Nariño', 'Cundinamarca', 'Antioquia')
LIMIT 30;
```

### Entidades con más contratos (no solo valor)
```sql
SELECT 
    nombre_entidad,
    departamento,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total
FROM marts.contratacion
GROUP BY nombre_entidad, departamento
ORDER BY num_contratos DESC
LIMIT 20;
```

---

## E-05 · Distribución de Contratos por Sector

### Tabla ya disponible: `marts.resumen_sector`
```sql
SELECT * FROM marts.resumen_sector ORDER BY valor_total DESC;
```

### Educación vs Salud (comparación 2025)
```sql
SELECT 
    CASE 
        WHEN sector LIKE '%Educaci%' THEN 'Educación'
        WHEN sector LIKE '%Salud%' OR sector LIKE '%Social%' THEN 'Salud'
        WHEN sector LIKE '%Transporte%' THEN 'Transporte'
        WHEN sector LIKE '%defensa%' OR sector LIKE '%seguridad%' THEN 'Defensa'
        ELSE 'Otros'
    END AS categoria,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio
FROM marts.contratacion
WHERE EXTRACT(YEAR FROM fecha_inicio) = 2025
GROUP BY 1
ORDER BY valor_total DESC;
```

### Porcentaje por sector
```sql
WITH totales AS (
    SELECT SUM(valor_contrato) AS total_general
    FROM marts.contratacion
)
SELECT 
    COALESCE(sector, 'Sin información') AS sector,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    ROUND(SUM(valor_contrato) * 100.0 / t.total_general, 2) AS porcentaje
FROM marts.contratacion
CROSS JOIN totales t
GROUP BY sector, t.total_general
ORDER BY valor_total DESC;
```

---

## E-06 · Contratos por Tipo de Proceso

### Tabla ya disponible: `marts.resumen_tipo_proceso`
```sql
SELECT * FROM marts.resumen_tipo_proceso ORDER BY valor_total DESC;
```

### Top tipos de proceso
```sql
SELECT 
    proceso,
    num_contratos,
    valor_total,
    ROUND(valor_total / num_contratos, 0) AS valor_promedio_contrato
FROM marts.resumen_tipo_proceso
ORDER BY num_contratos DESC
LIMIT 15;
```

### Procesos más frecuentes
```sql
SELECT 
    proceso_de_compra,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio
FROM marts.contratacion
GROUP BY proceso_de_compra
ORDER BY num_contratos DESC
LIMIT 10;
```

---

## Preguntas Específicas Adicionales

### P1 · ¿Qué entidad contrató más en mi departamento el último año?
```sql
-- Reemplazar 'Nariño' por el departamento deseado
SELECT 
    nombre_entidad,
    departamento,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    MAX(fecha_inicio) AS ultimo_contrato
FROM marts.contratacion
WHERE departamento = 'Nariño'
  AND fecha_inicio >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY nombre_entidad, departamento
ORDER BY valor_total DESC
LIMIT 10;
```

### P2 · ¿Cuánto va en contratos de educación vs salud en 2025?
```sql
SELECT 
    CASE 
        WHEN LOWER(sector) LIKE '%educaci%' THEN 'Educación'
        WHEN LOWER(sector) LIKE '%salud%' OR LOWER(sector) LIKE '%social%' THEN 'Salud'
        ELSE 'Otros'
    END AS sector,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    SUM(valor_pagado) AS valor_pagado,
    SUM(valor_contrato) - SUM(valor_pagado) AS valor_pendiente
FROM marts.contratacion
WHERE EXTRACT(YEAR FROM fecha_inicio) = 2025
  AND (LOWER(sector) LIKE '%educaci%' OR LOWER(sector) LIKE '%salud%' OR LOWER(sector) LIKE '%social%')
GROUP BY 1
ORDER BY valor_total DESC;
```

### P3 · ¿Qué proveedores reciben más contratos del Estado en mi región?
```sql
-- Reemplazar 'Nariño' por el departamento deseado
SELECT 
    proveedor,
    COUNT(*) AS num_contratos,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio,
    COUNT(DISTINCT nombre_entidad) AS num_entidades_contratantes
FROM marts.contratacion
WHERE departamento = 'Nariño'
  AND proveedor IS NOT NULL
  AND proveedor != ''
GROUP BY proveedor
ORDER BY valor_total DESC
LIMIT 20;
```

---

## Detección de Anomalías

### A1 · Contratos con un solo proponente (posible falta de competencia)
```sql
-- Requiere columna 'numero_proponentes' o similar
-- Si no existe, usar como proxy: contratos con el mismo proveedor en同一个 proceso
SELECT 
    nombre_entidad,
    proveedor,
    COUNT(*) AS num_contratos_similar,
    SUM(valor_contrato) AS valor_total,
    AVG(valor_contrato) AS valor_promedio
FROM marts.contratacion
WHERE proceso_de_compra = 'Selección Abreviada'
GROUP BY nombre_entidad, proveedor
HAVING COUNT(*) > 5
ORDER BY valor_total DESC;
```

### A2 · Valores atípicos (fuera de percentiles)
```sql
WITH percentiles AS (
    SELECT 
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_contrato) AS p25,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_contrato) AS p75
    FROM marts.contratacion
),
iqr_calc AS (
    SELECT p25, p75, (p75 - p25) * 1.5 AS iqr_mult
    FROM percentiles
)
SELECT 
    id_contrato,
    nombre_entidad,
    proveedor,
    valor_contrato,
    fecha_inicio,
    departamento
FROM marts.contratacion, iqr_calc
WHERE valor_contrato < (p25 - iqr_mult) 
   OR valor_contrato > (p75 + iqr_mult)
ORDER BY valor_contrato DESC
LIMIT 50;
```

### A3 · Contratos con valores significativamente mayores al promedio del sector
```sql
SELECT 
    c.id_contrato,
    c.nombre_entidad,
    c.sector,
    c.valor_contrato,
    c.proveedor,
    r.valor_promedio AS promedio_sector,
    c.valor_contrato / r.valor_promedio AS ratio_vs_promedio
FROM marts.contratacion c
JOIN marts.resumen_sector r ON c.sector = r.sector
WHERE c.valor_contrato > r.valor_promedio * 10
ORDER BY ratio_vs_promedio DESC
LIMIT 30;
```

---

## Limitaciones y Consideraciones

1. **Valores negativos o cero**: Los contratos con valor 0 o negativo fueron filtrados en la limpieza
2. **Departamentos sin información**: Registrados como "No Definido" o "Sin info"
3. **Sectores NULL**: Algunos contratos no tienen sector asignado
4. **Fechas inválidas**: Registros con fechas inconsistentes fueron excluidos
5. **Proveedores duplicados**: Mismo proveedor con nombres diferentes (ej: "S.A.S" vs "SAS")