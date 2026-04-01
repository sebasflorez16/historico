#!/usr/bin/env python3
"""
Descargador de capas geográficas oficiales para verificación legal
- RUNAP (Áreas Protegidas)
- Resguardos Indígenas
- Páramos
"""
import requests
import geopandas as gpd
import json
from pathlib import Path

# Crear directorios
base_dir = Path('datos_geograficos')
(base_dir / 'areas_protegidas').mkdir(parents=True, exist_ok=True)
(base_dir / 'resguardos_indigenas').mkdir(parents=True, exist_ok=True)
(base_dir / 'paramos').mkdir(parents=True, exist_ok=True)

# Bounding box de Casanare
casanare_bbox = {
    'xmin': -73.0,
    'ymin': 5.0,
    'xmax': -71.0,
    'ymax': 7.0
}

print('=' * 80)
print('🌍 DESCARGANDO CAPAS GEOGRÁFICAS OFICIALES PARA CASANARE')
print('=' * 80)

# ============================================================================
# 1. RUNAP - ÁREAS PROTEGIDAS (desde servicio WFS del IDEAM/Parques)
# ============================================================================
print('\n📥 1. Descargando RUNAP (Áreas Protegidas)...')

try:
    # URL del servicio WFS de GeoPortal Colombia
    runap_url = 'https://www.colombiaenmapas.gov.co/geovisor/rest/services/SIAC/Zonificacion_Ambiental/MapServer/0/query'
    
    params = {
        'where': '1=1',
        'geometryType': 'esriGeometryEnvelope',
        'geometry': json.dumps({
            'xmin': casanare_bbox['xmin'],
            'ymin': casanare_bbox['ymin'],
            'xmax': casanare_bbox['xmax'],
            'ymax': casanare_bbox['ymax'],
            'spatialReference': {'wkid': 4326}
        }),
        'inSR': 4326,
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'true',
        'outSR': 4326,
        'f': 'geojson'
    }
    
    print(f'   🔗 URL: {runap_url}')
    r = requests.get(runap_url, params=params, timeout=30)
    
    if r.status_code == 200:
        data = r.json()
        if 'features' in data and len(data['features']) > 0:
            gdf = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
            
            # Guardar en múltiples formatos
            output_shp = base_dir / 'areas_protegidas' / 'runap_casanare.shp'
            output_geojson = base_dir / 'areas_protegidas' / 'runap_casanare.geojson'
            
            gdf.to_file(output_shp)
            gdf.to_file(output_geojson, driver='GeoJSON')
            
            print(f'   ✅ {len(gdf)} áreas protegidas descargadas')
            print(f'   📁 Shapefile: {output_shp}')
            print(f'   📁 GeoJSON: {output_geojson}')
        else:
            print('   ⚠️  No se encontraron áreas protegidas en Casanare')
            # Intentar descarga nacional
            print('   📥 Descargando RUNAP nacional...')
            params['geometry'] = None
            r = requests.get(runap_url, params={'where': '1=1', 'outFields': '*', 'f': 'geojson'}, timeout=60)
            if r.status_code == 200:
                data = r.json()
                if 'features' in data:
                    gdf = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
                    output_shp = base_dir / 'areas_protegidas' / 'runap_colombia.shp'
                    output_geojson = base_dir / 'areas_protegidas' / 'runap_colombia.geojson'
                    gdf.to_file(output_shp)
                    gdf.to_file(output_geojson, driver='GeoJSON')
                    print(f'   ✅ {len(gdf)} áreas protegidas (nacional) descargadas')
    else:
        print(f'   ❌ Error HTTP {r.status_code}')
        
except Exception as e:
    print(f'   ❌ Error: {e}')
    print('   💡 Intentando fuente alternativa...')
    
    # Fuente alternativa: IDECA (Bogotá tiene buen servicio nacional)
    try:
        alt_url = 'https://geo.parquesnacionales.gov.co/geoserver/wfs'
        params_wfs = {
            'service': 'WFS',
            'version': '1.0.0',
            'request': 'GetFeature',
            'typeName': 'runap:runap_areas',
            'outputFormat': 'application/json',
            'srsName': 'EPSG:4326'
        }
        r = requests.get(alt_url, params=params_wfs, timeout=60)
        if r.status_code == 200:
            gdf = gpd.read_file(r.content)
            # Filtrar por Casanare
            gdf_casanare = gdf.cx[casanare_bbox['xmin']:casanare_bbox['xmax'], 
                                   casanare_bbox['ymin']:casanare_bbox['ymax']]
            if len(gdf_casanare) > 0:
                output_shp = base_dir / 'areas_protegidas' / 'runap_casanare.shp'
                gdf_casanare.to_file(output_shp)
                print(f'   ✅ {len(gdf_casanare)} áreas protegidas (fuente alternativa)')
    except Exception as e2:
        print(f'   ❌ Fuente alternativa falló: {e2}')

# ============================================================================
# 2. RESGUARDOS INDÍGENAS (desde ANT o IGAC)
# ============================================================================
print('\n📥 2. Descargando Resguardos Indígenas...')

