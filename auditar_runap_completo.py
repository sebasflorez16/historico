#!/usr/bin/env python3
"""
Script de auditoría exhaustiva para validar la integridad de datos RUNAP
Compara shapefile vs geojson departamental y detecta inconsistencias
"""

import geopandas as gpd
import json
from pathlib import Path
from shapely.geometry import shape, mapping
import sys

def validar_geometrias(gdf, nombre_capa):
    """Valida integridad de geometrías"""
    print(f"\n🔍 Validando geometrías de {nombre_capa}:")
    
    # Geometrías inválidas
    invalidas = (~gdf.is_valid).sum()
    print(f"  ❌ Geometrías inválidas: {invalidas}")
    
    # Geometrías vacías
    vacias = gdf.is_empty.sum()
    print(f"  📭 Geometrías vacías: {vacias}")
    
    # Tipos de geometría
    tipos = gdf.geom_type.value_counts()
    print(f"  📐 Tipos de geometría:")
    for tipo, count in tipos.items():
        print(f"     - {tipo}: {count}")
    
    # CRS
    print(f"  🌍 Sistema de coordenadas: {gdf.crs}")
    
    return invalidas == 0 and vacias == 0

def analizar_campos(gdf, nombre_capa):
    """Analiza campos y sus valores"""
    print(f"\n📊 Análisis de campos en {nombre_capa}:")
    print(f"  Total de columnas: {len(gdf.columns)}")
    print(f"  Columnas: {list(gdf.columns)}")
    
    # Campos con valores nulos
    nulos = gdf.isnull().sum()
    if nulos.any():
        print(f"\n  ⚠️  Campos con valores nulos:")
        for col, count in nulos[nulos > 0].items():
            if col != 'geometry':
                print(f"     - {col}: {count} nulos ({count/len(gdf)*100:.1f}%)")
    
    # Campos clave para RUNAP
    campos_clave = ['NOMBRE_GEO', 'CATEGORÍA', 'DEPARTAMEN', 'ESTADO']
    for campo in campos_clave:
        # Buscar campo con nombre similar (case-insensitive)
        col_match = [c for c in gdf.columns if c.upper() == campo.upper()]
        if col_match:
            campo_real = col_match[0]
            print(f"\n  🔑 Campo '{campo_real}':")
            valores = gdf[campo_real].value_counts().head(10)
            for val, count in valores.items():
                print(f"     - {val}: {count}")
        else:
            print(f"\n  ❌ Campo '{campo}' NO encontrado")

def comparar_datasets(shp_gdf, geojson_gdf, departamento="CASANARE"):
    """Compara shapefile nacional con geojson departamental"""
    print(f"\n🔄 Comparando datasets para {departamento}:")
    
    # Buscar campo de departamento en shapefile
    dep_field = None
    for col in shp_gdf.columns:
        if 'DEPART' in col.upper():
            dep_field = col
            break
    
    if not dep_field:
        print(f"  ⚠️  No se encontró campo de departamento en shapefile")
        return
    
    # Filtrar shapefile por departamento
    shp_dept = shp_gdf[shp_gdf[dep_field].str.upper().str.contains(departamento.upper(), na=False)]
    
    print(f"\n  📊 Estadísticas:")
    print(f"     - Shapefile nacional total: {len(shp_gdf)} features")
    print(f"     - Shapefile filtrado ({departamento}): {len(shp_dept)} features")
    print(f"     - GeoJSON {departamento}: {len(geojson_gdf)} features")
    
    # Diferencia en conteo
    diferencia = len(geojson_gdf) - len(shp_dept)
    if diferencia == 0:
        print(f"  ✅ Conteos coinciden perfectamente")
    elif abs(diferencia) <= 5:
        print(f"  ⚠️  Diferencia menor: {diferencia} features")
    else:
        print(f"  ❌ DIFERENCIA SIGNIFICATIVA: {diferencia} features")
    
    # Comparar nombres de áreas (si existe el campo)
    nombre_field_shp = None
    nombre_field_json = None
    
    for col in shp_dept.columns:
        if 'NOMBRE' in col.upper():
            nombre_field_shp = col
            break
    
    for col in geojson_gdf.columns:
        if 'NOMBRE' in col.upper() or 'NAME' in col.upper():
            nombre_field_json = col
            break
    
    if nombre_field_shp and nombre_field_json:
        nombres_shp = set(shp_dept[nombre_field_shp].dropna().str.upper())
        nombres_json = set(geojson_gdf[nombre_field_json].dropna().str.upper())
        
        solo_shp = nombres_shp - nombres_json
        solo_json = nombres_json - nombres_shp
        
        if solo_shp:
            print(f"\n  🔍 Áreas solo en shapefile ({len(solo_shp)}):")
            for nombre in list(solo_shp)[:10]:
                print(f"     - {nombre}")
        
        if solo_json:
            print(f"\n  🔍 Áreas solo en geojson ({len(solo_json)}):")
            for nombre in list(solo_json)[:10]:
                print(f"     - {nombre}")
        
        if not solo_shp and not solo_json:
            print(f"  ✅ Todos los nombres coinciden")

