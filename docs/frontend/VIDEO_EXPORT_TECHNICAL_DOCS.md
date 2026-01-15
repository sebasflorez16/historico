# Exportación de Video Timeline - Documentación Técnica

## 🎬 Sistema de Exportación Profesional

Sistema completo de exportación de videos del Timeline usando **FFmpeg + Python PIL/Pillow** para generar videos MP4 de máxima calidad.

### 📋 Características Principales

✅ **Alta Calidad Visual**
- Resolución Full HD (1920x1080) por defecto
- Bitrate profesional 8 Mbps
- Codec H.264 (libx264) con CRF 18 (visualmente sin pérdidas)
- Pixel format yuv420p (compatible universal)

✅ **Generación 100% Backend**
- No usa MediaRecorder ni canvas.captureStream
- Frames generados como PNG sin compresión
- FFmpeg con control total de parámetros
- Sin dependencias del navegador

✅ **Réplica Exacta del Timeline Web**
- Mismos colores, fuentes y layout
- Overlay con metadata completa
- Soporte para placeholders cuando no hay imagen
- Gradientes y efectos visuales

✅ **Configurabilidad Total**
- FPS ajustable (default: 2 fps = 0.5s por mes)
- Resolución personalizable
- Bitrate y calidad configurables
- Duración por frame controlada

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│  timeline_player.js → downloadVideo(indice)                 │
│  - Muestra loading con progreso                             │
│  - Llama endpoint de backend                                │
│  - Descarga archivo MP4                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ HTTP GET
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                             │
│  views.py → exportar_video_timeline()                       │
│  1. Obtiene datos del TimelineProcessor                     │
│  2. Crea instancia de TimelineVideoExporter                 │
│  3. Genera frames individuales (PNG)                        │
│  4. Une frames con FFmpeg → MP4                             │
│  5. Retorna FileResponse con video                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              TimelineVideoExporter                          │
│  exporters/video_exporter.py                                │
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │ 1. _generate_frames()                        │           │
│  │    - Itera sobre frames_data                 │           │
│  │    - Para cada frame:                        │           │
│  │      * Descarga imagen satelital             │           │
│  │      * Redimensiona y centra (cover mode)    │           │
│  │      * Dibuja overlay con metadata           │           │
│  │    - Guarda como PNG sin compresión          │           │
│  └──────────────────────────────────────────────┘           │
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │ 2. _create_video_ffmpeg()                    │           │
│  │    - Crea archivo de lista de frames         │           │
│  │    - Ejecuta FFmpeg con parámetros óptimos:  │           │
│  │      * -c:v libx264                          │           │
│  │      * -preset slow                          │           │
│  │      * -crf 18                               │           │
│  │      * -b:v 8000k                            │           │
│  │      * -pix_fmt yuv420p                      │           │
│  │    - Verifica archivo generado               │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura de Archivos

```
informes/
├── exporters/
│   ├── __init__.py
│   └── video_exporter.py          # 🆕 Exportador de video
│
├── processors/
│   └── timeline_processor.py      # Procesador de datos del timeline
│
├── views.py                        # 🆕 Vista exportar_video_timeline()
└── urls.py                         # 🆕 URL /timeline/exportar-video/

static/js/timeline/
└── timeline_player.js              # 🆕 Método downloadVideo() actualizado
```

---

## 🔧 Uso

### Desde el Frontend

```javascript
// El usuario hace clic en botón de descarga
player.downloadVideo('ndvi');  // o 'ndmi', 'savi'

// Internamente llama:
fetch(`/informes/parcelas/${parcelaId}/timeline/exportar-video/?indice=ndvi`)
  .then(blob => descargar como MP4)
```

### Desde Python (Testing/Scripts)

```python
from informes.processors.timeline_processor import TimelineProcessor
from informes.exporters.video_exporter import TimelineVideoExporter
from informes.models import Parcela

# Obtener parcela
parcela = Parcela.objects.get(id=1)

# Generar datos del timeline
timeline_data = TimelineProcessor.generar_timeline_completo(
    parcela=parcela,
    request=None  # None para uso sin request
)

# Crear exportador
exporter = TimelineVideoExporter(
    width=1920,
    height=1080,
    fps=2,
    bitrate='8000k',
    crf=18
)

# Generar video
video_path = exporter.export_timeline(
    frames_data=timeline_data['frames'],
    indice='ndvi'
)

print(f"Video generado: {video_path}")
```

---

## ⚙️ Parámetros de Configuración

### URL Parameters (GET)

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `indice` | string | `'ndvi'` | Índice a exportar: `ndvi`, `ndmi`, `savi` |
| `fps` | int | `2` | Frames por segundo (velocidad) |
| `width` | int | `1920` | Ancho del video en píxeles |
| `height` | int | `1080` | Alto del video en píxeles |
| `bitrate` | string | `'8000k'` | Bitrate del video (calidad) |

### Ejemplos de Uso

