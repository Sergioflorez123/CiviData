-- Funciones SQL para consultas analíticas de CiviData
-- Schema: marts


-- 1. Top entidades por valor contratado por departamento
CREATE OR REPLACE FUNCTION marts.entidades_por_departamento(
    p_departamento VARCHAR,
    p_limite INTEGER DEFAULT 20
)
RETURNS TABLE(
    entidad VARCHAR,
    total_contratos BIGINT,
    valor_total NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.nombre_entidad,
        COUNT(*)::BIGINT AS total_contratos,
        SUM(c.valor_contrato)::NUMERIC AS valor_total
    FROM clean.contratacion c
    WHERE c.departamento = p_departamento
    GROUP BY c.nombre_entidad
    ORDER BY valor_total DESC
    LIMIT p_limite;
END;
$$ LANGUAGE plpgsql;


-- 2. Comparación educación vs salud por año
CREATE OR REPLACE FUNCTION marts.contratos_por_sector(p_anno INTEGER)
RETURNS TABLE(
    sector VARCHAR,
    total_contratos BIGINT,
    valor_total NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN LOWER(c.objeto_contrato) LIKE '%educacion%' THEN 'Educación'
            WHEN LOWER(c.objeto_contrato) LIKE '%salud%' THEN 'Salud'
            ELSE 'Otros'
        END AS sector,
        COUNT(*)::BIGINT,
        SUM(c.valor_contrato)::NUMERIC
    FROM clean.contratacion c
    WHERE EXTRACT(YEAR FROM c.fecha_inicio) = p_anno
    GROUP BY 1
    ORDER BY valor_total DESC;
END;
$$ LANGUAGE plpgsql;


-- 3. Top proveedores por región
CREATE OR REPLACE FUNCTION marts.top_proveedores_region(
    p_departamento VARCHAR,
    p_limite INTEGER DEFAULT 10
)
RETURNS TABLE(
    proveedor VARCHAR,
    num_contratos BIGINT,
    valor_total NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.proveedor,
        COUNT(*)::BIGINT,
        SUM(c.valor_contrato)::NUMERIC
    FROM clean.contratacion c
    WHERE c.departamento = p_departamento
    GROUP BY c.proveedor
    ORDER BY valor_total DESC
    LIMIT p_limite;
END;
$$ LANGUAGE plpgsql;


-- 4. Detección de anomalías: contratos con un solo proponente
CREATE OR REPLACE FUNCTION marts.contratos_un_proponente(p_anno INTEGER)
RETURNS TABLE(
    entidad VARCHAR,
    objeto_contrato VARCHAR,
    valor_contrato NUMERIC,
    proveedor VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.nombre_entidad,
        c.objeto_contrato,
        c.valor_contrato,
        c.proveedor
    FROM clean.contratacion c
    WHERE EXTRACT(YEAR FROM c.fecha_inicio) = p_anno
    AND c.numero_proponentes = 1
    ORDER BY c.valor_contrato DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;


-- 5. Verificar estado de datasets
CREATE OR REPLACE FUNCTION marts.dataset_stats()
RETURNS TABLE(
    dataset VARCHAR,
    ultima_actualizacion TIMESTAMP,
    num_registros BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'contratacion'::VARCHAR,
        MAX(fecha_inicio) AS ultima_actualizacion,
        COUNT(*)::BIGINT
    FROM clean.contratacion;
END;
$$ LANGUAGE plpgsql;