# Análisis de Educación - Consultas SQL

> ⚠️ **Estado**: Dataset incompleto - Solo 14 registros de prueba
> 
> **Necesario**: Extraer más datos de datos.gov.co antes de implementar dashboard

---

## Indicadores de Educación

---

## E-E1 · Tasa de deserción por universidad/departamento

**Estado**: Requiere dataset adicional con información de deserción.

### Fuentes necesarias:
- Datos del SNIES (Sistema Nacional de Información de Educación Superior)
- Dataset esperado: Abandonos por institución, semestre, programa

### Consulta sugerida (cuando haya datos):
```sql
SELECT 
    institucion,
    departamento,
    anno,
    semestre,
    COUNT(matricula) AS total_matriculados,
    COUNT(desertores) AS total_desertores,
    ROUND(COUNT(desertores) * 100.0 / COUNT(matricula), 2) AS tasa_desercion
FROM clean.educacion_desercion
GROUP BY institucion, departamento, anno, semestre
ORDER BY tasa_desercion DESC;
```

---

## E-E2 · Programas con más graduados vs matriculados

### Consulta sugerida:
```sql
SELECT 
    programa,
    institucion,
    COUNT(matricula) AS total_matriculados,
    COUNT(graduado) AS total_graduados,
    ROUND(COUNT(graduado) * 100.0 / NULLIF(COUNT(matricula), 0), 2) AS tasa_graduacion,
    ROUND(COUNT(matricula) * 100.0 / NULLIF(SUM(COUNT(matricula)) OVER(), 0), 2) AS porcentaje_matricula
FROM clean.educacion_programas
GROUP BY programa, institucion
ORDER BY total_graduados DESC
LIMIT 20;
```

### Programas con menor relación matriculados/graduados
```sql
SELECT 
    programa,
    institucion,
    total_matriculados,
    total_graduados,
    CASE 
        WHEN total_matriculados > 0 THEN ROUND(total_graduados * 100.0 / total_matriculados, 2)
        ELSE 0
    END AS tasa_graduacion
FROM (
    SELECT 
        programa,
        institucion,
        COUNT(CASE WHEN tipo_registro = 'MATRICULA' END) AS total_matriculados,
        COUNT(CASE WHEN tipo_registro = 'GRADUADO' END) AS total_graduados
    FROM clean.educacion_datos
    GROUP BY programa, institucion
) sub
WHERE total_graduados > 0
ORDER BY tasa_graduacion ASC
LIMIT 20;
```

---

## E-E3 · Correlación nivel educativo y empleo por región

**Estado**: Requiere dataset de mercado laboral (GEIH DANE).

### Consulta sugerida (empleo vs nivel educativo):
```sql
SELECT 
    departamento,
    nivel_educativo,
    tasa_empleo,
    tasa_desempleo,
    ingreso_promedio,
    COUNT(*) AS num_personas
FROM clean.geih_empleo
GROUP BY departamento, nivel_educativo
ORDER BY departamento, nivel_educativo;
```

### Correlación educación-ingresos
```sql
SELECT 
    departamento,
    nivel_educativo,
    AVG(ingreso) AS ingreso_promedio,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ingreso) AS ingreso_mediano,
    COUNT(*) AS muestra
FROM clean.geih_datos
WHERE ingreso > 0
GROUP BY departamento, nivel_educativo
ORDER BY departamento, nivel_educativo DESC;
```

---

## Datos Actualmente Disponibles

### Dataset: `clean.datos_educacion_20260423_clean`
```sql
SELECT * FROM clean.datos_educacion_20260423_clean LIMIT 10;
```

### Ver estructura:
```sql
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'datos_educacion_20260423_clean'
ORDER BY ordinal_position;
```

---

## Próximos Datasets a Extraer

| Dataset | Fuente | Resource ID | Descripción |
|---------|--------|-------------|-------------|
| Directorio Establecimientos | datos.gov.co | 9bqa-vc8t | Todos los colegios/universidades |
| Estadísticas Educación Superior | MEN | - | Tasas de deserción, matricula |
| GEIH Educación | DANE | - | Empleo por nivel educativo |

---

## Extracción de Nuevos Datos

```python
# En src/extract/extract_educacion.py agregar:

DATASETS = {
    "establecimientos": {
        "resource_id": "9bqa-vc8t",
        "url": "https://www.datos.gov.co/resource/9bqa-vc8t.json",
    },
}
```

---

## Consideraciones

1. **Datos limitados**: El dataset actual es de prueba
2. **Fuentes externas**: El MEN y DANE tienen datasets más completos
3. **Frecuencia**: Datos de educación se actualizan por año académico
4. **Divipola**: Usar códigos DIVIPOLA para normalizar ubicaciones