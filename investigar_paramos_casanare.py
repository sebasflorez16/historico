#!/usr/bin/env python3
"""
Investigar los páramos detectados en Casanare
"""

import geopandas as gpd
from pathlib import Path

def investigar_paramos_casanare():
    print("=" * 80)
    print("🔍 INVESTIGACIÓN: PÁRAMOS EN CASANARE")
    print("=" * 80)
    
    # Cargar shapefile
    shp_path = Path("datos_geograficos/paramos/Paramos_Delimitados_Junio_2020.shp")
    gdf = gpd.read_file(shp_path)
    
    print(f"\n📊 Total de páramos: {len(gdf)}")
    print(f"🌍 CRS: {gdf.crs}")
    
    # Filtrar por bbox de Casanare
    print(f"\n🔍 Filtrando por bbox de Casanare (5-6.5°N, 69-73°W)...")
    casanare_bbox = gdf.cx[-73:-69, 5:6.5]
    
    print(f"✅ Páramos encontrados en bbox: {len(casanare_bbox)}")
    
    if len(casanare_bbox) > 0:
        print(f"\n📋 DETALLES DE PÁRAMOS EN CASANARE:")
        
        # Agrupar por nombre para ver complejos únicos
        nombres_unicos = casanare_bbox['Nombre'].unique()
        print(f"\n🏔️  Complejos únicos: {len(nombres_unicos)}")
        
        for nombre in nombres_unicos:
            paramos_complejo = casanare_bbox[casanare_bbox['Nombre'] == nombre]
            area_total = paramos_complejo['Area_Ha'].sum()
            
            print(f"\n   • {nombre}")
            print(f"     Polígonos: {len(paramos_complejo)}")
            print(f"     Área total: {area_total:.2f} ha")
            
            # Mostrar coordenadas de cada polígono
            for idx, row in paramos_complejo.iterrows():
                centroid = row.geometry.centroid
                print(f"     Polígono {idx}: {centroid.y:.4f}°N, {centroid.x:.4f}°W ({row['Area_Ha']:.2f} ha)")
    
    # Verificar si realmente están DENTRO de Casanare o solo en el bbox
    print(f"\n" + "=" * 80)
    print(f"🗺️  ANÁLISIS GEOGRÁFICO")
    print(f"=" * 80)
    
    print(f"\n📍 Límites de Casanare:")
    print(f"   Latitud: 4.5° - 6.6°N")
    print(f"   Longitud: 69.5° - 73.0°W")
    print(f"   Altitud: 150 - 500 msnm (llanura)")
    
    print(f"\n🏔️  Páramos requieren:")
    print(f"   Altitud mínima: >3000 msnm")
    
    print(f"\n💡 HIPÓTESIS:")
    print(f"   Los páramos detectados probablemente están en:")
    print(f"   1. Límite con Boyacá (zona andina del occidente)")
    print(f"   2. Bordes montañosos fuera de Casanare pero en el bbox rectangular")
    
    # Verificar nombres para confirmar
    if len(casanare_bbox) > 0:
        print(f"\n✅ CONFIRMACIÓN:")
        for nombre in nombres_unicos:
            print(f"   • '{nombre}' - Revisar si está en límite con Boyacá/Santander")

if __name__ == "__main__":
    investigar_paramos_casanare()
