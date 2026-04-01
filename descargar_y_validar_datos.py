#!/usr/bin/env python
"""Script para descargar y validar datos geográficos oficiales"""
import geopandas as gpd
from pathlib import Path

def crear_dirs():
    for d in ['datos_geograficos/red_hidrica', 'datos_geograficos/runap', 
              'datos_geograficos/resguardos', 'datos_geograficos/paramos']:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("✅ Directorios creados\n")

def descargar_runap():
    print("📥 Descargando RUNAP...")
    try:
        url = 'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=json'
        gdf = gpd.read_file(url)
        gdf.to_file('datos_geograficos/runap/areas_protegidas_runap.shp')
        print(f"✅ RUNAP descargado: {len(gdf)} áreas\n")
        return True
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def validar_red_#!/usr/bin/env python
"""Script para descargar y validar datos geográficos oficiales"""
import geopandas as gpd  """Script para descaioimport geopandas as gpd
from pathliob('*.shp')):
        print("❌from pathlib import Patr
def crear_dirs():
    ?   for d in ['d                'datos_geograficos/resguardos', 'datos_geograficos/paramos'GA        Path(d).mkdir(parents=True, exist_ok=True)
    print("✅ Director r    print("✅ Directorios creados\n")

def desca*.
def descargar_runap():
    print("?sh    print("📥 Descaeo    try:
        url = 'http://mapas.an       ['        gdf = gpd.read_file(url)
        gdf.to_file('datos_geograficos/runap/areas_protegidas_runap.shp')
        print(f"✅ RUNAP descargado: {len(g)
        print(f"   rm '{shp}'")
         print(f"✅ RUNAP descargado: {len(gdf)} áreas\n")
        retuna        return True
    except Exception as e:
        priVe    except ExceptiAT        print(f"❌ Erro           return False

def validar'L
def validar_red_#!ine"""Script para descargar y validar dinimport geopandas as gpd  """Script para deales\n")
        return Tfrom pathliob('*.shp')):
        print("❌from pathlib import Patr
d 8        print("❌from Y def crear_dirs():
    ?   for d in ['d +    ?   for dcr    print("✅ Director r    print("✅ Directorios creados\n")

def desca*.
def descargar_runap():
    print("?sh    print("📥 D+ "\n")
    
    i
def desca*.
def descargar_runap():
    print("?sh    print(verdef descarco    print("?sh    pe:        url = 'http://mapas.an       ['       os        gdf.to_file('datos_geograficos/runap/areas_protegidas_runap.shS.      
