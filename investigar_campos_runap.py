#!/usr/bin/env python3
"""
Script para investigar los campos reales de RUNAP y su contenido
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path

def main():
    print("=" * 80)
    print("🔍 INVESTIGACIÓN DE CAMPOS RUNAP")
    print("=" * 80)
    
    # Cargar shapefile
    shp_path = Path("datos_geograficos/runap/runap.shp")
    print(f"\n📂 Cargando: {shp_path}")
    gdf = gpd.read_file(shp_path)
    
    print(f"\n✅ Cargado: {len(gdf)} features")
    print(f"📊 Columnas ({len(gdf.columns)}): {list(gdf.columns)}")
    
    # Mostrar primeras 5 filas de campos clave
    print("\n" + "=" * 80)
    print("📋 PRIMERAS 5 ÁREAS PROTEGIDAS")
    print("=" * 80)
    
    campos_mostrar = ['ap_nombre', 'ap_categor', 'area_ha_to', 'condicion', 'territoria', 'sirap']
    
    for idx, row in gdf.head(5).iterrows():
        print(f"\n🌳 Área {idx + 1}:")
        for campo in campos_mostrar:
            if campo in row:
                valor = row[campo]
                print(f"  {campo:15} = {valor}")
    
    # Analizar categorías
    print("\n" + "=" * 80)
    print("📊 CATEGORÍAS DE ÁREAS PROTEGIDAS")
    print("=" * 80)
    if 'ap_categor' in gdf.columns:
        categorias = gdf['ap_categor'].value_counts()
        print(f"\nTotal de categorías: {len(categorias)}")
        for cat, count in categorias.items():
            print(f"  - {cat}: {count}")
    
    # Analizar territorio (podría ser departamento)
    print("\n" + "=" * 80)
    print("🗺️  ANÁLISIS DE TERRITORIOS")
    print("=" * 80)
    
    # Probar diferentes campos que podrían contener ubicación
    campos_territorio = ['territoria', 'territor_1', 'sirap']
    
    for campo in campos_territorio:
        if campo in gdf.columns:
            valores = gdf[campo].dropna().value_counts()
            if len(valores) > 0:
                print(f"\n🔍 Campo '{campo}' ({len(valores)} valores únicos):")
                for val, count in valores.head(15).items():
                    print(f"  - {val}: {count}")
    
    # Buscar áreas en Casanare por nombre
    print("\n" + "=" * 80)
    print("🔍 BÚSQUEDA DE ÁREAS EN CASANARE")
    print("=" * 80)
    
    if 'ap_nombre' in gdf.columns:
        # Buscar por nombre
        casanare_nombre = gdf[gdf['ap_nombre'].str.contains('CASANARE', case=False, na=False)]
        print(f"\n📍 Áreas con 'CASANARE' en el nombre: {len(casanare_nombre)}")
        if len(casanare_nombre) > 0:
            for idx, row in casanare_nombre.iterrows():
                print(f"  - {row['ap_nombre']}")
    
    # Buscar por coordenadas (Casanare: aproximadamente 5-6.5°N, 69-73°W)
    print("\n📍 Áreas en rango de coordenadas de Casanare (5-6.5°N, 69-73°W):")
    casanare_bbox = gdf.cx[-73:-69, 5:6.5]
    print(f"  Total: {len(casanare_bbox)}")
    
    if len(casanare_bbox) > 0:
        print("\n  Listado:")
        for idx, row in casanare_bbox.iterrows():
            centroid = row.geometry.centroid
            print(f"  - {row['ap_nombre']}")
            print(f"    Categoría: {row['ap_categor']}")
            print(f"    Centroide: {centroid.y:.4f}°N, {centroid.x:.4f}°W")
            print(f"    Área: {row['area_ha_to']:.2f} ha")
    
    # Comparar con geojson
    print("\n" + "=" * 80)
    print("🔄 COMPARACIÓN CON GEOJSON CASANARE")
    print("=" * 80)
    
    geojson_path = Path("datos_geograficos/runap/runap_casanare.geojson")
    if geojson_path.exists():
        gdf_json = gpd.read_file(geojson_path)
        print(f"\n✅ GeoJSON: {len(gdf_json)} features")
        print(f"📊 Shapefile filtrado por bbox: {len(casanare_bbox)} features")
        
        # Comparar nombres
        if 'ap_nombre' in gdf.columns and 'ap_nombre' in gdf_json.columns:
            nombres_shp = set(casanare_bbox['ap_nombre'].dropna())
            nombres_json = set(gdf_json['ap_nombre'].dropna())
            
            print(f"\n🔍 Nombres únicos:")
            print(f"  - Shapefile (bbox): {len(nombres_shp)}")
            print(f"  - GeoJSON: {len(nombres_json)}")
            
            solo_shp = nombres_shp - nombres_json
            solo_json = nombres_json - nombres_shp
            
            if solo_shp:
                print(f"\n  ⚠️  Solo en shapefile ({len(solo_shp)}):")
                for nombre in list(solo_shp)[:10]:
                    print(f"     - {nombre}")
            
            if solo_json:
                print(f"\n  ⚠️  Solo en geojson ({len(solo_json)}):")
                for nombre in list(solo_json)[:10]:
                    print(f"     - {nombre}")
            
            comunes = nombres_shp & nombres_json
            if comunes:
                print(f"\n  ✅ Nombres comunes: {len(comunes)}")

if __name__ == "__main__":
    main()
