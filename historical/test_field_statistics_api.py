#!/usr/bin/env python
"""
Prueba el endpoint de Statistics API alternativo usando Field Management
"""

import os
import sys
import django
import requests
from datetime import date, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.conf import settings
from informes.models import Parcela

def test_field_statistics():
    """Prueba diferentes endpoints de estadísticas"""
    
    api_key = settings.EOSDA_API_KEY
    base_url = settings.EOSDA_BASE_URL
    
    # Usar la parcela 11 recién creada
    parcela = Parcela.objects.get(id=11)
    field_id = parcela.eosda_field_id
    
    print("\n" + "="*80)
    print("  🧪 PRUEBA DE ENDPOINTS DE ESTADÍSTICAS")
    print("="*80)
    print(f"\nField ID: {field_id}")
    print(f"Base URL: {base_url}")
    
    # Definir período
    end_date = date.today()
    start_date = end_date - timedelta(days=180)  # 6 meses
    
    print(f"Período: {start_date} a {end_date}")
    
    # ==========================================
    # OPCIÓN 1: Field Management Statistics
    # ==========================================
    print("\n" + "="*80)
    print("  📊 OPCIÓN 1: /field-management/{field_id}/statistics")
    print("="*80)
    
    url1 = f"{base_url}/field-management/{field_id}/statistics?api_key={api_key}"
    url1 += f"&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
    url1 += "&index=ndvi"
    
    print(f"\nURL: {url1[:100]}...")
    
    try:
        response1 = requests.get(url1, headers={'Accept': 'application/json'}, timeout=30)
        print(f"Status: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"✅ ÉXITO!")
            print(f"Respuesta: {str(data1)[:500]}")
        else:
            print(f"❌ Error: {response1.text[:200]}")
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
    
    # ==========================================
    # OPCIÓN 2: Statistics API directa CON GEOMETRÍA
    # ==========================================
    print("\n" + "="*80)
    print("  📊 OPCIÓN 2: /api/gdw/api (Statistics API con geometría)")
    print("="*80)
    
    # Obtener geometría de la parcela
    import json
    
    try:
        if hasattr(parcela, 'geometria') and parcela.geometria:
            geojson_dict = json.loads(parcela.geometria.geojson)
        else:
            geojson_dict = parcela.coordenadas_dict
    except:
        geojson_dict = parcela.coordenadas_dict
    
    url2 = f"{base_url}/api/gdw/api?api_key={api_key}"
    
    # ⭐ IMPORTANTE: Usar geometría, NO field_id
    payload = {
        'type': 'mt_stats',
        'params': {
            'geometry': geojson_dict,  # ← CAMBIO: usar geometría en vez de field_id
            'bm_type': ['NDVI'],  # ← Probar con mayúsculas
            'date_start': start_date.isoformat(),
            'date_end': end_date.isoformat(),
            'sensors': ['S2L2A'],
            'reference': f'test_{parcela.id}_{date.today().isoformat()}',  # ← REQUERIDO
            'max_cloud_cover_in_aoi': 100,
            'limit': 50,
            'exclude_cover_pixels': True,
            'cloud_masking_level': 3
        }
    }
    
    print(f"\nURL: {url2}")
    print(f"Payload (geometría con {len(geojson_dict.get('coordinates', [[]])[0])} puntos)")
    
    try:
        response2 = requests.post(url2, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
        print(f"Status: {response2.status_code}")
        
        if response2.status_code in [200, 201, 202]:
            data2 = response2.json()
            print(f"✅ ÉXITO!")
            print(f"Respuesta: {data2}")
            
            if 'task_id' in data2:
                print(f"\n📋 Task ID: {data2['task_id']}")
                print("Esperando resultados (10 segundos)...")
                
                # Esperar y obtener resultados
                import time
                time.sleep(10)  # Esperar más tiempo para que procese
                
                task_url = f"{base_url}/api/gdw/api/{data2['task_id']}?api_key={api_key}"
                task_response = requests.get(task_url, timeout=30)
                
                print(f"\nURL tarea: {task_url[:80]}...")
                print(f"Status tarea: {task_response.status_code}")
                
                if task_response.status_code == 200:
                    task_data = task_response.json()
                    print(f"Estado: {task_data.get('status')}")
                    
                    # Verificar si hay error
                    if 'error_message' in task_data:
                        print(f"❌ Error en tarea: {task_data['error_message']}")
                    elif 'result' in task_data and task_data['result']:
                        print(f"✅ ¡HAY RESULTADOS!")
                        print(f"Número de escenas: {len(task_data['result'])}")
                        
                        # Mostrar primeras escenas
                        for i, escena in enumerate(task_data['result'][:5], 1):
                            fecha = escena.get('date', escena.get('dt', 'N/A'))
                            cloud = escena.get('cloud', escena.get('cloud_cover', 0))
                            ndvi = escena.get('ndvi', {}).get('mean', 'N/A')
                            print(f"  Escena {i}: {fecha}, Nubosidad: {cloud}%, NDVI: {ndvi}")
                    else:
                        print(f"⏳ Tarea aún procesando o sin resultados")
                        print(f"Respuesta completa: {task_data}")
                else:
                    print(f"Resultado: {task_response.text[:500]}")
        else:
            print(f"❌ Error: {response2.text[:200]}")
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
    
    # ==========================================
    # OPCIÓN 3: Field Imagery API
    # ==========================================
    print("\n" + "="*80)
    print("  📊 OPCIÓN 3: /field-imagery (Imagery API)")
    print("="*80)
    
    url3 = f"{base_url}/field-imagery?api_key={api_key}"
    url3 += f"&field_id={field_id}&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
    
    print(f"\nURL: {url3[:100]}...")
    
    try:
        response3 = requests.get(url3, headers={'Accept': 'application/json'}, timeout=30)
        print(f"Status: {response3.status_code}")
        
        if response3.status_code == 200:
            data3 = response3.json()
            print(f"✅ ÉXITO!")
            print(f"Respuesta: {str(data3)[:500]}")
        else:
            print(f"❌ Error: {response3.text[:200]}")
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
    
    # ==========================================
    # OPCIÓN 4: Scenes endpoint
    # ==========================================
    print("\n" + "="*80)
    print("  📊 OPCIÓN 4: /field-management/{field_id}/scenes")
    print("="*80)
    
    url4 = f"{base_url}/field-management/{field_id}/scenes?api_key={api_key}"
    url4 += f"&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
    
    print(f"\nURL: {url4[:100]}...")
    
    try:
        response4 = requests.get(url4, headers={'Accept': 'application/json'}, timeout=30)
        print(f"Status: {response4.status_code}")
        
        if response4.status_code == 200:
            data4 = response4.json()
            print(f"✅ ÉXITO!")
            print(f"Respuesta: {str(data4)[:500]}")
        else:
            print(f"❌ Error: {response4.text[:200]}")
    except Exception as e:
        print(f"❌ Excepción: {str(e)}")
    
    print("\n" + "="*80)
    print("  📋 RESUMEN")
    print("="*80)
    print("\nSe probaron 4 endpoints diferentes para obtener datos satelitales.")
    print("Revisa cuál respondió con Status 200 para usarlo en el código.\n")

if __name__ == '__main__':
    test_field_statistics()
