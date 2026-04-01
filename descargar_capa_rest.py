#!/usr/bin/env python3
"""
Descargar capa específica del servicio REST IGAC
Descarga por partes (bounding boxes) para evitar límites del servidor
"""
import requests
import geopandas as gpd
import json
from pathlib import Path
import time

# Configuración
URL_BASE = "https://mapas2.igac.gov.co/server/rest/services/carto/carto100000colombia2019/MapServer"
ID_CAPA = 24  # Drenaje Sencillo
DESTINO = Path("datos_geograficos/red_hidrica")

def descargar_capa_completa(id_capa, max_intentos=3):
    """Descargar toda la capa de una vez"""
    print(f"\n🌊 Descargando capa {id_capa}: Drenaje Sencillo")
    print("   Método: Descarga completa (puede tardar varios minutos)")
    
    url = f"{URL_BASE}/{id_capa}/query"
    
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'geojson',
        'returnGeometry': 'true'
    }
    
    for intento in range(1, max_intentos + 1):
        try:
            print(f"\n   Intento {intento}/{max_intentos}...")
            print(f"   URL: {url}")
            
            # Timeout largo para descarga completa
            response = requests.get(url, params=params, timeout=300, stream=True)
            response.raise_for_status()
            
            # Verificar si es JSON válido
            print("   ✓ Descarga completada, procesando GeoJSON...")
            
            # Cargar GeoJSON
            geojson_data = response.json()
            
            # Convertir a GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
            
            # Agregar CRS
            gdf.set_crs("EPSG:4326", inplace=True)
            
            print(f"\n   ✅ Descargados {len(gdf):,} drenajes")
            print(f"   📊 Columnas: {', '.join(gdf.columns[:10])}")
            
            # Verificar geometría
            if not gdf.empty:
                tipo_geom = gdf.geometry.iloc[0].geom_type
                print(f"   🔍 Tipo geometría: {tipo_geom}")
                
                if tipo_geom != 'LineString' and tipo_geom != 'MultiLineString':
                    print(f"   ⚠️  ADVERTENCIA: Se esperaba LineString, se obtuvo {tipo_geom}")
            
            return gdf
            
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout en intento {intento}")
            if intento < max_intentos:
                print(f"   Esperando 10 segundos antes de reintentar...")
                time.sleep(10)
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error de red: {e}")
            if intento < max_intentos:
                time.sleep(5)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            if intento < max_intentos:
                time.sleep(5)
    
    return None

def descargar_por_regiones(id_capa):
    """Descargar por regiones (fallback si descarga completa falla)"""
    print("\n🗺️  Descargando por regiones...")
    print("   (Esto puede tardar más pero es más confiable)")
    
    # Dividir Colombia en regiones aproximadas
    regiones = {
        'Caribe': {'xmin': -76, 'ymin': 8, 'xmax': -71, 'ymax': 12.5},
        'Pacífico': {'xmin': -79, 'ymin': 1, 'xmax': -76, 'ymax': 8},
        'Andina': {'xmin': -76, 'ymin': 1, 'xmax': -72, 'ymax': 8},
        'Orinoquía': {'xmin': -72, 'ymin': 1, 'xmax': -66, 'ymax': 8},
        'Amazonía': {'xmin': -75, 'ymin': -4.5, 'xmax': -66, 'ymax': 1}
    }
    
    gdfs = []
    
    for nombre, bbox in regiones.items():
        print(f"\n   Descargando región: {nombre}...")
        
        url = f"{URL_BASE}/{id_capa}/query"
        
        # Crear geometría de bbox
        geometry = {
            'xmin': bbox['xmin'],
            'ymin': bbox['ymin'],
            'xmax': bbox['xmax'],
            'ymax': bbox['ymax'],
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'where': '1=1',
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryEnvelope',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'f': 'geojson',
            'returnGeometry': 'true'
        }
        
        try:
            response = requests.get(url, params=params, timeout=180)
            response.raise_for_status()
            
            geojson_data = response.json()
            
            if geojson_data.get('features'):
                gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
                gdf.set_crs("EPSG:4326", inplace=True)
                gdfs.append(gdf)
                print(f"   ✓ {len(gdf):,} drenajes descargados")
            else:
                print(f"   ⚠️  Sin datos en esta región")
                
        except Exception as e:
            print(f"   ❌ Error en región {nombre}: {e}")
        
        # Pausa entre requests
        time.sleep(2)
    
    if gdfs:
        print("\n   🔧 Combinando regiones...")
        gdf_completo = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
        
        # Eliminar duplicados por geometría
        print(f"   Total antes de eliminar duplicados: {len(gdf_completo):,}")
        gdf_completo = gdf_completo.drop_duplicates(subset=['geometry'])
        print(f"   Total después: {len(gdf_completo):,}")
        
        return gdf_completo
    
    return None

