#!/usr/bin/env python3
"""
Script para generar los 3 videos del timeline (NDVI, NDMI, SAVI) en batch
Útil para exportación completa de una parcela

@author: AgroTech Team
@date: 15 de enero de 2026
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.processors.timeline_processor import TimelineProcessor
from informes.exporters.video_exporter import TimelineVideoExporter


def generar_videos_completos(parcela_id: int = 6):
    """
    Genera los 3 videos del timeline (NDVI, NDMI, SAVI) para una parcela
    
    Args:
        parcela_id: ID de la parcela
    """
    print("=" * 80)
    print(f"🎬 GENERACIÓN BATCH DE VIDEOS DEL TIMELINE")
    print("=" * 80)
    
    # 1. Obtener la parcela
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        print(f"\n📍 Parcela: {parcela.nombre}")
        print(f"   Propietario: {parcela.propietario}")
        print(f"   Cultivo: {parcela.tipo_cultivo}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
    except Parcela.DoesNotExist:
        print(f"❌ ERROR: No existe la parcela con ID {parcela_id}")
        return []
    
    # 2. Verificar que hay datos históricos
    registros_count = IndiceMensual.objects.filter(parcela=parcela).count()
    print(f"\n📊 Registros históricos: {registros_count}")
    
    if registros_count == 0:
        print("❌ ERROR: No hay registros históricos para esta parcela")
        return []
    
    # 3. Generar metadata del timeline (una sola vez)
    print(f"\n⚙️  Generando metadata del timeline...")
    timeline_data = TimelineProcessor.generar_timeline_completo(parcela)
    
    if timeline_data.get('error'):
        print(f"❌ ERROR: {timeline_data.get('mensaje')}")
        return []
    
    frames_data = timeline_data.get('frames', [])
    print(f"✅ {len(frames_data)} frames generados")
    
    # 4. Inicializar exportador (una sola vez)
    print(f"\n🎬 Inicializando exportador de video...")
    exporter = TimelineVideoExporter()
    
    # 5. Generar los 3 videos
    indices = ['ndvi', 'ndmi', 'savi']
    videos_generados = []
    
    inicio_total = datetime.now()
    
    for i, indice in enumerate(indices, 1):
        print(f"\n{'='*80}")
        print(f"🎥 [{i}/3] Generando video {indice.upper()}...")
        print(f"{'='*80}")
        
        # Verificar que hay imágenes para este índice
        frames_con_imagen = [
            f for f in frames_data 
            if f.get('imagenes', {}).get(indice)
        ]
        
        print(f"   Frames con imagen {indice.upper()}: {len(frames_con_imagen)}")
        
        if len(frames_con_imagen) == 0:
            print(f"   ⚠️  Sin imágenes {indice.upper()}, saltando...")
            continue
        
        print(f"   Resolución: {exporter.width}x{exporter.height}")
        print(f"   FPS: {exporter.fps}")
        print(f"   Duración estimada: {len(frames_con_imagen) * exporter.FRAME_DURATION:.1f}s")
        
        try:
            inicio = datetime.now()
            
            video_path = exporter.export_timeline(
                frames_data=frames_con_imagen,
                indice=indice
            )
            
            fin = datetime.now()
            duracion = (fin - inicio).total_seconds()
            
            # Obtener tamaño del archivo
            if os.path.exists(video_path):
                file_size = os.path.getsize(video_path) / (1024 * 1024)
                
                print(f"\n   ✅ Video {indice.upper()} generado exitosamente!")
                print(f"   📁 Ruta: {video_path}")
                print(f"   💾 Tamaño: {file_size:.2f} MB")
                print(f"   ⏱️  Tiempo: {duracion:.1f}s")
                
                videos_generados.append({
                    'indice': indice,
                    'path': video_path,
                    'size_mb': file_size,
                    'duration_s': duracion
                })
            
        except Exception as e:
            print(f"\n   ❌ ERROR generando video {indice.upper()}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 6. Resumen final
    fin_total = datetime.now()
    duracion_total = (fin_total - inicio_total).total_seconds()
    
    print("\n" + "=" * 80)
    print("🎉 PROCESO BATCH COMPLETADO")
    print("=" * 80)
    
    if videos_generados:
        print(f"\n✅ Videos generados: {len(videos_generados)}/3")
        
        size_total = sum(v['size_mb'] for v in videos_generados)
        
        print(f"\n📹 Resumen:")
        for video in videos_generados:
            print(f"   • {video['indice'].upper()}: {video['size_mb']:.2f} MB ({video['duration_s']:.1f}s)")
        
        print(f"\n💾 Tamaño total: {size_total:.2f} MB")
        print(f"⏱️  Tiempo total: {duracion_total:.1f}s")
        
        print(f"\n📂 Ubicación:")
        print(f"   {os.path.dirname(videos_generados[0]['path'])}")
        
        print(f"\n💡 Abrir todos los videos:")
        for video in videos_generados:
            print(f"   open '{video['path']}'")
    else:
        print(f"\n❌ No se generó ningún video")
        return []
    
    return videos_generados


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generar los 3 videos del timeline de una parcela')
    parser.add_argument('--parcela', type=int, default=6, help='ID de la parcela')
    
    args = parser.parse_args()
    
    videos = generar_videos_completos(args.parcela)
    
    if videos:
        print("\n" + "=" * 80)
        print("✨ EXPORTACIÓN BATCH EXITOSA")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ EXPORTACIÓN BATCH FALLIDA")
        print("=" * 80)
        sys.exit(1)
