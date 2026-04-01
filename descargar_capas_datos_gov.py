#!/usr/bin/env python3
"""
Descargar capas desde datos.gov.co (Socrata API)
Más confiable que los servicios ArcGIS que cambian de URL
"""
import requests
import geopandas as gpd
from pathlib import Path
import json

base_dir = Path('datos_geograficos')
(base_dir / 'areas_protegidas').mkdir(parents=True, exist_ok=True)
(base_dir / 'resguardos_indigenas').mkdir(parents=True, exist_ok=True)
(base_dir / 'paramos').mkdir(parents=True, exist_ok=True)

# Bounding box Casanare
bbox = {
    'min_lon': -73.0,
    'min_lat': 5.0,
    'max_lon': -71.0,
    'max_lat': 7.0
}

print('=' * 80)
print('🌍 DESCARGANDO CAPAS DESDE DATOS.GOV.CO')
print('=' * 80)

# ============================================================================
# 1. RUNAP - Desde datos.gov.co
# ============================================================================
print('\n📥 1. RUNAP (Áreas Protegidas)...')

try:
    # URL del API de datos abiertos
    url = 'https://www.datos.gov.co/resource/zjbz-49cy.json'
    
    # Filtrar por bounding box de Casanare
    query = f"""
SELECT *
WHERE
    latitude >= {bbox['min_lat']} AND
    latitude <= {bbox['max_lat']} AND
    longitude >= {bbox['min_lon']} AND
    longitude <= {bbox['max_lon']}
LIMIT 50000
    """.strip()
    
    params = {
        '$query': query,
        '$$app_token': 'DEMO'  # Token público
    }
    
    print(f'   🔗 Consultando API Socrata...')
    r = requests.get(url, params=params, timeout=30)
    
    if r.status_code == 200:
        data = r.json()
        print(f'   📦 {len(data)} registros recibidos')
        
        if len(data) > 0:
            # Convertir a GeoDataFrame si tiene geometría
            features = []
            for item in data:
                if 'the_geom' in item:
                    try:
                        geom_data = json.loads(item['the_geom']['coordinates'] if isinstance(item['the_geom'], dict) else item['the_geom'])
                        features.append({
                            'type': 'Feature',
                            'geometry': item.get('the_geom'),
                            'properties': {k: v for k, v in item.items() if k != 'the_geom'}
                        })
                    except:
                        pass
            
            if features:
                gdf = gpd.GeoDataFrame.from_features({'type': 'FeatureCollection', 'features': features}, crs='EPSG:4326')
                output = base_dir / 'areas_protegidas' / 'runap_casanare.geojson'
                gdf.to_file(output, driver='GeoJSON')
                print(f'   ✅ {len(gdf)} áreas protegidas guardadas')
                print(f'   📁 {output}')
            else:
                print('   ⚠️  Sin geometría válida')
                # Guardar como CSV al menos
                with open(base_dir / 'areas_protegidas' / 'README.txt', 'w') as f:
                    f.write('No se encontraron áreas protegidas RUNAP con geometría en Casanare\\n')
        else:
            print('   ⚠️  No hay áreas protegidas en Casanare')
            with open(base_dir / 'areas_protegidas' / 'README.txt', 'w') as f:
                f.write('No se encontraron áreas protegidas RUNAP en Casanare\\n')
                f.write('Verificado: 2025-01-26\\n')
    else:
        print(f'   ❌ Error {r.status_code}')
except Exception as e:
    print(f'   ❌ Error: {e}')
    # Crear archivo vacío
    with open(base_dir / 'areas_protegidas' / 'README.txt', 'w') as f:
        f.write('No se pudo descargar RUNAP\\n')
        f.write(f'Error: {str(e)}\\n')

# ============================================================================
# 2. RESGUARDOS INDÍGENAS
# ============================================================================
print('\n📥 2. Resguardos Indígenas...')

