#!/usr/bin/env python
"""
Descarga Automática de Red Hídrica desde Múltiples Fuentes
===========================================================

Intenta 4 métodos de descarga en orden de preferencia:
1. REST API - Atlas Colombia 2024 (PREFERIDO - datos oficiales) ⭐
2. WFS Service - IGAC (BACKUP 1 - datos oficiales) 🔄
3. OpenStreetMap Overpass API (BACKUP 2 - automático) 🗺️
4. Descarga manual GDB Nacional (BACKUP 3 - guía) 📖

Descarga:
- Capa: Río (LineString - cauces)
- Zona: Departamentos Casanare + Meta
- Formato salida: Shapefile (.shp)

Autor: AgroTech Histórico
Fecha: Enero 2026
"""

import os
import sys
import requests
import geopandas as gpd
from pathlib import Path
import json
import time
from shapely.geometry import LineString, MultiLineString, mapping

print("=" * 80)
print("🌊 DESCARGA AUTOMÁTICA DE RED HÍDRICA (MULTI-FUENTE)")
print("=" * 80)

# Configuración de métodos de descarga
METODO_1_REST = {
    'nombre': 'REST API - Atlas Colombia 2024',
    'url': 'https://mapas.igac.gov.co/server/rest/services/atlas/hidrografiasuperficial/MapServer/0/query',
    'tipo': 'rest',
    'prioridad': 1,
    'fuente': 'oficial'
}

METODO_2_WFS = {
    'nombre': 'WFS Service - IGAC',
    'url': 'https://mapas.igac.gov.co/server/services/atlas/hidrografiasuperficial/MapServer/WFSServer',
    'tipo': 'wfs',
    'layer': 'atlas_hidrografiasuperficial:Río',
    'prioridad': 2,
    'fuente': 'oficial'
}

METODO_3_OSM = {
    'nombre': 'OpenStreetMap Overpass API',
    'url': 'https://overpass-api.de/api/interpreter',
    'tipo': 'osm',
    'prioridad': 3,
    'fuente': 'colaborativa'
}

OUTPUT_DIR = Path(__file__).parent / 'datos_geograficos' / 'red_hidrica'
OUTPUT_FILE = 'red_hidrica_casanare_meta_igac_2024.shp'
BBOX_TAURAMENA = [-72.5, 5.0, -72.0, 5.5]  # Para validación de cobertura
BBOX_CASANARE_META = (-74.5, 2.0, -69.0, 6.5)  # [min_lon, min_lat, max_lon, max_lat]

# Crear directorio si no existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def descargar_rest_api(filtro_dpto: str = "DEPARTAMENTO IN ('CASANARE', 'META')") -> gpd.GeoDataFrame:
    """
    Método 1: Descarga desde REST API IGAC (JSON/GeoJSON) ⭐
    
    Args:
        filtro_dpto: Filtro SQL para departamentos
        
    Returns:
        GeoDataFrame con cauces o None si falla
    """
    print(f"\n📡 MÉTODO 1: {METODO_1_REST['nombre']}")
    print(f"   Fuente: {METODO_1_REST['fuente'].upper()}")
    print(f"   URL: {METODO_1_REST['url']}")
    
    # Parámetros de consulta para ArcGIS REST API
    params = {
        'where': filtro_dpto,
        'outFields': '*',
        'f': 'geojson',
        'returnGeometry': 'true',
        'spatialRel': 'esriSpatialRelIntersects',
        'outSR': '4326'
    }
    
    print(f"   Filtro: {filtro_dpto}")
    print(f"   Formato: GeoJSON")
    
    try:
        print(f"   ⏳ Descargando datos...")
        response = requests.get(METODO_1_REST['url'], params=params, timeout=120)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
        
        geojson_data = response.json()
        
        if 'error' in geojson_data:
            raise Exception(f"Error del servicio: {geojson_data['error']}")
        
        if 'features' not in geojson_data or len(geojson_data['features']) == 0:
            raise Exception("No se encontraron datos con el filtro especificado")
        
        num_features = len(geojson_data['features'])
        print(f"   ✅ Descargados: {num_features:,} cauces")
        
        # Convertir a GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf.set_crs('EPSG:4326', inplace=True)
        
        return gdf
        
    except Exception as e:
        print(f"   ❌ Error en REST API: {e}")
        return None


