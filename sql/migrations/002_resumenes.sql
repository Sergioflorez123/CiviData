-- Resumen por departamento (arreglado)
DROP TABLE IF EXISTS marts.resumen_departamento;
CREATE TABLE marts.resumen_departamento AS
SELECT COALESCE(departamento, 'Sin info') AS depto,
    count(*)::bigint AS num_contratos,
    sum(valor_del_contrato)::numeric(20,2) AS valor_total,
    avg(valor_del_contrato)::numeric(20,2) AS valor_promedio,
    count(distinct nombre_entidad)::bigint AS num_entidades
FROM marts.contratacion GROUP BY depto ORDER BY valor_total DESC;

-- Resumen por entidad
DROP TABLE IF EXISTS marts.resumen_entidad;
CREATE TABLE marts.resumen_entidad AS
SELECT nombre_entidad, COALESCE(departamento, 'Sin info') AS depto,
    count(*)::bigint AS num_contratos, sum(valor_del_contrato)::numeric(20,2) AS valor_total
FROM marts.contratacion GROUP BY nombre_entidad, depto ORDER BY valor_total DESC LIMIT 100;

-- Resumen por sector
DROP TABLE IF EXISTS marts.resumen_sector;
CREATE TABLE marts.resumen_sector AS
SELECT COALESCE(sector, 'Sin info') AS sector,
    count(*)::bigint AS num_contratos, sum(valor_del_contrato)::numeric(20,2) AS valor_total
FROM marts.contratacion GROUP BY sector ORDER BY valor_total DESC;

-- Resumen por proceso
DROP TABLE IF EXISTS marts.resumen_tipo_proceso;
CREATE TABLE marts.resumen_tipo_proceso AS
SELECT COALESCE(proceso_de_compra, 'Sin info') AS proceso,
    count(*)::bigint AS num_contratos, sum(valor_del_contrato)::numeric(20,2) AS valor_total
FROM marts.contratacion GROUP BY proceso ORDER BY valor_total DESC;

SELECT * FROM marts.resumen_departamento LIMIT 5;