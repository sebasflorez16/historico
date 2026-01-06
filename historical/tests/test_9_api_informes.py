#!/usr/bin/env python
"""
Test rápido de la API de informes personalizados
Simula una request desde el navegador
"""

import requests
import json

# URL de la API
url = "http://127.0.0.1:8000/parcelas/1/generar-informe-personalizado/"

# Configuración de prueba (optimización de riego)
configuracion = {
    "nivel_detalle": "estandar",
    "indices": ["ndvi", "msavi", "ndmi"],
    "secciones": ["tendencias", "recomendaciones_riego", "estadisticas", "clima"],
    "formato": {
        "orientacion": "vertical",
        "estilo": "completo",
        "idioma": "es"
    },
    "comparacion": {
        "habilitada": False,
        "tipo": None
    },
    "personalizacion": {
        "enfoque_especial": "Optimización de riego y detección de estrés hídrico",
        "notas_adicionales": None
    }
}

# Datos del request
data = {
    "configuracion": configuracion,
    "meses": 6  # 6 meses para ser más rápido
}

print("\n" + "="*80)
print("🧪 TEST DE API - INFORME PERSONALIZADO")
print("="*80)

print("\n📋 Configuración:")
print(json.dumps(configuracion, indent=2, ensure_ascii=False))

print("\n📡 Enviando request a API...")
print(f"URL: {url}")

try:
    # Login primero (si es necesario)
    session = requests.Session()
    
    # Hacer login
    login_url = "http://127.0.0.1:8000/login/"
    login_response = session.get(login_url)
    
    # Extraer CSRF token
    csrf_token = None
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
    
    print(f"🔑 CSRF Token: {csrf_token[:20]}..." if csrf_token else "❌ No CSRF token")
    
    # Login con credenciales
    login_data = {
        'username': 'admin',  # Cambiar según tu usuario
        'password': 'admin',  # Cambiar según tu contraseña
        'csrfmiddlewaretoken': csrf_token
    }
    
    login_post = session.post(login_url, data=login_data)
    
    if login_post.status_code == 200 or login_post.status_code == 302:
        print("✅ Login exitoso")
    else:
        print(f"⚠️  Login status: {login_post.status_code}")
    
    # Obtener nuevo CSRF token después del login
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']
    
    # Hacer request a la API
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Referer': 'http://127.0.0.1:8000/'
    }
    
    response = session.post(url, json=data, headers=headers, timeout=180)  # 3 minutos timeout
    
    print(f"\n📊 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ RESPUESTA EXITOSA:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            print(f"\n🎉 ¡Informe generado exitosamente!")
            print(f"📄 ID: {result.get('informe_id')}")
            print(f"📁 PDF: {result.get('pdf_url')}")
            print(f"🔗 Detalle: {result.get('url_detalle')}")
            print(f"📦 Archivo: {result.get('nombre_archivo')}")
        else:
            print(f"\n❌ Error: {result.get('error')}")
    else:
        print(f"\n❌ ERROR {response.status_code}")
        try:
            error_data = response.json()
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
        except:
            print(response.text[:500])

except requests.exceptions.Timeout:
    print("\n⏱️  TIMEOUT - La generación está tardando más de 3 minutos")
    print("Esto es normal para informes completos. Revisa el log del servidor.")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")