def descargar_wfs_service(bbox: tuple = None) -> gpd.GeoDataFrame:
    """
    Método 2: Descarga desde WFS Service IGAC (BACKUP) 🔄
    
    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        
    Returns:
        GeoDataFrame con cauces o None si falla
    """
    print(f"\n📡 MÉTODO 2 (BACKUP): {METODO_2_WFS['nombre']}")
    print(f"   Fuente: {METODO_2_WFS['fuente'].upper()}")
    print(f"   URL: {METODO_2_WFS['url']}")
    
    try:
        # Bbox de Casanare + Meta (amplio para asegurar cobertura)
        if bbox is None:
            bbox = BBOX_CASANARE_META
        
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        
        params = {
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typeName': METODO_2_WFS['layer'],
            'outputFormat': 'application/json',
            'srsName': 'EPSG:4326',
            'bbox': bbox_str
        }
        
        print(f"   Bbox: {bbox_str}")
        print(f"   ⏳ Descargando datos...")
        
        response = requests.get(METODO_2_WFS['url'], params=params, timeout=120)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        geojson_data = response.json()
        
        if 'features' not in geojson_data or len(geojson_data['features']) == 0:
            raise Exception("No se encontraron features")
        
        num_features = len(geojson_data['features'])
        print(f"   ✅ Descargados: {num_features:,} cauces")
        
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf.set_crs('EPSG:4326', inplace=True)
        
        return gdf
        
    except Exception as e:
        print(f"   ❌ Error en WFS: {e}")
        return None


