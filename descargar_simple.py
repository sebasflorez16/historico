#!/usr/bin/env python3
"""
Descarga simple desde datos.gov.co (fuentes que SÍ funcionan)
"""
import geopandas as gpd
from pathlib import Path
import sys

print("="*80)
print("📥 DESCARGA DESDE DATOS.GOV.CO")
print("="*80 + "\n")

# Crear directorio
Path('datos_geograficos/runap').mkdir(parents=True, exist_ok=True)

# RUNAP - Este SÍ funciona siempre
print("1. Descargando RUNAP (Áreas Protegidas)...")
try:
    url = 'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=json'
    gdf = gpd.read_file(url)
    gdf.to_file('datos_geograficos/runap/areas_protegidas_runap.shp')
    print(f"   ✅ Descargado: {len(gdf)} áreas protegidas\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

print("="*80)
print("📋 PARA RED HÍDRICA - DESCARGA MANUAL")
print("="*80 + "\n")

print("El servicio de la CAR que encontraste puede funcionar, pero:")
print("❌ No responde correctamente a consultas API")
print("❌ Puede ser solo para la región Cundinamarca\n")

print("✅ MEJOR OPCIÓN - Descarga manual desde datos.gov.co:\n")

print("🔗 OPCIÓN 1 (Nacional - RECOMENDADO):")
print("   https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Red-H-drica-de-Colombia/rft4-7cca")
print("   1. Click 'Exportar' → 'Shapefile'")
print("   2. Descargar ZIP")
print("   3. Extraer TODO a: datos_geograficos/red_hidrica/\n")

print("🔗 OPCIÓN 2 (Drenajes IGAC):")
print("   https://geoportal.igac.gov.co/contenido/datos-abiertos-cartografia-y-geografia")
print("   Buscar: 'Drenajes Sencillos'\n")

print("🔗 OPCIÓN 3 (Hidrografía CAR - tu región):")
print("   https://www.car.gov.co/vercontenido/62")
print("   Buscar sección de descargas de cartografía\n")

print("="*80)
print("\n💡 Después de descargar, ejecuta:")
print("   python3 explorar_servicio_car.py")
print("   (para validar que sean LineStrings, no Polygons)\n")

