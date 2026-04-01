#!/usr/bin/env python3
"""
Descarga drenajes desde servicios oficiales del IGAC
https://www.colombiaenmapas.gov.co/
"""
import geopandas as gpd
from pathlib import Path
import requests

print("="*80)
print("🚀 DESCARGA DESDE IGAC OFICIAL - colombiaenmapas.gov.co")
print("="*80 + "\n")

# Crear directorio
Path('datos_geograficos/red_hidrica').mkdir(parents=True, exist_ok=True)

# URLs de servicios WFS del IGAC
# Servicio 204 = 1:500.000 (nacional)
# Servicio 205 = 1:100.000 (regional - MEJOR OPCIÓN)
# Servicio 206 = 1:25.000 (muy detallado)

print("📥 Intentando descargar drenajes IGAC escala 1:100.000...")
print("   (Servicio 205 - colombiaenmapas.gov.co)\n")

# Construcción de URLs WFS posibles para drenajes
urls_igac = [
    # Servicio 205 - Escala 1:100.000
    "https://geoservicios.igac.gov.co/geoserver/cartografia_basica/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=cartografia_basica:cb_drenaje_sencillo_100k&outputFormat=json",
    "https://geoservicios.igac.gov.co/geoserver/cartografia_basica/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=cartografia_basica:drenaje_sencillo&outputFormat=json",
    # Alternativas
    "https://geoservicios.igac.gov.co/geoserver/cartografia_basica/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=cartografia_basica:drenaje_sencillo&outputFormat=json",
]

descargado = False

for i, url in enumerate(urls_igac, 1):
    try:
        print(f"🌐 Intento {i}/{len(urls_igac)}...")
        print(f"   URL: {url[:100]}...")
        
        # Intentar descargar
        gdf = gpd.read_file(url)
        
        print(f"   ✅ Descargado: {len(gdf)} elementos")
        print(f"   CRS: {gdf.crs}")
        
        # Validar geometría
        tipos = gdf.geometry.geom_type.value_counts()
        print(f"   Tipos de geometría:")
        for tipo, count in tipos.items():
            print(f"      • {tipo}: {count}")
        
        # Verificar que sean líneas
        if any(t in ['LineString', 'MultiLineString'] for t in gdf.geometry.geom_type.unique()):
            print(f"\n   ✅ CORRECTO: Son drenajes lineales (ríos/quebradas)")
            
            # Guardar
            output = 'datos_geograficos/red_hidrica/drenajes_igac_100k.shp'
            gdf.to_file(output)
            
            size_mb = Path(output).stat().st_size / (1024 * 1024)
            print(f"   💾 Guardado: {output}")
            print(f"   📏 Tamaño: {size_mb:.2f} MB")
            
            descargado = True
            break
        else:
            print(f"   ⚠️  No son líneas, continuando...")
            
    except Exception as e:
        error_msg = str(e)[:200]
        print(f"   ❌ Error: {error_msg}")

if not descargado:
    print("\n" + "="*80)
    print("❌ NO SE PUDO DESCARGAR AUTOMÁTICAMENTE")
    print("="*80)
    print("\n💡 DESCARGA MANUAL:")
    print("\n1. Ir a: https://www.colombiaenmapas.gov.co/?b=igac&u=0&t=23&servicio=205")
    print("2. Buscar capa: 'Drenaje Sencillo' o 'Hidrografía'")
    print("3. Click derecho → Descargar como Shapefile")
    print("4. Guardar en: datos_geograficos/red_hidrica/")
    print("\nO intenta desde:")
    print("https://geoportal.igac.gov.co/contenido/datos-abiertos-cartografia-y-geografia\n")
else:
    print("\n" + "="*80)
    print("✅ DESCARGA EXITOSA")
    print("="*80)
    print("\n🎯 Siguiente paso:")
    print("   conda run -n agro-rest python test_pdf_verificacion_con_mapa.py\n")
