#!/usr/bin/env python
"""
Calcular distancias REALES a cauces usando drenaje correcto
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

import geopandas as gpd
from pathlib import Path
from informes.models import Parcela
from django.contrib.gis.geos import GEOSGeometry
from shapely import wkt

print("=" * 80)
print("📏 DISTANCIAS REALES A RED HÍDRICA (DRENAJE CORRECTO)")
print("=" * 80)

# Cargar parcela 6
parcela = Parcela.objects.get(id=6)
parcela_geom = wkt.loads(parcela.geometria.wkt)
print(f"\n✅ Parcela: {parcela.nombre}")
print(f"   Área: {parcela.area_hectareas:.2f} ha")
print(f"   Centroide: {parcela_geom.centroid}\n")

# Cargar drenaje CORRECTO
archivo = Path(__file__).parent / 'datos_geograficos' / 'red_hidrica' / 'drenajes_sencillos_igac.shp'
red = gpd.read_file(str(archivo))
if red.crs != 'EPSG:4326':
    red = red.to_crs('EPSG:4326')

print(f"✅ Red hídrica cargada: {len(red):,} cauces (LineString)")

# Filtrar Casanare
bbox = [-73.0, 5.0, -69.0, 6.5]
red_cas = red.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
print(f"✅ Cauces en Casanare: {len(red_cas):,}\n")

# Calcular distancias en metros
red_proj = red_cas.to_crs('EPSG:3116')
parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
parcela_proj = parcela_gdf.to_crs('EPSG:3116')

distancias_m = red_proj.distance(parcela_proj.geometry.iloc[0])

# Top 10 cauces más cercanos
print("🔝 TOP 10 CAUCES MÁS CERCANOS A LA PARCELA:")
print("-" * 80)
for i, (idx, dist_m) in enumerate(distancias_m.nsmallest(10).items(), 1):
    cauce = red_cas.loc[idx]
    nombre = cauce.get('NOMBRE_GEO')
    nombre = nombre if nombre and str(nombre) != 'None' else "Sin nombre oficial"
    
    # Calcular dirección
    centroide_cauce = cauce.geometry.centroid
    centroide_parcela = parcela_geom.centroid
    dx = centroide_cauce.x - centroide_parcela.x
    dy = centroide_cauce.y - centroide_parcela.y
    
    if abs(dy) > abs(dx) * 1.5:
        direccion = "Norte" if dy > 0 else "Sur"
    elif abs(dx) > abs(dy) * 1.5:
        direccion = "Este" if dx > 0 else "Oeste"
    else:
        direccion_ns = "Norte" if dy > 0 else "Sur"
        direccion_eo = "este" if dx > 0 else "oeste"
        direccion = f"{direccion_ns}{direccion_eo}"
    
    dist_km = dist_m / 1000
    print(f"{i}. {nombre}")
    print(f"   Distancia: {dist_km:.2f} km ({dist_m:.0f} m)")
    print(f"   Dirección: {direccion}")
    print(f"   Requiere retiro: {'SÍ ⚠️' if dist_m < 30 else 'NO'}")
    print()

# Estadísticas
dist_min = distancias_m.min()
print("=" * 80)
print(f"📊 RESUMEN:")
print(f"   Cauce más cercano: {dist_min:.0f} m ({dist_min/1000:.2f} km)")
print(f"   Requiere retiro mínimo (30m): {'SÍ ⚠️' if dist_min < 30 else 'NO ✅'}")
print("=" * 80)
