#!/usr/bin/env python
"""
Script de diagnóstico para probar API Key de EOSDA
Verifica permisos y acceso a diferentes endpoints
"""

import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

API_KEY = os.getenv('EOSDA_API_KEY')
BASE_URL = 'https://api-connect.eos.com'

print("=" * 70)
print("🔍 DIAGNÓSTICO DE API KEY EOSDA")
print("=" * 70)
print(f"\n📋 API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
print(f"🌐 Base URL: {BASE_URL}\n")

# Crear sesión con headers
session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
})

# Test 1: Verificar que la API key es válida (listar fields)
print("=" * 70)
print("TEST 1: Verificar API Key con Fields List")
print("=" * 70)

try:
    url = f"{BASE_URL}/fields"
    response = session.get(url, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}\n")
    
    if response.status_code == 200:
        print("✅ API Key VÁLIDA - Fields List funciona")
        data = response.json()
        print(f"Total fields: {len(data.get('results', []))}")
        if data.get('results'):
            print(f"Primer field: {data['results'][0].get('name')} (ID: {data['results'][0].get('id')})")
    elif response.status_code == 401:
        print("❌ API Key INVÁLIDA o EXPIRADA")
        print(f"Response: {response.text[:500]}")
    else:
        print(f"⚠️ Error inesperado: {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"❌ Error en petición: {str(e)}")

# Test 2: Probar Statistics API (gratuito)
print("\n" + "=" * 70)
print("TEST 2: Statistics API (incluido en plan gratuito)")
print("=" * 70)

try:
    # Usar field_id conocido: 10846423
    field_id = "10846423"
    url = f"{BASE_URL}/fields/{field_id}/statistics"
    
    payload = {
        "start_date": "2025-12-01",
        "end_date": "2025-12-31",
        "indices": ["ndvi"],
        "cloud_cover_max": 50
    }
    
    response = session.post(url, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Statistics API FUNCIONA")
        data = response.json()
        print(f"Total escenas: {len(data.get('results', []))}")
    elif response.status_code == 403:
        print("❌ ACCESO DENEGADO - Sin permisos para Statistics API")
        print(f"Response: {response.text[:500]}")
    else:
        print(f"⚠️ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"❌ Error en petición: {str(e)}")

# Test 3: Probar Field Imagery API (requiere plan de pago)
print("\n" + "=" * 70)
print("TEST 3: Field Imagery API (requiere plan PRO)")
print("=" * 70)

try:
    field_id = "10846423"
    url = f"{BASE_URL}/field-imagery/indicies/{field_id}"
    
    payload = {
        'params': {
            'view_id': 'S2L2A/18/N/YK/2025/12/15/0',
            'index': 'NDVI',
            'format': 'png'
        }
    }
    
    response = session.post(url, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code in [200, 201, 202]:
        print("✅ Field Imagery API FUNCIONA")
        data = response.json()
        print(f"Request ID: {data.get('request_id')}")
    elif response.status_code == 403:
        print("❌ ACCESO DENEGADO - Sin permisos para Field Imagery API")
        print("\n💡 DIAGNÓSTICO:")
        print("   Tu plan de EOSDA NO incluye Field Imagery API")
        print("   Solo tienes acceso a Statistics API (datos numéricos)")
        print("\n📌 SOLUCIONES:")
        print("   1. Upgrade a plan PRO en eos.com/pricing")
        print("   2. Usar solo datos de Statistics (gráficos sin imágenes)")
        print("   3. Contactar a soporte de EOSDA para verificar tu plan")
        print(f"\nResponse: {response.text[:300]}")
    else:
        print(f"⚠️ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"❌ Error en petición: {str(e)}")

# Test 4: Verificar límites de la cuenta
print("\n" + "=" * 70)
print("TEST 4: Información de la cuenta")
print("=" * 70)

try:
    url = f"{BASE_URL}/account"
    response = session.get(url, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Información de cuenta obtenida")
        data = response.json()
        print(f"Account info: {data}")
    else:
        print(f"⚠️ No se pudo obtener info de cuenta: {response.status_code}")
except Exception as e:
    print(f"⚠️ Endpoint no disponible: {str(e)}")

print("\n" + "=" * 70)
print("RESUMEN DEL DIAGNÓSTICO")
print("=" * 70)
print("\n✓ Si Statistics API funciona: Puedes obtener datos numéricos (NDVI, NDMI, etc.)")
print("✓ Si Field Imagery da 403: No tienes acceso a descargar imágenes satelitales")
print("\n💡 AgroTech puede funcionar SOLO con Statistics API:")
print("   - Timeline visual con colores según índices")
print("   - Gráficos de tendencias con matplotlib")
print("   - Análisis IA basado en datos numéricos")
print("   - PDFs profesionales sin imágenes reales (con visualizaciones)")
print("=" * 70)
