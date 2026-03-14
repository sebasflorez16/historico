# 🌾 PLAN: AgroTech Demo - Link Único de Prueba

## 📋 Resumen Ejecutivo

Sistema de demo satelital para conversión comercial por WhatsApp.
Un link único permite al prospecto dibujar su parcela y ver 3 imágenes satelitales
(NDVI, NDMI, SAVI) con explicación breve. Después de usar el link, expira.

**Objetivo:** Funnel de conversión → WhatsApp → Demo → Cierre de venta

---

## 🔒 Principios de Seguridad y Aislamiento

| Principio | Implementación |
|-----------|----------------|
| **Sin autenticación** | Acceso solo por token UUID (no adivinable) |
| **Un solo uso** | Token se marca como `usado` al ver resultados |
| **Expiración** | 7 días por defecto (configurable al crear) |
| **Aislamiento total** | Modelos separados (`DemoToken`, `DemoLead`), NO toca `Parcela` ni `IndiceMensual` |
| **Sin acceso al sistema** | URLs `/demo/` no comparten vistas, templates ni lógica con `/informes/` |
| **EOSDA limitado** | Solo 3 imágenes recientes, sin histórico, sin PDF |
| **Parcela guardada** | Se guarda en `DemoLead` para reutilizar si contrata |

---

## 📱 Diseño Mobile-First (WhatsApp → Celular)

### Flujo de pantallas:

```
Pantalla 1: FORMULARIO DE REGISTRO
┌──────────────────────────┐
│  🌾 AgroTech              │
│  Análisis Satelital       │
│                           │
│  Complete sus datos para  │
│  acceder a su demo:       │
│                           │
│  Nombre completo *        │
│  [________________]       │
│                           │
│  Teléfono/WhatsApp *      │
│  [________________]       │
│                           │
│  Email (opcional)         │
│  [________________]       │
│                           │
│  Departamento             │
│  [▼ Seleccionar_____]     │
│                           │
│  Municipio                │
│  [________________]       │
│                           │
│  [ Continuar →    ]       │
└──────────────────────────┘

Pantalla 2: MAPA (dibujar parcela)
┌──────────────────────────┐
│  Dibuja tu parcela 🗺️     │
│                           │
│  ┌─────────────────────┐  │
│  │                     │  │
│  │  MAPA LEAFLET       │  │
│  │  (70% pantalla)     │  │
│  │                     │  │
│  │  [🔍 Buscar lugar]  │  │
│  │                     │  │
│  └─────────────────────┘  │
│                           │
│  📐 Área: 45.2 ha         │
│                           │
│  ℹ️ Toca los vértices      │
│  de tu parcela en el mapa │
│                           │
│  [ Ver Análisis → ]       │
└──────────────────────────┘

Pantalla 3: RESULTADOS
┌──────────────────────────┐
│  🛰️ Tu Análisis Satelital │
│                           │
│  📐 45.2 ha │ 📅 8 mar 2026│
│                           │
│  ┌── 🌿 NDVI ──────────┐ │
│  │  Vigor Vegetativo     │ │
│  │  [IMAGEN SATELITAL]   │ │
│  │  Mide la salud de     │ │
│  │  tus cultivos...      │ │
│  └───────────────────────┘ │
│                           │
│  ┌── 💧 NDMI ──────────┐ │
│  │  Contenido Hídrico    │ │
│  │  [IMAGEN SATELITAL]   │ │
│  │  Detecta el nivel     │ │
│  │  de humedad...        │ │
│  └───────────────────────┘ │
│                           │
│  ┌── 🌱 SAVI ──────────┐ │
│  │  Vegetación Ajustada  │ │
│  │  [IMAGEN SATELITAL]   │ │
│  │  Ideal para suelos    │ │
│  │  con baja cobertura...│ │
│  └───────────────────────┘ │
│                           │
│  ┌──────────────────────┐ │
│  │ 📊 Esto es solo una   │ │
│  │ captura del momento.  │ │
│  │                       │ │
│  │ Con el Informe        │ │
│  │ Histórico, nuestro    │ │
│  │ motor analiza MES A   │ │
│  │ MES durante 12 a 24   │ │
│  │ meses, detectando:    │ │
│  │                       │ │
│  │ ✅ Tendencias          │ │
│  │ ✅ Alertas tempranas   │ │
│  │ ✅ Estrés hídrico      │ │
│  │ ✅ Recomendaciones IA  │ │
│  │                       │ │
│  │ [ 📱 Contactar por   ]│ │
│  │ [    WhatsApp →      ]│ │
│  └──────────────────────┘ │
│                           │
│  🛰️ Imagen: Sentinel-2    │
│  📅 Capturada: 8 mar 2026 │
│  ☁️ Nubosidad: 12%        │
└──────────────────────────┘

Pantalla 4: EXPIRADO
┌──────────────────────────┐
│  🌾 AgroTech              │
│                           │
│  ⏰ Este link de demo     │
│  ya fue utilizado.        │
│                           │
│  Si desea contratar el    │
│  servicio completo:       │
│                           │
│  [ 📱 WhatsApp →    ]     │
│                           │
└──────────────────────────┘
```

---

## 🛰️ Manejo de Imágenes Satelitales

