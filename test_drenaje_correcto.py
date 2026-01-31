#!/usr/bin/env python
"""
Probar shapefile CORRECTO de drenaje (líneas de cauces)
"""
import geopandas as gpd
from pathlib import Path

archivo = Path("/Users/sebasflorez16/Documents/AgroTech Historico/datos_geograficos/red_hidrica/drenajes_sencillos_igac.shp")

print(f"🔍 Analizando: {archivo.name}")
print(f"   Tamaño: {archivo.stat().st_size / 1024:.1f} KB\n")

red = gpd.read_file(str(archivo))

if red.crs != 'EPSG:4326':
    red = red.to_crs('EPSG:4326')

print(f"Total registros: {len(red):,}")
print(f"Columnas: {list(red.columns)}")
print(f"\nTipos de geometría:")
tipos = red.geometry.geom_type.value_counts()
for tipo, count in tipos.items():
    print(f"  - {tipo}: {count:,} ({count/len(red)*100:.1f}%)")

# Filtrar Casanare
bbox = [-73.0, 5.0, -69.0, 6.5]
red_cas = red.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
print(f"\n✅ Registros en Casanare: {len(red_cas):,}")

# Mostrar muestra
if len(red_cas) > 0:
    print(f"\n📋 Muestra de 5 cauces:")
    for idx, row in red_cas.head(5).iterrows():
        print(f"  {idx}. {row.geometry.geom_type}")
        for col in red_cas.columns:
            if col != 'geometry':
                val = row.get(col)
                if val and str(val) != 'None':
                    print(f"      {col}: {val}")
