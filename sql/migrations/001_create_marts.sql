-- Script marts simplificado
CREATE SCHEMA IF NOT EXISTS marts;

DROP TABLE IF EXISTS marts.contratacion;
CREATE TABLE marts.contratacion AS
SELECT 
    id_contrato,
    referencia_del_contrato,
    nombre_entidad,
    nit_entidad,
    departamento,
    ciudad,
    proceso_de_compra,
    tipo_de_contrato,
    modalidad_de_contratacion,
    estado_contrato,
    NULLIF(fecha_de_firma::text, '')::date AS fecha_firma,
    NULLIF(fecha_de_inicio_del_contrato::text, '')::date AS fecha_inicio,
    valor_del_contrato,
    valor_pagado,
    proveedor_adjudicado,
    sector,
    now() AS fecha_carga
FROM clean.secop_ii_20260423_clean
WHERE valor_del_contrato IS NOT NULL AND valor_del_contrato > 0;

CREATE INDEX ON marts.contratacion(departamento);
CREATE INDEX ON marts.contratacion(fecha_inicio);
CREATE INDEX ON marts.contratacion(nombre_entidad);
CREATE INDEX ON marts.contratacion(valor_contrato);

DROP TABLE IF EXISTS marts.resumen_departamento;
CREATE TABLE marts.resumen_departamento AS
SELECT COALESCE(departamento, 'Sin info') AS depto,
    count(*)::bigint AS num_contratos,
    sum(valor_contrato)::numeric(20,2) AS valor_total,
    avg(valor_contrato)::numeric(20,2) AS valor_promedio,
    count(distinct nombre_entidad)::bigint AS num_entidades
FROM marts.contratacion GROUP BY depto ORDER BY valor_total DESC;

DROP TABLE IF EXISTS marts.resumen_entidad;
CREATE TABLE marts.resumen_entidad AS
SELECT nombre_entidad, COALESCE(departamento, 'Sin info') AS depto,
    count(*)::bigint AS num_contratos, sum(valor_contrato)::numeric(20,2) AS valor_total
FROM marts.contratacion GROUP BY nombre_entidad, depto ORDER BY valor_total DESC LIMIT 100;

DROP TABLE IF EXISTS marts.resumen_sector;
CREATE TABLE marts.resumen_sector AS
SELECT COALESCE(sector, 'Sin info') AS sector,
    count(*)::bigint AS num_contratos, sum(valor_contrato)::numeric(20,2) AS valor_total
FROM marts.contratacion GROUP BY sector ORDER BY valor_total DESC;

DROP TABLE IF EXISTS marts.resumen_tipo_proceso;
CREATE TABLE marts.resumen_tipo_proceso AS
SELECT COALESCE(proceso_de_compra, 'Sin info') AS proceso,
    count(*)::bigint AS num_contratos, sum(valor_contrato)::numeric(20,2) AS valor_total
FROM marts.contratacion GROUP BY proceso ORDER BY valor_total DESC;

SELECT 'marts.contratacion' AS tabla, count(*)::bigint AS registros FROM marts.contratacion;