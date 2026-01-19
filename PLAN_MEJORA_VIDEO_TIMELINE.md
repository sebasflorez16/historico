# 📋 PLAN DE MEJORA - Video Timeline Multi-Escena Profesional

## 🎯 Objetivo
Mejorar el exportador de videos timeline con información más completa, educativa y profesional, incluyendo análisis detallado del motor de informes PDF.

---

## 📐 NUEVA ESTRUCTURA DEL VIDEO

### **ESCENA 1: PORTADA COMPLETA** (4 segundos)
**Información a mostrar:**
- ✅ Logo AgroTech Histórico
- ✅ Nombre de la parcela/lote
- ✅ Coordenadas del centro (latitud, longitud)
- ✅ Área total en hectáreas
- ✅ Tipo de cultivo (si disponible)
- ✅ Rango de fechas completo (Mes Año - Mes Año)
- ✅ Índice a analizar (NDVI/NDMI/SAVI)
- ✅ Número total de meses con datos

**Layout propuesto:**
```
┌─────────────────────────────────────────┐
│         AGROTECH HISTÓRICO              │
│                                         │
│    Análisis Satelital - NDVI            │
│                                         │
│  📍 Parcela: [Nombre del Lote]          │
│  🌍 Centro: [lat], [lon]                │
│  📐 Área: [X.XX] hectáreas              │
│  🌾 Cultivo: [Tipo]                     │
│                                         │
│  📅 Período: Feb 2024 - Feb 2025        │
│  📊 Total meses analizados: 13          │
└─────────────────────────────────────────┘
```

---

### **ESCENA 2: EXPLICACIÓN DEL ÍNDICE** (5 segundos)
**Información a mostrar:**
- ✅ Título: "¿Qué es el NDVI?" (dinámico según índice)
- ✅ Definición técnica simplificada
- ✅ Rango de valores y su significado
- ✅ Para qué sirve en agricultura
- ✅ Cómo se aplica en ESTE terreno específico

**Contenido dinámico por índice:**

**NDVI (Normalized Difference Vegetation Index):**
```
┌─────────────────────────────────────────┐
│      ¿Qué es el NDVI?                   │
│                                         │
│  Índice de Vegetación Normalizado      │
│                                         │
│  • Mide la salud y vigor de las        │
│    plantas mediante luz infrarroja     │
│                                         │
│  • Rango: -1 a +1                       │
│    -1 a 0.2  → Sin vegetación          │
│    0.2 a 0.5 → Vegetación débil        │
│    0.5 a 0.8 → Vegetación saludable    │
│    0.8 a 1.0 → Vegetación muy densa    │
│                                         │
│  Aplicación en este terreno:            │
│  Monitoreo de crecimiento y estrés     │
│  vegetal en [X.XX] hectáreas de        │
│  cultivo de [tipo]                      │
└─────────────────────────────────────────┘
```

**NDMI (Normalized Difference Moisture Index):**
```
┌─────────────────────────────────────────┐
│      ¿Qué es el NDMI?                   │
│                                         │
│  Índice de Humedad Normalizado         │
│                                         │
│  • Mide el contenido de agua en        │
│    la vegetación                        │
│                                         │
│  • Rango: -1 a +1                       │
│    -1 a 0.0  → Muy seco                │
│    0.0 a 0.3 → Estrés hídrico          │
│    0.3 a 0.6 → Humedad moderada        │
│    0.6 a 1.0 → Bien hidratado          │
│                                         │
│  Aplicación en este terreno:            │
│  Control de irrigación y detección     │
│  de estrés hídrico en [X.XX] ha        │
└─────────────────────────────────────────┘
```

**SAVI (Soil-Adjusted Vegetation Index):**
```
┌─────────────────────────────────────────┐
│      ¿Qué es el SAVI?                   │
│                                         │
│  Índice de Vegetación Ajustado         │
│  por Suelo                              │
│                                         │
│  • Similar al NDVI pero minimiza       │
│    la influencia del suelo expuesto    │
│                                         │
│  • Rango: -1 a +1                       │
│    Ideal para cultivos con suelo       │
│    visible o vegetación dispersa       │
│                                         │
│  Aplicación en este terreno:            │
│  Análisis de cobertura vegetal en      │
│  zonas con suelo expuesto              │
└─────────────────────────────────────────┘
```

