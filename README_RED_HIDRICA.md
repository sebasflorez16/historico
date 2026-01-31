# 🌊 Red Hídrica - Integración Multi-Fuente

## Descripción

Sistema robusto de descarga y análisis de red hídrica para verificación legal de parcelas agrícolas en Colombia, con soporte para múltiples fuentes de datos y validación automática de cobertura.

## 🚀 Características

### Descarga Automática Multi-Fuente
- ✅ **REST API IGAC** (preferido - datos oficiales)
- ✅ **WFS Service IGAC** (backup - datos oficiales)
- ✅ **OpenStreetMap Overpass API** (backup automático)
- ✅ **Guía manual GDB Nacional** (fallback documentado)

### Validación Automática
- ✅ Verificación de cobertura geográfica (umbral 50 km)
- ✅ Validación de tipo de geometría (LineString)
- ✅ Detección de retiros hídricos (30 m mínimo)
- ✅ Advertencias claras si datos no confiables

### Cálculos Precisos
- ✅ Proyección UTM 18N (EPSG:32618) para Colombia
- ✅ Distancias en metros (unidad nativa)
- ✅ Sin warnings de GeoPandas
- ✅ Direcciones cardinales automáticas

## 📦 Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Las dependencias clave son:
# - geopandas
# - requests
# - shapely
```

## 🎯 Uso Rápido

### 1. Descargar Red Hídrica

```bash
python descargar_red_hidrica_igac.py
```

**Salida esperada:**
```
🌊 DESCARGA AUTOMÁTICA DE RED HÍDRICA (MULTI-FUENTE)
================================================================================
📡 MÉTODO 1: REST API IGAC → Intentando...
📡 MÉTODO 2: WFS Service → Intentando...
📡 MÉTODO 3: OSM Overpass → ✅ 10,586 cauces descargados
🎯 Cobertura Tauramena: ✅ 203 cauces
💾 Shapefile guardado: 12.51 MB
```

### 2. Diagnosticar Cobertura

```bash
python diagnosticar_red_hidrica_completo.py
```

**Salida esperada:**
```
🔍 DIAGNÓSTICO COMPLETO DE RED HÍDRICA
✅ Shapefile cargado: 10,586 registros
✅ Tipo geometría: LineString
✅ Distancia mínima a parcela: 0.06 km (63 m)
```

### 3. Generar PDF Legal

```bash
python generar_pdf_verificacion_casanare.py
```

**Salida esperada:**
```
📄 GENERANDO PDF MEJORADO DE VERIFICACIÓN LEGAL
✅ PDF generado: verificacion_legal_casanare_MEJORADO.pdf
✅ Tamaño: 396 KB
```

## 🔧 Configuración

### Archivo: `descargar_red_hidrica_igac.py`

```python
# URLs de servicios
METODO_1_REST = {
    'url': 'https://mapas.igac.gov.co/server/rest/services/...'
}

METODO_3_OSM = {
    'url': 'https://overpass-api.de/api/interpreter'
}

# Configuración de salida
OUTPUT_DIR = Path(__file__).parent / 'datos_geograficos' / 'red_hidrica'
OUTPUT_FILE = 'red_hidrica_casanare_meta_igac_2024.shp'

# Validación de cobertura
BBOX_TAURAMENA = [-72.5, 5.0, -72.0, 5.5]
```

### Archivo: `generador_pdf_legal.py`

```python
# Proyección para Colombia
UTM_COLOMBIA = 'EPSG:32618'  # UTM Zone 18N

# Umbral de cobertura
SIN_COBERTURA_THRESHOLD = 50  # km

