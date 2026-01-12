#!/usr/bin/env python
"""
Test específico de endpoints EOSDA que usa AgroTech
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

print("=" * 70)
print("TEST ESPECÍFICO DE ENDPOINTS QUE USA AGROTECH")
print("=" * 70)

# Test 1: Crear field (POST) - Lo que funciona según el usuario
print("\n1️⃣ TEST: Crear/Listar Fields (POST/GET)")
print("-" * 70)

# Primero listar fields existentes
try:
    url = f"{BASE_URL}/fields"
    params = {'limit': 5}
    response = session.get(url, params=params, timeout=10)
    
    print(f"GET /fields")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        fields = data.get('results', [])
        print(f"✅ Listar fields FUNCIONA - Total: {len(fields)}")
        
        if fields:
            field_ejemplo = fields[0]
            field_id = field_ejemplo.get('id')
            print(f"Field ejemplo: {field_ejemplo.get('name')} (ID: {field_id})")
            
            # Test 2: Obtener Statistics de ese field
            print(f"\n2️⃣ TEST: Statistics API para field {field_id}")
            print("-" * 70)
            
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
                print(f"✅ Statistics API FUNCIONA")
                print(f"Total escenas: {len(data_stats.get('results', []))}")
                
                if data_stats.get('results'):
                    primera_escena = data_stats['results'][0]
                    print(f"\nPrimera escena:")
                    print(f"  - Fecha: {primera_escena.get('date')}")
                    print(f"  - View ID: {primera_escena.get('view_id')}")
                    print(f"  - NDVI mean: {primera_escena.get('statistics', {}).get('ndvi', {}).get('mean')}")
                    
                    view_id = primera_escena.get('view_id')
                    
                    # Test 3: Intentar descargar imagen con ese view_id
                    print(f"\n3️⃣ TEST: Field Imagery API con view_id real")
                    print("-" * 70)
                    
                    url_imagery = f"{BASE_URL}/field-imagery/indicies/{field_id}"
                    payload_imagery = {
                        'params': {
                            'view_id': view_id,
                            'index': 'NDVI',
                            'format': 'png'
                        }
                    }
                    
                    print(f"POST {url_imagery}")
                    print(f"Payload: {json.dumps(payload_imagery, indent=2)}")
                    
                    response_imagery = session.post(url_imagery, json=payload_imagery, timeout=30)
                    print(f"Status: {response_imagery.status_code}")
                    print(f"Response: {response_imagery.text[:500]}")
                    
                    if response_imagery.status_code == 403:
                        print("\n❌ CONFIRMADO: Sin acceso a Field Imagery API")
                        print("   Tu plan NO incluye descargar imágenes satelitales")
                        print("   Solo puedes obtener datos numéricos (Statistics)")
                    elif response_imagery.status_code in [200, 201, 202]:
                        print("✅ Field Imagery API FUNCIONA")
                        print(f"Request ID: {response_imagery.json().get('request_id')}")
                    else:
                        print(f"⚠️ Error inesperado: {response_imagery.status_code}")
            elif response_stats.status_code == 403:
                print("❌ Sin acceso a Statistics API")
                print(f"Response: {response_stats.text[:500]}")
            else:
                print(f"⚠️ Error: {response_stats.status_code}")
                print(f"Response: {response_stats.text[:500]}")
    elif response.status_code == 403:
        print("❌ Sin acceso a listar fields")
        print("   Pero según usuario, crear fields SÍ funciona")
    else:
        print(f"⚠️ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("CONCLUSIÓN")
print("=" * 70)
print("""
Si Statistics API funciona (200) pero Field Imagery da 403:
  ✅ Tu API key está ACTIVA y FUNCIONANDO
  ✅ Puedes obtener datos numéricos (NDVI, NDMI, SAVI)
  ❌ NO puedes descargar imágenes PNG de satélite
  
SOLUCIÓN PARA AGROTECH:
  1. El timeline puede funcionar SIN imágenes (placeholder con colores)
  2. Los PDFs pueden tener gráficos generados (matplotlib)
  3. Todo el análisis funciona con datos numéricos
  4. Para imágenes reales: Upgrade a plan PRO de EOSDA
""")
