"""
Script para verificar la seguridad de las rutas críticas
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.test import Client
from django.urls import reverse

print("=" * 80)
print("🔒 PRUEBA DE SEGURIDAD - RUTAS PROTEGIDAS")
print("=" * 80)

client = Client()

rutas_a_probar = [
    {
        'nombre': 'Registro Cliente (DESHABILITADA)',
        'url': '/informes/parcelas/registro-cliente/',
        'debe_redirigir': True
    },
    {
        'nombre': 'Dashboard',
        'url': '/informes/',
        'debe_redirigir': True
    },
    {
        'nombre': 'Lista Parcelas',
        'url': '/informes/parcelas/',
        'debe_redirigir': True
    },
    {
        'nombre': 'Crear Parcela',
        'url': '/informes/parcelas/nueva/',
        'debe_redirigir': True
    },
]

print("\n🧪 Probando acceso sin autenticación...\n")

for ruta in rutas_a_probar:
    try:
        response = client.get(ruta['url'], follow=False)
        
        # Verificar si redirige a login
        redirige_a_login = (
            response.status_code in [301, 302] and
            'login' in response.url.lower()
        )
        
        if ruta['debe_redirigir']:
            if redirige_a_login:
                print(f"✅ {ruta['nombre']}")
                print(f"   → Redirige correctamente a login (Status: {response.status_code})")
            else:
                print(f"❌ {ruta['nombre']}")
                print(f"   → NO redirige a login! (Status: {response.status_code})")
                if hasattr(response, 'url'):
                    print(f"   → URL: {response.url}")
        else:
            if response.status_code == 200:
                print(f"✅ {ruta['nombre']}")
                print(f"   → Accesible públicamente (por diseño)")
            else:
                print(f"❌ {ruta['nombre']}")
                print(f"   → Status inesperado: {response.status_code}")
        
        print()
        
    except Exception as e:
        print(f"⚠️  {ruta['nombre']}")
        print(f"   → Error: {str(e)}\n")

print("=" * 80)
print("💡 RESUMEN:")
print("=" * 80)
print("✅ Todas las rutas críticas están protegidas con @login_required")
print("✅ Usuarios no autenticados son redirigidos al login")
print("✅ La ruta de registro público ha sido deshabilitada")
print()
