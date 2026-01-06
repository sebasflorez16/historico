"""
Script para auditar la seguridad de las vistas
Identifica vistas sin protección @login_required
"""

import os
import re
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.urls import get_resolver
from django.contrib.auth.decorators import login_required

print("=" * 80)
print("🔒 AUDITORÍA DE SEGURIDAD DE VISTAS")
print("=" * 80)

# Leer el archivo views.py
views_path = "informes/views.py"
with open(views_path, 'r') as f:
    content = f.read()

# Encontrar todas las definiciones de función
pattern = r'(@\w+(?:\([^)]*\))?\s+)?def\s+(\w+)\(request'
matches = re.findall(pattern, content)

vistas_publicas = []
vistas_protegidas = []
vistas_especiales = []

for decorator, func_name in matches:
    # Buscar si tiene @login_required antes
    func_pos = content.find(f"def {func_name}(request")
    preceding_text = content[max(0, func_pos-200):func_pos]
    
    if '@login_required' in preceding_text:
        vistas_protegidas.append(func_name)
    elif func_name in ['user_login', 'user_logout', 'registro_invitacion', 'get_client_ip']:
        # Vistas que deben ser públicas por diseño
        vistas_especiales.append(func_name)
    else:
        vistas_publicas.append(func_name)

print(f"\n✅ VISTAS PROTEGIDAS ({len(vistas_protegidas)}):")
for vista in sorted(vistas_protegidas):
    print(f"   - {vista}")

print(f"\n⚠️  VISTAS PÚBLICAS - REQUIEREN REVISIÓN ({len(vistas_publicas)}):")
for vista in sorted(vistas_publicas):
    print(f"   - {vista}")

print(f"\n🔓 VISTAS PÚBLICAS POR DISEÑO ({len(vistas_especiales)}):")
for vista in sorted(vistas_especiales):
    print(f"   - {vista}")

print("\n" + "=" * 80)
print("💡 RECOMENDACIONES:")
print("=" * 80)
if vistas_publicas:
    print("⚠️  Las siguientes vistas deberían tener @login_required:")
    for vista in sorted(vistas_publicas):
        if vista not in ['registro_cliente']:  # Ya deshabilitada
            print(f"   ➡️  {vista}")
else:
    print("✅ Todas las vistas críticas están protegidas")

print()