---

### **ESCENA 3: ANÁLISIS COMPLETO DEL MOTOR** (6-8 segundos)
**Información a mostrar:**
- ✅ Análisis generado por el motor de informes PDF (Motor de analisis nuestro)
- ✅ Tendencias detectadas en el período completo
- ✅ Comportamiento estacional
- ✅ Zonas de alerta o mejora
- ✅ Conclusiones principales

**Fuente de datos:**
```python
# Obtener del último InformeGenerado de la parcela
ultimo_informe = InformeGenerado.objects.filter(
    parcela=parcela
).order_by('-fecha_generacion').first()

analisis_completo = ultimo_informe.contenido_json.get('analisis_ia', {}).get('analisis_general', '')
```

**Layout propuesto:**
```
┌─────────────────────────────────────────┐
│    ANÁLISIS INTEGRAL DEL PERÍODO        │
│                                         │
│  [Texto del motor de análisis Gemini]  │
│                                         │
│  Ejemplo:                               │
│  "Durante el período Feb 2024 - Feb    │
│  2025, la parcela mostró un            │
│  crecimiento vegetativo sostenido con  │
│  valores NDVI promedio de 0.68,        │
│  indicando buena salud general.        │
│                                         │
│  Se detectaron 3 períodos críticos:    │
│  • Mayo 2024: Descenso por estrés      │
│    hídrico (NDVI 0.42)                 │
│  • Agosto 2024: Recuperación gradual   │
│  • Diciembre 2024: Máximo vigor        │
│    (NDVI 0.81)                         │
│                                         │
│  La zona norte presentó valores        │
│  consistentemente más bajos (-12%)     │
│  sugiriendo problemas de drenaje."     │
└─────────────────────────────────────────┘
```

---

### **ESCENA 4-N: MAPAS MENSUALES** (2.5 segundos cada uno)
**Cambios importantes:**

#### ✅ **SI HAY IMAGEN SATELITAL:**
- Mostrar imagen satelital como está actualmente
- Overlay con información mensual
- Estadísticas del mes
- Comparación con mes anterior

#### ❌ **SI NO HAY IMAGEN (alta nubosidad):**
**NUEVO: Pantalla informativa en lugar de negro**

```
┌─────────────────────────────────────────┐
│                                         │
│           🌥️ ☁️ 🌧️                     │
│                                         │
│     IMAGEN NO DISPONIBLE                │
│                                         │
│  Mes: [Mes Año]                         │
│                                         │
│  Debido a alta nubosidad durante       │
│  este período (>70%), no fue posible   │
│  obtener imágenes satelitales de       │
│  calidad suficiente para el análisis.  │
│                                         │
│  La siguiente imagen disponible        │
│  corresponde a: [Próximo mes]          │
│                                         │
│           - EOSDA API -                 │
└─────────────────────────────────────────┘
```

**Condición de detección:**
```python
# Considerar imagen no disponible si:
# 1. URL de imagen es None/vacía
# 2. Nubosidad > 70%
# 3. Calidad de imagen marcada como "mala"

if not imagen_url or nubosidad > 0.7:
    # Generar escena de "imagen no disponible"
else:
    # Generar escena normal con mapa
```

---

### **ESCENA FINAL: RECOMENDACIONES** (5 segundos)
**Información a mostrar:**
- ✅ Recomendaciones del motor de informes (si existen)
- ✅ Formato bullet points
- ✅ Máximo 3-4 recomendaciones principales

