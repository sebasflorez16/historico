#!/usr/bin/env python3
"""
Descargar drenajes desde WFS IGAC (sin límite de 2,000)
WFS es estándar OGC y generalmente permite descargas completas
"""
import geopandas as gpd
from pathlib import Path
import requests

# URL WFS del servicio
URL_WFS = "https://mapas2.igac.gov.co/server/rest/services/carto/carto100000colombia2019/MapServer/24/query"

DESTINO = Path("datos_geograficos/red_hidrica")

def descargar_por_bbox_cesar():
    """
    Descargar solo la región del Cesar (departamento del usuario)
    Esto reduce MUCHO el tamaño
    """
    print("🗺️  Descargando drenajes solo del departamento del Cesar")
    print("   (Mucho más rápido y ligero que todo Colombia)")
    
    # Bounding box aproximado del Cesar
    # Coordenadas: (lon_min, lat_min, lon_max, lat_max)
    bbox_cesar = {
        'xmin': -74.5,
        'ymin': 7.5,
        'xmax': -72.5,
        'ymax': 11.0
    }
    
    print(f"\n   📍 Área de descarga: Cesar")
    print(f"   📐 BBox: {bbox_cesar}")
    
    # Construir query con geometría
    params = {
        'where': '1=1',
        'geometry': f"{bbox_cesar['xmin']},{bbox_cesar['ymin']},{bbox_cesar['xmax']},{bbox_cesar['ymax']}",
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'outFields': '*',
        'returnGeometry': 'true',
        'f': 'geojson'
    }
    
    try:
        print("\n   ⏳ Descargando...")
        response = requests.get(URL_WFS, params=params, timeout=120)
        response.raise_for_status()
        
        geojson = response.json()
        
        if 'features' not in geojson or not geojson['features']:
            print("   ⚠️  No se encontraron datos en esta región")
            return None
        
        # Convertir a GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson['features'])
        gdf.set_crs("EPSG:4326", inplace=True)
        
        print(f"\n   ✅ Descargados: {len(gdf):,} drenajes")
        
        # Guardar
        DESTINO.mkdir(parents=True, exist_ok=True)
        
        ruta_geojson = DESTINO / "drenajes_cesar_igac.geojson"
        gdf.to_file(ruta_geojson, driver='GeoJSON')
        
        ruta_shp = DESTINO / "drenajes_cesar_igac.shp"
        gdf.to_file(ruta_shp, driver='ESRI Shapefile')
        
        tamaño = ruta_geojson.stat().st_size / (1024 * 1024)
        print(f"\n   💾 Guardado:")
        print(f"   - {ruta_geojson.name} ({tamaño:.1f} MB)")
        print(f"   - {ruta_shp.name}")
        
        return gdf
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        return None

def descargar_colombia_completa_paginado():
    """
    Descargar todo Colombia usando paginación
    (Descarga en bloques de 2,000 hasta obtener todos)
    """
    print("🌎 Descargando Colombia completa (con paginación)")
    print("   ⚠️  Esto puede tardar varios minutos...")
    
    gdfs = []
    offset = 0
    limit = 2000
    total_descargados = 0
    
    while True:
        print(f"\n   📦 Descargando bloque {len(gdfs) + 1} (offset: {offset})...")
        
        params = {
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': 'true',
            'resultOffset': offset,
            'resultRecordCount': limit,
            'f': 'geojson'
        }
        
        try:
            response = requests.get(URL_WFS, params=params, timeout=120)
            response.raise_for_status()
            
            geojson = response.json()
            
            if 'features' not in geojson or not geojson['features']:
                print("   ✓ No hay más datos, descarga completa")
                break
            
            num_features = len(geojson['features'])
            
            if num_features == 0:
                break
            
            gdf = gpd.GeoDataFrame.from_features(geojson['features'])
            gdf.set_crs("EPSG:4326", inplace=True)
            gdfs.append(gdf)
            
            total_descargados += num_features
            print(f"   ✓ {num_features:,} drenajes (total: {total_descargados:,})")
            
            # Si recibimos menos de 2000, no hay más datos
            if num_features < limit:
                print("   ✓ Última página alcanzada")
                break
            
            offset += limit
            
        except Exception as e:
            print(f"   ❌ Error en bloque {len(gdfs) + 1}: {e}")
            break
    
    if gdfs:
        print(f"\n   🔧 Combinando {len(gdfs)} bloques...")
        import pandas as pd
        gdf_completo = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
        
        # Guardar
        DESTINO.mkdir(parents=True, exist_ok=True)
        
        ruta_geojson = DESTINO / "drenajes_colombia_completo.geojson"
        gdf_completo.to_file(ruta_geojson, driver='GeoJSON')
        
        ruta_shp = DESTINO / "drenajes_colombia_completo.shp"
        gdf_completo.to_file(ruta_shp, driver='ESRI Shapefile')
        
        tamaño = ruta_geojson.stat().st_size / (1024 * 1024)
        print(f"\n   💾 Guardado:")
        print(f"   - {ruta_geojson.name} ({tamaño:.1f} MB)")
        print(f"   - {ruta_shp.name}")
        print(f"\n   📊 Total drenajes: {len(gdf_completo):,}")
        
        return gdf_completo
    
    return None

def main():
    print("=" * 80)
    print("🌊 DESCARGADOR DE DRENAJES IGAC - Versión WFS Mejorada")
    print("=" * 80)
    
    print("\n¿Qué región descargar?")
    print("1. Solo Cesar (rápido, ~5-10 MB)")
    print("2. Colombia completa con paginación (lento, puede fallar)")
    
    # Para automatizar, usar opción 1 (Cesar)
    print("\nUsando opción 1: Descarga regional (Cesar)")
    
    gdf = descargar_por_bbox_cesar()
    
    if gdf is not None and len(gdf) > 0:
        print("\n" + "=" * 80)
        print("✅ ¡DESCARGA EXITOSA!")
        print("=" * 80)
        print(f"\n📊 Drenajes descargados: {len(gdf):,}")
        print("\n💡 Siguiente paso:")
        print("   python test_pdf_verificacion_con_mapa.py")
    else:
        print("\n" + "=" * 80)
        print("⚠️ Descarga falló o sin datos")
        print("=" * 80)
        print("\n💡 Opciones:")
        print("   1. Intenta de nuevo (puede ser problema temporal del servidor)")
        print("   2. Usa los 2,000 drenajes ya descargados (suficiente para pruebas)")

if __name__ == "__main__":
    import pandas as pd
    main()
