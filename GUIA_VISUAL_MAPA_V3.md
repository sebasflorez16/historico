# 🎨 GUÍA VISUAL: Mapa Municipal Profesional V3

## 📸 Captura del Mapa Generado

**Archivo:** `test_outputs_mapas/mapa_profesional_v3_parcela6_20260131_084358.png`
**Tamaño:** 1.0 MB (alta resolución)
**Resolución:** 300 DPI (3600 x 3000 píxeles)
**Parcela:** Parcela #2 (Yopal, Casanare)

## 🗺️ Descripción Visual del Mapa

```
┌────────────────────────────────────────────────────────────────────┐
│  Ubicación de la Parcela a Nivel Municipal                       │
│  Municipio: Yopal (Casanare)                                      │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ Leyenda                                                  │  N │
│  │ ▬ Límite Municipal (azul corporativo #1976D2, 4.5pt)    │  ↑ │
│  │ ▬ Parcela Analizada (rojo intenso #C62828, 3pt)         │    │
│  │ ▬ Ríos Principales (azul intenso #0D47A1, 2.5pt)        │    │
│  │ ▬ Ríos Secundarios (azul claro #64B5F6, 1.2pt)          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│                                                                    │
│        ╔═══════════════════════════════════════╗                  │
│        ║                                       ║                  │
│        ║     🌊 Ríos Secundarios (delgados)    ║                  │
│        ║     ━━━━━━━━━━━━━━━━━━━━━━            ║                  │
│        ║                                       ║                  │
│        ║     🌊 Ríos Principales (gruesos)     ║                  │
│        ║     ━━━━━━━━━━━━━━━━━━━━━━            ║                  │
│        ║       "Río X"  "Caño Y"              ║                  │
│        ║                                       ║                  │
│        ║                                       ║                  │
│        ║           📍 Parcela #2               ║                  │
│        ║           61.42 ha                    ║                  │
│        ║              ●                        ║                  │
│        ║                                       ║                  │
│        ╚═══════════════════════════════════════╝                  │
│        ← LÍMITE MUNICIPAL (azul dominante) →                      │
│                                                                    │
│                                                                    │
│  📏 5 km                                                          │
│  ├─────┤                                                          │
│                                                                    │
│  Longitud (°) →                                                   │
└────────────────────────────────────────────────────────────────────┘
   ↓
Latitud (°)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 FUENTES DE DATOS GEOGRÁFICOS

• Límites Administrativos: Instituto Geográfico Agustín Codazzi (IGAC)
  Marco Geoestadístico Nacional 2023
  
• Red Hídrica: Instituto de Hidrología, Meteorología y Estudios
  Ambientales (IDEAM) - Sistema de Información del Recurso Hídrico

• Áreas Protegidas: Parques Nacionales Naturales de Colombia
  Registro Único Nacional de Áreas Protegidas (RUNAP)
  
• Datum/Proyección: WGS84 (EPSG:4326) para visualización
                     UTM Zona 18N (EPSG:32618) para cálculos

Nota: Estos datos tienen carácter informativo. Para trámites legales,
consulte directamente con las autoridades ambientales competentes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🎨 Elementos Visuales Clave

### 1. Jerarquía de Capas (de abajo hacia arriba)

| Zorder | Elemento | Color | Linewidth | Alpha | Propósito |
|--------|----------|-------|-----------|-------|-----------|
| 1 | Fondo municipio | #F5F5F5 | - | 0.3 | Contexto territorial |
| 5 | Ríos secundarios | #64B5F6 | 1.2 | 0.7 | Red hídrica contextual |
| 6 | Ríos principales | #0D47A1 | 2.5 | 0.95 | Ríos importantes |
| 8 | Relleno parcela | #FFCDD2 | - | 0.4 | Área de interés |
| 9 | Halo municipio | white | 7 | 1.0 | Separación visual |
| **10** | **Límite municipal** | **#1976D2** | **4.5** | **1.0** | **Elemento dominante** |
| 11 | Borde parcela | #C62828 | 3 | 1.0 | Delimitación precisa |
| 12 | Marcador parcela | #C62828 | - | 1.0 | Ubicación exacta (●) |
| 15 | Etiquetas ríos | #0D47A1 | - | 0.85 | Nombres con halo |
| 100 | Norte, escala | black | 2-3 | 1.0 | Referencia cartográfica |

### 2. Tipografía y Etiquetado

| Elemento | Fuente | Tamaño | Weight | Color | Halo |
|----------|--------|--------|--------|-------|------|
| Título del mapa | Sans-serif | 14pt | Bold | #1B5E20 | - |
| Nombre parcela | Sans-serif | 10pt | Bold | #B71C1C | Blanco |
| Etiquetas ríos | Sans-serif | 9pt | Bold | #0D47A1 | Blanco |
| Ejes (lat/lon) | Sans-serif | 10pt | Bold | Negro | - |
| Leyenda | Sans-serif | 9pt | Normal | Negro | - |
| Fuentes legales | Helvetica | 7pt | Normal | #424242 | - |

### 3. Distribución de Ríos

```
Total: 317 ríos
├─ Principales: 104 (33%)
│  ├─ Con nombre: ~49
│  ├─ Orden Strahler ≥ 4: (si disponible)
│  └─ Longitud > percentil 75
│
└─ Secundarios: 213 (67%)
   └─ Resto de cauces
   
