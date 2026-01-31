#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🗺️ Descarga de Límites Departamentales OFICIALES de Colombia
=============================================================

Descarga y procesa shapefiles de límites departamentales desde:
1. Natural Earth (global, alta calidad)
2. Geoportal IGAC (oficial Colombia)
3. DANE (estadísticas oficiales)

Genera GeoJSON compatible con generador_pdf_legal.py

Autor: AgroTech Histórico
Fecha: 2025
"""

import os
import sys
import requests
import zipfile
import geopandas as gpd
from pathlib import Path
import json

# Rutas
BASE_DIR = Path(__file__).parent
DATOS_DIR = BASE_DIR / 'datos_geograficos' / 'limites_departamentales'
DATOS_DIR.mkdir(parents=True, exist_ok=True)

# 🌎 URLs de fuentes oficiales
FUENTES = {
    'natural_earth': {
        'url': 'https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_1_states_provinces.zip',
        'archivo': 'ne_10m_admin_1_states_provinces.shp',
        'campo_pais': 'admin',
        'campo_nombre': 'name',
        'descripcion': 'Natural Earth - Estados/Provincias del Mundo (10m)'
    },
    'gadm': {
        'url': 'https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_COL_shp.zip',
        'archivo': 'gadm41_COL_1.shp',  # Nivel 1 = departamentos
        'campo_pais': 'COUNTRY',
        'campo_nombre': 'NAME_1',
        'descripcion': 'GADM - Base de Datos Global de Áreas Administrativas'
    }
}

def descargar_archivo(url: str, destino: Path) -> bool:
    """
    Descarga un archivo con barra de progreso
    """
    try:
        print(f"📥 Descargando: {url}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        with open(destino, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progreso = (downloaded / total_size) * 100
                        print(f"   Progreso: {progreso:.1f}%", end='\r')
        
        print(f"\n✅ Descarga completada: {destino.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        return False

def extraer_zip(archivo_zip: Path, directorio_destino: Path) -> bool:
    """
    Extrae un archivo ZIP
    """
    try:
        print(f"📦 Extrayendo: {archivo_zip.name}")
        with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
            zip_ref.extractall(directorio_destino)
        print(f"✅ Archivos extraídos en: {directorio_destino}")
        return True
        
    except Exception as e:
        print(f"❌ Error al extraer: {e}")
        return False

def procesar_shapefile_colombia(shapefile_path: Path, campo_nombre: str, campo_pais: str = None) -> gpd.GeoDataFrame:
    """
    Carga shapefile y filtra solo departamentos de Colombia
    """
    try:
        print(f"🗺️  Cargando shapefile: {shapefile_path.name}")
        gdf = gpd.read_file(shapefile_path)
        
        print(f"   Registros totales: {len(gdf)}")
        print(f"   CRS original: {gdf.crs}")
        
        # Filtrar Colombia
        if campo_pais and campo_pais in gdf.columns:
            colombia_gdf = gdf[gdf[campo_pais] == 'Colombia'].copy()
            print(f"   Registros de Colombia: {len(colombia_gdf)}")
        else:
            # Si no hay campo de país, intentar filtrar por nombre o código
            colombia_gdf = gdf.copy()
        
        # Reproyectar a WGS84 si es necesario
        if colombia_gdf.crs != 'EPSG:4326':
            print(f"   Reproyectando a EPSG:4326...")
            colombia_gdf = colombia_gdf.to_crs('EPSG:4326')
        
        # Normalizar nombres de departamentos
        if campo_nombre in colombia_gdf.columns:
            colombia_gdf['DPTO_CNMBR'] = colombia_gdf[campo_nombre].str.strip()
        
        # Simplificar geometría para reducir tamaño (tolerancia 0.01 grados ≈ 1km)
        print(f"   Simplificando geometrías...")
        colombia_gdf['geometry'] = colombia_gdf.geometry.simplify(tolerance=0.01, preserve_topology=True)
        
        print(f"✅ Shapefile procesado correctamente")
        print(f"   Departamentos encontrados: {list(colombia_gdf['DPTO_CNMBR'].unique())[:5]}...")
        
        return colombia_gdf
        
    except Exception as e:
        print(f"❌ Error al procesar shapefile: {e}")
        return None

def guardar_geojson(gdf: gpd.GeoDataFrame, output_path: Path):
    """
    Guarda GeoDataFrame como GeoJSON optimizado
    """
    try:
        print(f"💾 Guardando GeoJSON: {output_path.name}")
        
        # Seleccionar solo columnas necesarias
        columnas_mantener = ['DPTO_CNMBR', 'geometry']
        gdf_simple = gdf[columnas_mantener].copy()
        
        # Guardar GeoJSON
        gdf_simple.to_file(output_path, driver='GeoJSON')
        
        # Verificar tamaño
        tamaño_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"✅ GeoJSON guardado ({tamaño_mb:.2f} MB)")
        print(f"   Ruta: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar GeoJSON: {e}")
        return False

def main():
    """
    Proceso principal de descarga e integración
    """
    print("=" * 70)
    print("🗺️  DESCARGA DE LÍMITES DEPARTAMENTALES OFICIALES DE COLOMBIA")
    print("=" * 70)
    print()
    
    # Intentar con GADM primero (más confiable para Colombia)
    fuente = 'gadm'
    config = FUENTES[fuente]
    
    print(f"🎯 Fuente seleccionada: {config['descripcion']}")
    print()
    
    # Paso 1: Descargar ZIP
    zip_path = DATOS_DIR / f"{fuente}_download.zip"
    
    if not zip_path.exists():
        if not descargar_archivo(config['url'], zip_path):
            print("❌ No se pudo descargar el archivo. Abortando.")
            return False
    else:
        print(f"✅ ZIP ya existe: {zip_path.name}")
    
    # Paso 2: Extraer archivos
    extract_dir = DATOS_DIR / f"{fuente}_extract"
    extract_dir.mkdir(exist_ok=True)
    
    if not (extract_dir / config['archivo']).exists():
        if not extraer_zip(zip_path, extract_dir):
            print("❌ No se pudo extraer el archivo. Abortando.")
            return False
    else:
        print(f"✅ Archivos ya extraídos en: {extract_dir}")
    
    # Paso 3: Procesar shapefile
    shapefile_path = extract_dir / config['archivo']
    
    if not shapefile_path.exists():
        print(f"❌ No se encontró el shapefile esperado: {shapefile_path}")
        print(f"   Archivos disponibles: {list(extract_dir.glob('*.shp'))}")
        return False
    
    colombia_gdf = procesar_shapefile_colombia(
        shapefile_path,
        config['campo_nombre'],
        config.get('campo_pais')
    )
    
    if colombia_gdf is None or len(colombia_gdf) == 0:
        print("❌ No se pudo procesar el shapefile o no se encontraron departamentos.")
        return False
    
    # Paso 4: Guardar GeoJSON final
    output_geojson = DATOS_DIR / 'departamentos_colombia_oficial.geojson'
    
    if not guardar_geojson(colombia_gdf, output_geojson):
        print("❌ No se pudo guardar el GeoJSON final.")
        return False
    
    # Paso 5: Verificación final
    print()
    print("=" * 70)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 70)
    print()
    print(f"📊 Estadísticas finales:")
    print(f"   • Departamentos procesados: {len(colombia_gdf)}")
    print(f"   • Archivo generado: {output_geojson.name}")
    print(f"   • Tamaño: {output_geojson.stat().st_size / (1024 * 1024):.2f} MB")
    print()
    print("🎯 Lista de departamentos incluidos:")
    for i, dept in enumerate(sorted(colombia_gdf['DPTO_CNMBR'].unique()), 1):
        print(f"   {i:2d}. {dept}")
    print()
    print("📝 Próximos pasos:")
    print("   1. Verificar que 'Casanare' está en la lista")
    print("   2. Actualizar generador_pdf_legal.py para usar este archivo")
    print("   3. Regenerar PDF y validar que la silueta sea correcta")
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