**SI NO HAY RECOMENDACIONES:**
```
┌─────────────────────────────────────────┐
│         RESUMEN DEL ANÁLISIS            │
│                                         │
│  ✅ Análisis completado exitosamente    │
│                                         │
│  📊 Meses analizados: 13                │
│  📈 Promedio NDVI: 0.68                 │
│  🎯 Estado general: Saludable           │
│                                         │
│  Para obtener recomendaciones          │
│  personalizadas, genera un informe     │
│  completo desde el panel de control.   │
└─────────────────────────────────────────┘
```

---

### **ESCENA CIERRE** (3 segundos)
- ✅ Logo AgroTech
- ✅ Mensaje de cierre
- ✅ Información de contacto

---

## 🔧 CAMBIOS TÉCNICOS NECESARIOS

### 1. **Modificar `TimelineVideoExporterMultiScene`**

#### Nuevos métodos a crear:
```python
def _generate_cover_complete_scene(self, parcela_info, frames_data, indice, temp_dir, start_idx)
    """Portada completa con toda la información de la parcela"""

def _generate_index_explanation_scene(self, indice, parcela_info, temp_dir, start_idx)
    """Explicación educativa del índice (NDVI/NDMI/SAVI)"""

def _generate_full_analysis_scene(self, analisis_texto, indice, temp_dir, start_idx)
    """Análisis completo del motor de informes"""

def _generate_monthly_map_or_unavailable(self, frame_data, indice, temp_dir, start_idx)
    """Mapa mensual O pantalla de "imagen no disponible" """

def _generate_unavailable_image_scene(self, mes, año, nubosidad, temp_dir, start_idx)
    """Pantalla para meses sin imagen por nubosidad"""
```

#### Modificar método principal:
```python
def _generate_all_scenes(self, ...):
    """
    NUEVO ORDEN:
    1. Portada completa (6s)
    2. Explicación del índice (6s)
    3. Análisis completo del motor (6-8s)
    4. Mapas mensuales (2.5s c/u) o "no disponible"
    5. Recomendaciones o resumen (5s)
    6. Cierre (3s)
    """
```

### 2. **Actualizar `export_timeline()` en views.py**

Pasar información adicional al exportador:
```python
# En views.py::exportar_video_timeline
parcela_info = {
    'nombre': parcela.nombre,
    'centro_lat': parcela.geometria.centroid.y,
    'centro_lon': parcela.geometria.centroid.x,
    'area_hectareas': parcela.area_hectareas,
    'tipo_cultivo': parcela.tipo_cultivo,
    # ... más campos
}

# Obtener análisis del último informe
ultimo_informe = InformeGenerado.objects.filter(
    parcela=parcela
).order_by('-fecha_generacion').first()

analisis_completo = None
recomendaciones = None

if ultimo_informe:
    analisis_completo = ultimo_informe.contenido_json.get('analisis_ia', {}).get('analisis_general')
    recomendaciones = ultimo_informe.contenido_json.get('recomendaciones', [])
```

### 3. **Crear helpers para contenido educativo**

Nuevo archivo: `informes/exporters/video_content_helpers.py`
```python
INDICE_EXPLICACIONES = {
    'ndvi': {
        'nombre_completo': 'Índice de Vegetación Normalizado',
        'nombre_ingles': 'Normalized Difference Vegetation Index',
        'descripcion_corta': 'Mide la salud y vigor de las plantas',
        'descripcion_larga': 'Utiliza luz infrarroja para detectar...',
        'rangos': [
            {'min': -1.0, 'max': 0.2, 'label': 'Sin vegetación', 'color': '#8B4513'},
            {'min': 0.2, 'max': 0.5, 'label': 'Vegetación débil', 'color': '#FFD700'},
            {'min': 0.5, 'max': 0.8, 'label': 'Saludable', 'color': '#90EE90'},
            {'min': 0.8, 'max': 1.0, 'label': 'Muy densa', 'color': '#006400'},
        ],
        'aplicacion': 'Monitoreo de crecimiento y estrés vegetal'
    },
    'ndmi': {
        # Similar estructura...
    },
    'savi': {
        # Similar estructura...
    }
}

def generar_texto_explicacion_indice(indice: str, parcela_info: dict) -> str:
    """Genera texto educativo del índice aplicado al terreno"""

def detectar_proximo_mes_disponible(frames_data: list, current_index: int) -> str:
    """Encuentra el próximo mes con imagen disponible"""
```

