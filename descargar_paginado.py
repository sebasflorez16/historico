import requests
import geopandas as gpd
from pathlib import Path
import json

print("Descargando datos mediante query paginado...\n")

BASE = Path("datos_geograficos")

# Resguardos - descarga paginada por lotes
print("📥 RESGUARDOS INDÍGENAS (ANT)")
print("-" * 60)

url = "https://services.arcgis.com/DDzi7vRExVRMO5AB/arcgis/rest/services/Resguardo_Indigena_Formalizado/FeatureServer/0/query"

all_features = []
offset = 0
batch_size = 1000

while True:
    params = {
        'where': 'DEPARTAMEN LIKE \'%CASANARE%\' OR DPTO LIKE \'%CASANARE%\' OR COD_DPTO=\'85\'',
        'outFields': '*',
        'returnGeometry': 'true',
        'resultOffset': offset,
        'resultRecordCount': batch_size,
        'f': 'json'
    }
    
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            print(f"  ⚠️  HTTP {r.status_code}, probando sin filtro departamental...")
            # Intentar query simple
            params2 = {
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'resultOffset': offset,
                'resultRecordCount': batch_size,
                'f': 'json'
            }
            r = requests.get(url, params=params2, timeout=30)
        
        data = r.json()
        
        if 'features' in data:
            features = data['features']
            if not features:
                break
            all_features.extend(features)
            print(f"  📦 Lote {offset//batch_size + 1}: {len(features)} elementos")
            offset += batch_size
        else:
            print(f"  ❌ Sin features: {data.get('error', 'Error desconocido')}")
            break
    except Exception as e:
        print(f"  ❌ Error: {e}")
        break

if all_features:
    print(f"\n  ✅ Total descargado: {len(all_features)} resguardos")
    
    # Convertir a GeoJSON y guardar
    geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }
    
    # Filtrar por Casanare usando GeoPandas
    gdf = gpd.GeoDataFrame.from_features(geojson['features'], crs='EPSG:4326')
    gdf_casanare = gdf.cx[-73.0:-69.8, 4.5:6.8]
    
    output_dir = BASE / 'resguardos_indigenas'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'resguardos_casanare.geojson'
    gdf_casanare.to_file(output_file, driver='GeoJSON')
    
    print(f"  💾 {output_file}: {len(gdf_casanare)} en Casanare")
else:
    print("  ⚠️  No se descargaron resguardos")

print("\n" + "="*60)
print("✅ Proceso completado")
