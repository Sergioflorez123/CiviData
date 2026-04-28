# Análisis de Educación - Consultas SQL

> **Estado**: Extracción configurada - Pendiente ejecutar pipeline

## Fuentes de Datos

| Dataset | Fuente | URL | Método |
|---------|--------|-----|--------|
| Directorio Establecimientos | MEN/datos.gov.co | datos.gov.co/resource/9bqa-vc8t.json | Socrata SODA API |
| Matrícula Preescolar | MEN/datos.gov.co | datos.gov.co/resource/yq23-98uj.json | Socrata SODA API |
| Matrícula Primaria | MEN/datos.gov.co | datos.gov.co/resource/43rp-p3xh.json | Socrata SODA API |
| Matrícula Secundaria | MEN/datos.gov.co | datos.gov.co/resource/53kw-8w94.json | Socrata SODA API |
| Tasa Deserción | MEN/datos.gov.co | datos.gov.co/resource/46xr-3wpi.json | Socrata SODA API |
| Graduados Superior | MEN/datos.gov.co | datos.gov.co/resource/4p5n-8qix.json | Socrata SODA API |
| Saber 11 Resultados | MEN/datos.gov.co | datos.gov.co/resource/pjs3-8v9p.json | Socrata SODA API |
| GEIH 2024 Mercado Laboral | DANE/microdatos | microdatos.dane.gov.co | Descarga CSV |
| Educación Formal | DANE | dane.gov.co/estadisticas/educacion | CSV + Excel |

---

## Indicadores de Educación

---

## E-E1 · Tasa de deserción por departamento

**Fuente**: MEN - datasets de deserción (46xr-3wpi)

### Consulta sugerida:
```sql
SELECT 
    departamento,
    anno,
    nivel,
    SUM(matricula) AS total_matriculados,
    SUM(desertores) AS total_desertores,
    ROUND(SUM(desertores) * 100.0 / NULLIF(SUM(matricula), 0), 2) AS tasa_desercion
FROM clean.men_tasa_desercion
GROUP BY departamento, anno, nivel
ORDER BY tasa_desercion DESC;
```

---

## E-E2 · Matrícula por nivel educativo y departamento

### Consulta sugerida:
```sql
SELECT 
    departamento,
    nivel_educativo,
    SUM(cantidad) AS total_matricula,
    COUNT(DISTINCT institucion) AS num_instituciones
FROM clean.men_matricula_preescolar
GROUP BY departamento, nivel_educativo
UNION ALL
SELECT 
    departamento,
    nivel_educativo,
    SUM(cantidad) AS total_matricula,
    COUNT(DISTINCT institucion) AS num_instituciones
FROM clean.men_matricula_primaria
-- ... otros niveles
ORDER BY total_matricula DESC;
```

### Matrícula por año
```sql
SELECT 
    anno,
    nivel_educativo,
    SUM(cantidad) AS total_matricula
FROM clean.men_matricula_preescolar
GROUP BY anno, nivel_educativo
ORDER BY anno, nivel_educativo;
```

---

## E-E3 · Correlación nivel educativo y empleo (GEIH DANE)

**Fuente**: DANE - GEIH 2024

### Consulta sugerida (empleo vs nivel educativo):
```sql
SELECT 
    departamento,
    nivel_educativo,
    COUNT(*) AS muestra,
    SUM(CASE WHEN ocupada = 1 THEN 1 END) AS ocupadas,
    SUM(CASE WHEN desempleo = 1 THEN 1 END) AS_desempleadas,
    ROUND(SUM(CASE WHEN desempleo = 1 THEN 1 END) * 100.0 / COUNT(*), 2) AS tasa_desempleo
FROM clean.dane_geih_empleo
GROUP BY departamento, nivel_educativo
ORDER BY tasa_desempleo DESC;
```

### Correlación educación-ingresos
```sql
SELECT 
    departamento,
    nivel_educativo,
    AVG(ingreso) AS ingreso_promedio,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ingreso) AS ingreso_mediano,
    COUNT(*) AS muestra
FROM clean.dane_geih_empleo
WHERE ingreso > 0
GROUP BY departamento, nivel_educativo
ORDER BY departamento, nivel_educativo DESC;
```

---

## E-E4 · Establecimientos educativos por departamento

**Fuente**: Directorio establecimientos MEN

### Consulta sugerida:
```sql
SELECT 
    departamento,
    tipo_establecimiento,
    COUNT(*) AS num_establecimientos,
    COUNT(DISTINCT municipio) AS num_municipios
FROM clean.men_establecimientos
GROUP BY departamento, tipo_establecimiento
ORDER BY num_establecimientos DESC;
```

---

## E-E5 · Resultados Saber 11 por departamento

**Fuente**: MEN - Resultados ICFES Saber 11

### Consulta sugerida:
```sql
SELECT 
    departamento,
    anno,
    AVG(puntaje_global) AS promedio_puntaje,
    MIN(puntaje_global) AS puntaje_min,
    MAX(puntaje_global) AS puntaje_max,
    COUNT(*) AS num_estudiantes
FROM clean.men_saber11_resultados
GROUP BY departamento, anno
ORDER BY promedio_puntaje DESC;
```

---

## Tablas Disponibles Después de Extracción

### Esquema clean:
```sql
-- Lista de tablas de educación
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'clean' 
  AND table_name LIKE '%educacion%' 
  OR table_name LIKE '%men_%' 
  OR table_name LIKE '%dane_%';
```

### Tablas esperadas:
- `clean.men_establecimientos` - Directorio de colegios/universidades
- `clean.men_matricula_preescolar` - Matrícula preescolar
- `clean.men_matricula_primaria` - Matrícula primaria
- `clean.men_matricula_secundaria` - Matrícula secundaria
- `clean.men_tasa_desercion` - Tasas de deserción
- `clean.men_graduados_superior` - Graduadosuniversitarios
- `clean.men_saber11_resultados` - Resultados ICFES
- `clean.dane_geih_empleo` - GEIH mercado laboral
- `clean.dane_educacion_formal` - Estadísticas educación DANE

---

## Extracción de Datos

### Ejecutar pipeline:
```bash
cd CiviData
uv run python pipeline.py --phase extract
```

### Estructura de archivos:
```
datalake/
├── raw/educacion/          # Datos crudos descargados
├── clean/educacion/        # Datos normalizados
└── export/educacion/       # CSV listo para uso externo
```

### Ver archivos:
```bash
ls -la datalake/export/educacion/
```

---

## Consideraciones

1. **Frecuencia**: Datos de educación se actualizan por año académico
2. **Divipola**: Usar códigos DIVIPOLA para normalizar ubicaciones
3. **GEIH**: Gran Encuesta Integrada de Hogares - datos de mercado laboral
4. **SNIES**: Sistema Nacional de Información de Educación Superior