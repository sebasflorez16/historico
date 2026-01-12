#!/usr/bin/env python
"""
Test del fix: x-api-key header en GET para Field Imagery API
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
print("TEST FIX: x-api-key header en Field Imagery GET")
print("=" * 80)

# PASO 1: Obtener view_id con /api/gdw/api (ya funciona)
print("\n📋 PASO 1: Obtener view_id")
print("-" * 80)

session = requests.Session()
session.headers.update({'Content-Type': 'application/json'})

url_stats = f"{BASE_URL}/api/gdw/api?api_key={API_KEY}"
payload = {
    'type': 'mt_stats',
    'params': {
        'bm_type': ['ndvi'],
        'date_start': '2024-01-01',
        'date_end': '2024-12-31',
        'field_id': field_id,
        'sensors': ['S2L2A'],
        'reference': f'test_header_fix_{field_id}',
        'limit': 5,
        'max_cloud_cover_in_aoi': 80
    }
}

print(f"POST {url_stats.replace(API_KEY, '***')}")
resp = session.post(url_stats, json=payload, timeout=60)
print(f"Status: {resp.status_code}")

if resp.status_code == 202:
    task_id = resp.json().get('task_id')
    print(f"Task ID: {task_id}")
    
    # Esperar resultados
    url_task = f"{BASE_URL}/api/gdw/api/{task_id}?api_key={API_KEY}"
    
    for i in range(30):
        time.sleep(3)
        print(f"Polling {i+1}...", end=' ')
        
        task_resp = session.get(url_task, timeout=30)
        if task_resp.status_code == 200:
            task_data = task_resp.json()
            status = task_data.get('status')
            print(f"status={status}")
            
            if status == 'DONE':
                data_items = task_data.get('data', [])
                if data_items:
                    view_id = data_items[0].get('view_id')
                    print(f"\n✅ View ID: {view_id}")
                    
                    # PASO 2: Field Imagery con x-api-key header
                    print("\n" + "=" * 80)
                    print("🖼️ PASO 2: Field Imagery API con x-api-key header")
                    print("=" * 80)
                    
                    # Crear request de imagen
                    url_img = f"{BASE_URL}/field-imagery/indicies/{field_id}?api_key={API_KEY}"
                    payload_img = {
                        "params": {
                            "view_id": view_id,
                            "index": "NDVI",
                            "format": "png"
                        }
                    }
                    
                    print(f"\nPOST {url_img.replace(API_KEY, '***')}")
                    resp_img = session.post(url_img, json=payload_img, timeout=60)
                    print(f"Status: {resp_img.status_code}")
                    
                    if resp_img.status_code in [200, 201, 202]:
                        request_id = resp_img.json().get('request_id')
                        print(f"Request ID: {request_id}")
                        
                        # GET con x-api-key header
                        url_download = f"{BASE_URL}/field-imagery/{field_id}/{request_id}"
                        
                        for j in range(15):
                            time.sleep(5)
                            print(f"\nGET intento {j+1}/15")
                            print(f"URL: {url_download}")
                            print(f"Header: x-api-key: {API_KEY[:20]}...")
                            
                            # ✅ ESTE ES EL FIX: agregar x-api-key header
                            resp_download = session.get(
                                url_download,
                                headers={'x-api-key': API_KEY},
                                timeout=60
                            )
                            
                            print(f"Status: {resp_download.status_code}")
                            print(f"Content-Type: {resp_download.headers.get('Content-Type', 'N/A')}")
                            print(f"Content-Length: {resp_download.headers.get('Content-Length', 'N/A')}")
                            
                            if resp_download.status_code == 200:
                                content_type = resp_download.headers.get('Content-Type', '')
                                if 'image' in content_type:
                                    print(f"\n✅ ¡IMAGEN DESCARGADA! ({len(resp_download.content)} bytes)")
                                    print(f"PNG válido: {resp_download.content[:4] == b'\\x89PNG'}")
                                    break
                                else:
                                    try:
                                        data = resp_download.json()
                                        print(f"JSON: {json.dumps(data, indent=2)[:200]}")
                                    except:
                                        print(f"Response: {resp_download.text[:200]}")
                            elif resp_download.status_code == 404:
                                print("⏳ Imagen aún no lista...")
                            else:
                                print(f"Response: {resp_download.text[:300]}")
                                break
                    else:
                        print(f"❌ Error: {resp_img.text[:300]}")
                break
            elif status in ['FAILED', 'ERROR']:
                print(f"\n❌ Task falló")
                break
else:
    print(f"❌ Error: {resp.text[:300]}")

print("\n" + "=" * 80)
