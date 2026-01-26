#!/usr/bin/env python3
"""
Descargador robusto de capas geográficas oficiales
Prueba múltiples fuentes hasta encontrar una que funcione
"""

import requests
import geopandas as gpd
from pathlib import Path
import json
import zipfile
import io

BASE_DIR = Path("datos_geograficos")
BBOX = (-73.0, 4.5, -69.8, 6.8)  # Casanare

print("="*80)
print("🔍 BUSCANDO FUENTES REALES DE DATOS GEOGRÁFICOS")
print("="*80)

# ============================================================================
# RESGUARDOS INDÍGENAS - Múltiples fuentes
# ============================================================================
print("\n" + "#"*80)
print("## RESGUARDOS INDÍGENAS")
print("#"*80)

resguardos_sources = [
    {
        "name": "ANT ArcGIS Hub",
        "url": "https://services.arcgis.com/DDzi7vRExVRMO5AB/arcgis/rest/services/Resguardo_Indigena_Formalizado/FeatureServer/0/query",
        "type": "arcgis",
        "params": {
            "where": "1=1",
            "outFields": "*",
            "geometryType": "esriGeometryEnvelope",
            "geometry": json.dumps({
                "xmin": BBOX[0], "ymin": BBOX[1],
                "xmax": BBOX[2], "ymax": BBOX[3],
                "spatialReference": {"wkid": 4326}
            }),
            "spatialRel": "esriSpatialRelIntersects",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "pgeojson"  # Probar pgeojson en lugar de geojson
        }
    },
    {
        "name": "ANT Simple Query",
        "url": "https://services.arcgis.com/DDzi7vRExVRMO5AB/arcgis/rest/services/Resguardo_Indigena_Formalizado/FeatureServer/0/query",
        "type": "arcgis_simple",
        "params": {
            "where": "DEPARTAMENTO='CASANARE'",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "pgeojson"
        }
    },
    {
        "name": "GeoNode Colombia",
        "url": "https://geonode.colombiaenmapas.gov.co/geoserver/ows",
        "type": "wfs",
        "params": {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": "geonode:resguardos_indigenas",
            "outputFormat": "application/json",
            "srsName": "EPSG:4326"
        }
    },
    {
        "name": "IGAC Tierras MapServer",
        "url": "https://mapas2.igac.gov.co/server/rest/services/carto/carto100000colombia2019/MapServer/27/query",
        "type": "arcgis",
        "params": {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "pgeojson"
        }
    }
]

resguardos_descargados = False