def descargar_osm_overpass(bbox: tuple = None) -> gpd.GeoDataFrame:
    """
    Método 3: Descarga desde OpenStreetMap Overpass API (BACKUP AUTOMÁTICO) 🗺️
    
    Descarga ríos, arroyos, quebradas y canales de OSM.
    Menor calidad que datos oficiales pero mejor cobertura.
    
    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        
    Returns:
        GeoDataFrame con cauces o None si falla
    """
    print(f"\n📡 MÉTODO 3 (BACKUP OSM): {METODO_3_OSM['nombre']}")
    print(f"   Fuente: {METODO_3_OSM['fuente'].upper()}")
    print(f"   URL: {METODO_3_OSM['url']}")
    print(f"   ⚠️  Nota: Datos colaborativos, pueden tener menor precisión")
    
    try:
        if bbox is None:
            bbox = BBOX_CASANARE_META
        
        # Query Overpass QL para obtener waterways (ríos, arroyos, canales)
        # Incluye: river, stream, creek, canal
        overpass_query = f"""
        [out:json][timeout:120];
        (
          way["waterway"="river"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
          way["waterway"="stream"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
          way["waterway"="canal"]({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]});
        );
        out geom;
        """
        
        print(f"   Bbox: {bbox}")
        print(f"   Tipos: river, stream, canal")
        print(f"   ⏳ Descargando datos de OSM...")
        
        response = requests.post(
            METODO_3_OSM['url'],
            data={'data': overpass_query},
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        osm_data = response.json()
        
        if 'elements' not in osm_data or len(osm_data['elements']) == 0:
            raise Exception("No se encontraron waterways en OSM")
        
        print(f"   ✅ Descargados: {len(osm_data['elements']):,} elementos")
        
        # Convertir OSM ways a geometrías LineString
        features = []
        for element in osm_data['elements']:
            if element['type'] != 'way' or 'geometry' not in element:
                continue
            
            coords = [(node['lon'], node['lat']) for node in element['geometry']]
            
            if len(coords) < 2:
                continue
            
            # Crear feature con propiedades
            props = element.get('tags', {})
            props['osm_id'] = element['id']
            props['NOMBRE_GEO'] = props.get('name', 'Sin nombre')
            props['TIPO'] = props.get('waterway', 'N/A').upper()
            
            features.append({
                'type': 'Feature',
                'geometry': mapping(LineString(coords)),
                'properties': props
            })
        
        print(f"   📊 Procesados: {len(features):,} cauces válidos")
        
        if len(features) == 0:
            raise Exception("No se pudieron procesar geometrías válidas")
        
        # Crear GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(features)
        gdf.set_crs('EPSG:4326', inplace=True)
        
        return gdf
        
    except Exception as e:
        print(f"   ❌ Error en OSM: {e}")
        return None



def validar_y_guardar(gdf: gpd.GeoDataFrame, metodo: str) -> bool:
    """
    Valida el GeoDataFrame y lo guarda como shapefile
    
    Args:
        gdf: GeoDataFrame con datos descargados
        metodo: Nombre del método usado
        
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    print(f"\n� Validando datos descargados con {metodo}...")
    
    # Mostrar información del dataset
    print(f"   Total de cauces: {len(gdf):,}")
    print(f"   Columnas: {list(gdf.columns)}")
    print(f"   CRS: {gdf.crs}")
    
    # Verificar tipos de geometría
    tipos_geom = gdf.geometry.geom_type.value_counts()
    print(f"\n🔷 Tipos de geometría:")
    for tipo, count in tipos_geom.items():
        print(f"     - {tipo}: {count:,} ({count/len(gdf)*100:.1f}%)")
    
    # Validar que sean LineString o MultiLineString
    if 'LineString' not in tipos_geom.index and 'MultiLineString' not in tipos_geom.index:
        print(f"   ⚠️  ADVERTENCIA: No se encontraron geometrías LineString")
        print(f"   El shapefile puede no ser correcto para red hídrica")
        return False
    
    # Verificar cobertura en zona de Tauramena
    print(f"\n🎯 Verificando cobertura en zona Tauramena...")
    print(f"   Bbox: {BBOX_TAURAMENA}")
    
    try:
        gdf_tau = gdf.cx[BBOX_TAURAMENA[0]:BBOX_TAURAMENA[2], 
                          BBOX_TAURAMENA[1]:BBOX_TAURAMENA[3]]
        
        print(f"   Cauces encontrados: {len(gdf_tau):,}")
        
        if len(gdf_tau) > 0:
            print(f"   ✅ HAY COBERTURA en la zona de Tauramena")
            
            # Mostrar muestra de cauces
            print(f"\n   📋 Muestra de cauces:")
            for idx, row in gdf_tau.head(5).iterrows():
                # Intentar obtener nombre del cauce
                nombre = (row.get('NOMBRE_GEO') or 
                         row.get('NOMBRE') or 
                         row.get('NOM_GEOGRA') or 
                         'Sin nombre')
                tipo = (row.get('TIPO') or 
                       row.get('CLASE_DREN') or 
                       row.get('TIPO_DREN') or 
                       'N/A')
                print(f"       - {nombre} (Tipo: {tipo})")
        else:
            print(f"   ⚠️  NO HAY COBERTURA en zona Tauramena")
            print(f"   El shapefile puede no cubrir la región de interés")
            return False
            
    except Exception as e:
        print(f"   ⚠️  Error al verificar cobertura: {e}")
        return False
    
    # Guardar como shapefile
    output_path = OUTPUT_DIR / OUTPUT_FILE
    print(f"\n💾 Guardando shapefile...")
    print(f"   Ruta: {output_path}")
    
    try:
        gdf.to_file(output_path)
        
        if output_path.exists():
            file_size_mb = output_path.stat().st_size / 1024 / 1024
            print(f"   ✅ Shapefile guardado exitosamente")
            print(f"   Tamaño: {file_size_mb:.2f} MB")
            print(f"   Registros: {len(gdf):,}")
            return True
        else:
            print(f"   ❌ Error: Archivo no se creó")
            return False
            
    except Exception as e:
        print(f"   ❌ Error al guardar shapefile: {e}")
        return False


def mostrar_guia_manual():
    """
    Muestra guía para descarga manual si todos los métodos automáticos fallan
    """
    print(f"\n" + "=" * 80)
    print(f"📖 MÉTODO 3 (MANUAL): Descarga desde GDB Nacional")
    print(f"=" * 80)
    print(f"\nTodos los métodos automáticos fallaron. Opciones:")
    print(f"\n1️⃣  Descarga manual con QGIS:")
    print(f"   - Ver guía completa: GUIA_DESCARGA_RED_HIDRICA_IGAC.md")
    print(f"   - URL: https://www.colombiaenmapas.gov.co/")
    print(f"   - Buscar: 'Drenaje sencillo' o 'Red hídrica nacional'")
    print(f"   - Descargar GDB completo (nacional)")
    print(f"   - Filtrar en QGIS: Departamentos CASANARE y META")
    print(f"   - Exportar a: {OUTPUT_DIR / OUTPUT_FILE}")
    print(f"\n2️⃣  Contactar soporte IGAC:")
    print(f"   - Email: soporte@igac.gov.co")
    print(f"   - Reportar que los servicios REST/WFS no responden")
    print(f"\n3️⃣  Usar datos OSM (menor calidad):")
    print(f"   - Descargar de: https://download.geofabrik.de/south-america/colombia.html")
    print(f"   - Extraer capa 'waterways' con ogr2ogr")
    print(f"=" * 80)


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def main():
    """
    Ejecuta descarga con múltiples métodos de respaldo
    """
    print(f"\n🚀 Iniciando descarga con múltiples métodos de respaldo...")
    print(f"   Métodos disponibles: REST API → WFS → OSM → Manual")
    
    gdf_resultado = None
    metodo_exitoso = None
    
    # Intentar método 1: REST API (datos oficiales)
    gdf_resultado = descargar_rest_api()
    if gdf_resultado is not None:
        metodo_exitoso = METODO_1_REST['nombre']
    
    # Si falla, intentar método 2: WFS (datos oficiales)
    if gdf_resultado is None:
        print(f"\n🔄 Intentando método de respaldo (WFS)...")
        gdf_resultado = descargar_wfs_service()
        if gdf_resultado is not None:
            metodo_exitoso = METODO_2_WFS['nombre']
    
    # Si ambos fallan, intentar método 3: OSM (colaborativo)
    if gdf_resultado is None:
        print(f"\n🔄 Intentando método de respaldo (OSM)...")
        print(f"   ⚠️  Usando datos colaborativos de OpenStreetMap")
        gdf_resultado = descargar_osm_overpass()
        if gdf_resultado is not None:
            metodo_exitoso = METODO_3_OSM['nombre']
    
    # Si todos fallan, mostrar guía manual
    if gdf_resultado is None:
        print(f"\n❌ Todos los métodos automáticos fallaron")
        mostrar_guia_manual()
        sys.exit(1)
    
    # Validar y guardar
    print(f"\n✅ Datos descargados con: {metodo_exitoso}")
    exito = validar_y_guardar(gdf_resultado, metodo_exitoso)
    
    if exito:
        print(f"\n🎉 DESCARGA COMPLETADA EXITOSAMENTE")
        print(f"\n📝 Próximos pasos:")
        print(f"   1. Ejecutar: python diagnosticar_red_hidrica_completo.py")
        print(f"   2. Ejecutar: python generar_pdf_verificacion_casanare.py")
        print(f"   3. Validar distancias verosímiles (1-5 km esperado)")
        print(f"   4. Verificar nombre correcto del río (ej. Río Cravo Sur)")
    else:
        print(f"\n⚠️  Descarga parcial - revisar advertencias arriba")
        print(f"   Considera usar método manual (ver guía)")
        sys.exit(1)
    
    print(f"\n" + "=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Descarga cancelada por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n💡 Alternativa: Descarga manual (ver arriba o GUIA_DESCARGA_RED_HIDRICA_IGAC.md)")
        sys.exit(1)