def validar_cobertura_nacional(gdf):
    """Valida que el shapefile tenga cobertura nacional"""
    print(f"\n🗺️  Validando cobertura nacional:")
    
    # Buscar campo de departamento
    dep_field = None
    for col in gdf.columns:
        if 'DEPART' in col.upper():
            dep_field = col
            break
    
    if dep_field:
        departamentos = gdf[dep_field].dropna().unique()
        print(f"  📍 Departamentos encontrados: {len(departamentos)}")
        print(f"  Departamentos: {sorted([d for d in departamentos if isinstance(d, str)])[:10]}...")
        
        # Colombia tiene 32 departamentos + Bogotá D.C.
        if len(departamentos) >= 30:
            print(f"  ✅ Cobertura nacional completa")
        else:
            print(f"  ⚠️  Cobertura posiblemente incompleta (esperados ~33 departamentos)")
    else:
        print(f"  ❌ No se pudo validar cobertura (campo departamento no encontrado)")

def analizar_bbox_y_extension(gdf, nombre_capa):
    """Analiza la extensión geográfica del dataset"""
    print(f"\n📏 Extensión geográfica de {nombre_capa}:")
    
    bounds = gdf.total_bounds
    print(f"  📐 Bounding Box:")
    print(f"     - Min Lon: {bounds[0]:.4f}")
    print(f"     - Min Lat: {bounds[1]:.4f}")
    print(f"     - Max Lon: {bounds[2]:.4f}")
    print(f"     - Max Lat: {bounds[3]:.4f}")
    
    # Validar si está dentro de Colombia aproximadamente
    # Colombia: Lon [-79, -66], Lat [-4, 13]
    if -79 <= bounds[0] and bounds[2] <= -66 and -4 <= bounds[1] and bounds[3] <= 13:
        print(f"  ✅ Extensión dentro de límites de Colombia")
    else:
        print(f"  ⚠️  Extensión fuera de límites esperados de Colombia")

def main():
    print("=" * 80)
    print("🔍 AUDITORÍA COMPLETA DE DATOS RUNAP")
    print("=" * 80)
    
    base_path = Path("datos_geograficos/runap")
    
    # 1. Validar shapefile nacional
    shp_path = base_path / "runap.shp"
    if shp_path.exists():
        print(f"\n📂 Cargando shapefile: {shp_path}")
        try:
            shp_gdf = gpd.read_file(shp_path)
            print(f"✅ Shapefile cargado: {len(shp_gdf)} features")
            
            # Validaciones del shapefile
            validar_geometrias(shp_gdf, "Shapefile Nacional")
            analizar_campos(shp_gdf, "Shapefile Nacional")
            validar_cobertura_nacional(shp_gdf)
            analizar_bbox_y_extension(shp_gdf, "Shapefile Nacional")
            
        except Exception as e:
            print(f"❌ Error cargando shapefile: {e}")
            shp_gdf = None
    else:
        print(f"❌ Shapefile no encontrado: {shp_path}")
        shp_gdf = None
    
    # 2. Validar geojson departamental
    geojson_path = base_path / "runap_casanare.geojson"
    if geojson_path.exists():
        print(f"\n📂 Cargando GeoJSON: {geojson_path}")
        try:
            # Verificar si el archivo está vacío
            with open(geojson_path, 'r') as f:
                content = f.read()
                if not content.strip() or content.strip() == '{}':
                    print(f"⚠️  Archivo GeoJSON vacío")
                    geojson_gdf = None
                else:
                    geojson_gdf = gpd.read_file(geojson_path)
                    print(f"✅ GeoJSON cargado: {len(geojson_gdf)} features")
                    
                    # Validaciones del geojson
                    validar_geometrias(geojson_gdf, "GeoJSON Casanare")
                    analizar_campos(geojson_gdf, "GeoJSON Casanare")
                    analizar_bbox_y_extension(geojson_gdf, "GeoJSON Casanare")
        except Exception as e:
            print(f"❌ Error cargando GeoJSON: {e}")
            geojson_gdf = None
    else:
        print(f"❌ GeoJSON no encontrado: {geojson_path}")
        geojson_gdf = None
    
    # 3. Comparar datasets si ambos existen
    if shp_gdf is not None and geojson_gdf is not None:
        comparar_datasets(shp_gdf, geojson_gdf, "CASANARE")
    
    # 4. Resumen final
    print("\n" + "=" * 80)
    print("📋 RESUMEN DE AUDITORÍA")
    print("=" * 80)
    
    if shp_gdf is not None:
        print(f"✅ Shapefile nacional: {len(shp_gdf)} áreas protegidas")
        # Estimar Casanare
        dep_field = None
        for col in shp_gdf.columns:
            if 'DEPART' in col.upper():
                dep_field = col
                break
        if dep_field:
            casanare_count = len(shp_gdf[shp_gdf[dep_field].str.upper().str.contains('CASANARE', na=False)])
            print(f"   └─ Casanare: {casanare_count} áreas protegidas")
    else:
        print(f"❌ Shapefile nacional: NO DISPONIBLE")
    
    if geojson_gdf is not None:
        print(f"✅ GeoJSON Casanare: {len(geojson_gdf)} áreas protegidas")
    else:
        print(f"⚠️  GeoJSON Casanare: VACÍO O NO DISPONIBLE")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
