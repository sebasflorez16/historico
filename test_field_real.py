#!/usr/bin/env python
"""
Test con field_id REAL que existe: 10772494
"""

import requests
import json
import time

API_KEY = "apk.32451a8331eb39702e5ae49d3ff9488abf0c64314e620874843962e015ca6468"
BASE_URL = 'https://api-connect.eos.com'
field_id = "10772494"

print("=" * 80)
print("TEST CON FIELD REAL 10772494")
print("=" * 80)

session = requests.Session()
session.headers.update({'Content-Type': 'application/json'})

# PASO 1: Obtener view_id con Statistics API
print(f"\n📋 PASO 1: Obtener view_id reciente")
print("-" * 80)

url_stats = f"{BASE_URL}/api/gdw/api?api_key={API_KEY}"
payload_stats = {
    'type': 'mt_stats',
    'params': {
        'bm_type': ['ndvi'],
        'date_start': '2024-01-01',
        'date_end': '2024-12-31',
        'field_id': field_id,
        'sensors': ['S2L2A'],
        'reference': f'test_real_{field_id}',
        'limit': 3,
        'max_cloud_cover_in_aoi': 80
    }
}

print(f"POST {url_stats.replace(API_KEY, '***')}")
resp = session.post(url_stats, json=payload_stats, timeout=60)
print(f"Status: {resp.status_code}")

if resp.status_code == 202:
    task_id = resp.json().get('task_id')
    print(f"Task ID: {task_id}")
    
    url_task = f"{BASE_URL}/api/gdw/api/{task_id}?api_key={API_KEY}"
    
    # Esperar resultados (máximo 60 segundos)
    for i in range(20):
        time.sleep(3)
        print(f"Polling {i+1}/20...", end=' ')
        
        task_resp = session.get(url_task, timeout=30)
        if task_resp.status_code == 200:
            task_data = task_resp.json()
            status = task_data.get('status')
            print(f"status={status}")
            
            if status == 'DONE':
                data_items = task_data.get('data', [])
                if data_items and len(data_items) > 0:
                    view_id = data_items[0].get('view_id')
                    print(f"\n✅ View ID obtenido: {view_id}")
                    
                    # PASO 2: Field Imagery con view_id
                    print("\n" + "=" * 80)
                    print("🖼️ PASO 2: Field Imagery API")
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
                    print(f"View ID: {view_id}")
                    
                    resp_img = session.post(url_img, json=payload_img, timeout=60)
                    print(f"Status: {resp_img.status_code}")
                    print(f"Response: {resp_img.text}")
                    
                    if resp_img.status_code in [200, 201, 202]:
                        request_id = resp_img.json().get('request_id')
                        print(f"\n✅ Request ID: {request_id}")
                        
                        # PASO 3: GET con x-api-key header (EL FIX)
                        url_download = f"{BASE_URL}/field-imagery/{field_id}/{request_id}"
                        
                        print(f"\n" + "=" * 80)
                        print("📥 PASO 3: Descargar imagen CON x-api-key header")
                        print("=" * 80)
                        
                        for j in range(12):
                            time.sleep(5)
                            print(f"\n⏳ Intento {j+1}/12")
                            print(f"GET {url_download}")
                            print(f"Header: x-api-key: {API_KEY[:20]}...")
                            
                            # ✅ FIX: usar x-api-key header
                            resp_download = session.get(
                                url_download,
                                headers={'x-api-key': API_KEY},
                                timeout=60
                            )
                            
                            print(f"Status: {resp_download.status_code}")
                            content_type = resp_download.headers.get('Content-Type', 'N/A')
                            content_length = resp_download.headers.get('Content-Length', 'N/A')
                            print(f"Content-Type: {content_type}")
                            print(f"Content-Length: {content_length}")
                            
                            if resp_download.status_code == 200:
                                if 'image' in content_type or len(resp_download.content) > 1000:
                                    is_png = resp_download.content[:4] == b'\x89PNG'
                                    print(f"\n🎉 ¡IMAGEN DESCARGADA EXITOSAMENTE!")
                                    print(f"   Tamaño: {len(resp_download.content)} bytes")
                                    print(f"   PNG válido: {is_png}")
                                    
                                    # Guardar
                                    with open('test_imagen_field_10772494.png', 'wb') as f:
                                        f.write(resp_download.content)
                                    print(f"   ✅ Guardada: test_imagen_field_10772494.png")
                                    print(f"\n✅✅✅ FIX FUNCIONÓ - x-api-key header es correcto")
                                    break
                                else:
                                    # Revisar JSON
                                    try:
                                        data = resp_download.json()
                                        img_status = data.get('status', 'unknown')
                                        print(f"JSON status: {img_status}")
                                        if img_status in ['failed', 'error']:
                                            print(f"❌ Error: {data}")
                                            break
                                    except:
                                        print(f"Response: {resp_download.text[:200]}")
                            elif resp_download.status_code == 404:
                                print("⏳ Imagen aún procesándose...")
                            elif resp_download.status_code == 403:
                                print("❌ Error 403 - x-api-key header NO funciona o sin permisos")
                                print(f"Response: {resp_download.text[:300]}")
                                break
                            else:
                                print(f"Response: {resp_download.text[:300]}")
                    else:
                        print(f"❌ Error creando request: {resp_img.text}")
                else:
                    print("❌ No hay datos disponibles")
                break
            elif status in ['FAILED', 'ERROR']:
                print(f"\n❌ Task falló: {task_data}")
                break
        else:
            print(f"Error {task_resp.status_code}")
else:
    print(f"❌ Error: {resp.text}")

print("\n" + "=" * 80)
