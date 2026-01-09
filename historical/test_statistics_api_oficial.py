#!/usr/bin/env python
"""
Script FINAL para probar la Statistics API de EOSDA con la configuración correcta
según la documentación oficial: https://doc.eos.com/docs/statistics/
"""

import os
import sys
import django
import requests
import json
import time
from datetime import date, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.conf import settings
from informes.models import Parcela

def obtener_imagenes_disponibles(parcela, fecha_inicio, fecha_fin):
    """
    Obtiene todas las imágenes disponibles usando Statistics API según documentación oficial.
    """
    
    print("\n" + "="*80)
    print(f"  🛰️ OBTENIENDO IMÁGENES DISPONIBLES - {parcela.nombre}")
    print("="*80)
    
    api_key = settings.EOSDA_API_KEY
    base_url = settings.EOSDA_BASE_URL
    
    # Obtener geometría
    try:
        if hasattr(parcela, 'geometria') and parcela.geometria:
            geojson_dict = json.loads(parcela.geometria.geojson)
        else:
            geojson_dict = parcela.coordenadas_dict
    except:
        geojson_dict = parcela.coordenadas_dict
    
    # ⭐ PAYLOAD SEGÚN DOCUMENTACIÓN OFICIAL ⭐
    # https://doc.eos.com/docs/statistics/vegetation-indices-analytics/
    payload = {
        'type': 'mt_stats',
        'params': {
            'bm_type': ['NDVI', 'NDMI', 'SAVI'],  # ✅ MAYÚSCULAS según ejemplo oficial
            'date_start': fecha_inicio.isoformat(),
            'date_end': fecha_fin.isoformat(),
            'geometry': geojson_dict,
            'reference': f'agrotech_{parcela.id}_{int(time.time())}',
            'sensors': ['S2L2A'],  # Sentinel-2 Level 2A
            'limit': 100,
            'max_cloud_cover_in_aoi': 100,  # Sin filtro para ver TODAS las imágenes
            'exclude_cover_pixels': True,
            'cloud_masking_level': 3
        }
    }
    
    print(f"\n📋 Configuración:")
    print(f"   Parcela: {parcela.nombre} (ID: {parcela.id})")
    print(f"   Período: {fecha_inicio} a {fecha_fin}")
    print(f"   Índices: NDVI, NDMI, SAVI")
    print(f"   Sensor: Sentinel-2 L2A")
    print(f"   Umbral nubosidad: 100% (sin filtro)")
    
    # PASO 1: Crear tarea
    print(f"\n🔄 PASO 1: Creando tarea...")
    create_url = f"{base_url}/api/gdw/api?api_key={api_key}"
    
    try:
        response = requests.post(create_url, json=payload, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code not in [200, 201, 202]:
            print(f"   ❌ Error: {response.text}")
            return None
        
        task_data = response.json()
        task_id = task_data.get('task_id')
        
        print(f"   ✅ Tarea creada: {task_id}")
        print(f"   Status: {task_data.get('status')}")
        print(f"   Timeout: {task_data.get('task_timeout')} segundos")
        
    except Exception as e:
        print(f"   ❌ Error creando tarea: {str(e)}")
        return None
    
    # PASO 2: Consultar resultado (con reintentos)
    print(f"\n⏳ PASO 2: Consultando resultado...")
    status_url = f"{base_url}/api/gdw/api/{task_id}?api_key={api_key}"
    
    max_intentos = 20  # Aumentar a 20 intentos
    for intento in range(1, max_intentos + 1):
        print(f"   Intento {intento}/{max_intentos}...")
        
        try:
            time.sleep(5)  # Esperar 5 segundos entre intentos
            
            response = requests.get(status_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Mostrar lo que devuelve la API
                print(f"   📊 Respuesta: {json.dumps(data, indent=2)[:500]}...")
                
                # Verificar si hay resultados
                resultados = data.get('result', [])
                errores = data.get('errors', [])
                
                if resultados:
                    print(f"\n✅ ¡Datos disponibles!")
                    print(f"   Total de escenas: {len(resultados)}")
                    
                    if errores:
                        print(f"   ⚠️ Errores en {len(errores)} escenas")
                    
                    return data
                elif errores and not resultados:
                    print(f"\n❌ Solo hay errores, no hay resultados")
                    print(f"   Errores: {len(errores)}")
                    for err in errores[:3]:
                        print(f"   - {err.get('error', 'N/A')}")
                    return None
                else:
                    print(f"   ⏳ Procesando... (aún no hay resultados)")
            else:
                print(f"   ⚠️ Status: {response.status_code}")
                print(f"   Respuesta: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n⚠️ Timeout: No se obtuvieron resultados después de {max_intentos} intentos")
    return None

def mostrar_estadisticas(datos):
    """Muestra estadísticas detalladas de las imágenes."""
    
    if not datos:
        return
    
    resultados = datos.get('result', [])
    
    print("\n" + "="*80)
    print("  📊 ESTADÍSTICAS DE IMÁGENES DISPONIBLES")
    print("="*80)
    
    # Organizar por mes
    from collections import defaultdict
    from datetime import datetime
    
    por_mes = defaultdict(list)
    
    for escena in resultados:
        fecha_str = escena.get('date', '')
        if fecha_str:
            fecha = datetime.fromisoformat(fecha_str)
            mes_clave = fecha.strftime('%Y-%m')
            por_mes[mes_clave].append(escena)
    
    # Mostrar por mes
    print(f"\n📅 DISPONIBILIDAD POR MES:")
    print("="*80)
    
    for mes in sorted(por_mes.keys(), reverse=True):
        escenas_mes = por_mes[mes]
        mes_obj = datetime.strptime(mes, '%Y-%m')
        mes_nombre = mes_obj.strftime('%B %Y')
        
        nubosidades = [e.get('cloud', 0) for e in escenas_mes]
        nub_min = min(nubosidades)
        nub_max = max(nubosidades)
        nub_prom = sum(nubosidades) / len(nubosidades)
        
        # Clasificar por calidad
        excelentes = sum(1 for n in nubosidades if n < 20)
        buenas = sum(1 for n in nubosidades if 20 <= n < 50)
        aceptables = sum(1 for n in nubosidades if 50 <= n < 80)
        malas = sum(1 for n in nubosidades if n >= 80)
        
        print(f"\n📆 {mes_nombre.upper()}")
        print(f"   {'─'*76}")
        print(f"   Total imágenes: {len(escenas_mes)}")
        print(f"   Nubosidad: {nub_min:.1f}% - {nub_max:.1f}% (promedio: {nub_prom:.1f}%)")
        print(f"   🌟 Excelentes (<20%): {excelentes}  |  ☁️ Buenas (20-50%): {buenas}")
        print(f"   ⚠️ Aceptables (50-80%): {aceptables}  |  ❌ Malas (≥80%): {malas}")
        
        # Mostrar mejor imagen
        mejor = min(escenas_mes, key=lambda x: x.get('cloud', 100))
        ndvi = mejor.get('indexes', {}).get('NDVI', {}).get('average', 'N/A')
        print(f"   🎯 Mejor imagen: {mejor.get('date')} - Nubosidad: {mejor.get('cloud'):.1f}%")
        if isinstance(ndvi, (int, float)):
            print(f"      NDVI promedio: {ndvi:.3f}")
    
    # Resumen general
    print("\n" + "="*80)
    todas_nubosidades = [e.get('cloud', 0) for e in resultados]
    total_excelentes = sum(1 for n in todas_nubosidades if n < 20)
    total_buenas = sum(1 for n in todas_nubosidades if 20 <= n < 50)
    total_aceptables = sum(1 for n in todas_nubosidades if 50 <= n < 80)
    total_malas = sum(1 for n in todas_nubosidades if n >= 80)
    
    print(f"\n🎯 RESUMEN GENERAL:")
    print(f"   Total de imágenes: {len(resultados)}")
    print(f"   Meses con datos: {len(por_mes)}")
    print(f"\n   Distribución por calidad:")
    print(f"   🌟 Excelentes (<20%): {total_excelentes} ({total_excelentes/len(resultados)*100:.1f}%)")
    print(f"   ☁️ Buenas (20-50%): {total_buenas} ({total_buenas/len(resultados)*100:.1f}%)")
    print(f"   ⚠️ Aceptables (50-80%): {total_aceptables} ({total_aceptables/len(resultados)*100:.1f}%)")
    print(f"   ❌ Malas (≥80%): {total_malas} ({total_malas/len(resultados)*100:.1f}%)")

def main():
    print("\n")
    print("="*80)
    print("  🌾 TEST FINAL - STATISTICS API SEGÚN DOCUMENTACIÓN OFICIAL")
    print("="*80)
    
    # Obtener parcela 11
    parcela = Parcela.objects.get(id=11)
    
    # Rango de 6 meses
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=180)
    
    # Obtener imágenes
    datos = obtener_imagenes_disponibles(parcela, fecha_inicio, fecha_fin)
    
    # Mostrar estadísticas
    if datos:
        mostrar_estadisticas(datos)
        print("\n✅ ÉXITO: Se obtuvieron los datos correctamente")
    else:
        print("\n❌ No se pudieron obtener datos")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
