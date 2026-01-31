#!/usr/bin/env python
"""
Script de diagnóstico para identificar columnas correctas de la red hídrica
y extraer nombres reales de ríos/quebradas en Casanare
"""

import geopandas as gpd
from pathlib import Path

def diagnosticar_red_hidrica():
    """Analiza la estructura del shapefile de red hídrica"""
    
    red_path = Path('datos_geograficos/red_hidrica/drenajes_sencillos_igac.shp')
    
    if not red_path.exists():
        print(f"❌ ERROR: No se encontró {red_path}")
        return
    
    print("="*80)
    print("🔍 DIAGNÓSTICO RED HÍDRICA - IGAC")
    print("="*80)
    
    # Cargar shapefile
    print(f"\n📂 Cargando {red_path}...")
    red_gdf = gpd.read_file(red_path)
    
    print(f"✅ Shapefile cargado exitosamente")
    print(f"📊 Número total de registros: {len(red_gdf):,}")
    print(f"🗺️  Sistema de coordenadas: {red_gdf.crs}")
    
    # Mostrar todas las columnas
    print("\n" + "="*80)
    print("📋 COLUMNAS DISPONIBLES:")
    print("="*80)
    for i, col in enumerate(red_gdf.columns, 1):
        tipo = str(red_gdf[col].dtype)
        print(f"{i:2}. {col:25} | Tipo: {tipo:15}")
    
    # Buscar columnas relacionadas con nombres
    print("\n" + "="*80)
    print("🔎 COLUMNAS CON NOMBRES/IDENTIFICADORES:")
    print("="*80)
    columnas_interes = [col for col in red_gdf.columns 
                        if any(keyword in col.upper() for keyword in 
                              ['NOM', 'NAME', 'TIPO', 'ORDEN', 'CLASE', 'CATEGORY'])]
    
    if columnas_interes:
        for col in columnas_interes:
            print(f"  • {col}")
            # Mostrar valores únicos (primeros 10)
            valores_unicos = red_gdf[col].unique()[:10]
            print(f"    Valores ejemplo: {valores_unicos}")
            print()
    else:
        print("  ⚠️  No se encontraron columnas con nombres estándar")
    
    # Muestra general de los primeros registros
    print("="*80)
    print("📄 MUESTRA DE DATOS (primeros 10 registros):")
    print("="*80)
    
    # Seleccionar columnas más relevantes
    cols_mostrar = [col for col in red_gdf.columns if col != 'geometry'][:8]
    print(red_gdf[cols_mostrar].head(10).to_string(index=False))
    
    # Filtrar por Casanare
    print("\n" + "="*80)
    print("🌎 FILTRADO POR CASANARE:")
    print("="*80)
    
    bbox_casanare = [-73.0, 5.0, -69.0, 6.5]  # [min_lon, min_lat, max_lon, max_lat]
    
    print(f"📍 BBox Casanare: {bbox_casanare}")
    red_casanare = red_gdf.cx[bbox_casanare[0]:bbox_casanare[2], bbox_casanare[1]:bbox_casanare[3]]
    
    print(f"✅ Registros en Casanare: {len(red_casanare):,}")
    print(f"📊 Porcentaje del total: {len(red_casanare)/len(red_gdf)*100:.1f}%")
    
    if len(red_casanare) > 0:
        print("\n🔍 Muestra de registros en Casanare:")
        print(red_casanare[cols_mostrar].head(15).to_string(index=False))
        
        # Análisis de tipos de drenaje en Casanare
        if columnas_interes:
            print("\n" + "="*80)
            print("📊 ANÁLISIS DE TIPOS/NOMBRES EN CASANARE:")
            print("="*80)
            
            for col in columnas_interes:
                if col in red_casanare.columns:
                    conteo = red_casanare[col].value_counts()
                    print(f"\n{col}:")
                    print(conteo.head(15))
    
    # Buscar registros con nombres específicos
    print("\n" + "="*80)
    print("🏞️  BÚSQUEDA DE RÍOS PRINCIPALES EN CASANARE:")
    print("="*80)
    
    rios_principales = ['CRAVO', 'META', 'CUSIANA', 'ARIPORO', 'PAUTO', 'GUANAPALO']
    
    for col in columnas_interes:
        if col in red_casanare.columns and red_casanare[col].dtype == 'object':
            for rio in rios_principales:
                matches = red_casanare[red_casanare[col].astype(str).str.contains(rio, case=False, na=False)]
                if len(matches) > 0:
                    print(f"\n✅ '{rio}' encontrado en columna '{col}': {len(matches)} registros")
                    print(f"   Ejemplos: {matches[col].head(5).tolist()}")
    
    # Resumen y recomendaciones
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES PARA EL CÓDIGO:")
    print("="*80)
    
    if columnas_interes:
        print("✅ Usar las siguientes columnas para extraer información:")
        for col in columnas_interes:
            print(f"   • {col}")
        
        # Sugerir código
        print("\n📝 Código sugerido:")
        print("""
# Intentar extraer nombre en orden de prioridad
nombre_rio = red.loc[idx_min].get('NOMBRE_GEO', 
              red.loc[idx_min].get('NOMBRE', 
              red.loc[idx_min].get('NOM_GEO', 'Cauce sin nombre oficial')))

tipo_rio = red.loc[idx_min].get('TIPO', 
           red.loc[idx_min].get('CLASE_DREN', 
           red.loc[idx_min].get('CATEGORIA', 'Drenaje natural')))
        """)
    else:
        print("⚠️  ADVERTENCIA: No se encontraron columnas estándar de nombres")
        print("   Se recomienda revisar manualmente el shapefile")
    
    print("\n" + "="*80)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*80)

if __name__ == '__main__':
    diagnosticar_red_hidrica()