### Comunicación al usuario:
- Sentinel-2 pasa cada ~5 días
- Se selecciona la mejor imagen de los últimos 90 días
- Filtro de nubosidad < 30%
- Se muestra fecha real de la imagen y porcentaje de nubosidad

### Texto en el template:
> 🛰️ Imagen capturada por satélite Sentinel-2 el [FECHA]
> Nubosidad: [X]% — Se selecciona automáticamente la imagen más reciente
> con buena visibilidad (menos del 30% de nubes).

### Si no hay imágenes disponibles:
> ☁️ No encontramos imágenes con buena visibilidad en los últimos 90 días.
> Esto es normal en zonas con alta cobertura de nubes.
> Contacta a nuestro equipo para una evaluación personalizada.

---

## 🗂️ Archivos a Crear

```
informes/
├── models_demo.py          # DemoToken + DemoLead (NUEVO)
├── admin_demo.py           # Admin con botón WhatsApp (NUEVO)
├── views_demo.py           # 4 vistas aisladas (NUEVO)
├── urls_demo.py            # 4 URLs bajo /demo/ (NUEVO)

templates/informes/demo/
├── landing.html            # Formulario de registro (NUEVO)
├── mapa.html               # Mapa Leaflet para dibujar (NUEVO)
├── resultado.html          # 3 imágenes + CTA (NUEVO)
├── expirado.html           # Link expirado + WhatsApp (NUEVO)

agrotech_historico/
├── urls.py                 # + include('informes.urls_demo') (EDITAR)
```

---

## 🔧 Archivos a Editar

| Archivo | Cambio |
|---------|--------|
| `agrotech_historico/urls.py` | Agregar `path('demo/', include('informes.urls_demo'))` |
| `informes/admin.py` | Agregar import de `admin_demo` al final |

---

## 🧪 Plan de Testing Paso a Paso

| # | Test | Verificación |
|---|------|-------------|
| 1 | Crear modelos | `makemigrations` + `migrate` sin errores |
| 2 | Test de modelos | Script que crea token, registra datos, crea lead, marca como usado |
| 3 | Admin funciona | Crear token desde Django Admin, copiar link |
| 4 | Landing carga | Abrir link → ver formulario de registro |
| 5 | Formulario funciona | Llenar datos → redirige a mapa |
| 6 | Mapa carga | Ver mapa Leaflet, dibujar polígono |
| 7 | Guardar parcela | Clic "Ver Análisis" → guardar geometría en DemoLead |
| 8 | EOSDA responde | Obtener 3 imágenes (NDVI, NDMI, SAVI) |
| 9 | Resultados muestran | Ver 3 imágenes con explicación + CTA |
| 10 | Token expira | Volver a abrir link → ver pantalla "expirado" |
| 11 | Responsive móvil | Probar en Chrome DevTools (iPhone, Android) |
| 12 | Deploy Railway | Push → verificar en URL pública |

---

## ⏱️ Estimación por Paso

| Paso | Tarea | Tiempo |
|------|-------|--------|
| 1 | Modelos + Migración | 5 min |
| 2 | Admin | 5 min |
| 3 | URLs | 3 min |
| 4 | Views | 15 min |
| 5 | Template: Landing (formulario) | 15 min |
| 6 | Template: Mapa (Leaflet) | 20 min |
| 7 | Template: Resultado (3 imágenes) | 20 min |
| 8 | Template: Expirado | 5 min |
| 9 | Integración EOSDA demo | 15 min |
| 10 | Testing completo | 15 min |
| 11 | Deploy a Railway | 5 min |
| **TOTAL** | | **~2 horas** |

---

## 📊 Tu Flujo Comercial

```
1. Cliente te escribe por WhatsApp
2. Tú entras al Django Admin → Tokens de Demo → "Agregar"
3. Llenas: nombre, teléfono, notas comerciales
4. Copias el link generado (botón "Enviar por WhatsApp")
5. El cliente abre, completa formulario, dibuja parcela, ve imágenes
6. Tú ves en Admin:
   - Lead registrado con geometría guardada
   - Área en hectáreas calculada
   - Departamento/municipio
   - Estado: ✅ Usado
7. Si cierra la venta:
   - Marcas "Convertido a cliente"
   - Creas la Parcela real usando la misma geometría
   - Generas el informe histórico completo
```

---

## 🚀 Estado del Desarrollo

- [x] Paso 1: Modelos + Migración
- [x] Paso 2: Admin
- [x] Paso 3: URLs
- [x] Paso 4: Views
- [x] Paso 5: Template Landing
- [x] Paso 6: Template Mapa
- [x] Paso 7: Template Resultado
- [x] Paso 8: Template Expirado
- [x] Paso 9: Integración EOSDA (heatmaps Matplotlib con datos reales)
- [x] Paso 10: Testing (10/10 tests end-to-end)
- [x] Paso 11: Panel de Demos en Dashboard (crear, detalle, conversión, WhatsApp, eliminar)
- [x] Paso 12: Widget de demos en dashboard principal
- [x] Paso 13: Conversión Demo → Parcela real (reutiliza geometría)
- [x] Paso 14: Tests del Panel (14/14 tests)
- [x] Paso 14b: Flujo profesional WhatsApp/Email con vista previa (8/8 tests)
- [ ] Paso 15: Deploy Railway
