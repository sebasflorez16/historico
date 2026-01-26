#!/usr/bin/env python3
"""
Descarga profesional de capas geográficas oficiales para verificación legal
- RUNAP (Áreas Protegidas) - Parques Nacionales
- Resguardos Indígenas - ANT
- Páramos - SIAC/MADS

Filtra por departamento (Casanare = código 85) y guarda en estructura organizada.
"""

import os
import requests
import zipfile
import geopandas as gpd
from pathlib import Path
import json

# Configuración
DEPARTAMENTO = "CASANARE"
COD_DEPTO = "85"
BBOX_CASANARE = [-73.0, 4.5, -69.8, 6.8]  # [minx, miny, maxx, maxy]

# Directorios de salida
BASE_DIR = Path("datos_geograficos")
RUNAP_DIR = BASE_DIR / "runap"
RESGUARDOS_DIR = BASE_DIR / "resguardos_indigenas"
PARAMOS_DIR = BASE_DIR / "paramos"

# Crear directorios
for dir_path in [RUNAP_DIR, RESGUARDOS_DIR, PARAMOS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# URLs oficiales
URLS = {
    "runap": "https://storage.googleapis.com/pnn_geodatabase/runap/latest.zip",
    "resguardos": "https://opendata.arcgis.com/api/v3/datasets/f6dud8dwd8/downloads/data?format=shp&spatialRefId=4326",
    "paramos": "https://siac-datosabiertos-mads.hub.arcgis.com/datasets/9631ed8c44274baa824e6277276de48f_0.zip"
}

def descargar_archivo(url, output_path, nombre_capa):
    """Descarga un archivo con barra de progreso"""
    print(f"\n{'='*80}")
    print(f"📥 Descargando: {nombre_capa}")
    print(f"🔗 URL: {url}")
    print(f"{'='*80}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   ⏳ Progreso: {percent:.1f}% ({downloaded/(1024*1024):.2f} MB / {total_size/(1024*1024):.2f} MB)", end='')
        
        print(f"\n   ✅ Descarga completada: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"\n   ❌ Error descargando {nombre_capa}: {e}")
        return False

def extraer_zip(zip_path, extract_dir):
    """Extrae un archivo ZIP"""
    print(f"\n📦 Extrayendo {zip_path.name}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"   ✅ Extraído en: {extract_dir}")
        return True
    except Exception as e:
        print(f"   ❌ Error extrayendo: {e}")
        return False

def filtrar_por_bbox(gdf, bbox, nombre_capa):
    """Filtra GeoDataFrame por bounding box"""
    print(f"\n🔍 Filtrando {nombre_capa} por Casanare...")
    print(f"   📊 Total nacional: {len(gdf):,} elementos")
    
    # Asegurar CRS
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    elif gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    # Filtrar por bbox
    minx, miny, maxx, maxy = bbox
    filtered = gdf.cx[minx:maxx, miny:maxy]
    
    print(f"   ✅ En Casanare: {len(filtered):,} elementos")
    return filtered

def procesar_runap():
    """Descarga y procesa áreas protegidas RUNAP"""
    print(f"\n{'#'*80}")
    print("## 1️⃣  ÁREAS PROTEGIDAS (RUNAP) - Parques Nacionales")
    print(f"{'#'*80}")
    
    zip_path = RUNAP_DIR / "runap_nacional.zip"
    
    # Descargar
    if not descargar_archivo(URLS["runap"], zip_path, "RUNAP Nacional"):
        return False
    
    # Extraer
    if not extraer_zip(zip_path, RUNAP_DIR):
        return False
    
    # Buscar shapefile principal
    shapefiles = list(RUNAP_DIR.glob("**/*.shp"))
    if not shapefiles:
        print("   ❌ No se encontró shapefile en el ZIP")
        return False
    
    shp_principal = shapefiles[0]
    print(f"\n📂 Shapefile encontrado: {shp_principal.name}")
    
    # Cargar y filtrar
    gdf = gpd.read_file(shp_principal)
    gdf_casanare = filtrar_por_bbox(gdf, BBOX_CASANARE, "RUNAP")
    
    # Guardar
    output_file = RUNAP_DIR / "runap_casanare.geojson"
    gdf_casanare.to_file(output_file, driver="GeoJSON")
    print(f"\n💾 Guardado: {output_file}")
    print(f"   📏 Tamaño: {output_file.stat().st_size / (1024*1024):.2f} MB")
    
    return True

def procesar_resguardos():
    """Descarga y procesa resguardos indígenas ANT"""
    print(f"\n{'#'*80}")
    print("## 2️⃣  RESGUARDOS INDÍGENAS - ANT")
    print(f"{'#'*80}")
    
    # Descargar shapefile completo desde ArcGIS Download API
    download_url = "https://opendata.arcgis.com/api/v3/datasets/f6dud8dwd8c442de9f2ad23dbc5b77ae_0/downloads/data?format=shp&spatialRefId=4326"
    
    zip_path = RESGUARDOS_DIR / "resguardos_nacional.zip"
    
    print(f"\n📥 Descargando shapefile completo de ANT...")
    print(f"   🔗 {download_url}")
    
    try:
        # Descargar con ID de dataset correcto
        response = requests.get(download_url, stream=True, timeout=120)
        
        if response.status_code == 404:
            # Intentar URL alternativa directa
            alt_url = "https://services.arcgis.com/DDzi7vRExVRMO5AB/arcgis/rest/services/Resguardo_Indigena_Formalizado/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
            print(f"\n   ⚠️  URL principal no disponible, intentando alternativa...")
            print(f"   🔗 {alt_url}")
            response = requests.get(alt_url, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            if "features" in data:
                gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
                print(f"   📊 Total nacional: {len(gdf):,} resguardos")
                
                # Filtrar
                gdf_casanare = filtrar_por_bbox(gdf, BBOX_CASANARE, "Resguardos")
                
                # Guardar
                output_file = RESGUARDOS_DIR / "resguardos_casanare.geojson"
                gdf_casanare.to_file(output_file, driver="GeoJSON")
                print(f"\n💾 Guardado: {output_file}")
                print(f"   📏 Tamaño: {output_file.stat().st_size / 1024:.2f} KB")
                return True
        else:
            response.raise_for_status()
            # Procesar ZIP
            total_size = int(response.headers.get('content-length', 0))
            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   ⏳ {percent:.1f}%", end='')
            
            print(f"\n   ✅ Descargado")
            
            # Extraer
            if not extraer_zip(zip_path, RESGUARDOS_DIR):
                return False
            
            # Buscar shapefile
            shapefiles = list(RESGUARDOS_DIR.glob("**/*.shp"))
            if not shapefiles:
                print("   ❌ No se encontró shapefile")
                return False
            
            # Cargar y filtrar
            gdf = gpd.read_file(shapefiles[0])
            gdf_casanare = filtrar_por_bbox(gdf, BBOX_CASANARE, "Resguardos")
            
            # Guardar
            output_file = RESGUARDOS_DIR / "resguardos_casanare.geojson"
            gdf_casanare.to_file(output_file, driver="GeoJSON")
            print(f"\n💾 Guardado: {output_file}")
            print(f"   📏 Tamaño: {output_file.stat().st_size / 1024:.2f} KB")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def procesar_paramos():
    """Descarga y procesa páramos delimitados"""
    print(f"\n{'#'*80}")
    print("## 3️⃣  PÁRAMOS - SIAC/MADS")
    print(f"{'#'*80}")
    
    # Descargar GeoJSON completo sin filtro bbox (a veces los filtros no funcionan)
    base_url = "https://services.arcgis.com/zNC4XQ1B0uOEuIBN/arcgis/rest/services/Paramos_Delimitados/FeatureServer/0/query"
    
    params = {
        "where": "1=1",
        "outFields": "*",
        "f": "geojson"
    }
    
    print(f"\n📥 Descargando páramos completos...")
    print(f"   🔗 {base_url}")
    
    try:
        response = requests.get(base_url, params=params, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        if "features" in data:
            print(f"   📊 Total nacional: {len(data['features'])} páramos")
            
            # Convertir a GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(data['features'], crs="EPSG:4326")
            
            # Filtrar por bbox
            gdf_casanare = filtrar_por_bbox(gdf, BBOX_CASANARE, "Páramos")
            
            if len(gdf_casanare) == 0:
                print(f"   ℹ️  Casanare no tiene páramos delimitados (dato esperado para esa región)")
            
            # Guardar
            output_file = PARAMOS_DIR / "paramos_casanare.geojson"
            gdf_casanare.to_file(output_file, driver="GeoJSON")
            print(f"\n💾 Guardado: {output_file}")
            print(f"   📏 Tamaño: {output_file.stat().st_size / 1024:.2f} KB")
            return True
        else:
            print(f"   ❌ Respuesta inesperada de la API")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print(f"""
{'='*80}
🗺️  DESCARGA PROFESIONAL DE CAPAS GEOGRÁFICAS OFICIALES
{'='*80}
Departamento: {DEPARTAMENTO} (código {COD_DEPTO})
Bounding Box: {BBOX_CASANARE}

Capas a descargar:
  1️⃣  Áreas Protegidas (RUNAP) - Parques Nacionales
  2️⃣  Resguardos Indígenas - ANT
  3️⃣  Páramos - SIAC/MADS

{'='*80}
""")
    
    resultados = {
        "RUNAP": procesar_runap(),
        "Resguardos": procesar_resguardos(),
        "Páramos": procesar_paramos()
    }
    
    print(f"\n{'='*80}")
    print("📊 RESUMEN DE DESCARGAS")
    print(f"{'='*80}")
    for capa, exito in resultados.items():
        status = "✅ Exitosa" if exito else "❌ Falló"
        print(f"   {capa:20s} → {status}")
    
    total_exitosas = sum(resultados.values())
    print(f"\n   Total: {total_exitosas}/3 capas descargadas correctamente")
    print(f"{'='*80}\n")
    
    if total_exitosas == 3:
        print("✅ TODAS LAS CAPAS DESCARGADAS EXITOSAMENTE")
        print("\n🔄 Siguiente paso: Actualizar verificador_legal.py para usar estas capas")
    else:
        print("⚠️  Algunas capas no se descargaron. Revisa los errores arriba.")

if __name__ == "__main__":
    main()
