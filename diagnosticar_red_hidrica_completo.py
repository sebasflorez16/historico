#!/usr/bin/env python
"""
Diagnóstico COMPLETO de Red Hídrica
====================================
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

import geopandas as gpd
from pathlib import Path
from informes.models import Parcela
from django.contrib.gis.geos import GEOSGeometry
from shapely import wkt

print("=" * 80)
print("🔍 DIAGNÓSTICO COMPLETO DE RED HÍDRICA - CASANARE")
print("=" * 80)

# 1. Cargar la parcela 6
print("\n📍 PASO 1: Cargando parcela 6...")
parcela = Parcela.objects.get(id=6)

# Convertir geometría Django a Shapely
if hasattr(parcela, 'geometria'):
    # Si es un campo GeoDjango (GEOSGeometry)
    if isinstance(parcela.geometria, GEOSGeometry):
        parcela_geom = wkt.loads(parcela.geometria.wkt)
    else:
        # Si es WKT string
        parcela_geom = wkt.loads(str(parcela.geometria))
else:
    print("❌ Parcela no tiene campo 'geometria'")
    print(f"   Campos disponibles: {[f.name for f in parcela._meta.get_fields()]}")
    sys.exit(1)

print(f"✅ Parcela: {parcela.nombre}")
print(f"   Propietario: {parcela.propietario}")
print(f"   Área: {parcela.area_hectareas:.2f} ha")
print(f"   Tipo de cultivo: {parcela.tipo_cultivo if parcela.tipo_cultivo else 'No especificado'}")
print(f"   Centroide: {parcela_geom.centroid}")
print(f"   Bounds: {parcela_geom.bounds}")

# 2. Buscar shapefile de red hídrica
print("\n🗂️  PASO 2: Buscando shapefile de red hídrica...")
directorio_red = Path(__file__).parent / 'datos_geograficos' / 'red_hidrica'
print(f"   Directorio: {directorio_red}")

if directorio_red.exists():
    shapefiles = list(directorio_red.glob('*.shp'))
    print(f"   Shapefiles encontrados: {len(shapefiles)}")
    for shp in shapefiles:
        print(f"     - {shp.name} ({shp.stat().st_size / 1024 / 1024:.1f} MB)")
    
    if not shapefiles:
        print("   ❌ No se encontraron shapefiles (.shp)")
        sys.exit(1)
    
    # Usar el primero
    archivo = str(shapefiles[0])
    print(f"\n   ✅ Usando: {shapefiles[0].name}")
else:
    print(f"   ❌ Directorio no existe: {directorio_red}")
    sys.exit(1)

# 3. Cargar shapefile
print("\n📊 PASO 3: Analizando shapefile...")
red = gpd.read_file(archivo)

# Reproyectar si es necesario
if red.crs != 'EPSG:4326':
    print(f"   Reproyectando de {red.crs} a EPSG:4326...")
    red = red.to_crs('EPSG:4326')

print(f"   ✅ Registros totales: {len(red):,}")
print(f"   CRS: {red.crs}")
print(f"   Columnas: {list(red.columns)}")

# 4. Analizar tipos de geometría
print("\n🔷 PASO 4: Analizando tipos de geometría...")
tipos_geom = red.geometry.geom_type.value_counts()
print("   Tipos de geometría:")
for tipo, count in tipos_geom.items():
    print(f"     - {tipo}: {count:,} ({count/len(red)*100:.1f}%)")

tiene_lineas = any(t in ['LineString', 'MultiLineString'] for t in tipos_geom.index)
tiene_poligonos = any(t in ['Polygon', 'MultiPolygon'] for t in tipos_geom.index)

if tiene_poligonos and not tiene_lineas:
    print("\n   ⚠️  PROBLEMA: El shapefile contiene POLÍGONOS, no líneas")
    print("   Esto es ZONIFICACIÓN HÍDRICA, no la red de drenaje real")
    print("   Confianza: BAJA")
elif tiene_lineas:
    print("\n   ✅ CORRECTO: El shapefile contiene LÍNEAS (drenaje real)")
    print("   Confianza: ALTA")

# 5. Cobertura geográfica
print("\n🗺️  PASO 5: Cobertura geográfica...")
bounds = red.total_bounds  # [minx, miny, maxx, maxy]
print(f"   Bounding Box:")
print(f"     - Longitud: {bounds[0]:.4f} a {bounds[2]:.4f}")
print(f"     - Latitud: {bounds[1]:.4f} a {bounds[3]:.4f}")

# Verificar si la parcela está dentro del bbox
parcela_bounds = parcela_geom.bounds
parcela_dentro = (
    bounds[0] <= parcela_bounds[0] <= bounds[2] and
    bounds[0] <= parcela_bounds[2] <= bounds[2] and
    bounds[1] <= parcela_bounds[1] <= bounds[3] and
    bounds[1] <= parcela_bounds[3] <= bounds[3]
)

if parcela_dentro:
    print(f"\n   ✅ La parcela ESTÁ dentro del bbox del shapefile")
else:
    print(f"\n   ⚠️  La parcela NO está dentro del bbox del shapefile")
    print(f"      Parcela bbox: {parcela_bounds}")

# 6. Filtrar por departamento (Casanare)
print("\n🎯 PASO 6: Filtrando por región de Casanare...")
# Bbox de Casanare: [-73.0, 5.0, -69.0, 6.5]
bbox_casanare = [-73.0, 5.0, -69.0, 6.5]
try:
    red_casanare = red.cx[bbox_casanare[0]:bbox_casanare[2], bbox_casanare[1]:bbox_casanare[3]]
    print(f"   ✅ Registros en región Casanare: {len(red_casanare):,}")
    
    if len(red_casanare) == 0:
        print("   ❌ NO HAY REGISTROS en la región de Casanare")
        print("   Esto explica por qué no se encuentran ríos cercanos")
    else:
        # Calcular distancia mínima a la parcela
        print("\n📏 PASO 7: Calculando distancias a la parcela...")
        red_casanare_proj = red_casanare.to_crs('EPSG:3116')
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        parcela_proj = parcela_gdf.to_crs('EPSG:3116')
        
        distancias_m = red_casanare_proj.distance(parcela_proj.geometry.iloc[0])
        dist_min_m = distancias_m.min()
        dist_min_km = dist_min_m / 1000
        idx_min = distancias_m.idxmin()
        
        print(f"   ✅ Distancia mínima: {dist_min_km:.2f} km ({dist_min_m:.0f} m)")
        print(f"   Cauce más cercano:")
        
        # Mostrar info del cauce más cercano
        cauce = red_casanare.loc[idx_min]
        print(f"     - Geometría: {cauce.geometry.geom_type}")
        
        # Buscar columna de nombre
        columnas_nombre = ['NOMBRE_GEO', 'NOMBRE', 'NOM_GEO', 'nombre', 'NOM', 'NAME']
        nombre = None
        for col in columnas_nombre:
            if col in red_casanare.columns:
                nombre = cauce.get(col)
                if nombre and str(nombre) != 'None':
                    print(f"     - Nombre ({col}): {nombre}")
                    break
        
        # Mostrar todas las columnas del cauce
        print(f"\n   📋 Todas las columnas del cauce más cercano:")
        for col in red_casanare.columns:
            if col != 'geometry':
                valor = cauce.get(col)
                if valor is not None and str(valor) != 'None':
                    print(f"       {col}: {valor}")
        
        # Mostrar los 10 cauces más cercanos
        print(f"\n   🔝 Top 10 cauces más cercanos:")
        distancias_sorted = distancias_m.sort_values()
        for i, (idx, dist_m) in enumerate(distancias_sorted.head(10).items(), 1):
            dist_km = dist_m / 1000
            cauce = red_casanare.loc[idx]
            nombre = None
            for col in columnas_nombre:
                if col in red_casanare.columns:
                    nombre = cauce.get(col)
                    if nombre and str(nombre) != 'None':
                        break
            nombre = nombre if nombre else "Sin nombre"
            print(f"       {i}. {dist_km:.2f} km - {nombre} ({cauce.geometry.geom_type})")

except Exception as e:
    print(f"   ❌ Error filtrando: {e}")
    import traceback
    traceback.print_exc()

# 7. Resumen final
print("\n" + "=" * 80)
print("�� RESUMEN DEL DIAGNÓSTICO")
print("=" * 80)
print(f"✅ Shapefile cargado: {Path(archivo).name}")
print(f"✅ Total de registros: {len(red):,}")
print(f"✅ Tipo de geometría: {', '.join(tipos_geom.index.tolist())}")
if 'red_casanare' in locals():
    print(f"✅ Registros en Casanare: {len(red_casanare):,}")
if 'dist_min_km' in locals():
    print(f"✅ Distancia mínima a parcela: {dist_min_km:.2f} km")
print("=" * 80)
