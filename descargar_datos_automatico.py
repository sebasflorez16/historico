#!/usr/bin/env python3
"""
Descarga automática de datos geográficos oficiales para verificación legal
"""
import geopandas as gpd
from pathlib import Path

print("="*80)
print("🚀 DESCARGA AUTOMÁTICA DE DATOS GEOGRÁFICOS")
print("="*80 + "\n")

# Crear directorios
for d in ['datos_geograficos/red_hidrica', 'datos_geograficos/runap', 
          'datos_geograficos/resguardos', 'datos_geograficos/paramos']:
    Path(d).mkdir(parents=True, exist_ok=True)

# 1. RUNAP
print("📥 1/4 RUNAP (Áreas Protegidas)...")
try:
    url = 'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=json'
    gdf = gpd.read_file(url)
    gdf.to_file('datos_geograficos/runap/areas_protegidas_runap.shp')
    print(f"✅ DESCARGADO: {len(gdf)} áreas\n")
except Exception as e:
    print(f"❌ ERROR: {e}\n")

# 2. Red Hídrica IGAC
print("📥 2/4 Red Hídrica IGAC...")
urls = [
    "https://geoservicios.igac.gov.co/geoserver/cartografia_basica/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=cartografia_basica:drenaje_sencillo&outputFormat=json",
    "https://www.datos.gov.co/api/geospatial/rft4-7cca?method=export&format=GeoJSON"
]

ok = False
for i, url in enumerate(urls, 1):
    try:
        print(f"   Fuente {i}...")
        gdf = gpd.read_file(url)
        tipos = gdf.geometry.geom_type.unique()
        if any(t in ['LineString', 'MultiLineString'] for t in tipos):
            gdf.to_file('datos_geograficos/red_hidrica/drenajes_igac.shp')
            print(f"✅ DESCARGADO: {len(gdf)} drenajes\n")
            ok = True
            break
    except Exception as e:
        print(f"   ⚠️  Falló: {str(e)[:80]}")

if not ok:
    print("❌ No se pudo descargar automáticamente\n")

# 3. Resguardos
print("📥 3/4 Resguardos Indígenas...")
try:
    url = "https://www.datos.gov.co/api/geospatial/mqfn-ttqs?method=export&format=GeoJSON"
    gdf = gpd.read_file(url)
    gdf.to_file('datos_geograficos/resguardos/resguardos_indigenas.shp')
    print(f"✅ DESCARGADO: {len(gdf)} resguardos\n")
except Exception as e:
    print(f"❌ ERROR: {e}\n")

# 4. Páramos
print("📥 4/4 Páramos...")
try:
    url = "https://www.datos.gov.co/api/geospatial/qfpw-ga2x?method=export&format=GeoJSON"
    gdf = gpd.read_file(url)
    gdf.to_file('datos_geograficos/paramos/delimitacion_paramos.shp')
    print(f"✅ DESCARGADO: {len(gdf)} páramos\n")
except Exception as e:
    print(f"❌ ERROR: {e}\n")

# Validación
print("="*80)
print("📊 RESUMEN")
print("="*80 + "\n")

base = Path('datos_geograficos')
for nombre, carpeta in [
    ('Red Hídrica', 'red_hidrica'),
    ('RUNAP', 'runap'),
    ('Resguardos', 'resguardos'),
    ('Páramos', 'paramos')
]:
    dir_path = base / carpeta
    if dir_path.exists() and list(dir_path.glob('*.shp')):
        shp = list(dir_path.glob('*.shp'))[0]
        gdf = gpd.read_file(str(shp))
        print(f"✅ {nombre}: {len(gdf)} elementos")
    else:
        print(f"❌ {nombre}: NO encontrado")

print("\n" + "="*80)
