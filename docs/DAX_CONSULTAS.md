# Consultas DAX para Power BI - Contratación SECOP

## Estructura del Dataset

**Fuente**: `datalake/export/consolidated/secop_consolidado_latest.csv`

**Registros**: ~133,371

**Columnas disponibles**:
```
uid, nombre_entidad, nit_entidad, departamento, modalidad, 
tipo_contrato, valor_contrato, fecha_firma, proveedor, origen
```

---

## 1. KPIs Globales (Tarjetas)

### Total Contratos
```dax
Total Contratos = COUNTROWS('SECOP Consolidado')
```

### Valor Total Contratado
```dax
Valor Total = SUM('SECOP Consolidado'[valor_contrato])
```

### Valor Promedio por Contrato
```dax
Valor Promedio = AVERAGE('SECOP Consolidado'[valor_contrato])
```

### Número de Entidades
```dax
Num Entidades = DISTINCTCOUNT('SECOP Consolidado'[nombre_entidad])
```

### Número de Departamentos
```dax
Num Departamentos = DISTINCTCOUNT('SECOP Consolidado'[departamento])
```

### Número de Proveedores
```dax
Num Proveedores = DISTINCTCOUNT('SECOP Consolidado'[proveedor])
```

---

## 2. Dashboard: E-02a - Distribución por Valor

### Medida: Rango de Valor
```dax
Rango Valor = SWITCH(
    TRUE(),
    'SECOP Consolidado'[valor_contrato] < 1000000, "Menor a 1M",
    'SECOP Consolidado'[valor_contrato] < 5000000, "1M - 5M",
    'SECOP Consolidado'[valor_contrato] < 10000000, "5M - 10M",
    'SECOP Consolidado'[valor_contrato] < 50000000, "10M - 50M",
    'SECOP Consolidado'[valor_contrato] < 100000000, "50M - 100M",
    'SECOP Consolidado'[valor_contrato] < 500000000, "100M - 500M",
    'SECOP Consolidado'[valor_contrato] < 1000000000, "500M - 1B",
    "Mayor a 1B"
)
```

### Tabla: Contratos por Rango
```dax
Contratos por Rango = SUMMARIZE(
    'SECOP Consolidado',
    'SECOP Consolidado'[Rango Valor],
    "Num Contratos", COUNTROWS('SECOP Consolidado'),
    "Valor Total", SUM('SECOP Consolidado'[valor_contrato])
)
```

---

## 3. Dashboard: E-02b - Por Tipo de Contrato

### Tabla: Resumen Tipo Contrato
```dax
Resumen Tipo Contrato = SUMMARIZE(
    'SECOP Consolidado',
    'SECOP Consolidado'[tipo_contrato],
    "Num Contratos", COUNTROWS('SECOP Consolidado'),
    "Valor Total", SUM('SECOP Consolidado'[valor_contrato]),
    "Valor Promedio", AVERAGE('SECOP Consolidado'[valor_contrato]),
    "% Total", DIVIDE(SUM('SECOP Consolidado'[valor_contrato]), CALCULATE(SUM('SECOP Consolidado'[valor_contrato]), ALL('SECOP Consolidado')))
)
```

### Top 10 Tipos por Valor
```dax
Top Tipos por Valor = TOPN(10, 'Resumen Tipo Contrato', [Valor Total], DESC)
```

---

## 4. Dashboard: E-02c - Por Modalidad

### Tabla: Resumen Modalidad
```dax
Resumen Modalidad = SUMMARIZE(
    'SECOP Consolidado',
    'SECOP Consolidado'[modalidad],
    "Num Contratos", COUNTROWS('SECOP Consolidado'),
    "Valor Total", SUM('SECOP Consolidado'[valor_contrato]),
    "% Contratos", DIVIDE(COUNTROWS('SECOP Consolidado'), CALCULATE(COUNTROWS('SECOP Consolidado'), ALL('SECOP Consolidado')))
)
```

---

## 5. Dashboard: E-03 - Por Departamento

### Tabla: Resumen Departamento
```dax
Resumen Departamento = SUMMARIZE(
    'SECOP Consolidado',
    'SECOP Consolidado'[departamento],
    "Num Contratos", COUNTROWS('SECOP Consolidado'),
    "Valor Total", SUM('SECOP Consolidado'[valor_contrato]),
    "Valor Promedio", AVERAGE('SECOP Consolidado'[valor_contrato]),
    "Num Entidades", DISTINCTCOUNT('SECOP Consolidado'[nombre_entidad]),
    "Num Proveedores", DISTINCTCOUNT('SECOP Consolidado'[proveedor])
)
```

### Top 10 Departamentos
```dax
Top 10 Deptos = TOPN(10, 'Resumen Departamento', [Valor Total], DESC)
```

### Porcentaje del Total
```dax
% Valor Deptos = DIVIDE([Valor Total], CALCULATE(SUM('SECOP Consolidado'[valor_contrato]), ALL('SECOP Consolidado')))
```

---

## 6. Dashboard: E-04 - Top Entidades