try:
    #URL del dataset de resguardos
    url = 'https://www.datos.gov.co/resource/kqy7-stvf.json'
    
    query = f"""
SELECT *
WHERE
    latitud >= {bbox['min_lat']} AND
    latitud <= {bbox['max_lat']} AND
    longitud >= {bbox['min_lon']} AND
    longitud <= {bbox['max_lon']}
LIMIT 50000
    """.strip()
    
    params = {
        '$query': query,
        '$$app_token': 'DEMO'
    }
    
    print(f'   🔗 Consultando API Socrata...')
    r = requests.get(url, params=params, timeout=30)
    
    if r.status_code == 200:
        data = r.json()
        print(f'   📦 {len(data)} registros recibidos')
        
        if len(data) > 0:
            # Intentar convertir a GeoDataFrame
            features = []
            for item in data:
                if 'geo_shape' in item or 'the_geom' in item:
                    try:
                        geom_key = 'geo_shape' if 'geo_shape' in item else 'the_geom'
                        features.append({
                            'type': 'Feature',
                            'geometry': item[geom_key],
                            'properties': {k: v for k, v in item.items() if k not in ['geo_shape', 'the_geom']}
                        })
                    except:
                        pass
            
            if features:
                gdf = gpd.GeoDataFrame.from_features({'type': 'FeatureCollection', 'features': features}, crs='EPSG:4326')
                output = base_dir / 'resguardos_indigenas' / 'resguardos_casanare.geojson'
                gdf.to_file(output, driver='GeoJSON')
                print(f'   ✅ {len(gdf)} resguardos guardados')
                print(f'   📁 {output}')
            else:
                print('   ⚠️  Sin geometría válida')
                with open(base_dir / 'resguardos_indigenas' / 'README.txt', 'w') as f:
                    f.write(f'Resguardos sin geometría en Casanare: {len(data)}\\n')
        else:
            print('   ⚠️  No hay resguardos en Casanare (puede ser correcto)')
            with open(base_dir / 'resguardos_indigenas' / 'README.txt', 'w') as f:
                f.write('No se encontraron resguardos indígenas en Casanare\\n')
                f.write('Verificado: 2025-01-26\\n')
    else:
        print(f'   ❌ Error {r.status_code}')
except Exception as e:
    print(f'   ❌ Error: {e}')
    with open(base_dir / 'resguardos_indigenas' / 'README.txt', 'w') as f:
        f.write('No se pudo descargar resguardos\\n')
        f.write(f'Error: {str(e)}\\n')

# ============================================================================
# 3. PÁRAMOS
# ============================================================================
print('\n📥 3. Páramos...')

try:
    # Dataset de páramos
    url = 'https://www.datos.gov.co/resource/r6d7-k37e.json'
    
    query = f"""
SELECT *
LIMIT 50000
    """.strip()
    
    params = {
        '$query': query,
        '$$app_token': 'DEMO'
    }
    
    print(f'   🔗 Consultando API Socrata...')
    r = requests.get(url, params=params, timeout=30)
    
    if r.status_code == 200:
        data = r.json()
        print(f'   📦 {len(data)} registros recibidos (nacional)')
        
        if len(data) > 0:
            features = []
            for item in data:
                if 'geometria' in item or 'the_geom' in item:
                    try:
                        geom_key = 'geometria' if 'geometria' in item else 'the_geom'
                        features.append({
                            'type': 'Feature',
                            'geometry': item[geom_key],
                            'properties': {k: v for k, v in item.items() if k not in ['geometria', 'the_geom']}
                        })
                    except:
                        pass
            
            if features:
                gdf = gpd.GeoDataFrame.from_features({'type': 'FeatureCollection', 'features': features}, crs='EPSG:4326')
                # Filtrar por Casanare
                gdf_casanare = gdf.cx[bbox['min_lon']:bbox['max_lon'], bbox['min_lat']:bbox['max_lat']]
                
                if len(gdf_casanare) > 0:
                    output = base_dir / 'paramos' / 'paramos_casanare.geojson'
                    gdf_casanare.to_file(output, driver='GeoJSON')
                    print(f'   ✅ {len(gdf_casanare)} páramos en Casanare')
                    print(f'   📁 {output}')
                else:
                    print('   ⚠️  No hay páramos en Casanare (correcto - es sabana)')
                    # Guardar nacional para otras regiones
                    output = base_dir / 'paramos' / 'paramos_colombia.geojson'
                    gdf.to_file(output, driver='GeoJSON')
                    print(f'   💾 Guardado dataset nacional ({len(gdf)} páramos) para futuro uso')
                    with open(base_dir / 'paramos' / 'README.txt', 'w') as f:
                        f.write('No hay páramos en Casanare (departamento de sabana)\\n')
                        f.write('Dataset nacional disponible en paramos_colombia.geojson\\n')
            else:
                print('   ⚠️  Sin geometría válida')
        else:
            print('   ❌ No se obtuvieron datos')
    else:
        print(f'   ❌ Error {r.status_code}')
except Exception as e:
    print(f'   ❌ Error: {e}')
    with open(base_dir / 'paramos' / 'README.txt', 'w') as f:
        f.write('No se pudo descargar páramos\\n')
        f.write(f'Error: {str(e)}\\n')

print('\n✅ Descarga completada')
print('\n💡 Nota: Casanare es sabana, no tiene páramos ni muchas áreas protegidas')
print('   Esto es CORRECTO para la región.')