```bash
# Video estándar Full HD
GET /informes/parcelas/1/timeline/exportar-video/?indice=ndvi

# Video más lento (1 mes por segundo)
GET /informes/parcelas/1/timeline/exportar-video/?indice=ndvi&fps=1

# Video 4K con máxima calidad
GET /informes/parcelas/1/timeline/exportar-video/?indice=savi&width=3840&height=2160&bitrate=16000k

# Video más rápido (4 meses por segundo)
GET /informes/parcelas/1/timeline/exportar-video/?indice=ndmi&fps=4
```

---

## 🎨 Diseño Visual

El exportador replica **exactamente** el diseño del timeline web:

### Estructura del Frame

```
┌────────────────────────────────────────────────┐
│                                                │
│         IMAGEN SATELITAL (centrada)            │
│              o PLACEHOLDER                     │
│                                                │
│                                                │
├────────────────────────────────────────────────┤ ← Overlay (20% altura)
│ PERÍODO        ICONO + ETIQUETA                │
│ (Ene 2024)     🌱 Vegetación Saludable         │
│                Descripción del estado          │
│                                                │
│ NDVI: 0.650                  ☁️ Nubosidad: 5%  │
└────────────────────────────────────────────────┘
```

### Colores y Fuentes

- **Fuentes**: Helvetica (sistema) con fallback a default
  - Título: 36px bold
  - Valor índice: 60px bold (color según clasificación)
  - Etiquetas: 28px bold
  - Pequeño: 20px

- **Gradientes**:
  - Overlay: Negro semi-transparente (0 → 85% opacidad)
  - Placeholder: Gradiente radial basado en color de clasificación

- **Colores dinámicos**: Según clasificación del índice
  - Verde vibrante: Vegetación saludable
  - Amarillo: Estrés moderado
  - Rojo: Estrés severo
  - etc.

---

## 🔍 Troubleshooting

### FFmpeg no encontrado

```bash
# macOS (Homebrew)
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Verificar instalación
ffmpeg -version
```

### Error de fuentes

Si las fuentes del sistema no están disponibles, el código usa fallback automático:

```python
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
except:
    font = ImageFont.load_default()  # ← Fallback
```

### Video se ve mal/pixelado

Aumentar calidad modificando parámetros:

```python
exporter = TimelineVideoExporter(
    width=3840,      # 4K
    height=2160,
    bitrate='16000k',  # 16 Mbps
    crf=15           # Máxima calidad (más lento)
)
```

### Video muy pesado

Reducir calidad pero mantener nitidez:

```python
exporter = TimelineVideoExporter(
    width=1280,      # HD
    height=720,
    bitrate='4000k',   # 4 Mbps
    crf=23           # Calidad balanceada
)
```

---

## 📊 Métricas de Calidad

### Comparación de Configuraciones

| Config | Resolución | FPS | Bitrate | CRF | Tamaño (12 meses) | Calidad Visual |
|--------|-----------|-----|---------|-----|-------------------|----------------|
| **Máxima** | 3840x2160 | 2 | 16000k | 15 | ~30 MB | ⭐⭐⭐⭐⭐ Excelente |
| **Profesional** | 1920x1080 | 2 | 8000k | 18 | ~12 MB | ⭐⭐⭐⭐ Muy buena |
| **Estándar** | 1280x720 | 2 | 4000k | 23 | ~6 MB | ⭐⭐⭐ Buena |
| **Rápida** | 1280x720 | 4 | 3000k | 28 | ~4 MB | ⭐⭐ Aceptable |

---

## 🚀 Próximas Mejoras

- [ ] Soporte para exportación GIF animado
- [ ] Marca de agua personalizable
- [ ] Comparación lado a lado de múltiples índices
- [ ] Gráficos estadísticos integrados en video
- [ ] Exportación con audio (narración automática)
- [ ] Codificación paralela para múltiples índices
- [ ] Progreso en tiempo real vía WebSocket

---

## 📝 Notas Técnicas

### ¿Por qué FFmpeg y no MoviePy?

- **Control total**: FFmpeg permite configurar cada parámetro de codificación
- **Rendimiento**: FFmpeg es nativo y mucho más rápido
- **Calidad**: Acceso directo a libx264 con todas sus opciones
- **Dependencias**: No requiere bibliotecas pesadas adicionales
- **Debugging**: Logs claros y estándar de la industria

### Flujo de Procesamiento

1. **Frame individual** (PNG sin compresión):
   - Tamaño: ~5-10 MB por frame
   - Tiempo: ~0.5-1s por frame
   - Total para 12 meses: ~60-120 MB temporales

2. **Video final** (MP4 comprimido):
   - Tamaño: ~10-15 MB para 12 meses @ 1080p
   - Tiempo total: ~10-15s para 12 meses
   - Ratio compresión: ~80-90%

### Compatibilidad

✅ **Navegadores**: Todos (descarga estándar de archivo)
✅ **Sistemas**: Windows, macOS, Linux, iOS, Android
✅ **Reproductores**: VLC, QuickTime, Windows Media, etc.
✅ **Redes sociales**: YouTube, Instagram, Facebook, Twitter

---

**Autor**: AgroTech Team  
**Versión**: 1.0.0  
**Fecha**: Enero 2026
