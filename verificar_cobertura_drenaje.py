#!/usr/bin/env python
"""
Verificar cobertura del shapefile de drenaje vs ubicación de la parcela
"""
import geopandas as gpd
from pathlib import Path

archivo = Path(__file__).parent / 'datos_geograficos' / 'red_hidrica' / 'drenajes_sencillos_igac.shp'
red = gpd.read_file(str(archivo))
if red.crs != 'EPSG:4326':
    red = red.to_crs('EPSG:4326')

print(f"📊 Shapefile: {archivo.name}")
print(f"   Total registros: {len(red):,}\n")

# Bbox del shapefile completo
bounds = red.total_bounds
print(f"Cobertura TOTAL del shapefile:")
print(f"  Longitud: {bounds[0]:.4f} a {bounds[2]:.4f}")
print(f"  Latitud: {bounds[1]:.4f} a {bounds[3]:.4f}\n")

# Parcela 6 ubicación
parcela_lon, parcela_lat = -72.236, 5.222
print(f"Ubicación parcela 6: {parcela_lon:.4f}, {parcela_lat:.4f}")
print(f"  Tauramena, Casanare (región noroccidental)\n")

# Filtrar por bbox de Casanare
bbox_casanare = [-73.0, 5.0, -69.0, 6.5]
red_cas = red.cx[bbox_casanare[0]:bbox_casanare[2], bbox_casanare[1]:bbox_casanare[3]]
print(f"Registros filtrados por bbox Casanare [-73.0, 5.0, -69.0, 6.5]: {len(red_cas)}")

if len(red_cas) > 0:
    bounds_cas = red_cas.total_bounds
    print(f"  Cobertura real de esos {len(red_cas)} cauces:")
    print(f"    Longitud: {bounds_cas[0]:.4f} a {bounds_cas[2]:.4f}")
    print(f"    Latitud: {bounds_cas[1]:.4f} a {bounds_cas[3]:.4f}\n")
    
    # Verificar si parcela está dentro
    dentro = (bounds_cas[0] <= parcela_lon <= bounds_cas[2] and
              bounds_cas[1] <= parcela_lat <= bounds_cas[3])
    
    if dentro:
        print(f"✅ La parcela ESTÁ dentro de la cobertura de los cauces filtrados")
    else:
        print(f"❌ La parcela NO está dentro de la cobertura de los cauces filtrados")
        print(f"\n  Distancia aproximada:")
        print(f"    Longitud parcela: {parcela_lon:.4f}")
        print(f"    Longitud más cercana del shapefile: {bounds_cas[0]:.4f}")
        print(f"    Diferencia: ~{abs(parcela_lon - bounds_cas[0]) * 111:.0f} km")

# Filtrar por bbox MUY específico alrededor de Tauramena
bbox_tauramena = [-72.5, 5.0, -72.0, 5.5]
red_tau = red.cx[bbox_tauramena[0]:bbox_tauramena[2], bbox_tauramena[1]:bbox_tauramena[3]]
print(f"\n🎯 Registros en bbox específico de Tauramena [-72.5, 5.0, -72.0, 5.5]: {len(red_tau)}")

if len(red_tau) == 0:
    print(f"   ❌ NO HAY CAUCES en la zona de Tauramena")
    print(f"   Este shapefile probablemente solo cubre PARTE de Casanare")
    print(f"   (ej: solo zona oriental/Meta, no zona noroccidental)")
