# 🌊 Guía Completa: Descarga de Red Hídrica IGAC para Casanare

## ✅ Fuentes Oficiales Verificadas

### Opción 1: Servicio REST - Atlas de Colombia 2024 (RECOMENDADO)

**URL del servicio:**
```
https://mapas.igac.gov.co/server/rest/services/atlas/hidrografiasuperficial/MapServer
```

**Capas disponibles:**
- ✅ **Río** (Layer 0) - LineString - LO QUE NECESITAMOS
- Nombre de áreas hidrográficas (Layer 1)
- Límite de área hidrográfica (Layer 2) - Polygon
- Zonas hidrográficas (Layer 3) - Polygon

**Cobertura:** Nacional (incluye TODO Casanare y Meta)
**Geometría:** LineString (cauces lineales) ✅
**Actualización:** 2024

---

## 📥 Método 1: QGIS con Servicio REST (MÁS RÁPIDO)

### Paso 1: Abrir QGIS
```bash
# Si no tienes QGIS instalado:
# macOS: brew install qgis
# O descarga de https://qgis.org/
```

### Paso 2: Conectar al servicio REST del IGAC
1. Abrir QGIS
2. `Capa` → `Añadir capa` → `Añadir capa ArcGIS REST Server`
3. Nombre de conexión: `IGAC - Hidrografía Superficial`
4. URL: `https://mapas.igac.gov.co/server/rest/services/atlas/hidrografiasuperficial/MapServer`
5. Clic en `Conectar`
6. Seleccionar la capa **"Río"** (Layer 0)
7. Clic en `Añadir`

### Paso 3: Filtrar por región (Casanare + Meta)
1. Clic derecho en la capa → `Filtrar...`
2. Usar expresión SQL:
   ```sql
   "DEPARTAMENTO" IN ('CASANARE', 'META')
   ```
3. Aplicar filtro

### Paso 4: Exportar a Shapefile
1. Clic derecho en la capa filtrada → `Exportar` → `Guardar objetos como...`
2. Formato: `ESRI Shapefile`
3. Nombre de archivo: `red_hidrica_casanare_meta_igac_2024.shp`
4. CRS: `EPSG:4326 - WGS 84`
5. Guardar en: `/Users/sebasflorez16/Documents/AgroTech Historico/datos_geograficos/red_hidrica/`
6. Clic en `Aceptar`

**Resultado esperado:**
- ✅ Archivo: `red_hidrica_casanare_meta_igac_2024.shp`
- ✅ Geometría: LineString (cauces)
- ✅ Cobertura: Casanare + Meta completos
- ✅ Campos: NOMBRE_GEO, DEPARTAMENTO, TIPO, etc.

---

## 📥 Método 2: Cartografía Base IGAC 1:100.000 (MÁS COMPLETO)

### Paso 1: Descargar GDB Nacional
**URL:**
```
https://www.colombiaenmapas.gov.co/?b=igac&u=0&t=23&servicio=205
```

**Pasos:**
1. Ir a Colombia en Mapas
2. Seleccionar `Cartografía Base 1:100.000`
3. Descargar geodatabase (GDB) nacional o por plancha
4. Archivo descargado: `Cartografia_Base_100K.gdb` (~varios GB)

### Paso 2: Extraer capa de drenajes en QGIS
1. Abrir QGIS
2. `Capa` → `Añadir capa` → `Añadir capa vectorial`
3. Tipo de fuente: `Directorio`
4. Tipo: `OpenFileGDB`
5. Seleccionar carpeta `.gdb` descargada
6. Buscar y seleccionar capas:
   - ✅ `drenajesencillo` (LineString) - Ríos, quebradas, caños
   - ✅ `drenajedoble` (Polygon) - Ríos anchos (>50m)

### Paso 3: Filtrar por departamento
```sql
"DEPARTAMENTO" IN ('CASANARE', 'META')
-- O si usa código:
"COD_DPTO" IN ('85', '50')
```

### Paso 4: Exportar a Shapefile
- Igual que Método 1, Paso 4

---

## 🐍 Método 3: Script Python Automatizado (PRÓXIMAMENTE)

