# 📍 DÓNDE DESCARGAR LÍMITES DEPARTAMENTALES OFICIALES DE COLOMBIA

## 🎯 Lo que necesitas:
Un archivo **shapefile** (`.shp`) o **GeoJSON** (`.geojson`) con los límites departamentales de Colombia.

**Características técnicas:**
- ✅ Tipo de geometría: `Polygon` o `MultiPolygon`
- ✅ Sistema de coordenadas: WGS84 (EPSG:4326) o proyecciones colombianas (EPSG:3116, EPSG:9377)
- ✅ Precisión: Al menos escala 1:100,000 (mientras más detalle, mejor)
- ✅ Atributos: Debe tener campo con nombre del departamento ("Casanare", etc.)

---

## 🇨🇴 FUENTES OFICIALES RECOMENDADAS

### 1️⃣ IGAC (Instituto Geográfico Agustín Codazzi) - **MÁS OFICIAL**

**URL directa:**
https://www.colombiaenmapas.gov.co/

**Qué buscar:**
- Ir a: "Descargas" → "Límites administrativos"
- Archivo: **"Límites departamentales de Colombia"**
- Formatos disponibles: `.shp`, `.geojson`, `.kml`

**Ventajas:**
- ✅ Fuente oficial del gobierno colombiano
- ✅ Datos verificados y actualizados
- ✅ Precisión cartográfica certificada
- ✅ Incluye metadatos (códigos DANE, áreas, etc.)

---

### 2️⃣ DANE (Departamento Administrativo Nacional de Estadística)

**URL:**
https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/descarga-mgn/

**Qué buscar:**
- **Marco Geoestadístico Nacional (MGN)**
- Archivo: **"DEPARTAMENTO.shp"** o **"MGN_DPTO_POLITICO.shp"**
- Formato: Shapefile (.shp)

**Ventajas:**
- ✅ Usado en censos y estadísticas oficiales
- ✅ Compatible con análisis demográficos
- ✅ Gratis y de libre uso

---

### 3️⃣ Natural Earth Data - **MÁS FÁCIL** (datos globales)

**URL:**
https://www.naturalearthdata.com/downloads/10m-cultural-vectors/

**Qué descargar:**
- **"Admin 1 – States, Provinces"** (nivel 1 = departamentos)
- Archivo: `ne_10m_admin_1_states_provinces.zip`
- Formato: Shapefile (.shp)

**Ventajas:**
- ✅ Descarga directa sin registro
- ✅ Datos globales (incluye todos los países)
- ✅ Precisión aceptable para visualización
- ❌ Menos preciso que IGAC/DANE para análisis legal

**Cómo usarlo:**
1. Descargar el ZIP
2. Filtrar por `admin="Colombia"` y `name="Casanare"`

---

### 4️⃣ OpenStreetMap (OSM) - **ALTERNATIVA COMUNITARIA**

**URL:**
https://download.geofabrik.de/south-america/colombia.html

**Qué descargar:**
- Archivo: **"colombia-latest-free.shp.zip"**
- O usar: https://overpass-turbo.eu/ (consulta personalizada)

**Query para Overpass API:**
```
[out:json];
area["name"="Casanare"]["admin_level"="4"]->.a;
(
  relation(area.a)["boundary"="administrative"];
);
out geom;
```

**Ventajas:**
- ✅ Datos comunitarios actualizados frecuentemente
- ✅ Gratis y sin restricciones
- ❌ Precisión variable (depende de contribuidores)

---

### 5️⃣ Google Earth Engine (para usuarios avanzados)

**URL:**
https://code.earthengine.google.com/

**Dataset:**
```javascript
var colombia = ee.FeatureCollection('FAO/GAUL/2015/level1')
  .filter(ee.Filter.eq('ADM0_NAME', 'Colombia'));
```

**Ventajas:**
- ✅ API programática
- ✅ Datos globales certificados (FAO)
- ❌ Requiere cuenta de Google Earth Engine

