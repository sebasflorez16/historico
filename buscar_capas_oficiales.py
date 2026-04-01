#!/usr/bin/env python3
"""
Buscar servicios oficiales de capas geográficas para verificación legal
"""
import requests
import json

print('🔍 Buscando capas oficiales de Colombia...\n')

# 1. Buscar en IGAC
print('=' * 80)
print('📍 INSTITUTO GEOGRÁFICO AGUSTÍN CODAZZI (IGAC)')
print('=' * 80)

base_url = 'https://mapas2.igac.gov.co/server/rest/services'
servicios_igac = [
    'carto/carto100000colombia2019/MapServer',
    'IGAC_Catastro/MapServer',
]

for servicio in servicios_igac:
    try:
        url = f'{base_url}/{servicio}?f=json'
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f'\n✅ {servicio}')
            if 'layers' in data:
                for layer in data['layers']:
                    nombre = layer.get('name', '').lower()
                    if any(x in nombre for x in ['runap', 'parque', 'proteg', 'resguardo', 'indigena', 'paramo', 'reserva']):
                        print(f'   🎯 Layer {layer["id"]}: {layer["name"]}')
    except Exception as e:
        print(f'   ❌ Error: {e}')

# 2. Buscar en Parques Nacionales (RUNAP)
print('\n' + '=' * 80)
print('🌳 PARQUES NACIONALES NATURALES (RUNAP)')
print('=' * 80)

runap_urls = [
    'https://mapas.parquesnacionales.gov.co/server/rest/services',
    'https://geoservicios.parquesnacionales.gov.co/arcgis/rest/services'
]

for base in runap_urls:
    try:
        r = requests.get(f'{base}?f=json', timeout=10)
        if r.status_code == 200:
            print(f'\n✅ Servidor encontrado: {base}')
            data = r.json()
            if 'services' in data:
                for svc in data['services'][:10]:
                    print(f'   📁 {svc["name"]} ({svc["type"]})')
    except:
        pass

# 3. GeoPortal DANE
print('\n' + '=' * 80)
print('📊 DANE - DEPARTAMENTO ADMINISTRATIVO NACIONAL DE ESTADÍSTICA')
print('=' * 80)

dane_urls = [
    'https://geoportal.dane.gov.co/geovisores',
    'https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services'
]

for url in dane_urls:
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            print(f'✅ Accesible: {url}')
    except:
        pass

# 4. GeoPortal de datos abiertos
print('\n' + '=' * 80)
print('🌐 DATOS ABIERTOS COLOMBIA')
print('=' * 80)

print("""
Fuentes recomendadas:

1. RUNAP (Áreas Protegidas):
   https://www.datos.gov.co/dataset/Registro-Único-Nacional-de-Áreas-Protegidas-RUN/5tzj-nh25

2. Resguardos Indígenas:
   https://www.datos.gov.co/dataset/Resguardos-Indígenas/a4cr-a9mr
   
3. Páramos:
   https://www.datos.gov.co/dataset/Páramos-Colombia/c4gx-b6f5

4. GeoPortal IDE Colombia:
   https://www.colombiaenmapas.gov.co
""")

print('\n✅ Búsqueda completada')