# Retiro mínimo legal
RETIRO_MINIMO_M = 30  # metros (Decreto 1541/1978)
```

## 📊 Fuentes de Datos

### IGAC (Oficial - Preferido)
- **Nombre:** Instituto Geográfico Agustín Codazzi
- **Calidad:** Alta - datos oficiales del gobierno
- **Cobertura:** Nacional completa
- **Actualización:** Periódica (variable)
- **Formato:** REST API, WFS, GDB
- **Estado actual:** Servicios intermitentes (503/400 errors)

### OpenStreetMap (Colaborativo - Backup)
- **Nombre:** OpenStreetMap via Overpass API
- **Calidad:** Media - datos colaborativos
- **Cobertura:** Variable por región
- **Actualización:** Continua (comunidad)
- **Formato:** GeoJSON via Overpass QL
- **Estado actual:** ✅ Funcional y confiable

## 🗺️ Compatibilidad de Campos

El sistema soporta automáticamente campos de múltiples fuentes:

| Concepto | IGAC | OSM | Fallback |
|----------|------|-----|----------|
| Nombre | `NOMBRE_GEO`, `NOMBRE` | `name` | "Cauce sin nombre" |
| Tipo | `TIPO`, `CLASE_DREN` | `waterway` | "Drenaje natural" |
| ID | `OBJECTID` | `osm_id` | Index |

## 📏 Validación de Distancias

| Distancia | Interpretación | PDF |
|-----------|----------------|-----|
| < 30m | Afecta retiro hídrico | ⚠️ Requiere retiro |
| 30m - 5km | Normal en llanura | ✅ Válido |
| 5km - 50km | Revisar manualmente | 🔍 Verificar |
| > 50km | Sin cobertura | ❌ Advertencia |

## 🧪 Tests

```bash
# Test de descarga
python descargar_red_hidrica_igac.py

# Test de diagnóstico
python diagnosticar_red_hidrica_completo.py

# Test de PDF (parcela de prueba)
python generar_pdf_verificacion_casanare.py

# Test de PDF (parcela real DB)
python generar_pdf_legal.py  # usa parcela.id = 6
```

## 📚 Documentación

- `PROBLEMA_RED_HIDRICA_CASANARE.md` - Diagnóstico del problema original
- `GUIA_DESCARGA_RED_HIDRICA_IGAC.md` - Guía para descarga manual
- `REFACTORIZACION_DISTANCIAS_COMPLETADA.md` - Detalles técnicos UTM
- `RESUMEN_COMPLETO_REFACTORIZACION_RED_HIDRICA.md` - Resumen completo
- `PROGRESO_FINAL_RED_HIDRICA_PDF.md` - Estado de completitud

## 🐛 Troubleshooting

### Error: Servicios IGAC no responden (503/400)
**Solución:** El sistema automáticamente usa OSM como backup.

### Error: Sin cobertura en zona X
**Solución:** 
1. Verifica que el departamento esté en el filtro
2. Revisa `BBOX_TAURAMENA` en el script
3. Descarga GDB Nacional manualmente (ver `GUIA_DESCARGA_RED_HIDRICA_IGAC.md`)

### Error: Distancias ilógicas (>50 km)
**Solución:** El sistema detecta automáticamente y muestra advertencia en PDF.

### Warning: "Geometry is in a geographic CRS"
**Solución:** ✅ Ya resuelto en versión actual (usa UTM 18N)

## 🔄 Actualización de Datos

### OSM (Recomendado cada 6 meses):
```bash
# Re-ejecutar descarga
python descargar_red_hidrica_igac.py
```

### IGAC (Cuando servicios estén activos):
1. Monitorear status de servicios REST/WFS
2. Ajustar prioridad en `descargar_red_hidrica_igac.py`
3. Re-ejecutar descarga

## 📞 Soporte

### Servicios IGAC caídos:
- Email: soporte@igac.gov.co
- Reportar: "Servicios REST/WFS de hidrografía no responden"

### Datos OSM incompletos:
- Contribuir: https://www.openstreetmap.org
- Wiki: https://wiki.openstreetmap.org/wiki/ES:Waterways

## 📜 Licencia

- Datos IGAC: Dominio público (gobierno de Colombia)
- Datos OSM: ODbL (Open Database License)
- Código: [Tu licencia]

## 🙏 Créditos

- **IGAC:** Instituto Geográfico Agustín Codazzi
- **OpenStreetMap:** Comunidad de colaboradores
- **GeoPandas:** Biblioteca espacial de Python
- **Overpass API:** Servicio de consultas OSM

---

**Última actualización:** 29 enero 2026  
**Versión:** 2.0 (Multi-fuente + UTM)  
**Mantenedor:** AgroTech Histórico