---

## 📥 OPCIÓN RÁPIDA: Archivos ya listos

### GitHub - Repositorios con datos de Colombia

**Opción A: colombiajs/colombia-admin-divisions**
```bash
git clone https://github.com/colombiajs/colombia-admin-divisions
# Incluye departamentos, municipios, veredas
```

**Opción B: datasketch/datos-colombia**
```bash
# URL: https://github.com/datasketch/datos-colombia
# Archivos: departamentos.geojson
```

---

## 🔧 CÓMO INTEGRAR EL ARCHIVO EN AGROTECH

### Paso 1: Descargar el archivo

**Ejemplo (IGAC):**
```bash
cd /Users/sebasflorez16/Documents/AgroTech\ Historico/datos_geograficos/limites_departamentales/
# Descargar de IGAC y descomprimir
```

Deberías tener archivos como:
```
DEPARTAMENTO.shp
DEPARTAMENTO.shx
DEPARTAMENTO.dbf
DEPARTAMENTO.prj
```

**O un solo archivo:**
```
departamentos_colombia_oficial.geojson
```

---

### Paso 2: Validar el archivo

```python
import geopandas as gpd

# Leer el shapefile/geojson
gdf = gpd.read_file('DEPARTAMENTO.shp')  # o .geojson

# Ver estructura
print(gdf.columns)  # Ver campos disponibles
print(gdf[gdf['NOMBRE_DPT'] == 'CASANARE'])  # Filtrar Casanare

# Ver cuántos puntos tiene el polígono
casanare = gdf[gdf['NOMBRE_DPT'] == 'CASANARE'].iloc[0]
print(f"Puntos en el polígono: {len(casanare.geometry.exterior.coords)}")
# Si tiene >100 puntos = BUENA CALIDAD
# Si tiene <10 puntos = MUY SIMPLIFICADO
```

---

### Paso 3: Convertir a GeoJSON (si es shapefile)

```python
# Leer shapefile
gdf = gpd.read_file('DEPARTAMENTO.shp')

# Asegurar EPSG:4326 (WGS84)
if gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)

# Guardar como GeoJSON
gdf.to_file(
    'departamentos_colombia_oficial.geojson',
    driver='GeoJSON'
)
```

---

### Paso 4: Modificar el código en `generador_pdf_legal.py`

```python
# En el método _generar_mapa_contexto_regional()

# REEMPLAZAR ESTA LÍNEA:
geojson_path = os.path.join(
    settings.BASE_DIR, 
    'datos_geograficos', 
    'limites_departamentales', 
    'departamentos_colombia.geojson'  # ❌ SIMPLIFICADO
)

# POR ESTA:
geojson_path = os.path.join(
    settings.BASE_DIR, 
    'datos_geograficos', 
    'limites_departamentales', 
    'departamentos_colombia_oficial.geojson'  # ✅ OFICIAL DE IGAC/DANE
)
```

**Y listo** — el mapa mostrará la silueta real de Casanare con todos sus detalles.

---

## 🎯 RECOMENDACIÓN FINAL

### Para calidad LEGAL (uso en informes jurídicos):
✅ **IGAC** (colombiaenmapas.gov.co) → Escala 1:100,000 o mejor

### Para visualización rápida (MVP):
✅ **Natural Earth** → Descarga directa, sin registro

### Para desarrollo ágil:
✅ **GitHub colombiajs/colombia-admin-divisions** → Git clone y listo

---

## 📞 AYUDA ADICIONAL

Si tienes problemas descargando, avísame:
- Puedo guiarte paso a paso en la descarga
- Puedo escribir un script que descargue automáticamente desde APIs públicas
- Puedo convertir el formato que consigas al formato que necesitas

---

**Estado:** 📝 Documento guía creado  
**Siguiente paso:** Usuario descarga archivo oficial y lo integra en el proyecto
