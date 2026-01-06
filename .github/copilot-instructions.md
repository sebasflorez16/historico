# AgroTech Histórico - Instrucciones para Agentes IA 🌾

Sistema Django completo de análisis satelital agrícola con integración EOSDA API, Google Gemini AI y generación automatizada de informes PDF.

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico
- **Backend:** Django 4.2.7 + GeoDjango (PostGIS)
- **Base de datos:** PostgreSQL 15+ con extensión PostGIS para datos geoespaciales
- **APIs externas:** EOSDA API (datos satelitales), Google Gemini AI (análisis), OpenMeteo (clima)
- **PDF Generation:** ReportLab + Matplotlib/Seaborn
- **Deploy:** Railway (producción), SQLite (desarrollo)

### Estructura de Directorios
```
informes/                      # App principal Django
├── models.py                  # Parcela, IndiceMensual, InformeGenerado
├── models_clientes.py         # ClienteInvitacion, RegistroEconomico
├── views.py                   # Vistas principales (2081 líneas)
├── views_eliminacion.py       # Eliminación segura de recursos
├── generador_pdf.py           # GeneradorPDFProfesional (1725 líneas)
├── services/                  # Servicios externos
│   ├── eosda_api.py          # EosdaAPIService - datos satelitales
│   ├── gemini_service.py     # GeminiService - análisis IA
│   ├── weather_service.py    # OpenMeteoWeatherService
│   └── email_service.py      # Envío de invitaciones
├── analizadores/             # Procesadores de índices
│   ├── ndvi_analyzer.py      # AnalizadorNDVI
│   ├── ndmi_analyzer.py      # AnalizadorNDMI
│   ├── savi_analyzer.py      # AnalizadorSAVI
│   ├── tendencias_analyzer.py # DetectorTendencias
│   └── recomendaciones_engine.py
└── processors/
    └── timeline_processor.py  # TimelineProcessor para visualización

tests/                         # Scripts de prueba independientes
scripts/                       # Utilidades y mantenimiento
docs/                          # Documentación completa
```

## 🔑 Conceptos Clave del Dominio

### Flujo de Datos Satelitales (EOSDA → DB → Análisis → PDF)
1. **Sincronización EOSDA:** `eosda_api.py` obtiene imágenes satelitales (NDVI, NDMI, SAVI) usando Field Management API
2. **Almacenamiento PostGIS:** Modelo `Parcela` con campo `geometria = PolygonField(srid=4326)` para consultas geoespaciales
3. **Caché de análisis:** Modelo `AnalisisImagen` cachea resultados Gemini por 30 días (campo `hash_imagen`)
4. **Generación PDF:** `GeneradorPDFProfesional` combina gráficos, mapas y análisis IA en reporte único

### Sistema de Cuotas Gemini
- **Límite diario:** 3 informes/día por usuario (modelo `InformeGenerado.puede_generar_informe()`)
- **Tipos de análisis:** 'rapido' (10 imágenes) vs 'completo' (30 imágenes)
- **Tracking:** Campos `tokens_consumidos`, `peticiones_api`, `num_imagenes_analizadas`

### Análisis Espacialmente Consciente
- **Coordenadas reales:** Cada imagen tiene `bbox [min_lat, min_lon, max_lat, max_lon]` y `centroide`
- **Referencias geográficas:** Gemini genera recomendaciones por zona ("zona norte", "zona sur", etc.)
- **Metadatos EOSDA:** Campos `satelite_imagen`, `resolucion_imagen`, `nubosidad_imagen` en `IndiceMensual`

## 🚀 Flujos de Trabajo Críticos

### Desarrollo Local
```bash
# Setup inicial (requiere PostgreSQL + PostGIS instalado)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configurar EOSDA_API_KEY, GEMINI_API_KEY

# Migraciones PostGIS
python manage.py makemigrations
python manage.py migrate

# Servidor de desarrollo
python manage.py runserver
```

### Testing
```bash
# Los tests NO usan pytest - son scripts standalone Django
python tests/test_gemini_service.py      # Test de análisis IA
python tests/test_eosda_febrero_2025.py  # Test de API satelital
python tests/test_field_imagery_api.py   # Test de imágenes EOSDA
```

### Debugging de Informes PDF
1. **Error común:** HTML incompatible con ReportLab → usar `limpiar_html_para_reportlab()` 
2. **Matplotlib thread-safety:** Usar backend `matplotlib.use('Agg')` antes de imports
3. **Verificar PDF generado:** `python verificar_pdf_generado.py`

## 📝 Convenciones del Proyecto

### Código en Español
- **Comentarios, docstrings, variables:** Español
- **Logs:** Español con emojis (`logger.info("✅ Análisis generado")`)
- **Nombres de modelos/campos:** Snake_case español (`tipo_cultivo`, `area_hectareas`)

### Seguridad y Autenticación
- **Decorador estándar:** `@login_required` en todas las vistas (excepto registro público)
- **Permisos admin:** `@user_passes_test(lambda u: u.is_superuser)` para dashboard
- **Sistema de invitaciones:** `ClienteInvitacion` con token único, eliminar tras registro

### Manejo de Errores
```python
# Patrón estándar en servicios
try:
    logger.info(f"🚀 Iniciando proceso...")
    # lógica
    logger.info(f"✅ Proceso completado")
except Exception as e:
    logger.error(f"❌ Error: {str(e)}")
    return {'error': str(e), 'datos': None}
```

## 🔗 Integraciones Críticas

### EOSDA API
- **Autenticación:** API key como query param `?api_key=xxx` (NO en headers)
- **Rate limits:** Respetar límites de la API (implementado en `EosdaAPIService`)
- **Mapeo de cultivos:** Ver `mapeo_cultivos` en `eosda_api.py` (ej: "maíz" → "Other")

### Google Gemini AI
- **Modelo:** `gemini-2.0-flash` (FREE tier: 1500 req/día, 15 req/min)
- **Caché obligatorio:** Siempre verificar `AnalisisImagen` antes de llamar API
- **Prompt enriquecido:** Incluir metadatos espaciales (coordenadas, zona, satélite)

### PostgreSQL + PostGIS
- **Engine:** `django.contrib.gis.db.backends.postgis` en settings.py
- **Campos espaciales:** `PolygonField`, `PointField` con SRID 4326 (WGS84)
- **Queries optimizadas:** Usar métodos de PostGIS (`area`, `centroid`, `contains`)

## 📚 Referencias Rápidas

### Documentación Clave
- [FLUJO_IMAGENES_SATELITALES.md](docs/sistema/FLUJO_IMAGENES_SATELITALES.md) - Flujo completo EOSDA
- [IMPLEMENTACION_COMPLETADA.md](IMPLEMENTACION_COMPLETADA.md) - Análisis espacial con Gemini
- [CONEXION_EOSDA_GUIA_COMPLETA.md](CONEXION_EOSDA_GUIA_COMPLETA.md) - Integración EOSDA
- [README.md](README.md) - Setup y estructura general

### Archivos de Configuración
- `.env.example` - Template de variables de entorno (EOSDA_API_KEY, GEMINI_API_KEY)
- `settings_production.py` - Configuración Railway (PostgreSQL, WhiteNoise)
- `railway.toml` - Configuración de deploy

### Scripts de Utilidad
- `verificar_sistema.py` - Healthcheck completo del sistema
- `actualizar_metadatos_espaciales.py` - Migrar metadata de imágenes
- `create_superuser.py` - Crear admin sin interacción