#!/usr/bin/env python3
"""
Script para generar video del timeline de una parcela
Simula la descarga desde la interfaz web

@author: AgroTech Team
@date: 15 de enero de 2026
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.processors.timeline_processor import TimelineProcessor
from informes.exporters.video_exporter import TimelineVideoExporter


def generar_video_timeline(parcela_id: int = 6, indice: str = 'ndvi'):
    """
    Genera video del timeline para una parcela específica
    
    Args:
        parcela_id: ID de la parcela
        indice: Índice a exportar ('ndvi', 'ndmi', 'savi')
    """
    print("=" * 80)
    print(f"🎬 GENERACIÓN DE VIDEO DEL TIMELINE")
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
        return None
    
    # 2. Verificar que hay datos históricos
    registros_count = IndiceMensual.objects.filter(parcela=parcela).count()
    print(f"\n📊 Registros históricos: {registros_count}")
    
    if registros_count == 0:
        print("❌ ERROR: No hay registros históricos para esta parcela")
        print("   Sincroniza datos con EOSDA primero")
        return None
    
    # 3. Verificar que hay imágenes para el índice solicitado
    campo_imagen = f'imagen_{indice}'
    registros_con_imagen = IndiceMensual.objects.filter(
        parcela=parcela
    ).exclude(**{campo_imagen: ''}).exclude(**{f'{campo_imagen}__isnull': True})
    
    print(f"\n🖼️  Registros con imagen {indice.upper()}: {registros_con_imagen.count()}")
    
    if registros_con_imagen.count() == 0:
        print(f"❌ ERROR: No hay imágenes {indice.upper()} para esta parcela")
        print("   Descarga imágenes satelitales primero")
        return None
    
    # 4. Generar metadata del timeline usando TimelineProcessor
    print(f"\n⚙️  Generando metadata del timeline...")
    timeline_data = TimelineProcessor.generar_timeline_completo(parcela)
    
    if timeline_data.get('error'):
        print(f"❌ ERROR: {timeline_data.get('mensaje')}")
        return None
    
    frames_data = timeline_data.get('frames', [])
    print(f"✅ {len(frames_data)} frames generados")
    
    # 5. Filtrar frames que tengan imagen para el índice solicitado
    frames_con_imagen = [
        f for f in frames_data 
        if f.get('imagenes', {}).get(indice)
    ]
    
    print(f"   {len(frames_con_imagen)} frames con imagen {indice.upper()}")
    
    if len(frames_con_imagen) == 0:
        print(f"❌ ERROR: No hay frames con imagen {indice.upper()}")
        return None
    
    # 6. Inicializar exportador de video
    print(f"\n🎬 Inicializando exportador de video...")
    exporter = TimelineVideoExporter()
    
    # 7. Generar video
    print(f"\n🎥 Generando video {indice.upper()}...")
    print(f"   Resolución: {exporter.width}x{exporter.height}")
    print(f"   FPS: {exporter.fps}")
    print(f"   Duración por frame: {exporter.FRAME_DURATION}s")
    print(f"   Duración total estimada: {len(frames_con_imagen) * exporter.FRAME_DURATION:.1f}s")
    
    try:
        video_path = exporter.export_timeline(
            frames_data=frames_con_imagen,
            indice=indice
        )
        
        print(f"\n✅ Video generado exitosamente!")
        print(f"   📁 Ruta: {video_path}")
        
        # Obtener tamaño del archivo
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / (1024 * 1024)
            print(f"   💾 Tamaño: {file_size:.2f} MB")
        
        return video_path
        
    except Exception as e:
        print(f"\n❌ ERROR generando video: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generar video del timeline de una parcela')
    parser.add_argument('--parcela', type=int, default=6, help='ID de la parcela')
    parser.add_argument('--indice', choices=['ndvi', 'ndmi', 'savi'], default='ndvi', help='Índice a exportar')
    
    args = parser.parse_args()
    
    video_path = generar_video_timeline(args.parcela, args.indice)
    
    if video_path:
        print("\n" + "=" * 80)
        print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\n📹 Video disponible en: {video_path}")
        print("\n💡 Puedes abrir el video con:")
        print(f"   open '{video_path}'")
    else:
        print("\n" + "=" * 80)
        print("❌ PROCESO FALLIDO")
        print("=" * 80)
        sys.exit(1)
