#!/usr/bin/env python
"""
Diagnóstico rápido: ¿Por qué no se carga la red hídrica?
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from verificador_legal import VerificadorRestriccionesLegales
from pathlib import Path

print("=" * 70)
print("🔍 DIAGNÓSTICO: RED HÍDRICA")
print("=" * 70)

# Verificar archivos disponibles
red_hidrica_dir = Path("datos_geograficos/red_hidrica")
print(f"\n📂 Directorio: {red_hidrica_dir}")
print(f"   Existe: {red_hidrica_dir.exists()}")

if red_hidrica_dir.exists():
    shapefiles = list(red_hidrica_dir.glob("*.shp"))
    print(f"\n📄 Archivos .shp encontrados: {len(shapefiles)}")
    for shp in shapefiles:
        size_mb = shp.stat().st_size / (1024 * 1024)
        print(f"   • {shp.name} ({size_mb:.1f} MB)")

# Inicializar verificador
print(f"\n🔧 Inicializando verificador...")
verificador = VerificadorRestriccionesLegales()

# Verificar qué se cargó
print(f"\n📊 Resultado:")
print(f"   Red hídrica cargada: {verificador.stats['red_hidrica_loaded']}")
if verificador.red_hidrica is not None:
    print(f"   Elementos en red_hidrica: {len(verificador.red_hidrica)}")
    print(f"   Columnas: {list(verificador.red_hidrica.columns)}")
    
    # Verificar geometrías
    tipos = verificador.red_hidrica.geometry.geom_type.value_counts()
    print(f"   Tipos de geometría:")
    for tipo, count in tipos.items():
        print(f"      {tipo}: {count}")
    
    # Ver bounds
    bounds = verificador.red_hidrica.total_bounds
    print(f"   Bounds: {bounds}")
    
    # Ver primeros registros
    print(f"\n🔍 Primeros 3 registros:")
    print(verificador.red_hidrica.head(3))
else:
    print(f"   ❌ red_hidrica es None")

print("\n" + "=" * 70)