### 4. **Actualizar duraciones**

```python
# Nuevas duraciones
COVER_COMPLETE_DURATION = 4.0      # Era 3.0
INDEX_EXPLANATION_DURATION = 5.0    # NUEVO
FULL_ANALYSIS_DURATION = 7.0       # Era parte de analysis
MONTHLY_MAP_DURATION = 2.5          # Sin cambios
UNAVAILABLE_IMAGE_DURATION = 2.5    # NUEVO
RECOMMENDATIONS_DURATION = 5.0      # Sin cambios
CLOSING_DURATION = 3.0              # Sin cambios
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Fase 1: Preparación
- [ ] Crear `video_content_helpers.py` con explicaciones de índices
- [ ] Documentar estructura de datos necesaria
- [ ] Actualizar modelos si es necesario (verificar campos disponibles)

### Fase 2: Portada Completa
- [ ] Implementar `_generate_cover_complete_scene()`
- [ ] Extraer coordenadas del centroide de la geometría
- [ ] Formatear información de la parcela
- [ ] Probar con parcela #6

### Fase 3: Explicación del Índice
- [ ] Implementar `_generate_index_explanation_scene()`
- [ ] Crear layouts para NDVI, NDMI, SAVI
- [ ] Añadir rangos de valores con colores
- [ ] Texto de aplicación específica al terreno

### Fase 4: Análisis Completo del Motor
- [ ] Implementar `_generate_full_analysis_scene()`
- [ ] Integrar con `InformeGenerado.contenido_json`
- [ ] Formatear texto largo con word wrap
- [ ] Manejo de casos sin informe disponible

### Fase 5: Imágenes No Disponibles
- [ ] Implementar `_generate_unavailable_image_scene()`
- [ ] Lógica de detección (nubosidad > 70%)
- [ ] Pantalla informativa con iconos de clima
- [ ] Detectar próximo mes disponible

### Fase 6: Integración
- [ ] Modificar `_generate_all_scenes()` con nuevo orden
- [ ] Actualizar `export_timeline()` en views.py
- [ ] Pasar `parcela_info` completa
- [ ] Pasar `analisis_completo` y `recomendaciones`

### Fase 7: Testing
- [ ] Test con parcela #6 (tiene datos completos)
- [ ] Test con parcela que tenga meses sin imágenes
- [ ] Verificar duraciones totales
- [ ] Verificar calidad visual de todas las escenas

### Fase 8: Documentación
- [ ] Actualizar docstrings
- [ ] Crear ejemplos de uso
- [ ] Documentar nuevos parámetros
- [ ] Guía de troubleshooting

---

## 🎯 RESULTADO ESPERADO

### Video mejorado con:
✅ **Portada profesional** con info completa de la parcela  
✅ **Educación al usuario** sobre el índice analizado  
✅ **Análisis profundo** del motor Gemini AI  
✅ **Manejo elegante** de meses sin datos (no más pantallas negras)  
✅ **Experiencia completa** y profesional  

### Duración estimada total:
```
Portada:           4.0s
Explicación:       5.0s
Análisis:          7.0s
Mapas (13 meses):  32.5s (13 × 2.5s)
Recomendaciones:   5.0s
Cierre:            3.0s
─────────────────────
TOTAL:            ~56.5 segundos
```

### Tamaño estimado:
- Resolución: 1920×1080 @ 24fps
- Tamaño aprox: 1.2 - 1.5 MB (vs 0.66 MB actual)

---

## 🚀 PRÓXIMOS PASOS

1. **Revisar y aprobar este plan**
2. **Implementar fase por fase** (8 fases)
3. **Testing incremental** después de cada fase
4. **Generar video final** con parcela #6
5. **Documentar cambios** en markdown

---

**¿Procedo con la implementación? ¿Algún ajuste al plan?** 🎬
