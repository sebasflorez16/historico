import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('EOSDA_API_KEY')
base_url = 'https://api-connect.eos.com'

session = requests.Session()
session.headers.update({
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
})

print("=" * 70)
print("TEST DE ENDPOINTS CORRECTOS")
print("=" * 70)

# Test 1: field-management (el que usa la app)
print('\n1. field-management endpoint...')
url = f'{base_url}/field-management'
response = session.get(url, timeout=10)
print(f'GET {url}')
print(f'Status: {response.status_code}')
print(f'Response: {response.text[:300]}')

# Test 2: satellite-imagery/statistics (el que DEBERÍA funcionar)
print('\n2. satellite-imagery statistics endpoint...')
field_id = '10846423'  
url = f'{base_url}/satellite-imagery/fields/{field_id}/statistics'
payload = {
    'start_date': '2025-12-01',
    'end_date': '2025-12-31',
    'indices': ['ndvi'],
    'cloud_cover_max': 50
}
response = session.post(url, json=payload, timeout=30)
print(f'POST {url}')
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f'✅ Statistics API FUNCIONA - {len(data.get("results", []))} resultados')
    if data.get('results'):
        print(f'Primera escena: {data["results"][0].get("date")} - NDVI: {data["results"][0].get("statistics", {}).get("ndvi", {}).get("mean")}')
else:
    print(f'❌ Error: {response.text[:300]}')

# Test 3: field-imagery (el que DA 403)
print('\n3. field-imagery endpoint...')
url = f'{base_url}/field-imagery/indicies/{field_id}'
payload_img = {
    'params': {
        'view_id': 'S2L2A/18/N/YK/2025/12/15/0',
        'index': 'NDVI',
        'format': 'png'
    }
}
response = session.post(url, json=payload_img, timeout=30)
print(f'POST {url}')
print(f'Status: {response.status_code}')
if response.status_code == 403:
    print('❌ CONFIRMADO: Sin acceso a Field Imagery API (imágenes PNG)')
    print('   Solo tienes acceso a datos numéricos (Statistics)')
elif response.status_code in [200, 201, 202]:
    print(f'✅ Field Imagery funciona - Request ID: {response.json().get("request_id")}')
else:
    print(f'Response: {response.text[:300]}')

print("\n" + "=" * 70)
print("CONCLUSIÓN")
print("=" * 70)
print("Si Statistics funciona pero Field Imagery da 403:")
print("  ✅ API key VÁLIDA")
print("  ✅ Datos numéricos disponibles (NDVI, NDMI, SAVI)")
print("  ❌ Imágenes PNG NO disponibles (requiere plan PRO)")
print("=" * 70)
