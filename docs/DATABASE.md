# CiviData - Base de Datos Completa

## Esquemas

| Esquema | Propósito | Tablas |
|---------|-----------|--------|
| `clean` | Datos normalizados por categoría | 5 tablas |
| `marts` | Tablas consolidadas para análisis | 5 tablas |

---

## Esquema `clean` - Datos Normalizados

### Tabla: `clean.secop_ii_20260423_clean`
Contratos Electrónicos SECOP II - Principal dataset

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| id_contrato | text | Identificador único del contrato | CONVE-2024-00001 |
| referencia_del_contrato | text | Número de referencia | REF-2024-001 |
| nombre_entidad | text | Nombre de la entidad contratante | Alcaldía de Pasto |
| nit_entidad | bigint | NIT de la entidad | 800123456 |
| departamento | text | Departamento de la entidad | Nariño |
| ciudad | text | Ciudad/Municipio | Pasto |
| localizaci_n | text | Detalle ubicación | Zona urbana |
| orden | text | Rama del poder | Ejecitivo |
| sector | text | Sector del contrato | Educación Nacional |
| rama | text | Rama del estado | Gobierno Central |
| entidad_centralizada | text | Tipo entidad | Alcaldía Municipal |
| proceso_de_compra | text | Tipo de proceso | Licitación Pública |
| id_contrato | text | ID del contrato | CONVE-2024-00001 |
| referencia_del_contrato | text | Referencia | REF-2024-001 |
| estado_contrato | text | Estado actual | Adjudivado |
| codigo_de_categoria_principal | text | Código categoría | 95101600 |
| descripcion_del_proceso | text | Descripción del proceso | Suministro de materiales |
| tipo_de_contrato | text | Tipo de contrato | Suministros |
| modalidad_de_contratacion | text | Modalidad | Licitación Pública |
| justificacion_modalidad_de | text | Razón modalidad | Por monto |
| fecha_de_firma | text | Fecha firma (YYYY-MM-DD) | 2024-01-15 |
| fecha_de_inicio_del_contrato | text | Fecha inicio | 2024-02-01 |
| fecha_de_fin_del_contrato | text | Fecha fin | 2024-12-31 |
| condiciones_de_entrega | text | Condiciones entrega | Según especificaciones |
| tipodocproveedor | text | Tipo doc proveedor | NIT |
| documento_proveedor | text | Número documento proveedor | 900123456789 |
| proveedor_adjudicado | text | Nombre del proveedor | Inversiones XYZ S.A.S |
| es_grupo | text | Es grupo empresarial | No |
| es_pyme | text | Es PYME | Sí |
| valor_del_contrato | bigint | Valor total del contrato en COP | 50000000 |
| valor_de_pago_adelantado | bigint | Pago adelantado | 0 |
| valor_facturado | bigint | Valor facturado | 25000000 |
| valor_pendiente_de_pago | bigint | Pendiente pago | 25000000 |
| valor_pagado | bigint | Valor pagado | 25000000 |
| valor_amortizado | bigint | Valor amortizado | 0 |
| valor_pendiente_de | text | Pendiente de | - |
| valor_pendiente_de_ejecucion | bigint | Pendiente ejecución | 25000000 |

### Índices
```sql
CREATE INDEX idx_secop_departamento ON clean.secop_ii_20260423_clean(departamento);
CREATE INDEX idx_secop_fecha ON clean.secop_ii_20260423_clean(fecha_de_inicio_del_contrato);
CREATE INDEX idx_secop_entidad ON clean.secop_ii_20260423_clean(nombre_entidad);
```

---

### Tabla: `clean.secop_integrado_20260423_clean`
SECOP I + II Combinados - 10,000 registros

Mismas columnas que SECOP II. Usar para análisis histórico completo.

---

### Tabla: `clean.secop_i_20260423_clean`
SECOP I - Procesos de Compra - 9,693 registros

Columnas similares con variaciones menores.

---

### Tabla: `clean.secop_ii_2025_20260423_clean`
SECOP II desde 2025 - 9,998 registros

Datos más recientes del nuevo sistema.

---

## Esquema `marts` - Tablas de Análisis

### Tabla: `marts.contratacion`
**Tabla maestra consolidada** - 48,311 registros

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id_contrato | text | Identificador único |
| referencia | text | Número de referencia |
| nombre_entidad | text | Entidad contratante |
| nit_entidad | bigint | NIT entidad |
| departamento | text | Departamento |
| ciudad | text | Ciudad |
| proceso_de_compra | text | Tipo proceso |
| tipo_contrato | text | Tipo contrato |
| modalidad | text | Modalidad |
| estado_contrato | text | Estado |
| fecha_firma | date | Fecha firma |
| fecha_inicio | date | Fecha inicio |
| valor_contrato | numeric(20,2) | Valor total |
| valor_pagado | numeric(20,2) | Valor pagado |
| proveedor | text | Proveedor |
| sector | text | Sector |
| fecha_carga | timestamp | Fecha carga |

### Tabla: `marts.resumen_departamento`
Resumen por departamento - 34 filas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| depto | text | Nombre departamento |
| num_contratos | bigint | Total contratos |
| valor_total | numeric(20,2) | Valor total |
| valor_promedio | numeric(20,2) | Valor promedio |
| num_entidades | bigint | Número entidades |

### Tabla: `marts.resumen_entidad`
Top 100 entidades - 100 filas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| nombre_entidad | text | Nombre entidad |
| depto | text | Departamento |
| num_contratos | bigint | Total contratos |
| valor_total | numeric(20,2) | Valor total |

### Tabla: `marts.resumen_sector`
Por sector - 25 filas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| sector | text | Nombre sector |
| num_contratos | bigint | Total contratos |
| valor_total | numeric(20,2) | Valor total |

### Tabla: `marts.resumen_tipo_proceso`
Por tipo proceso - 47,692 filas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| proceso | text | Tipo proceso |
| num_contratos | bigint | Total contratos |
| valor_total | numeric(20,2) | Valor total |

---

## Consultas de Ejemplo

### Conexión Power BI
```sql
-- En Power BI: Transformar datos → Avanzadas
SELECT * FROM marts.contratacion WHERE departamento = 'Nariño';
```

### Ver estructura completa
```sql
-- Listar todas las tablas de marts
SELECT table_name FROM information_schema.tables WHERE table_schema = 'marts';

-- Ver columnas de una tabla
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'marts' AND table_name = 'contratacion'
ORDER BY ordinal_position;
```

---

## Relaciones entre Tablas

```
marts.contratacion (1) ──(N)── marts.resumen_departamento
        │                              │
        │                        (agrupado por depto)
        │
        └── departamento = depto

marts.contratacion (N) ──(1)── marts.resumen_entidad
        │                        │
        │                  (agrupado por entidad)
        └── nombre_entidad
```

---

## Consideraciones

1. **Fechas**: Almacenadas como TEXT en clean, DATE en marts
2. **Valores**: BIGINT en clean, NUMERIC(20,2) en marts
3. **Encoding**: UTF-8
4. **Zona horaria**: America/Bogotá (UTC-5)