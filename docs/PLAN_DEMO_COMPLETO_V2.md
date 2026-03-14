# 🌾 PLAN COMPLETO: Demo Link Único - V2 (Actualizado)

## 📋 Estado Actual — ¿Qué hay hecho y qué falta?

### ✅ COMPLETADO
| # | Componente | Archivo | Estado |
|---|-----------|---------|--------|
| 1 | Modelos (DemoToken + DemoLead) | `informes/models_demo.py` | ✅ Migrado |
| 2 | Admin (tokens, leads, WhatsApp) | `informes/admin_demo.py` | ✅ Listo |
| 3 | URLs aisladas | `informes/urls_demo.py` | ✅ 4 endpoints |
| 4 | Vistas (landing, registrar, guardar-parcela, resultado) | `informes/views_demo.py` | ⚠️ Parcial* |
| 5 | Template: Landing (formulario) | `templates/informes/demo/landing.html` | ✅ Mobile-first |
| 6 | Template: Mapa (Leaflet draw) | `templates/informes/demo/mapa.html` | ✅ Mobile-first |
| 7 | Registro en urls.py | `agrotech_historico/urls.py` | ✅ Incluido |

> *`views_demo.py`: La lógica de `_obtener_imagenes_demo()` solo obtiene stats, NO genera
> imágenes PNG visuales. Retorna `'datos_disponibles'` como placeholder.

### ❌ PENDIENTE — Por construir
| # | Componente | Archivo | Prioridad |
|---|-----------|---------|-----------|
| 8 | Template: `resultado.html` | `templates/informes/demo/resultado.html` | ✅ HECHO |
| 9 | Template: `expirado.html` | `templates/informes/demo/expirado.html` | ✅ HECHO |
| 10 | Imágenes demo: generarlas con Matplotlib | `views_demo.py` → `_generar_imagenes_heatmap()` | ✅ HECHO |
| 11 | Servir imágenes desde media/demo/ | `views_demo.py` | ✅ HECHO |
| 12 | Número WhatsApp real en settings | `views_demo.py` + `settings.py` | ✅ HECHO |
| 13 | Test del flujo completo end-to-end | `tests/test_demo_flujo.py` | ✅ HECHO (10/10) |
| 14 | Actualizar plan con checkboxes | `docs/PLAN_DEMO_COMPLETO_V2.md` | ✅ HECHO |

---

## 🎯 Plan de Ejecución — Paso a Paso

### Paso 8: Template `resultado.html` (3 imágenes + CTA)
**Objetivo:** Pantalla mobile-first que muestra 3 tarjetas con imágenes satelitales
(NDVI, NDMI, SAVI), explicaciones simples, y un CTA grande de WhatsApp.

**Diseño:**
- Header con nombre del usuario y datos de la parcela (área, ubicación)
- 3 cards con: icono + título + imagen satelital + texto explicativo
- Card final: CTA para contratar (botón WhatsApp verde)
- Footer: metadata del satélite (Sentinel-2, fecha, nubosidad)
- Marca como `usado` al cargar (token no reutilizable)

**Textos explicativos (no técnicos, para agricultor):**
- **NDVI (🌿 Salud del Cultivo):** "Muestra qué tan verde y saludable está tu cultivo.
  Verde intenso = plantas vigorosas. Amarillo/rojo = zonas con posibles problemas."
- **NDMI (💧 Nivel de Humedad):** "Indica la cantidad de agua en tus plantas y suelo.
  Azul = buena hidratación. Naranja/rojo = estrés hídrico (falta de agua)."
- **SAVI (🌱 Vegetación del Suelo):** "Análisis especializado para suelos con poca
  cobertura. Detecta vegetación real separándola del suelo expuesto."

### Paso 9: Template `expirado.html`
**Objetivo:** Pantalla simple para links ya usados/expirados.
- Mensaje claro de que el link ya fue utilizado
- Botón WhatsApp para contactar si quiere contratar
- Sin acceso a datos, imágenes ni información del lead

### Paso 10: Generar imágenes de demo con Matplotlib
**Problema actual:** EOSDA Statistics API retorna datos numéricos (promedios, min, max),
NO imágenes PNG visuales. La Field Imagery API requiere field_id + view_id y tiene
permisos limitados.

