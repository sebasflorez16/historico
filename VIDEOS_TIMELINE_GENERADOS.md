# Resumen de Videos Timeline Generados - Parcela #2 (Maíz)
## Fecha: 15 de enero de 2026

---

## 📹 Videos Generados con Columna Dinámica

### 1️⃣ Video NDVI - Salud Vegetal
**Archivo:** `timeline_ndvi_20260115_173703.mp4`  
**Tamaño:** 0.64 MB  
**Frames:** 10 meses de datos  
**Duración:** 25 segundos

**Leyenda de Colores:**
- 🟥 Muy bajo (0.0 - 0.2)
- 🟧 Bajo (0.2 - 0.4)
- 🟨 Moderado (0.4 - 0.6)
- 🟩 Bueno (0.6 - 0.8)
- 🟢 Excelente (0.8 - 1.0)

**Columna Dinámica Muestra:**
- Cambio mensual en salud vegetal (%)
- Calidad de imagen satelital
- Temperatura y precipitación del periodo

---

### 2️⃣ Video NDMI - Humedad del Cultivo
**Archivo:** `timeline_ndmi_20260115_174118.mp4`  
**Tamaño:** 0.50 MB  
**Frames:** 10 meses de datos  
**Duración:** 25 segundos

**Leyenda de Colores:**
- 🟥 Muy seco (-0.8 - -0.4)
- 🟧 Seco (-0.4 - 0.0)
- 🟨 Moderado (0.0 - 0.2)
- 🔵 Húmedo (0.2 - 0.4)
- 💙 Muy húmedo (0.4 - 0.8)

**Columna Dinámica Muestra:**
- Cambio mensual en contenido de humedad (%)
- Calidad de imagen satelital
- Temperatura y precipitación del periodo

---

### 3️⃣ Video SAVI - Cobertura Vegetal
**Archivo:** `timeline_savi_20260115_174155.mp4`  
**Tamaño:** 0.28 MB  
**Frames:** 10 meses de datos  
**Duración:** 25 segundos

**Leyenda de Colores:**
- 🟥 Muy bajo (0.0 - 0.2)
- 🟧 Bajo (0.2 - 0.4)
- 🟨 Moderado (0.4 - 0.6)
- 🟩 Bueno (0.6 - 0.8)
- 🟢 Excelente (0.8 - 1.0)

**Columna Dinámica Muestra:**
- Cambio mensual en cobertura vegetal (%)
- Calidad de imagen satelital
- Temperatura y precipitación del periodo

---

## 🎯 Características Comunes

### Estructura del Video
- **Resolución:** 1920x1080 Full HD
- **FPS:** 24 (cinematográfico)
- **Codec:** H.264 con preset veryslow (máxima calidad)
- **CRF:** 18 (calidad broadcast)
- **Bitrate:** 10 Mbps
- **Transiciones:** Fade in/out de 300ms

### Layout Profesional GIS
- **Header (superior izquierda):** Índice y periodo
- **Footer izquierdo:** Valor promedio del índice
- **Footer derecho:** Estado general del cultivo
- **Leyenda (inferior izquierda):** Rangos de colores con significado
- **Columna dinámica (derecha):** Información mensual específica

### Columna Dinámica (Lado Derecho)
**Posición:** 85% del ancho (1632px)

**Sección 1: CAMBIO MENSUAL**
- Porcentaje de cambio vs mes anterior
- Color verde para mejoras, rojo para deterioros
- Texto "vs mes anterior"

**Sección 2: CALIDAD IMAGEN**
- Etiqueta: Excelente/Buena/Moderada/Baja
- Porcentaje de nubosidad
- Color según calidad

**Sección 3: CLIMA DEL MES**
- Temperatura promedio (°C)
- Precipitación total (mm)
- Colores por rango

---

## 📊 Análisis Comparativo

### Tamaños de Archivo
- NDVI: 0.64 MB (mayor complejidad visual)
- NDMI: 0.50 MB (tonos azules)
- SAVI: 0.28 MB (menor variabilidad)

*Diferencia de tamaño debido a complejidad de patrones en el raster*

### Valores Dinámicos por Índice
Cada video muestra datos específicos del índice:

**NDVI (Vegetación):**
- Cambios en vigor vegetativo
- Estado de salud del cultivo
- Estrés vegetal

**NDMI (Humedad):**
- Cambios en contenido de agua
- Estrés hídrico
- Condiciones de riego

**SAVI (Cobertura):**
- Cambios en densidad vegetal
- Desarrollo del cultivo
- Cobertura del suelo

---

## ✅ Validación de Implementación

### Reglas Cumplidas en los 3 Videos
- ✅ Valores dinámicos por frame (no hardcoded)
- ✅ Solo texto, sin paneles de fondo
- ✅ Coordenadas fijas (85% del ancho)
- ✅ Sin overlap con el raster
- ✅ Advertencias para datos faltantes
- ✅ Colores semánticos por categoría
- ✅ Leyenda específica por índice
- ✅ Header y footer adaptados

### Diferencias entre Videos
1. **Paleta de colores:** Específica para cada índice
2. **Rangos de clasificación:** Adaptados al tipo de medición
3. **Interpretación:** Estado general cambia según índice
4. **Valores numéricos:** Cambios mensuales específicos

---

## 🚀 Uso de los Videos

### Para Presentaciones
Mostrar los 3 videos en secuencia para análisis completo:
1. NDVI → Estado general del cultivo
2. NDMI → Condiciones de humedad
3. SAVI → Desarrollo de cobertura

### Para Análisis Técnico
Revisar columna dinámica para:
- Identificar meses con cambios significativos
- Validar calidad de datos (nubosidad)
- Correlacionar clima con índices

### Para Clientes/Agricultores
Videos autoexplicativos que muestran:
- Evolución temporal clara
- Datos confiables con indicadores de calidad
- Información completa sin reportes adicionales

---

## 📂 Ubicación de Archivos

```
media/timeline_videos/
├── timeline_ndvi_20260115_173703.mp4  (0.64 MB)
├── timeline_ndmi_20260115_174118.mp4  (0.50 MB)
└── timeline_savi_20260115_174155.mp4  (0.28 MB)
```

**Total:** 1.42 MB para 75 segundos de video profesional (3 índices × 25s)

---

## 🎬 Comandos para Abrir

```bash
# NDVI
open 'media/timeline_videos/timeline_ndvi_20260115_173703.mp4'

# NDMI
open 'media/timeline_videos/timeline_ndmi_20260115_174118.mp4'

# SAVI
open 'media/timeline_videos/timeline_savi_20260115_174155.mp4'
```

---

## 💡 Próximos Pasos

### Opcionales
1. **Exportación batch:** Generar los 3 índices en un solo comando
2. **Video compuesto:** Combinar los 3 índices en pantalla dividida
3. **Marca de agua:** Agregar logo de AgroTech
4. **Metadata:** Embed información de la parcela en el archivo MP4

### Mejoras Futuras
1. **Gráficos adicionales:** Mini-plot de tendencia en la columna
2. **Alertas visuales:** Destacar meses críticos
3. **Comparación de parcelas:** Videos lado a lado
4. **Reportes automáticos:** PDF generado desde el video

---

**Estado:** ✅ **3 VIDEOS GENERADOS Y VALIDADOS**  
**Calidad:** Broadcast (CRF 18, 10 Mbps)  
**Compatibilidad:** Universal (H.264 + yuv420p)  
**Entregable:** Listo para producción