for source in resguardos_sources:
    print(f"\n📥 Intentando: {source['name']}")
    print(f"   🔗 {source['url']}")
    
    try:
        response = requests.get(source['url'], params=source['params'], timeout=60)
        
        if response.status_code == 200:
            try:
                # Intentar parsear como GeoJSON
                data = response.json()
                
                if 'features' in data and len(data['features']) > 0:
                    gdf = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
                    
                    # Filtrar por Casanare si es nacional
                    if len(gdf) > 100:  # Probablemente nacional
                        print(f"   📊 Dataset nacional: {len(gdf)} resguardos")
                        gdf = gdf.cx[BBOX[0]:BBOX[2], BBOX[1]:BBOX[3]]
                    
                    print(f"   ✅ Resguardos en Casanare: {len(gdf)}")
                    
                    if len(gdf) > 0:
                        # Guardar
                        output_dir = BASE_DIR / "resguardos_indigenas"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = output_dir / "resguardos_casanare.geojson"
                        gdf.to_file(output_file, driver="GeoJSON")
                        
                        print(f"   💾 Guardado: {output_file}")
                        print(f"   📏 {output_file.stat().st_size / 1024:.2f} KB")
                        resguardos_descargados = True
                        break
                    else:
                        print(f"   ℹ️  No hay resguardos en Casanare según {source['name']}")
                        # Guardar vacío pero con metadata
                        output_dir = BASE_DIR / "resguardos_indigenas"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = output_dir / "resguardos_casanare.geojson"
                        
                        empty_geojson = {
                            "type": "FeatureCollection",
                            "features": [],
                            "metadata": {
                                "fuente": source['name'],
                                "fecha": "2025-01-26",
                                "region": "Casanare",
                                "verificado": True,
                                "nota": "No hay resguardos indígenas formalizados en Casanare"
                            }
                        }
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(empty_geojson, f, indent=2, ensure_ascii=False)
                        
                        print(f"   💾 Verificado y guardado (sin resguardos): {output_file}")
                        resguardos_descargados = True
                        break
                        
            except Exception as e:
                print(f"   ⚠️  Error parseando respuesta: {e}")
        else:
            print(f"   ❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

if not resguardos_descargados:
    print("\n⚠️  No se pudo descargar resguardos de ninguna fuente")

# ============================================================================
# PÁRAMOS - Múltiples fuentes
# ============================================================================
print("\n" + "#"*80)
print("## PÁRAMOS")
print("#"*80)

paramos_sources = [
    {
        "name": "SIAC/MADS ArcGIS",
        "url": "https://services.arcgis.com/zNC4XQ1B0uOEuIBN/arcgis/rest/services/Paramos_Delimitados/FeatureServer/0/query",
        "type": "arcgis",
        "params": {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "pgeojson"
        }
    },
    {
        "name": "Instituto Humboldt",
        "url": "http://geoservicios.humboldt.org.co/arcgis/rest/services/Publico/Paramos/MapServer/0/query",
        "type": "arcgis",
        "params": {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "pgeojson"
        }
    },
    {
        "name": "GeoNode Colombia Páramos",
        "url": "https://geonode.colombiaenmapas.gov.co/geoserver/ows",
        "type": "wfs",
        "params": {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": "geonode:paramos",
            "outputFormat": "application/json",
            "srsName": "EPSG:4326"
        }
    }
]

paramos_descargados = False

for source in paramos_sources:
    print(f"\n📥 Intentando: {source['name']}")
    print(f"   🔗 {source['url']}")
    
    try:
        response = requests.get(source['url'], params=source['params'], timeout=60)
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if 'features' in data:
                    gdf = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
                    print(f"   📊 Páramos nacional: {len(gdf)}")
                    
                    # Filtrar por Casanare
                    gdf_casanare = gdf.cx[BBOX[0]:BBOX[2], BBOX[1]:BBOX[3]]
                    
                    print(f"   ✅ Páramos en Casanare: {len(gdf_casanare)}")
                    
                    # Guardar (incluso si está vacío - Casanare no tiene páramos)
                    output_dir = BASE_DIR / "paramos"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_file = output_dir / "paramos_casanare.geojson"
                    
                    if len(gdf_casanare) > 0:
                        gdf_casanare.to_file(output_file, driver="GeoJSON")
                    else:
                        # Guardar vacío con metadata
                        empty_geojson = {
                            "type": "FeatureCollection",
                            "features": [],
                            "metadata": {
                                "fuente": source['name'],
                                "fecha": "2025-01-26",
                                "region": "Casanare",
                                "verificado": True,
                                "nota": "Casanare no tiene páramos (es región de sabana/llanura)"
                            }
                        }
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(empty_geojson, f, indent=2, ensure_ascii=False)
                    
                    print(f"   💾 Guardado: {output_file}")
                    print(f"   📏 {output_file.stat().st_size / 1024:.2f} KB")
                    paramos_descargados = True
                    break
                    
            except Exception as e:
                print(f"   ⚠️  Error parseando respuesta: {e}")
        else:
            print(f"   ❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

if not paramos_descargados:
    print("\n⚠️  No se pudo descargar páramos de ninguna fuente")

# ============================================================================
# RESUMEN
# ============================================================================
print("\n" + "="*80)
print("📊 RESUMEN FINAL")
print("="*80)

capas_status = {
    "RUNAP (Áreas Protegidas)": BASE_DIR / "runap" / "runap_casanare.geojson",
    "Resguardos Indígenas": BASE_DIR / "resguardos_indigenas" / "resguardos_casanare.geojson",
    "Páramos": BASE_DIR / "paramos" / "paramos_casanare.geojson"
}

for nombre, archivo in capas_status.items():
    if archivo.exists():
        try:
            gdf = gpd.read_file(archivo)
            size = archivo.stat().st_size / 1024
            print(f"✅ {nombre}: {len(gdf)} elementos ({size:.2f} KB)")
        except:
            size = archivo.stat().st_size
            print(f"✅ {nombre}: Archivo presente ({size} bytes)")
    else:
        print(f"❌ {nombre}: No descargado")

print("\n" + "="*80)
