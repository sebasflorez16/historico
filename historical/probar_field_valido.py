#!/usr/bin/env python
"""
Script para probar un field válido y ver sus imágenes disponibles.
"""

import os
import sys
import django
import requests
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# Configurar Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.conf import settings

load_dotenv()

def obtener_imagenes_field(field_id):
    """Obtiene todas las imágenes disponibles para un field."""
    print("\n" + "="*80)
    print(f"  🛰️ OBTENIENDO IMÁGENES DEL FIELD #{field_id}")
    print("="*80)
    
    api_key = os.getenv('EOSDA_API_KEY')
    base_url = settings.EOSDA_BASE_URL
    url = f"{base_url}/field-imagery/scenes"
    
    try:
        response = requests.get(
            url,
            params={
                'api_key': api_key,
                'field_id': field_id,
                'start_date': '2024-01-01',
                'end_date': '2025-01-08'
            },
            headers={'Accept': 'application/json'}
        )
        
        print(f"\n📡 URL: {url}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Manejar diferentes formatos de respuesta
            if isinstance(data, list):
                scenes = data
            elif isinstance(data, dict):
                scenes = data.get('results', data.get('data', data.get('scenes', [])))
            else:
                scenes = []
            
            print(f"\n✅ Total de escenas: {len(scenes)}")
            
            if scenes:
                # Organizar por mes
                scenes_by_month = defaultdict(list)
                
                for scene in scenes:
                    date_str = scene.get('date', scene.get('dt', ''))
                    if date_str:
                        try:
                            if 'T' in date_str:
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            else:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            month_key = date_obj.strftime('%Y-%m')
                            scenes_by_month[month_key].append(scene)
                        except:
                            pass
                
                # Mostrar por mes
                print("\n📅 DISPONIBILIDAD POR MES:")
                print("="*80)
                
                for month_key in sorted(scenes_by_month.keys(), reverse=True):
                    month_scenes = scenes_by_month[month_key]
                    month_obj = datetime.strptime(month_key, '%Y-%m')
                    month_name = month_obj.strftime('%B %Y')
                    
                    print(f"\n   📆 {month_name.upper()}")
                    print(f"   {'─'*76}")
                    print(f"   Imágenes: {len(month_scenes)}")
                    
                    # Ordenar por nubosidad
                    month_scenes.sort(key=lambda x: x.get('cloud', x.get('cloud_cover', 100)))
                    
                    for i, scene in enumerate(month_scenes[:5], 1):  # Mostrar max 5 por mes
                        date = scene.get('date', scene.get('dt', 'N/A'))
                        cloud = scene.get('cloud', scene.get('cloud_cover', 0))
                        
                        if cloud < 20:
                            emoji = "🌟"
                            quality = "EXCELENTE"
                        elif cloud < 50:
                            emoji = "☁️"
                            quality = "BUENA"
                        elif cloud < 80:
                            emoji = "⚠️"
                            quality = "ACEPTABLE"
                        else:
                            emoji = "❌"
                            quality = "MALA"
                        
                        print(f"   {emoji} Imagen #{i}: {date[:10] if date else 'N/A'}")
                        print(f"      Nubosidad: {cloud:.1f}% ({quality})")
                        
                        if i == 1 and len(month_scenes) > 1:
                            print(f"      ⭐ MEJOR DEL MES")
                
                # Resumen
                print(f"\n" + "="*80)
                all_clouds = [s.get('cloud', s.get('cloud_cover', 0)) for s in scenes]
                if all_clouds:
                    print(f"\n   📊 RESUMEN DE NUBOSIDAD:")
                    print(f"      Mínima: {min(all_clouds):.1f}%")
                    print(f"      Máxima: {max(all_clouds):.1f}%")
                    print(f"      Promedio: {sum(all_clouds)/len(all_clouds):.1f}%")
                    
                    excelente = sum(1 for c in all_clouds if c < 20)
                    buena = sum(1 for c in all_clouds if 20 <= c < 50)
                    aceptable = sum(1 for c in all_clouds if 50 <= c < 80)
                    mala = sum(1 for c in all_clouds if c >= 80)
                    
                    print(f"\n   🎯 DISTRIBUCIÓN:")
                    print(f"      🌟 Excelente (< 20%): {excelente}")
                    print(f"      ☁️ Buena (20-50%): {buena}")
                    print(f"      ⚠️ Aceptable (50-80%): {aceptable}")
                    print(f"      ❌ Mala (≥ 80%): {mala}")
            else:
                print("\n⚠️ No hay imágenes disponibles para este field")
            
            return scenes
            
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            print(f"   Mensaje: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("\n")
    print("="*80)
    print("  🌾 PRUEBA DE FIELD VÁLIDO CON IMÁGENES")
    print("="*80)
    
    # Usar el primer field de la lista
    test_field_id = 10846417
    
    print(f"\n🔍 Probando con Field ID: {test_field_id}")
    
    scenes = obtener_imagenes_field(test_field_id)
    
    if scenes:
        print(f"\n✅ Este field tiene {len(scenes)} imágenes disponibles")
        print("   Puedes usar este field_id para la parcela 6")
    else:
        print("\n⚠️ Este field no tiene imágenes, probando con otro...")
        
        # Probar con otros fields
        other_fields = [10846421, 10846423, 10702032, 10693225]
        
        for field_id in other_fields:
            print(f"\n🔍 Probando Field ID: {field_id}")
            scenes = obtener_imagenes_field(field_id)
            
            if scenes:
                print(f"\n✅ Field #{field_id} tiene {len(scenes)} imágenes")
                break
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
