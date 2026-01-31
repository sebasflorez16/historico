#!/usr/bin/env python3
"""
Script para descargar límites departamentales oficiales de Colombia desde IGAC.

Descarga el shapefile oficial de departamentos de Colombia y lo guarda
en datos_geograficos/limites_departamentales/

Fuente: IGAC (Instituto Geográfico Agustín Codazzi)
https://geoportal.igac.gov.co/
"""

import os
import sys
import requests
import zipfile
from pathlib import Path

# Configuración
BASE_DIR = Path(__file__).parent
DATOS_DIR = BASE_DIR / "datos_geograficos" / "limites_departamentales"

# URL del WFS de IGAC - Límites Departamentales
# Usando la capa MGN_DPTO_POLITICO del Marco Geoestadístico Nacional
WFS_URL = "https://geoservicos.igac.gov.co/geoserver/MGN/wfs"

def descargar_departamentos_colombia():
    """
    Descarga los límites departamentales de Colombia desde IGAC usando WFS.
    """
    
    print("🗺️  Descargando límites departamentales de Colombia desde IGAC...")
    
    # Crear directorio si no existe
    DATOS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Parámetros WFS para descargar como GeoJSON
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeName': 'MGN:MGN_DPTO_POLITICO',  # Capa de departamentos
        'outputFormat': 'application/json',    # GeoJSON
        'srsName': 'EPSG:4326'                 # WGS84
    }
    
    try:
        # Descargar GeoJSON
        print(f"📥 Descargando desde: {WFS_URL}")
        response = requests.get(WFS_URL, params=params, timeout=60)
        response.raise_for_status()
        
        # Guardar GeoJSON
        output_file = DATOS_DIR / "departamentos_colombia.geojson"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Límites departamentales descargados exitosamente")
        print(f"📁 Guardado en: {output_file}")
        
        # Validar que sea un GeoJSON válido
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            features = data.get('features', [])
            print(f"📊 Total de departamentos: {len(features)}")
            
            # Listar departamentos
            departamentos = [f.get('properties', {}).get('DPTO_CNMBR', 'Sin nombre') 
                           for f in features]
            print("\n📋 Departamentos descargados:")
            for dept in sorted(departamentos):
                print(f"   - {dept}")
        
        return output_file
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar: {e}")
        print("\n🔄 Intentando método alternativo (descarga manual)...")
        return descargar_manual_backup()
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def descargar_manual_backup():
    """
    Método de respaldo: descarga desde fuente alternativa.
    """
    
    # URL alternativa - Datos Abiertos Colombia
    ALTERNATIVE_URL = "https://www.datos.gov.co/api/geospatial/xdk5-pm3f?method=export&format=GeoJSON"
    
    try:
        print(f"📥 Descargando desde fuente alternativa...")
        response = requests.get(ALTERNATIVE_URL, timeout=60)
        response.raise_for_status()
        
        output_file = DATOS_DIR / "departamentos_colombia.geojson"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Descarga alternativa exitosa")
        print(f"📁 Guardado en: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error en descarga alternativa: {e}")
        print("\n⚠️  Por favor, descarga manualmente desde:")
        print("   https://geoportal.igac.gov.co/")
        print("   Busca: Marco Geoestadístico Nacional > Departamentos")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("🇨🇴  DESCARGA DE LÍMITES DEPARTAMENTALES DE COLOMBIA - IGAC")
    print("=" * 70)
    print()
    
    resultado = descargar_departamentos_colombia()
    
    if resultado:
        print("\n" + "=" * 70)
        print("✅ DESCARGA COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print(f"\n📁 Archivo guardado en:")
        print(f"   {resultado}")
        print(f"\n💡 Ahora puedes usar este archivo en el generador de PDF")
    else:
        print("\n" + "=" * 70)
        print("❌ NO SE PUDO COMPLETAR LA DESCARGA")
        print("=" * 70)
        sys.exit(1)