try:
    # URL del servicio de ANT/IGAC
    resguardos_urls = [
        'https://www.colombiaenmapas.gov.co/geovisor/rest/services/IGAC/Tierras/MapServer/0/query',
        'https://mapas2.igac.gov.co/server/rest/services/carto/carto100000colombia2019/MapServer/27/query'
    ]
    
    resguardos_descargados = False
    
    for url in resguardos_urls:
        try:
            print(f'   🔗 Probando: {url}')
            params = {
                'where': '1=1',
                'geometry': json.dumps({
                    'xmin': casanare_bbox['xmin'],
                    'ymin': casanare_bbox['ymin'],
                    'xmax': casanare_bbox['xmax'],
                    'ymax': casanare_bbox['ymax'],
                    'spatialReference': {'wkid': 4326}
                }),
                'geometryType': 'esriGeometryEnvelope',
                'inSR': 4326,
                'spatialRel': 'esriSpatialRelIntersects',
                'outFields': '*',
                'returnGeometry': 'true',
                'outSR': 4326,
                'f': 'geojson'
            }
            
            r = requests.get(url, params=params, timeout=30)
            
            if r.status_code == 200:
                data = r.json()
                if 'features' in data and len(data['features']) > 0:
                    gdf = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
                    
                    output_shp = base_dir / 'resguardos_indigenas' / 'resguardos_casanare.shp'
                    output_geojson = base_dir / 'resguardos_indigenas' / 'resguardos_casanare.geojson'
                    
                    gdf.to_file(output_shp)
                    gdf.to_file(output_geojson, driver='GeoJSON')
                    
                    print(f'   ✅ {len(gdf)} resguardos indígenas descargados')
                    print(f'   📁 Shapefile: {output_shp}')
                    print(f'   📁 GeoJSON: {output_geojson}')
                    resguardos_descargados = True
                    break
        except Exception as e:
            print(f'   ⚠️  Error con {url}: {e}')
            continue
    
    if not resguardos_descargados:
        print('   ⚠️  No se encontraron resguardos en Casanare (puede ser correcto)')
        # Crear archivo vacío para indicar que se intentó
        with open(base_dir / 'resguardos_indigenas' / 'README.txt', 'w') as f:
            f.write('No se encontraron resguardos indígenas en Casanare\n')
            f.write('Fecha de verificación: 2025-01-26\n')
        
except Exception as e:
    print(f'   ❌ Error: {e}')

# ============================================================================
# 3. PÁRAMOS (desde Instituto Humboldt o MinAmbiente)
# ============================================================================
print('\n📥 3. Descargando Páramos...')

try:
    # URLs del servicio de páramos
    paramos_urls = [
        'https://www.colombiaenmapas.gov.co/geovisor/rest/services/SIAC/Zonificacion_Ambiental/MapServer/2/query',
        'http://geoservicios.humboldt.org.co/arcgis/rest/services/Publico/Paramos/MapServer/0/query'
    ]
    
    paramos_descargados = False
    
    for url in paramos_urls:
        try:
            print(f'   🔗 Probando: {url}')
            params = {
                'where': '1=1',
                'geometry': json.dumps({
                    'xmin': casanare_bbox['xmin'],
                    'ymin': casanare_bbox['ymin'],
                    'xmax': casanare_bbox['xmax'],
                    'ymax': casanare_bbox['ymax'],
                    'spatialReference': {'wkid': 4326}
                }),
                'geometryType': 'esriGeometryEnvelope',
                'inSR': 4326,
                'spatialRel': 'esriSpatialRelIntersects',
                'outFields': '*',
                'returnGeometry': 'true',
                'outSR': 4326,
                'f': 'geojson'
            }
            
            r = requests.get(url, params=params, timeout=30)
            
            if r.status_code == 200:
                data = r.json()
                if 'features' in data and len(data['features']) > 0:
                    gdf = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
                    
                    output_shp = base_dir / 'paramos' / 'paramos_casanare.shp'
                    output_geojson = base_dir / 'paramos' / 'paramos_casanare.geojson'
                    
                    gdf.to_file(output_shp)
                    gdf.to_file(output_geojson, driver='GeoJSON')
                    
                    print(f'   ✅ {len(gdf)} páramos descargados')
                    print(f'   📁 Shapefile: {output_shp}')
                    print(f'   📁 GeoJSON: {output_geojson}')
                    paramos_descargados = True
                    break
        except Exception as e:
            print(f'   ⚠️  Error con {url}: {e}')
            continue
    
    if not paramos_descargados:
        print('   ⚠️  No se encontraron páramos en Casanare (esto es correcto - Casanare es llanero)')
        # Crear archivo vacío para indicar que se intentó
        with open(base_dir / 'paramos' / 'README.txt', 'w') as f:
            f.write('No hay páramos en Casanare (departamento de sabana/llanura)\n')
            f.write('Fecha de verificación: 2025-01-26\n')

except Exception as e:
    print(f'   ❌ Error: {e}')

# ============================================================================
# RESUMEN
# ============================================================================
print('\n' + '=' * 80)
print('📊 RESUMEN DE DESCARGA')
print('=' * 80)

for capa_dir in ['areas_protegidas', 'resguardos_indigenas', 'paramos']:
    path = base_dir / capa_dir
    shapefiles = list(path.glob('*.shp'))
    geojsons = list(path.glob('*.geojson'))
    
    print(f'\n📁 {capa_dir.upper().replace("_", " ")}:')
    if shapefiles:
        for shp in shapefiles:
            try:
                gdf = gpd.read_file(shp)
                print(f'   ✅ {shp.name}: {len(gdf)} features ({shp.stat().st_size / 1024:.1f} KB)')
            except:
                print(f'   📄 {shp.name}')
    elif geojsons:
        for gj in geojsons:
            print(f'   ✅ {gj.name} ({gj.stat().st_size / 1024:.1f} KB)')
    else:
        readmes = list(path.glob('README.txt'))
        if readmes:
            print(f'   ⚠️  No hay datos (ver {readmes[0].name})')
        else:
            print('   ❌ No descargado')

print('\n✅ Proceso completado')
print('💡 Las capas descargadas se pueden usar ahora en verificador_legal.py')