### Tabla: Resumen Entidad
```dax
Resumen Entidad = SUMMARIZE(
    'SECOP Consolidado',
    'SECOP Consolidado'[nombre_entidad],
    'SECOP Consolidado'[departamento],
    'SECOP Consolidado'[nit_entidad],
    "Num Contratos", COUNTROWS('SECOP Consolidado'),
    "Valor Total", SUM('SECOP Consolidado'[valor_contrato]),
    "Valor Promedio", AVERAGE('SECOP Consolidado'[valor_contrato]),
    "Num Proveedores", DISTINCTCOUNT('SECOP Consolidado'[proveedor])
)
```

### Top 20 Entidades
```dax
Top 20 Entidades = TOPN(20, 'Resumen Entidad', [Valor Total], DESC)
```

### Ranking por Departamento
```dax
Rank Depto = RANKX(
    FILTER('Resumen Entidad', 'Resumen Entidad'[departamento] = EARLIER('Resumen Entidad'[departamento])),
    [Valor Total], , DESC
)
```

---

## 7. Dashboard: P2 - Educación vs Salud (Comparativa)

### Medida: Categoría
```dax
Categoria = IF(
    CONTAINSSTRING('SECOP Consolidado'[tipo_contrato], "Salud") || CONTAINSSTRING('SECOP Consolidado'[tipo_contrato], "Hospital") || CONTAINSSTRING('SECOP Consolidado'[nombre_entidad], "Salud") || CONTAINSSTRING('SECOP Consolidado'[nombre_entidad], "Hospital"),
    "Salud",
    IF(
        CONTAINSSTRING('SECOP Consolidado'[tipo_contrato], "Educacion") || CONTAINSSTRING('SECOP Consolidado'[tipo_contrato], "Educación") || CONTAINSSTRING('SECOP Consolidado'[nombre_entidad], "Educacion") || CONTAINSSTRING('SECOP Consolidado'[nombre_entidad], "Universidad") || CONTAINSSTRING('SECOP Consolidado'[nombre_entidad], "Colegio"),
        "Educación",
        "Otros"
    )
)
```

### Tabla: Comparativa
```dax
Comparativa Sectores = SUMMARIZE(
    'SECOP Consolidado',
    'SECOP Consolidado'[Categoria],
    "Num Contratos", COUNTROWS('SECOP Consolidado'),
    "Valor Total", SUM('SECOP Consolidado'[valor_contrato]),
    "% Total", DIVIDE(SUM('SECOP Consolidado'[valor_contrato]), CALCULATE(SUM('SECOP Consolidado'[valor_contrato]), ALL('SECOP Consolidado')))
)
```

---

## 8. Dashboard: P3 - Top Proveedores

### Tabla: Resumen Proveedor
```dax
Resumen Proveedor = SUMMARIZE(
    'SECOP Consolidado',
    'SECOP Consolidado'[proveedor],
    "Num Contratos", COUNTROWS('SECOP Consolidado'),
    "Valor Total", SUM('SECOP Consolidado'[valor_contrato]),
    "Valor Promedio", AVERAGE('SECOP Consolidado'[valor_contrato]),
    "Num Entidades", DISTINCTCOUNT('SECOP Consolidado'[nombre_entidad])
)
```

### Top 20 Proveedores
```dax
Top 20 Proveedores = TOPN(20, 'Resumen Proveedor', [Valor Total], DESC)
```

### Excluir "No Definido"
```dax
Top Proveedores Validos = FILTER('Top 20 Proveedores', 'Top 20 Proveedores'[proveedor] <> "No Definido")
```

---

## 9. Dashboard: P1 - Entidades por Departamento

### Medida: Entidades en Depto Seleccionado
```dax
Entidades en Depto Seleccionado = 
VAR DeptoSeleccionado = SELECTEDVALUE('SECOP Consolidado'[departamento])
RETURN
CALCULATE(
    DISTINCTCOUNT('SECOP Consolidado'[nombre_entidad]),
    'SECOP Consolidado'[departamento] = DeptoSeleccionado
)
```

### Tabla: Entidades en Depto Específico
```dax
Entidades En Nariño = FILTER(
    ALL('SECOP Consolidado'),
    'SECOP Consolidado'[departamento] = "Nariño"
)
```

---

## Estructura Sugerida del Reporte

```
Reporte SECOP Consolidado
├── Página 1: Overview (KPIs + mini gráficos)
├── Página 2: E-02a - Distribución por Valor
├── Página 3: E-02b - Tipo de Contrato
├── Página 4: E-02c - Modalidad
├── Página 5: E-03 - Por Departamento (mapa + tabla)
├── Página 6: E-04 - Top Entidades
├── Página 7: P2 - Educación vs Salud
└── Página 8: P3 - Top Proveedores
```

---

## Slicers Recomendados

Añadir slicers para filtrado interactivo:
- **Departamento** - Selección múltiple
- **Origen** - SECOP_I, SECOP_II, SECOP_INTEGRADO
- **Modalidad** - Selección múltiple
- **Tipo de Contrato** - Selección múltiple

---

## Notas

- Los valores de fecha pueden necesitar transformación en Power Query
- Los slicers deben usar la columna original, no las medidas calculadas
- Para mapas, usar columna `departamento` directamente
- "No Definido" debe ser excluido en visualizaciones relevantes