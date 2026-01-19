"""
Script para generar TODOS los videos timeline multi-escena
Genera videos para todas las parcelas y todos los índices

Uso:
    python generar_videos_multiscene_batch.py
    python generar_videos_multiscene_batch.py --parcela 6
    python generar_videos_multiscene_batch.py --indice ndvi
"""

import os
import sys
import django
import argparse
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.processors.timeline_processor import TimelineProcessor
from informes.exporters.video_exporter_multiscene import TimelineVideoExporterMultiScene
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generar_video_multiscene(parcela, indice):
    """
    Genera un video multi-escena para una parcela e índice específicos
    """
    logger.info(f"🎬 Generando video: Parcela #{parcela.id} - {indice.upper()}")
    
    # Obtener datos mensuales
    indices_mensuales = IndiceMensual.objects.filter(
        parcela=parcela
    ).order_by('año', 'mes')
    
    if not indices_mensuales.exists():
        logger.warning(f"⏭️ Sin datos para parcela #{parcela.id}")
        return None
    
    # Procesar timeline
    frames_data = []
    indices_list = list(indices_mensuales)
    for i, indice_mensual in enumerate(indices_list):
        mes_anterior = indices_list[i-1] if i > 0 else None
        frame_meta = TimelineProcessor.generar_metadata_frame(indice_mensual, mes_anterior)
        frames_data.append(frame_meta)
    
    # Información de parcela
    parcela_info = {
        'nombre': parcela.nombre,
        'area': float(parcela.area_hectareas) if parcela.area_hectareas else None,
        'cultivo': parcela.tipo_cultivo or 'No especificado'
    }
    
    # Generar video
    try:
        exporter = TimelineVideoExporterMultiScene()
        video_path = exporter.export_timeline(
            frames_data=frames_data,
            indice=indice,
            parcela_info=parcela_info,
            analisis_texto=None,  # Por ahora sin análisis
            recomendaciones_texto=None  # Por ahora sin recomendaciones
        )
        
        if os.path.exists(video_path):
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            logger.info(f"✅ Video generado: {video_path} ({size_mb:.2f} MB)")
            return video_path
        else:
            logger.error(f"❌ Video no encontrado: {video_path}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generando video: {e}")
        return None


def generar_batch(parcela_id=None, indice_filter=None):
    """
    Genera videos para múltiples parcelas e índices
    """
    inicio = datetime.now()
    logger.info("="*80)
    logger.info("🎬 GENERACIÓN BATCH DE VIDEOS MULTI-ESCENA")
    logger.info("="*80)
    
    # Filtrar parcelas
    if parcela_id:
        parcelas = Parcela.objects.filter(id=parcela_id)
    else:
        parcelas = Parcela.objects.all()
    
    # Filtrar índices
    if indice_filter:
        indices = [indice_filter]
    else:
        indices = ['ndvi', 'ndmi', 'savi']
    
    logger.info(f"📊 Parcelas a procesar: {parcelas.count()}")
    logger.info(f"📊 Índices a procesar: {', '.join([i.upper() for i in indices])}")
    logger.info("")
    
    # Contadores
    total_videos = 0
    videos_exitosos = 0
    videos_fallidos = 0
    
    # Generar videos
    for parcela in parcelas:
        logger.info(f"📍 Procesando Parcela #{parcela.id}: {parcela.nombre}")
        
        for indice in indices:
            total_videos += 1
            video_path = generar_video_multiscene(parcela, indice)
            
            if video_path:
                videos_exitosos += 1
            else:
                videos_fallidos += 1
        
        logger.info("")
    
    # Resumen final
    fin = datetime.now()
    duracion = (fin - inicio).total_seconds()
    
    logger.info("="*80)
    logger.info("📊 RESUMEN DE GENERACIÓN")
    logger.info("="*80)
    logger.info(f"✅ Videos exitosos: {videos_exitosos}/{total_videos}")
    logger.info(f"❌ Videos fallidos: {videos_fallidos}/{total_videos}")
    logger.info(f"⏱️ Tiempo total: {duracion:.1f} segundos")
    logger.info(f"📁 Directorio: media/timeline_videos/")
    logger.info("="*80)
    
    return videos_exitosos, videos_fallidos


def main():
    parser = argparse.ArgumentParser(
        description='Generar videos timeline multi-escena en batch'
    )
    parser.add_argument(
        '--parcela', 
        type=int, 
        help='ID de parcela específica (opcional, por defecto todas)'
    )
    parser.add_argument(
        '--indice', 
        choices=['ndvi', 'ndmi', 'savi'], 
        help='Índice específico (opcional, por defecto todos)'
    )
    
    args = parser.parse_args()
    
    exitosos, fallidos = generar_batch(
        parcela_id=args.parcela,
        indice_filter=args.indice
    )
    
    if fallidos > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
