# 🎬 Exportadores de Video Timeline

## Módulos Disponibles

### 1. `video_exporter_multiscene.py` ⭐ RECOMENDADO
**Exportador profesional multi-escena**

Genera videos completos con 5 escenas:
1. Portada profesional
2. Mapas mensuales con overlay completo
3. Análisis IA (opcional)
4. Recomendaciones (opcional)
5. Cierre profesional

**Características:**
- ✅ Full HD (1920x1080) @ 24fps
- ✅ Calidad broadcast (H.264, CRF 18)
- ✅ Solo usa datos dinámicos (NO inventa valores)
- ✅ Compatible con WhatsApp (<1 MB)
- ✅ Listo para entrega comercial

**Uso:**
```python
from informes.exporters.video_exporter_multiscene import TimelineVideoExporterMultiScene

exporter = TimelineVideoExporterMultiScene()
video_path = exporter.export_timeline(
    frames_data=frames_data,
    indice='ndvi',
    parcela_info={'nombre': 'Parcela #1'},
    analisis_texto="Texto del análisis...",
    recomendaciones_texto="- Recomendación 1\n- Recomendación 2"
)
```

### 2. `video_exporter.py`
**Exportador básico de mapas (legacy)**

Genera videos simples de mapas mensuales sin escenas adicionales.

**Uso:** Solo para casos especiales que requieran únicamente mapas.

---

## 🚀 Scripts de Generación

### Script Individual
```bash
python generar_video_multiscene.py --parcela 6 --indice ndvi
```

### Script Batch
```bash
python generar_videos_multiscene_batch.py --parcela 6
```

---

## 📊 Salida

Videos guardados en: `media/timeline_videos/`

Formato: `timeline_{indice}_multiscene_{timestamp}.mp4`

Ejemplo: `timeline_ndvi_multiscene_20260116_171848.mp4`

---

## 📚 Documentación

Ver:
- `/docs/VIDEO_MULTISCENE_COMPLETADO.md` - Documentación técnica
- `/docs/VIDEO_MULTISCENE_GUIA_RAPIDA.md` - Guía de uso
- `/IMPLEMENTACION_VIDEO_MULTISCENE_FINAL.md` - Resumen final
