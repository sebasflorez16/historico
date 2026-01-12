#!/usr/bin/env python
"""
Test con formato EXACTO de la documentación de EOSDA Field Imagery
https://doc.eos.com/docs/field-management-api/field-imagery/
"""

import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = 'https://api-connect.eos.com'
field_id = "10851431"

print("=" * 80)
print("TEST CON FORMATO EXACTO DE LA DOCUMENTACIÓN")
print("=" * 80)

# PASO 1: Obtener view_id usando /api/gdw/api
print("\n📋 PASO 1: Obtener view_id con api/gdw/api")
print("-" * 80)

session1 = requests.Session()
session1.headers.update({
    'Content-Type': 'application/json'
})

url_stats = f"{BASE_URL}/api/gdw/api?api_key={API_KEY}"
payload_stats = {
    'type': 'mt_stats',
    'params': {
        'bm_type': ['ndvi'],
        'date_start': '2025-12-01',
        'date_end': '2025-12-31',
        'field_id': field_id,
        'sensors': ['S2L2A'],
        'reference': f'test_{field_id}',
        'limit': 10,
        'max_cloud_cover_in_aoi': 50
    }
}

print(f"POST {url_stats.replace(API_KEY, '***')}")
print(f"Payload: {json.dumps(payload_stats, indent=2)}")

response1 = session1.post(url_stats, json=payload_stats, timeout=60)
print(f"Status: {response1.status_code}")

if response1.status_code in [200, 201, 202]:
    data1 = response1.json()
    print(f"✅ Request exitoso: {json.dumps(data1, indent=2)}")
    
    task_id = data1.get('task_id')
    if task_id:
        print(f"\nTask ID: {task_id}")
        
        # Esperar resultados
        url_task = f"{BASE_URL}/api/gdw/api/{task_id}?api_key={API_KEY}"
        
        for i in range(20):
            time.sleep(5)
            print(f"Polling intento {i+1}...")
            
            resp = session1.get(url_task, timeout=30)
            if resp.status_code == 200:
                task_data = resp.json()
                status = task_data.get('status')
                print(f"Task status: {status}")
                
                if status == 'DONE':
                    print("\n✅ DATOS OBTENIDOS")
                    
                    # Buscar view_id
                    data_items = task_data.get('data', [])
                    if data_items:
                        view_id = data_items[0].get('view_id')
                        print(f"View ID encontrado: {view_id}")
                        
                        # PASO 2: Descargar imagen con Field Imagery API
                        print("\n" + "=" * 80)
                        print("🖼️ PASO 2: Descargar imagen con Field Imagery API")
                        print("=" * 80)
                        
                        # OPCIÓN A: Con x-api-key header (según documentación)
                        print("\n1️⃣ Formato con x-api-key header:")
                        print("-" * 80)
                        
                        session2a = requests.Session()
                        session2a.headers.update({
                            'x-api-key': API_KEY,
                            'Content-Type': 'application/json'
                        })
                        
                        url_img_a = f"{BASE_URL}/field-imagery/indicies/{field_id}"
                        payload_img = {
                            "params": {
                                "view_id": view_id,
                                "index": "NDVI",
                                "format": "png"
                            }
                        }
                        
                        print(f"POST {url_img_a}")
                        print(f"Headers: x-api-key: {API_KEY[:20]}...")
                        print(f"Payload: {json.dumps(payload_img, indent=2)}")
                        
                        resp_a = session2a.post(url_img_a, json=payload_img, timeout=60)
                        print(f"Status: {resp_a.status_code}")
                        print(f"Response: {resp_a.text[:500]}")
                        
                        # OPCIÓN B: Con api_key en URL
                        print("\n2️⃣ Formato con api_key en URL:")
                        print("-" * 80)
                        
                        session2b = requests.Session()
                        session2b.headers.update({
                            'Content-Type': 'application/json'
                        })
                        
                        url_img_b = f"{BASE_URL}/field-imagery/indicies/{field_id}?api_key={API_KEY}"
                        
                        print(f"POST {url_img_b.replace(API_KEY, '***')}")
                        print(f"Payload: {json.dumps(payload_img, indent=2)}")
                        
                        resp_b = session2b.post(url_img_b, json=payload_img, timeout=60)
                        print(f"Status: {resp_b.status_code}")
                        print(f"Response: {resp_b.text[:500]}")
                        
                        # Ver cuál funcionó
                        if resp_a.status_code in [200, 201, 202]:
                            print("\n✅ OPCIÓN A (x-api-key header) FUNCIONA")
                            request_id = resp_a.json().get('request_id')
                            print(f"Request ID: {request_id}")
                        elif resp_b.status_code in [200, 201, 202]:
                            print("\n✅ OPCIÓN B (api_key en URL) FUNCIONA")
                            request_id = resp_b.json().get('request_id')
                            print(f"Request ID: {request_id}")
                        else:
                            print("\n❌ Ambas opciones fallaron")
                    break
                elif status in ['FAILED', 'ERROR']:
                    print(f"❌ Task falló")
                    break
else:
    print(f"❌ Error: {response1.text[:500]}")

print("\n" + "=" * 80)
