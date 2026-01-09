#!/usr/bin/env python
"""
Script para verificar el estado del API key de EOSDA y los permisos del field.
"""

import os
import sys
import django
import requests
from dotenv import load_dotenv

# Configurar Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

# Importar settings de Django
from django.conf import settings

# Cargar variables de entorno
load_dotenv()

def verificar_api_key():
    """Verifica que el API key esté configurado correctamente."""
    api_key = os.getenv('EOSDA_API_KEY')
    
    print("="*80)
    print("  🔑 VERIFICACIÓN DE API KEY EOSDA")
    print("="*80)
    
    if not api_key:
        print("❌ API key NO configurado en .env")
        return None
    
    print(f"✅ API key encontrado: {api_key[:10]}...{api_key[-10:]}")
    print(f"   Longitud: {len(api_key)} caracteres")
    
    return api_key

def verificar_field_management_api(api_key, field_id):
    """Verifica el acceso a la Field Management API."""
    print("\n" + "="*80)
    print(f"  🌾 VERIFICANDO FIELD #{field_id} (Field Management API)")
    print("="*80)
    
    base_url = settings.EOSDA_BASE_URL
    url = f"{base_url}/field-management/fields/{field_id}"
    
    try:
        response = requests.get(
            url,
            params={'api_key': api_key},
            headers={'Accept': 'application/json'}
        )
        
        print(f"\n📡 Base URL: {base_url}")
        print(f"📡 URL completa: {url}")
        print(f"🔧 Parámetros: api_key={api_key[:10]}...")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Field accesible:")
            print(f"   Nombre: {data.get('name', 'N/A')}")
            print(f"   Área: {data.get('area', 'N/A')} ha")
            print(f"   Cultivo: {data.get('crop', 'N/A')}")
            print(f"   Activo: {data.get('is_active', 'N/A')}")
            return True
        elif response.status_code == 403:
            print(f"\n❌ 403 FORBIDDEN - No tienes permisos para acceder a este field")
            print(f"   Mensaje: {response.text[:200]}")
            return False
        elif response.status_code == 404:
            print(f"\n❌ 404 NOT FOUND - El field no existe o no es accesible")
            return False
        else:
            print(f"\n⚠️ Respuesta inesperada: {response.status_code}")
            print(f"   {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")
        return False

def listar_fields_disponibles(api_key):
    """Lista todos los fields disponibles para este API key."""
    print("\n" + "="*80)
    print("  📋 LISTADO DE FIELDS DISPONIBLES")
    print("="*80)
    
    base_url = settings.EOSDA_BASE_URL
    url = f"{base_url}/field-management/fields"
    
    try:
        response = requests.get(
            url,
            params={'api_key': api_key},
            headers={'Accept': 'application/json'}
        )
        
        print(f"\n📡 Base URL: {base_url}")
        print(f"📡 URL completa: {url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # La respuesta puede ser una lista directa o un objeto con 'results'
            if isinstance(data, list):
                fields = data
            elif isinstance(data, dict):
                fields = data.get('results', data.get('data', []))
            else:
                fields = []
            
            print(f"\n✅ Total de fields disponibles: {len(fields)}")
            
            if fields:
                print("\n📋 Todos los fields disponibles:")
                for field in fields:
                    field_id = field.get('id')
                    name = field.get('name', 'Sin nombre')
                    area = field.get('area', 0)
                    crop = field.get('crop', 'N/A')
                    is_active = field.get('is_active', 'N/A')
                    print(f"   • ID: {field_id}, Nombre: {name}, Área: {area} ha, Cultivo: {crop}, Activo: {is_active}")
            else:
                print("\n⚠️ No hay fields disponibles para este API key")
            
            return fields
        elif response.status_code == 403:
            print(f"\n❌ 403 FORBIDDEN - No tienes permisos para listar fields")
            print(f"   Mensaje: {response.text[:200]}")
            return []
        else:
            print(f"\n⚠️ Respuesta inesperada: {response.status_code}")
            print(f"   {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def verificar_imagery_api(api_key, field_id):
    """Verifica el acceso a la Field Imagery API."""
    print("\n" + "="*80)
    print(f"  🛰️ VERIFICANDO IMAGERY API (Field #{field_id})")
    print("="*80)
    
    base_url = settings.EOSDA_BASE_URL
    url = f"{base_url}/field-imagery/scenes"
    
    try:
        response = requests.get(
            url,
            params={
                'api_key': api_key,
                'field_id': field_id,
                'start_date': '2024-01-01',
                'end_date': '2025-01-08'  # Último año
            },
            headers={'Accept': 'application/json'}
        )
        
        print(f"\n📡 Base URL: {base_url}")
        print(f"� URL completa: {url}")
        print(f"�🔧 Parámetros: api_key={api_key[:10]}..., field_id={field_id}, start_date=2024-01-01, end_date=2025-01-08")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            scenes = data.get('results', [])
            print(f"\n✅ Imagery API accesible")
            print(f"   Total de escenas disponibles: {len(scenes)}")
            
            if scenes:
                print("\n📸 Primeras 3 escenas:")
                for scene in scenes[:3]:
                    date = scene.get('date')
                    cloud = scene.get('cloud', 0)
                    print(f"   • Fecha: {date}, Nubosidad: {cloud:.1f}%")
            return True
        elif response.status_code == 403:
            print(f"\n❌ 403 FORBIDDEN - No tienes permisos para acceder a imágenes")
            print(f"   Mensaje: {response.text[:200]}")
            return False
        else:
            print(f"\n⚠️ Respuesta inesperada: {response.status_code}")
            print(f"   {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")
        return False

def main():
    print("\n")
    print("="*80)
    print("  🔬 DIAGNÓSTICO COMPLETO DE EOSDA API")
    print("="*80)
    print("\n")
    
    # 1. Verificar API key
    api_key = verificar_api_key()
    if not api_key:
        print("\n❌ No se puede continuar sin API key")
        return
    
    # 2. Listar fields disponibles
    fields = listar_fields_disponibles(api_key)
    
    # 3. Verificar field específico (el de la parcela 6)
    field_id = 10842160
    field_ok = verificar_field_management_api(api_key, field_id)
    
    # 4. Verificar Imagery API
    if field_ok:
        verificar_imagery_api(api_key, field_id)
    
    # 5. Resumen final
    print("\n" + "="*80)
    print("  📊 RESUMEN DEL DIAGNÓSTICO")
    print("="*80)
    
    if not api_key:
        print("\n❌ API key no configurado")
    elif not fields:
        print("\n❌ No puedes listar fields - posible problema de permisos")
    elif not field_ok:
        print(f"\n⚠️ El field #{field_id} no es accesible con este API key")
        print("   Posibles causas:")
        print("   • El field no existe")
        print("   • El field no está compartido con tu cuenta")
        print("   • El API key no tiene permisos")
    else:
        print(f"\n✅ El field #{field_id} es accesible y tiene imágenes disponibles")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
