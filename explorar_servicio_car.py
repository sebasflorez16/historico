#!/usr/bin/env python3
"""
Explorar y descargar datos del servicio ArcGIS de la CAR
"""
import geopandas as gpd
import requests
from pathlib import Path

print("="*80)
print("🔍 EXPLORANDO SERVICIO CAR")
print("="*80 + "\n")

base_url = "https://sig.car.gov.co/arcgis/rest/services/CARTOGRAFIA_EN_LINEA/CARTOGRAFIA_EN_LINEA/MapServer"

# 1. Ver capas disponibles
print("📊 Consultando capas disponibles...\n")
response = requests.get(f"{base_url}?f=json")
data = response.json()

if 'layers' in data:
    print(f"✅ Servicio: {data.get('mapName', 'Sin nombre')}")
    print(f"   Total capas: {len(data['layers'])}\n")
    
    print("Primeras 30 capas:")
    print("-" * 80)
    for layer in data['layers'][:30]:
        print(f"  {layer['id']:3d} - {layer['name']}")
    
    # 2. Buscar capas de red hídrica
    print("\n" + "="*80)
    print("🔍 BUSCANDO CAPAS DE RED HÍDRICA")
    print("="*80 + "\n")
    
    capas_hidrica = []
    for layer in data['layers']:
        nombre = layer['name'].lower()
        if any(palabra in nombre for palabra in ['red', 'hidri', 'drenaje', 'rio', 'quebrada', 'agua', 'corriente']):
            capas_hidrica.append(layer)
            print(f"  {layer['id']:3d} - {layer['name']}")
    
    # 3. Ver detalles de capa 7
    print("\n" + "="*80)
    print("🔍 DETALLES DE CAPA 7 (la que encontraste)")
    print("="*80 + "\n")
    
    response = requests.get(f"{base_url}/7?f=json")
    layer_data = response.json()
    
    print(f"Nombre: {layer_data.get('name', 'N/A')}")
    print(f"Tipo: {layer_data.get('type', 'N/A')}")
    print(f"Geometría: {layer_data.get('geometryType', 'N/A')}")
    
    geom_type = layer_data.get('geometryType', '')
    
    if 'Polyline' in geom_type or 'Line' in geom_type:
        print("✅ CORRECTO: Esta capa contiene LÍNEAS (red de drenaje)")
    elif 'Polygon' in geom_type:
        print("❌ INCORRECTO: Esta capa contiene POLÍGONOS (zonificación)")
    
    # 4. Intentar descargar capa 7
    if 'Polyline' in geom_type or 'Line' in geom_type or True:  # Intentar de todas formas
        print("\n" + "="*80)
        print("📥 INTENTANDO DESCARGAR CAPA 7")
        print("="*80 + "\n")
        
        try:
            # Convertir MapServer a FeatureServer para descarga
            feature_url = base_url.replace('/MapServer', '/FeatureServer')
            query_url = f"{feature_url}/7/query?where=1=1&outFields=*&f=geojson"
            
            print(f"URL de descarga: {query_url}\n")
            print("Descargando... (puede tardar varios minutos)\n")
            
            gdf = gpd.read_file(query_url)
            
            print(f"✅ Descargado: {len(gdf)} elementos")
            print(f"   Tipos: {gdf.geometry.geom_type.unique()}")
            
            # Guardar
            Path('datos_geograficos/red_hidrica').mkdir(parents=True, exist_ok=True)
            output = 'datos_geograficos/red_hidrica/red_hidrica_car.shp'
            gdf.to_file(output)
            
            print(f"\n✅ Guardado en: {output}")
            
        except Exception as e:
            print(f"❌ Error descargando: {e}")
            print("\n💡 ALTERNATIVA: Descarga manual")
            print(f"   1. Ir a: {base_url}/7")
            print(f"   2. Click 'Query'")
            print(f"   3. Format: GeoJSON")
            print(f"   4. Where: 1=1")
            print(f"   5. Submit Query")

print("\n" + "="*80)
