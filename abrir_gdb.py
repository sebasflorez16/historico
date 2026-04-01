#!/usr/bin/env python3
"""
Script para abrir archivos GDB (Geodatabase) y convertirlos a Shapefile
"""
import geopandas as gpd
import fiona
from pathlib import Path
import sys

print("="*80)
print("🗂️  ABRIR ARCHIVO GDB (GEODATABASE)")
print("="*80 + "\n")

# Buscar archivos GDB
archivos_gdb = list(Path('.').glob('*.gdb'))
carpetas_gdb = [d for d in Path('.').iterdir() if d.is_dir() and d.suffix == '.gdb']

print("📁 Buscando archivos GDB...")

if archivos_gdb:
    print(f"   Encontrados: {[str(g) for g in archivos_gdb]}")
    gdb_path = str(archivos_gdb[0])
elif carpetas_gdb:
    print(f"   Encontrados: {[str(g) for g in carpetas_gdb]}")
    gdb_path = str(carpetas_gdb[0])
else:
    print("❌ No se encontró ningún archivo .gdb")
    print("\n💡 Coloca el archivo/carpeta .gdb en:")
    print(f"   {Path.cwd()}")
    sys.exit(1)

print(f"\n📂 Abriendo: {gdb_path}\n")

try:
    # Listar capas disponibles en el GDB
    capas = fiona.listlayers(gdb_path)
    print(f"✅ Capas disponibles en el GDB ({len(capas)}):")
    for i, capa in enumerate(capas, 1):
        print(f"   {i}. {capa}")
    
    # Buscar capa de drenajes/hidrografía
    capas_drenaje = [c for c in capas if any(palabra in c.lower() 
                     for palabra in ['drenaje', 'hidro', 'rio', 'corriente', 'agua', 'cauce'])]
    
    if capas_drenaje:
        capa_usar = capas_drenaje[0]
        print(f"\n🎯 Capa detectada automáticamente: {capa_usar}")
    else:
        print(f"\n⚠️  No se detectó capa de drenaje automáticamente")
        print(f"   Usando primera capa: {capas[0]}")
        capa_usar = capas[0]
    
    # Leer la capa
    print(f"\n📥 Leyendo capa: {capa_usar}...")
    gdf = gpd.read_file(gdb_path, layer=capa_usar)
    
    print(f"✅ Leído: {len(gdf)} elementos")
    print(f"   CRS: {gdf.crs}")
    
    # Ver tipos de geometría
    tipos = gdf.geometry.geom_type.value_counts()
    print(f"   Tipos de geometría:")
    for tipo, count in tipos.items():
        print(f"      • {tipo}: {count}")
    
    # Validar si son líneas
    if any(t in ['LineString', 'MultiLineString'] for t in gdf.geometry.geom_type.unique()):
        print(f"\n✅ ¡CORRECTO! Son líneas (drenajes)")
        
        # Guardar como Shapefile
        Path('datos_geograficos/red_hidrica').mkdir(parents=True, exist_ok=True)
        output = 'datos_geograficos/red_hidrica/drenajes_colombia.shp'
        
        print(f"\n💾 Guardando como Shapefile...")
        gdf.to_file(output)
        
        size_mb = Path(output).stat().st_size / (1024 * 1024)
        print(f"✅ GUARDADO: {output}")
        print(f"   Tamaño: {size_mb:.2f} MB")
        
        print(f"\n🎯 ¡LISTO PARA USAR!")
        print(f"\nEjecuta el test:")
        print(f"   conda run -n agro-rest python test_pdf_verificacion_con_mapa.py")
        
    else:
        print(f"\n❌ No son líneas - estos son polígonos")
        print(f"   Necesitas la capa de DRENAJES, no zonificación")
        print(f"\n   Capas disponibles:")
        for capa in capas:
            print(f"      - {capa}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