**Solución pragmática:** Generar mapas de calor (heatmaps) con Matplotlib usando los
datos estadísticos de EOSDA. Esto es válido porque:
1. Los datos SON reales de EOSDA (satélite Sentinel-2)
2. El heatmap muestra el valor promedio del índice sobre la forma de la parcela
3. Es visualmente atractivo y entendible para el agricultor
4. NO requiere Field Imagery API (ahorra requests y evita 403)

**Implementación:**
```python
def _generar_imagen_indice_demo(geometria_geojson, indice, valor_promedio, lead):
    """
    Genera una imagen PNG tipo heatmap del índice sobre la parcela.
    - Usa matplotlib con backend 'Agg' (thread-safe)
    - Dibuja el polígono de la parcela como máscara
    - Colorea con paleta apropiada según índice
    - Guarda en media/demo/<token_hex>_<indice>.png
    - Retorna la ruta relativa para servir
    """
```

**Paletas de color por índice:**
- NDVI: RdYlGn (rojo → amarillo → verde)
- NDMI: RdBu (rojo → blanco → azul)
- SAVI: YlGn (amarillo → verde)

### Paso 11: Servir imágenes desde media/
- Guardar PNGs en `media/demo/<token_hex[:8]>/ndvi.png`
- Referenciar en `DemoLead.ndvi_url`, `ndmi_url`, `savi_url`
- Servir via Django/WhiteNoise en producción
- Limpiar imágenes de tokens expirados (management command futuro)

### Paso 12: Configurar WhatsApp real
- Usar `settings.ADMIN_WHATSAPP` (ya existe: '+57 322 308 8873')
- Limpiar formato para URL: `573223088873`
- Mensaje pre-llenado: "Hola, vi mi demo satelital de [X] ha en [municipio] y
  me interesa el informe completo."

### Paso 13: Test end-to-end
Script standalone Django que:
1. Crea un DemoToken
2. Simula registro (POST a /demo/<uuid>/registrar/)
3. Simula dibujo de parcela (POST a /demo/<uuid>/guardar-parcela/)
4. Verifica que se generaron 3 imágenes
5. Verifica que demo_resultado renderiza
6. Verifica que token queda como 'usado'
7. Verifica que segundo acceso muestra 'expirado'

---

## 🔧 Orden de Implementación

```
Paso 10: _generar_imagen_indice_demo() en views_demo.py    ← PRIMERO (sin esto no hay resultado)
Paso 11: Guardar/servir imágenes desde media/demo/          ← Va junto con 10
Paso 8:  resultado.html (template con imágenes reales)       ← Necesita las imágenes
Paso 9:  expirado.html (template simple)                     ← Independiente
Paso 12: WhatsApp real en todo el flujo                      ← Config rápida
Paso 13: Test end-to-end                                     ← Validación final
```

---

## 📐 Decisiones Técnicas

### ¿Por qué Matplotlib y no Field Imagery API?
1. Field Imagery API puede dar 403 si el plan no lo incluye
2. Requiere field_id registrado + view_id específico (más requests)
3. Para una demo de 3 imágenes, un heatmap generado localmente es suficiente
4. Los DATOS son 100% reales (de Statistics API con geometría)
5. El heatmap es más explicativo visualmente que una imagen cruda de satélite

### ¿Por qué no guardar las imágenes en DemoLead como BinaryField?
1. BinaryField no es servible por URL sin vista adicional
2. media/ se sirve directamente con WhiteNoise/nginx
3. Las URLs son estables y funcionan en el template con `<img src=>`
4. Más fácil de debuggear (puedes abrir el PNG manualmente)

### ¿Qué pasa si EOSDA no retorna datos?
1. Se muestra resultado con mensaje: "No encontramos imágenes con buena visibilidad"
2. Se ofrece texto explicativo sobre cobertura de nubes
3. Se muestra el CTA de WhatsApp igualmente
4. El token se marca como usado (no se puede reintentar indefinidamente)

### ¿Qué pasa si la parcela es muy pequeña (< 1 ha)?
1. Sentinel-2 tiene resolución de 10m/pixel
2. Parcelas < 1 ha pueden no tener suficientes píxeles
3. El sistema acepta cualquier tamaño pero advierte en el resultado
4. El heatmap se genera igualmente (es basado en promedios)

---

## 🚀 Empezamos: Paso 10 → 11 → 8 → 9 → 12 → 13