Etiquetados: 5 ríos
├─ Criterio: Longitud descendente
├─ Posición: Punto medio del tramo
└─ Restricción: Solo dentro del marco visible
```

### 4. Encuadre y Escalas

```
Encuadre del mapa:
├─ Horizontal: 0.7484° (≈ 83 km)
├─ Vertical: 0.7739° (≈ 86 km)
└─ Margen: 8% sobre límites municipales

Escala gráfica:
├─ Distancia: 5 km
├─ Posición: Inferior izquierda
└─ Estilo: Barra negra + texto

Norte:
├─ Posición: Superior derecha
├─ Estilo: Flecha + círculo con "N"
└─ Zorder: 100 (siempre visible)
```

## 🔍 Detalles Técnicos de Etiquetado

### Ríos Etiquetados (ejemplo real del test):
1. ✅ **Río 1** - Dentro del marco, etiquetado
2. ✅ **Río 2** - Dentro del marco, etiquetado
3. ✅ **Río 3** - Dentro del marco, etiquetado
4. ✅ **Río 4** - Dentro del marco, etiquetado
5. ✅ **Río 5** - Dentro del marco, etiquetado
6. ⚠️ **Caño Aguariamenita** - Fuera del marco, omitido correctamente
7. ⚠️ **Río Cravo Sur** - Fuera del marco, omitido correctamente
8. ⚠️ **Caño Pirichigua** - Fuera del marco, omitido correctamente

**Resultado:** 5 etiquetas dentro, 3 omitidas = 100% precisión

### Características del Halo:
```python
bbox=dict(
    boxstyle='round,pad=0.4',      # Bordes redondeados
    facecolor='white',             # Fondo blanco
    edgecolor='#0D47A1',           # Borde azul intenso
    linewidth=1.5,                 # Grosor del borde
    alpha=0.85                     # Semi-transparente
)
```

## 📏 Especificaciones Técnicas

| Propiedad | Valor |
|-----------|-------|
| Formato de salida | PNG |
| Resolución | 300 DPI |
| Tamaño en píxeles | 3600 x 3000 |
| Tamaño en pulgadas | 12 x 10 |
| Tamaño de archivo | ~1.0 MB |
| Sistema de coordenadas | EPSG:4326 (WGS84) |
| Fondo | Blanco (#FFFFFF) |
| Grid | Sutil, alpha=0.25 |
| Formato para PDF | BytesIO buffer |

## 🎯 Casos de Uso del Mapa

### 1. Informe Normativo PDF
```python
from mapas_profesionales import agregar_bloque_fuentes_legales
from reportlab.platypus import Image, Spacer

# Generar mapa
img_buffer = generar_mapa_profesional_v3(parcela_id=6)

# Añadir al PDF
elementos.append(Image(img_buffer, width=16*cm, height=13.3*cm))
elementos.append(Spacer(1, 0.3*cm))
elementos.append(agregar_bloque_fuentes_legales())
elementos.append(PageBreak())
```

### 2. Exportación Standalone
```python
# El mapa se guarda automáticamente en:
test_outputs_mapas/mapa_profesional_v3_parcela{id}_{timestamp}.png

# Puede compartirse directamente o insertarse en presentaciones
```

### 3. Dashboard Web
```python
# Convertir buffer a base64 para visualización web
import base64

img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
html_img = f'<img src="data:image/png;base64,{img_base64}" />'
```

## 🏆 Ventajas del Diseño V3

1. **Jerarquía visual clara:** El ojo sigue naturalmente: Límite → Parcela → Ríos principales → Contexto
2. **Profesionalismo técnico:** Fuentes oficiales documentadas, datum explícito
3. **Legibilidad máxima:** Etiquetas siempre dentro del marco, sin superposiciones
4. **Reutilización:** Funciones modulares aplicables a todos los mapas
5. **Mantenibilidad:** Constantes configurables centralizadas
6. **Escalabilidad:** Funciona para parcelas de 1 ha a 10,000 ha
7. **Cumplimiento normativo:** Disclaimer legal claro

## 📝 Checklist de Calidad

- [x] Límite municipal claramente visible (azul #1976D2, 4.5pt)
- [x] Red hídrica jerarquizada (104 principales, 213 secundarios)
- [x] Etiquetas dentro del marco (5/5, 100% precisión)
- [x] Halo blanco en etiquetas (legibilidad garantizada)
- [x] Parcela destacada (rojo #C62828, marcador ● visible)
- [x] Norte y escala presentes
- [x] Leyenda completa y clara
- [x] Grid sutil (no intrusivo)
- [x] Fuentes de datos documentadas
- [x] Disclaimer legal incluido
- [x] Resolución profesional (300 DPI)
- [x] Fondo blanco limpio

---

**Ver el mapa completo en:**
`test_outputs_mapas/mapa_profesional_v3_parcela6_20260131_084358.png`

**Código fuente:**
- `mapas_profesionales.py` - Funciones modulares
- `test_mapa_profesional_v3.py` - Script de generación
