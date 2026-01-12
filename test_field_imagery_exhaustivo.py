#!/usr/bin/env python
"""
Test EXHAUSTIVO de Field Imagery API de EOSDA
Probando diferentes formatos y endpoints según documentación
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = 'https://api-connect.eos.com'

session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
})

print("=" * 80)
print("TEST EXHAUSTIVO DE FIELD IMAGERY API")
print("=" * 80)

# Usar el field_id que acabas de crear
field_id = "10851431"

# Primero obtener un view_id válido reciente
print("\n📋 PASO 1: Obtener view_id válido con Statistics API")
print("-" * 80)

url_stats = f"{BASE_URL}/satellite-imagery/fields/{field_id}/statistics"
payload_stats = {
    "start_date": "2025-12-01",
    "end_date": "2025-12-31",
    "indices": ["ndvi"],
    "cloud_cover_max": 50
}

print(f"POST {url_stats}")
print(f"Payload: {json.dumps(payload_stats, indent=2)}")

response_stats = session.post(url_stats, json=payload_stats, timeout=30)
print(f"Status: {response_stats.status_code}")

if response_stats.status_code == 200:
    data_stats = response_stats.json()
    resultados = data_stats.get('results', [])
    print(f"✅ Statistics API funciona - {len(resultados)} escenas encontradas")
    
    if resultados:
        # Usar la escena más reciente
        escena = resultados[-1]
        view_id = escena.get('view_id')
        fecha = escena.get('date')
        ndvi_mean = escena.get('statistics', {}).get('ndvi', {}).get('mean')
        nubosidad = escena.get('cloud_cover')
        
        print(f"\n📸 Escena seleccionada:")
        print(f"  - Fecha: {fecha}")
        print(f"  - View ID: {view_id}")
        print(f"  - NDVI: {ndvi_mean}")
        print(f"  - Nubosidad: {nubosidad}%")
        
        # PROBAR DIFERENTES FORMATOS DE FIELD IMAGERY API
        print("\n" + "=" * 80)
        print("🔬 PASO 2: Probar diferentes formatos de Field Imagery API")
        print("=" * 80)
        
        # Test 1: Formato usado actualmente en el código
        print("\n1️⃣ TEST: Formato actual del código (indicies)")
        print("-" * 80)
        
        url1 = f"{BASE_URL}/field-imagery/indicies/{field_id}"
        payload1 = {
            'params': {
                'view_id': view_id,
                'index': 'NDVI',  # Mayúsculas
                'format': 'png'
            }
        }
        
        print(f"POST {url1}")
        print(f"Payload: {json.dumps(payload1, indent=2)}")
        
        response1 = session.post(url1, json=payload1, timeout=30)
        print(f"Status: {response1.status_code}")
        print(f"Response: {response1.text[:500]}")
        
        # Test 2: Intentar con 'indices' (plural) en URL
        print("\n2️⃣ TEST: Con 'indices' (plural)")
        print("-" * 80)
        
        url2 = f"{BASE_URL}/field-imagery/indices/{field_id}"
        
        print(f"POST {url2}")
        print(f"Payload: {json.dumps(payload1, indent=2)}")
        
        response2 = session.post(url2, json=payload2, timeout=30)
        print(f"Status: {response2.status_code}")
        print(f"Response: {response2.text[:500]}")
        
        # Test 3: Intentar con index en minúsculas
        print("\n3️⃣ TEST: Con index en minúsculas")
        print("-" * 80)
        
        payload3 = {
            'params': {
                'view_id': view_id,
                'index': 'ndvi',  # minúsculas
                'format': 'png'
            }
        }
        
        print(f"POST {url1}")
        print(f"Payload: {json.dumps(payload3, indent=2)}")
        
        response3 = session.post(url1, json=payload3, timeout=30)
        print(f"Status: {response3.status_code}")
        print(f"Response: {response3.text[:500]}")
        
        # Test 4: Sin params wrapper
        print("\n4️⃣ TEST: Sin wrapper 'params'")
        print("-" * 80)
        
        payload4 = {
            'view_id': view_id,
            'index': 'NDVI',
            'format': 'png'
        }
        
        print(f"POST {url1}")
        print(f"Payload: {json.dumps(payload4, indent=2)}")
        
        response4 = session.post(url1, json=payload4, timeout=30)
        print(f"Status: {response4.status_code}")
        print(f"Response: {response4.text[:500]}")
        
        # Test 5: Endpoint diferente (sin indicies)
        print("\n5️⃣ TEST: Endpoint field-imagery sin /indicies")
        print("-" * 80)
        
        url5 = f"{BASE_URL}/field-imagery/{field_id}"
        
        print(f"POST {url5}")
        print(f"Payload: {json.dumps(payload1, indent=2)}")
        
        response5 = session.post(url5, json=payload1, timeout=30)
        print(f"Status: {response5.status_code}")
        print(f"Response: {response5.text[:500]}")
        
        # Test 6: Verificar headers
        print("\n6️⃣ TEST: Verificar detalles de autenticación")
        print("-" * 80)
        
        print(f"Authorization header: Bearer {API_KEY[:20]}...{API_KEY[-10:]}")
        print(f"Content-Type: {session.headers.get('Content-Type')}")
        
        # Test 7: Intentar GET en lugar de POST
        print("\n7️⃣ TEST: Probar GET con query params")
        print("-" * 80)
        
        url7 = f"{BASE_URL}/field-imagery/indicies/{field_id}"
        params7 = {
            'view_id': view_id,
            'index': 'NDVI',
            'format': 'png'
        }
        
        print(f"GET {url7}")
        print(f"Params: {params7}")
        
        response7 = session.get(url7, params=params7, timeout=30)
        print(f"Status: {response7.status_code}")
        print(f"Response: {response7.text[:500]}")
        
    else:
        print("❌ No hay escenas disponibles en Statistics")
else:
    print(f"❌ Error en Statistics API: {response_stats.status_code}")
    print(f"Response: {response_stats.text[:500]}")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print("""
Busca el test que tenga Status 200/201/202 (exitoso)
Si todos dan 403: Tu plan no incluye Field Imagery API
Si alguno funciona: Hay que ajustar el código para usar ese formato exacto
""")