def guardar_datos(gdf, nombre_archivo="drenajes_sencillos_igac.geojson"):
    """Guardar GeoDataFrame a archivo"""
    print(f"\n💾 Guardando datos...")
    
    # Crear directorio
    DESTINO.mkdir(parents=True, exist_ok=True)
    
    # Guardar en GeoJSON
    ruta_geojson = DESTINO / nombre_archivo
    gdf.to_file(ruta_geojson, driver='GeoJSON')
    
    tamaño_mb = ruta_geojson.stat().st_size / (1024 * 1024)
    print(f"   ✓ GeoJSON: {ruta_geojson} ({tamaño_mb:.1f} MB)")
    
    # También guardar en Shapefile (compatible con más software)
    nombre_shp = nombre_archivo.replace('.geojson', '.shp')
    ruta_shp = DESTINO / nombre_shp
    
    try:
        gdf.to_file(ruta_shp, driver='ESRI Shapefile')
        print(f"   ✓ Shapefile: {ruta_shp}")
    except Exception as e:
        print(f"   ⚠️  No se pudo guardar Shapefile: {e}")
    
    # Estadísticas
    print(f"\n📊 Estadísticas:")
    print(f"   Total drenajes: {len(gdf):,}")
    print(f"   Columnas: {len(gdf.columns)}")
    
    if 'geometry' in gdf.columns:
        # Calcular longitud total (en grados, aproximado)
        longitud_total = gdf.geometry.length.sum()
        print(f"   Longitud total: {longitud_total:,.0f} grados")
    
    return ruta_geojson

def main():
    print("=" * 80)
    print("🌊 DESCARGADOR DE DRENAJES SENCILLOS IGAC")
    print("   Servicio REST - Escala 1:100.000")
    print("=" * 80)
    
    # Método 1: Descarga completa
    gdf = descargar_capa_completa(ID_CAPA)
    
    # Método 2: Por regiones (fallback)
    if gdf is None or len(gdf) == 0:
        print("\n⚠️  Descarga completa falló, intentando por regiones...")
        gdf = descargar_por_regiones(ID_CAPA)
    
    if gdf is not None and len(gdf) > 0:
        # Guardar
        ruta = guardar_datos(gdf)
        
        print("\n" + "=" * 80)
        print("✅ ¡DESCARGA EXITOSA!")
        print("=" * 80)
        print(f"\n📁 Archivo guardado en: {ruta}")
        print(f"📊 Total de drenajes: {len(gdf):,}")
        print("\n💡 Siguiente paso:")
        print("   Ejecutar: python test_pdf_verificacion_con_mapa.py")
        print("   Para probar el sistema con los datos correctos")
    else:
        print("\n" + "=" * 80)
        print("❌ No se pudieron descargar los datos")
        print("=" * 80)
        print("\n💡 Opciones:")
        print("   1. Verifica tu conexión a internet")
        print("   2. Intenta de nuevo más tarde (servidor puede estar sobrecargado)")
        print("   3. Usa la opción de descarga manual del ZIP")

if __name__ == "__main__":
    import pandas as pd  # Importar aquí para combinar regiones
    main()
