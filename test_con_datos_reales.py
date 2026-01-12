#!/usr/bin/env python
"""
Test DIRECTO con view_id y field_id reales de la BD
"""

import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = 'https://api-connect.eos.com'

# Datos reales de la BD
view_id = "S2L2A/18/N/YL/2025/12/17/0"
field_id = "10800423"

print("=" * 80)
print("TEST DIRECTO CON DATOS REALES")
print("=" * 80)
print(f"View ID: {view_id}")
print(f"Field ID: {field_id}")
print("=" * 80)

session = requests.Session()
session.headers.update({'Content-Type': 'application/json'})

# PASO 1: Crear request de imagen
url_img = f"{BASE_URL}/field-imagery/indicies/{field_id}?api_key={API_KEY}"
payload = {
    "params": {
        "view_id": view_id,
        "index": "NDVI",
        "format": "png"
    }
}

print(f"\n🎨 PASO 1: Crear request de imagen")
print(f"POST {url_img.replace(API_KEY, '***')}")
print(f"Payload: {json.dumps(payload, indent=2)}")

resp = session.post(url_img, json=payload, timeout=60)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

if resp.status_code in [200, 201, 202]:
    request_id = resp.json().get('request_id')
    print(f"\n✅ Request ID: {request_id}")
    
    # PASO 2: GET con x-api-key header (EL FIX)
    url_download = f"{BASE_URL}/field-imagery/{field_id}/{request_id}"
    
    print(f"\n" + "=" * 80)
    print(f"🖼️ PASO 2: Descargar imagen CON x-api-key header")
    print("=" * 80)
    
    for i in range(15):
        time.sleep(5)
        print(f"\n⏳ Intento {i+1}/15")
        print(f"GET {url_download}")
        print(f"Header: x-api-key: {API_KEY[:20]}...")
        
        # ✅ FIX: agregar x-api-key header
        resp_download = session.get(
            url_download,
            headers={'x-api-key': API_KEY},
            timeout=60
        )
        
        print(f"Status: {resp_download.status_code}")
        content_type = resp_download.headers.get('Content-Type', 'N/A')
        print(f"Content-Type: {content_type}")
        
        if resp_download.status_code == 200:
            if 'image' in content_type:
                content_len = len(resp_download.content)
                is_png = resp_download.content[:4] == b'\x89PNG'
                print(f"\n🎉 ¡IMAGEN DESCARGADA!")
                print(f"   Tamaño: {content_len} bytes")
                print(f"   PNG válido: {is_png}")
                print(f"   Content-Type: {content_type}")
                
                # Guardar muestra
                with open('test_imagen_eosda.png', 'wb') as f:
                    f.write(resp_download.content)
                print(f"   ✅ Guardada en test_imagen_eosda.png")
                break
            else:
                try:
                    data = resp_download.json()
                    status = data.get('status', 'unknown')
                    print(f"JSON status: {status}")
                    if status in ['failed', 'error']:
                        print(f"❌ Error: {data}")
                        break
                except:
                    print(f"Response: {resp_download.text[:200]}")
        elif resp_download.status_code == 404:
            print("⏳ Imagen aún procesándose...")
        elif resp_download.status_code == 403:
            print("❌ Error 403 - Sin acceso")
            print(f"Response: {resp_download.text[:300]}")
            break
        else:
            print(f"Response: {resp_download.text[:300]}")
            break
else:
    print(f"\n❌ Error en PASO 1: {resp.text}")

print("\n" + "=" * 80)
