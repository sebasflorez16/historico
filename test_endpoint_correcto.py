#!/usr/bin/env python
"""
Test con el endpoint CORRECTO /api/gdw/api
"""

import requests
import os
import json
import time
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
print("TEST CON ENDPOINT CORRECTO: /api/gdw/api")
print("=" * 80)

field_id = "10851431"  # El field que acabas de crear

# Test 1: Statistics con el endpoint correcto
print("\n1️⃣ Obtener Statistics con /api/gdw/api")
print("-" * 80)

url = f"{BASE_URL}/api/gdw/api"
payload = {
    'type': 'mt_stats',
    'params': {
        'bm_type': ['ndvi'],
        'date_start': '2025-12-01',
        'date_end': '2025-12-31',
        'field_id': field_id,
        'sensors': ['S2L2A'],
        'reference': f'test_{field_id}',
        'limit': 50,
        'max_cloud_cover_in_aoi': 80,
        'exclude_cover_pixels': True,
        'cloud_masking_level': 3
    }
}

print(f"POST {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = session.post(url, json=payload, timeout=60)
print(f"Status: {response.status_code}")

if response.status_code in [200, 201, 202]:
    data = response.json()
    print(f"✅ Request exitoso")
    print(f"Response keys: {list(data.keys())}")
    print(f"Full response: {json.dumps(data, indent=2)}")
    
    task_id = data.get('task_id')
    if task_id:
        print(f"\n📋 Task ID: {task_id}")
        print("\n2️⃣ Esperando resultados del task...")
        print("-" * 80)
        
        # Polling para obtener resultados
        url_task = f"{BASE_URL}/api/gdw/api/{task_id}"
        max_intentos = 20
        
        for intento in range(max_intentos):
            time.sleep(5)
            print(f"Intento {intento + 1}/{max_intentos}...")
            
            response_task = session.get(url_task, timeout=30)
            print(f"Status: {response_task.status_code}")
            
            if response_task.status_code == 200:
                task_data = response_task.json()
                status = task_data.get('status')
                print(f"Task status: {status}")
                
                if status == 'DONE':
                    print("\n✅ TASK COMPLETADO")
                    print(f"Response keys: {list(task_data.keys())}")
                    
                    # Ver si hay URLs de imágenes
                    if 'data' in task_data:
                        print("\n📊 Datos disponibles:")
                        data_items = task_data['data']
                        if isinstance(data_items, list) and len(data_items) > 0:
                            primer_item = data_items[0]
                            print(f"Primer item keys: {list(primer_item.keys())}")
                            print(f"Primer item: {json.dumps(primer_item, indent=2)[:1000]}")
                            
                            # Buscar URLs de imágenes
                            for key in primer_item.keys():
                                if 'url' in key.lower() or 'image' in key.lower() or 'img' in key.lower():
                                    print(f"\n🖼️ Posible URL de imagen encontrada en '{key}': {primer_item[key]}")
                    
                    print(f"\nFull task data: {json.dumps(task_data, indent=2)[:2000]}")
                    break
                elif status in ['FAILED', 'ERROR']:
                    print(f"❌ Task falló: {task_data.get('error', 'Unknown error')}")
                    break
            else:
                print(f"Error: {response_task.text[:300]}")
        else:
            print("⏱️ Timeout esperando task")
else:
    print(f"❌ Error: {response.text[:500]}")

print("\n" + "=" * 80)
print("CONCLUSIÓN")
print("=" * 80)
print("Si el endpoint funciona, veremos los datos y posibles URLs de imágenes")
