# 🎬 Guía Rápida - Video Timeline Multi-Escena

## ¿Qué es?

Sistema profesional de generación de videos timeline para análisis satelital agrícola.

**Características:**
- ✅ 5 escenas profesionales (Portada + Mapas + Análisis + Recomendaciones + Cierre)
- ✅ Full HD (1920x1080) @ 24fps
- ✅ Solo usa datos dinámicos (NO inventa valores)
- ✅ Compatible con WhatsApp
- ✅ Calidad profesional para clientes

---

## 🚀 Uso Rápido

```bash
# Video NDVI básico
python generar_video_multiscene.py --parcela 6 --indice ndvi

# Video NDMI básico
python generar_video_multiscene.py --parcela 6 --indice ndmi

# Video SAVI básico
python generar_video_multiscene.py --parcela 6 --indice savi

# Con ruta personalizada
python generar_video_multiscene.py --parcela 6 --indice ndvi --output mi_video.mp4
```

---

## 📊 Estructura del Video

### 1️⃣ Portada (3s)
- Logo AgroTech
- Índice analizado
- Nombre de parcela
- Rango temporal

### 2️⃣ Mapas Mensuales (2.5s cada uno)
- Imagen satelital (NDVI/NDMI/SAVI)
- Valor promedio
- Estado del cultivo
- Cambio vs mes anterior
- Calidad de imagen (nubosidad)
- Clima (temperatura y precipitación)

### 3️⃣ Análisis IA (5s) [OPCIONAL]
- Texto de análisis Gemini
- Máximo 2-3 frases

### 4️⃣ Recomendaciones (5s) [OPCIONAL]
- Máximo 3 recomendaciones
- Formato bullets

### 5️⃣ Cierre (3s)
- Logo AgroTech
- Mensaje profesional

---

## 📁 Videos Generados

### Ejemplo Parcela 6 - NDVI
- **Frames:** 924 frames (72 portada + 780 mapas + 72 cierre)
- **Duración:** ~38.5 segundos
- **Tamaño:** 0.66 MB
- **Ruta:** `/media/timeline_videos/timeline_ndvi_multiscene_YYYYMMDD_HHMMSS.mp4`

### Ejemplo Parcela 6 - NDMI
- **Frames:** 924 frames
- **Duración:** ~38.5 segundos
- **Tamaño:** 0.53 MB
- **Ruta:** `/media/timeline_videos/timeline_ndmi_multiscene_YYYYMMDD_HHMMSS.mp4`

---

## 💡 Reglas del Sistema

### ✅ Lo que SÍ hace
- Presenta datos del motor de análisis
- Muestra valores exactos
- Usa imágenes satelitales reales
- Indica cuando faltan datos

### ❌ Lo que NO hace
- NO inventa valores
- NO analiza datos por su cuenta
- NO modifica cifras
- NO recalcula índices
- NO agrega gráficos decorativos

---

## 🔧 Integración con Django

```python
from informes.exporters.video_exporter_multiscene import TimelineVideoExporterMultiScene
from informes.processors.timeline_processor import TimelineProcessor

# 1. Obtener datos
indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')

# 2. Procesar timeline
frames_data = []
for i, indice in enumerate(indices):
    mes_anterior = list(indices)[i-1] if i > 0 else None
    frame_data = TimelineProcessor.generar_metadata_frame(indice, mes_anterior)
    frames_data.append(frame_data)

# 3. Generar video
exporter = TimelineVideoExporterMultiScene()
video_path = exporter.export_timeline(
    frames_data=frames_data,
    indice='ndvi',
    parcela_info={'nombre': parcela.nombre},
    analisis_texto="Texto del análisis Gemini...",
    recomendaciones_texto="- Recomendación 1\n- Recomendación 2"
)
```

---

## 📦 Archivos del Sistema

```
informes/exporters/video_exporter_multiscene.py  # Exportador principal
generar_video_multiscene.py                      # Script CLI
docs/VIDEO_MULTISCENE_COMPLETADO.md             # Documentación completa
docs/VIDEO_MULTISCENE_GUIA_RAPIDA.md            # Esta guía
```

---

## 🎯 Estado del Proyecto

**✅ COMPLETADO Y FUNCIONAL**

- [x] Estructura multi-escena implementada
- [x] Todas las escenas funcionando
- [x] Calidad profesional Full HD
- [x] Script de generación CLI
- [x] Documentación completa
- [x] Validado con NDVI y NDMI

**El sistema está listo para producción.** 🚀
