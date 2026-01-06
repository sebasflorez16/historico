#!/usr/bin/env python3
"""
Test actualizado de EOSDA con api-connect.eos.com y query parameter
Basado en el commit del 2 de enero de 2026
"""

import os
import requests
import json

# Configuración
API_KEY = os.getenv('EOSDA_API_KEY', 'apk.3160391d89d7711663e46354c1f9b07e96b34bfb8964111ac18dc4ef58ed1d00')
BASE_URL = 'https://api-connect.eos.com'  # URL CORRECTA según commit de ayer

print("=" * 80)
print("TEST EOSDA - CONFIGURACIÓN ACTUALIZADA (api-connect.eos.com)")
print("=" * 80)

print(f"\n📋 CONFIGURACIÓN:")
print(f"  Base URL: {BASE_URL}")
print(f"  API Key: {API_KEY[:20]}...{API_KEY[-15:]}")
print(f"  Longitud: {len(API_KEY)} caracteres")

# Método de autenticación: Query Parameter (?api_key=xxx)
# NO usar headers de autenticación
print(f"\n🔐 MÉTODO DE AUTENTICACIÓN: Query Parameter")

# Test 1: Obtener lista de campos
print(f"\n{'='*80}")
print("TEST 1: Obtener lista de campos")
print("="*80)

endpoint = "field-management/fields"
url = f"{BASE_URL}/{endpoint}?api_key={API_KEY}"

print(f"\n🔗 URL completa:")
print(f"  {url[:50]}...{url[-30:]}")

headers = {
    'Content-Type': 'application/json'
}

print(f"\n📤 Headers enviados:")
for key, value in headers.items():
    print(f"  {key}: {value}")

print(f"\n⏳ Enviando petición...")

try:
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"\n📥 RESPUESTA:")
    print(f"  Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"  ✅ ÉXITO - Conexión exitosa!")
        
        try:
            data = response.json()
            print(f"\n  📊 Datos recibidos:")
            print(f"    Total de campos: {len(data)}")
            
            if data:
                print(f"\n  📝 Primer campo:")
                primer_campo = data[0]
                print(f"    - ID: {primer_campo.get('id', 'N/A')}")
                print(f"    - Nombre: {primer_campo.get('name', 'N/A')}")
                print(f"    - Área: {primer_campo.get('area', 'N/A')} ha")
                
                if len(data) > 1:
                    print(f"\n  📝 Otros campos:")
                    for campo in data[1:6]:  # Mostrar hasta 5 campos más
                        print(f"    - {campo.get('name', 'Sin nombre')} ({campo.get('id', 'N/A')})")
        except json.JSONDecodeError:
            print(f"  ⚠️  Respuesta no es JSON válido")
            print(f"  Contenido: {response.text[:200]}")
    
    elif response.status_code == 403:
        print(f"  ❌ ERROR 403 - Acceso denegado")
        print(f"  Mensaje: {response.text}")
        
        if "Missing Authentication Token" in response.text:
            print(f"\n  💡 Posibles causas:")
            print(f"    1. API Key inválida o expirada")
            print(f"    2. Cuenta sin acceso a Field Management API")
            print(f"    3. Restricciones de IP/dominio")
            print(f"    4. API Key necesita ser regenerada")
    
    elif response.status_code == 401:
        print(f"  ❌ ERROR 401 - No autorizado")
        print(f"  Mensaje: {response.text}")
    
    else:
        print(f"  ❌ ERROR {response.status_code}")
        print(f"  Mensaje: {response.text[:300]}")
    
    # Mostrar headers de respuesta
    print(f"\n  📋 Headers de respuesta:")
    for key, value in response.headers.items():
        if 'amz' in key.lower() or 'error' in key.lower() or 'auth' in key.lower():
            print(f"    {key}: {value}")

except requests.exceptions.Timeout:
    print(f"  ❌ ERROR: Timeout (la API no respondió en 30 segundos)")
except requests.exceptions.ConnectionError as e:
    print(f"  ❌ ERROR de conexión: {str(e)}")
except Exception as e:
    print(f"  ❌ ERROR inesperado: {str(e)}")

# Test 2: Obtener tipos de cultivos válidos
print(f"\n{'='*80}")
print("TEST 2: Obtener tipos de cultivos")
print("="*80)

endpoint = "field-management/fields/crop-types"
url = f"{BASE_URL}/{endpoint}?api_key={API_KEY}"

print(f"\n🔗 URL: {url[:50]}...{url[-30:]}")
print(f"⏳ Enviando petición...")

try:
    response = requests.get(url, headers=headers, timeout=30)
    
    print(f"\n📥 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ ÉXITO")
        try:
            cultivos = response.json()
            print(f"\n📊 Tipos de cultivo disponibles ({len(cultivos)}):")
            for i, cultivo in enumerate(cultivos[:20], 1):  # Mostrar primeros 20
                print(f"  {i}. {cultivo}")
            if len(cultivos) > 20:
                print(f"  ... y {len(cultivos) - 20} más")
        except:
            print(f"Respuesta: {response.text[:200]}")
    else:
        print(f"❌ ERROR {response.status_code}")
        print(f"Mensaje: {response.text[:200]}")

except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print(f"\n{'='*80}")
print("📊 RESUMEN")
print("="*80)

print(f"""
✅ Configuración correcta según commit de ayer:
  - Base URL: https://api-connect.eos.com
  - Autenticación: Query parameter (?api_key=xxx)
  - Sin headers de autenticación

❓ Si sigue fallando:
  1. Verificar API key en: https://eos.com/dashboard
  2. Regenerar API key si es necesario
  3. Verificar permisos de cuenta para Field Management API
  4. Verificar que no haya restricciones de dominio/IP
  5. Contactar soporte: support@eos.com
""")

print("="*80)