```python
#!/usr/bin/env python
"""
Descarga automática de red hídrica desde servicio REST IGAC
"""
import requests
import geopandas as gpd
from pathlib import Path

# URL del servicio REST
SERVICE_URL = "https://mapas.igac.gov.co/server/rest/services/atlas/hidrografiasuperficial/MapServer/0/query"

# Parámetros de consulta
params = {
    'where': "DEPARTAMENTO IN ('CASANARE', 'META')",
    'outFields': '*',
    'f': 'geojson',
    'returnGeometry': 'true'
}

# Descargar
response = requests.get(SERVICE_URL, params=params)
geojson_data = response.json()

# Convertir a GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
gdf.set_crs('EPSG:4326', inplace=True)

# Guardar como shapefile
output_path = Path(__file__).parent / 'datos_geograficos' / 'red_hidrica' / 'red_hidrica_casanare_meta_igac_2024.shp'
gdf.to_file(output_path)

print(f"✅ Descargado: {len(gdf)} cauces")
print(f"✅ Guardado en: {output_path}")
```

---

## 🔧 Actualizar Código AgroTech

Una vez descargado el shapefile correcto, actualizar:

### 1. Reemplazar archivo en `/datos_geograficos/red_hidrica/`
```bash
cd /Users/sebasflorez16/Documents/AgroTech\ Historico/datos_geograficos/red_hidrica/

# Renombrar archivos viejos (backup)
mv geo_export_f2706386-4e46-4c8d-b785-837ff6809bf0.shp geo_export_ZONIFICACION_OLD.shp.bak
mv drenajes_sencillos_igac.shp drenajes_sencillos_PARCIAL_OLD.shp.bak

# Copiar nuevo archivo
cp ~/Downloads/red_hidrica_casanare_meta_igac_2024.shp .
```

### 2. Actualizar `verificador_legal.py`
```python
# Línea ~165 - Priorizar archivo correcto
archivos_prioritarios = [
    'red_hidrica_casanare_meta_igac_2024.shp',  # NUEVO - Atlas 2024
    'drenajesencillo.shp',                       # De GDB 100K
    'drenajes_sencillos_igac.shp',              # Antiguo (parcial)
]
```

### 3. Verificar cobertura
```python
python diagnosticar_red_hidrica_completo.py
```

**Resultado esperado:**
```
✅ Registros en Casanare: 5,000+ cauces
✅ Cauces en bbox Tauramena [-72.5, -72.0, 5.0, 5.5]: 50+
✅ Distancia mínima a parcela: 1.2 km (Río Cravo Sur)
```

---

## ✅ Checklist de Validación

Después de descargar y configurar:

- [ ] Shapefile contiene geometría **LineString** (no Polygon)
- [ ] Cobertura incluye **Tauramena, Casanare** (lon: -72.2)
- [ ] Campo `NOMBRE_GEO` tiene nombres de ríos
- [ ] Filtrado por bbox Casanare [-73.0, 5.0, -69.0, 6.5] devuelve > 1000 registros
- [ ] Distancia a parcela 6 es < 5 km (verosímil)
- [ ] PDF generado muestra distancia correcta y nombre del río

---

## 🎯 Próximos Pasos

1. **Ejecutar Método 1** (REST con QGIS) - **15 minutos**
2. Reemplazar shapefile viejo
3. Ejecutar `python generar_pdf_verificacion_casanare.py`
4. Verificar que PDF muestre distancias reales (1-5 km)
5. Documentar en `MEJORAS_COMPLETADAS_PDF_LEGAL.md`

---

## 📚 Referencias

- **Servicio REST IGAC:** https://mapas.igac.gov.co/server/rest/services/atlas/hidrografiasuperficial/MapServer
- **Cartografía Base:** https://www.colombiaenmapas.gov.co/?b=igac&u=0&t=23&servicio=205
- **Documentación QGIS:** https://docs.qgis.org/
- **GeoPandas:** https://geopandas.org/

---

## 🚨 Notas Importantes

1. **No usar shapefiles de zonificación** (polígonos de cuencas)
2. **Verificar siempre** que `geometry.geom_type == 'LineString'`
3. **Filtrar por departamento** para reducir tamaño de archivo
4. **Mantener CRS EPSG:4326** para compatibilidad
5. **Documentar fuente y fecha** en metadatos

---

**Última actualización:** 29 de enero de 2026
**Autor:** AgroTech Histórico - Sistema de Verificación Legal
