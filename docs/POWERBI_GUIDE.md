# Guía de Conexión Power BI - CiviData

## Flujo Completo de Publicación

```
PostgreSQL (cividata)
    ↓ Power BI Desktop
Modelado de datos + Dashboard
    ↓ Publicar
Power BI Service (cuenta universitaria gratuita)
    ↓ Copiar iframe
Frontend (React/HTML)
```

---

## 1. Conectar Power BI Desktop a PostgreSQL

### Datos de conexión
```
Servidor: localhost
Puerto: 5432
Base de datos: cividata
Usuario: postgres
Contraseña: postgres
```

### Pasos en Power BI Desktop
1. **Archivo** → **Obtener datos** → **Más** → buscar "PostgreSQL"
2. Ingresar datos de conexión
3. Seleccionar tablas de `marts` y `clean`
4. **Transformar datos** → **Cargar**

---

## 2. Modelado de Datos (Power BI Desktop)

### Relaciones recomendadas
```
marts.contratacion.departamento  ──1:N──►  marts.resumen_departamento.depto
marts.contratacion.nombre_entidad ──N:1──► marts.resumen_entidad.nombre_entidad
marts.contratacion.sector        ──N:1──►  marts.resumen_sector.sector
marts.contratacion.proceso_de_compra ──N:1──► marts.resumen_tipo_proceso.proceso
```

### Medidas DAX básicas
```dax
Total Valor = SUM(marts.contratacion[valor_contrato])
Num Contratos = COUNTROWS(marts.contratacion)
Valor Promedio = AVERAGE(marts.contratacion[valor_contrato])
```

### Medidas para Educación vs Salud
```dax
Valor Educación = 
    CALCULATE(SUM(marts.contratacion[valor_contrato]),
        CONTAINSSTRING(marts.contratacion[sector], "Educaci"))

Valor Salud = 
    CALCULATE(SUM(marts.contratacion[valor_contrato]),
        CONTAINSSTRING(marts.contratacion[sector], "Salud"))
```

---

## 3. Crear Dashboard (Visualizaciones)

### Página 1: Contratación
- **Mapa coroplético** → valor_total por departamento
- **Barras horizontales** → Top 10 entidades
- **Pie chart** → Distribución por sector
- **Tarjetas** → KPIs (total contratos, valor total, valor promedio)

### Página 2: Análisis Temporal
- **Gráfico de líneas** → Contratos por mes/año
- **Stacked column** → Sectores por período

### Página 3: Anomalías
- **Scatter** → valor vs cantidad
- **Tabla** → Contratos atípicos

---

## 4. Publicar en Power BI Service

### Requisitos
- Cuenta universitaria (@.edu.co) o cuenta profesional
- Registro en https://app.powerbi.com

### Pasos
1. **Archivo** → **Publicar** → **Mi espacio de trabajo**
2. Esperar publicación completa
3. Ir a https://app.powerbi.com
4. Buscar el reporte publicado
5. **Archivo** → **Insertar** → **Publicar en la web**

---

## 5. Obtener Código Iframe

### Opción A: Publicar en la web (público)
1. En Power BI Service → Reporte → **Archivo** → **Publicar en la web**
2. Copiar código HTML generado
3. Ejemplo:
```html
<iframe 
    title="CiviData - Contratación"
    width="100%" 
    height="600"
    src="https://app.powerbi.com/reportEmbed?reportId=XXXXX&groupId=YYYYY"
    frameborder="0"
    allowFullScreen="true">
</iframe>
```

### Opción B: Enlace seguro (requiere cuenta)
```html
<iframe 
    title="CiviData Dashboard"
    src="https://app.powerbi.com/reportEmbed?reportId=XXXXX&autoAuth=true&ctid=ZZZZZ"
    width="100%" 
    height="600"
    frameborder="0"
    allowFullScreen="true">
</iframe>
```

---

## 6. Embeber en Frontend

### HTML Simple
```html
<!DOCTYPE html>
<html>
<head>
    <title>CiviData - Dashboard</title>
    <style>
        body { margin: 0; padding: 20px; background: #f5f5f5; }
        .dashboard-container { max-width: 1400px; margin: 0 auto; }
        h1 { color: #333; font-family: sans-serif; }
        iframe { border: none; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>Contratación Pública - Colombia</h1>
        <iframe 
            src="https://app.powerbi.com/reportEmbed?reportId=TU_ID&autoAuth=true&ctid=TU_TENANT"
            width="100%" 
            height="800"
            allowFullScreen="true">
        </iframe>
    </div>
</body>
</html>
```

### React Component
```jsx
// DashboardEmbed.jsx
import React from 'react';

const DashboardEmbed = ({ reportId, tenantId, title }) => {
    const embedUrl = `https://app.powerbi.com/reportEmbed?reportId=${reportId}&autoAuth=true&ctid=${tenantId}`;
    
    return (
        <div className="dashboard-container">
            <h2>{title}</h2>
            <iframe
                src={embedUrl}
                width="100%"
                height="600"
                frameBorder="0"
                allowFullScreen="true"
                title={title}
            />
        </div>
    );
};

export default DashboardEmbed;

// Uso en App.js
import DashboardEmbed from './DashboardEmbed';

function App() {
    return (
        <div>
            <DashboardEmbed 
                reportId="REPORT_ID"
                tenantId="TENANT_ID"
                title="Contratación Pública"
            />
        </div>
    );
}
```

### Estructura sugerida para React
```
src/
├── components/
│   ├── DashboardEmbed.jsx    # Componente reutilizable
│   ├── ContratacionDashboard.jsx
│   ├── EducacionDashboard.jsx
│   └── Layout/
│       ├── Navbar.jsx
│       └── Sidebar.jsx
├── pages/
│   ├── Home.jsx
│   ├── Contratacion.jsx
│   └── Educacion.jsx
└── App.jsx
```

---

## 7. Notas de Seguridad

### Para iframe público
- Cualquier persona puede ver el dashboard
- No incluir datos sensibles

### Para iframe privado
- El usuario debe iniciar sesión en Power BI Service
- Requiere cuenta con permisos al reporte

### Recomendaciones
- Usar HTTPS siempre
- Validar IDs de reporte en backend
- Considerar autenticación de usuario

---

## 8. Troubleshooting

### Error de conexión PostgreSQL
```
Verificar que PostgreSQL esté corriendo:
  docker-compose ps
```

### Iframe no carga
```
1. Verificar que el reporte esté publicado
2. Confirmar que el link es correcto
3. Revisar consola del navegador (F12)
```

### Actualizar datos en dashboard
```
1. Actualizar datos en PostgreSQL
2. Actualizar dataset en Power BI Service
3. O schedule refresh automático (Gateway)
```

---

## Recursos

- [Power BI Documentation](https://docs.microsoft.com/power-bi/)
- [Publicar en la web](https://docs.microsoft.com/power-bi/collaborate-share/service-publish-to-web)
- [Insertar iframe](https://docs.microsoft.com/power-bi/developer/embedded/embed-urls)