#!/usr/bin/env python3
"""
Descarga capas desde servicios WFS funcionales
"""

import geopandas as gpd
from pathlib import Path
import requests

print("\n" + "="*80)
print("🗺️  DESCARGA MEDIANTE WFS - PROFESIONAL")
print("="*80)

BASE_DIR = Path("datos_geograficos")
BBOX_CASANARE = (-73.0, 4.5, -69.8, 6.8)  # minx, miny, maxx, maxy

# 1. Resguardos Indígenas - desde geonode ANT
print("\n" + "#"*80)
print("## RESGUARDOS INDÍGENAS")
print("#"*80)

try:
    print("\n📥 Descargando desde GeoNode ANT...")
    url_resguardos = "https://geoservicios.ant.gov.co/arcgis/rest/services/Solicitudes/Resguardos_Indigenas/MapServer/1/query"
    
    params = {
        'where': '1=1',
        'outFields': '*',
        'outSR': '4326',
        'f': 'geojson'
    }
    
    response = requests.get(url_resguardos, params=params, timeout=120)
    
    if response.status_code == 200:
        gdf = gpd.read_file(response.text)
        print(f"   📊 Total nacional: {len(gdf):,} resguardos")
        
        # Filtrar por Casanare
        gdf_casanare = gdf.cx[BBOX_CASANARE[0]:BBOX_CASANARE[2], BBOX_CASANARE[1]:BBOX_CASANARE[3]]
        print(f"   ✅ En Casanare: {len(gdf_casanare):,} resguardos")
        
        # Guardar
        output_dir = BASE_DIR / "resguardos_indigenas"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "resguardos_casanare.geojson"
        gdf_casanare.to_file(output_file, driver="GeoJSON")
        print(f"\n💾 Guardado: {output_file}")
        print(f"   📏 {output_file.stat().st_size / 1024:.2f} KB")
    else:
        print(f"   ❌ Error HTTP {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Páramos - desde IDEAM
print("\n" + "#"*80)
print("## PÁRAMOS")
print("#"*80)

try:
    print("\n📥 Descargando desde IDEAM...")
    url_paramos = "http://geoservicios.ideam.gov.co/geoserver/ecosistemas/ows"
    
    params = {
        'service': 'WFS',
        'version': '1.0.0',
        'request': 'GetFeature',
        'typeName': 'ecosistemas:paramos',
        'outputFormat': 'json',
        'srsName': 'EPSG:4326'
    }
    
    response = requests.get(url_paramos, params=params, timeout=120)
    
    if response.status_code == 200:
        gdf = gpd.read_file(response.text)
        print(f"   📊 Total nacional: {len(gdf):,} páramos")
        
        # Filtrar por Casanare
        gdf_casanare = gdf.cx[BBOX_CASANARE[0]:BBOX_CASANARE[2], BBOX_CASANARE[1]:BBOX_CASANARE[3]]
        print(f"   ✅ En Casanare: {len(gdf_casanare):,} páramos")
        
        if len(gdf_casanare) == 0:
            print("   ℹ️  Casanare no tiene páramos (dato esperado)")
        
        # Guardar
        output_dir = BASE_DIR / "paramos"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "paramos_casanare.geojson"
        gdf_casanare.to_file(output_file, driver="GeoJSON")
        print(f"\n💾 Guardado: {output_file}")
        print(f"   📏 {output_file.stat().st_size / 1024:.2f} KB")
    else:
        print(f"   ❌ Error HTTP {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print("✅ PROCESO COMPLETADO")
print("="*80 + "\n")
