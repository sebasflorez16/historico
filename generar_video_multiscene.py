"""
Script para generar video timeline MULTI-ESCENA profesional
Implementa estructura completa según finalizando_timeline.md

Uso:
    python generar_video_multiscene.py --parcela 6 --indice ndvi
"""

import os
import sys
import django
import argparse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.processors.timeline_processor import TimelineProcessor
from informes.exporters.video_exporter_multiscene import TimelineVideoExporterMultiScene
import logging

# Intentar importar InformeGenerado
try:
    from informes.models import InformeGenerado
    INFORME_DISPONIBLE = True
except ImportError:
    INFORME_DISPONIBLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Modelo InformeGenerado no disponible - videos sin análisis/recomendaciones")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def obtener_analisis_y_recomendaciones(parcela):
    """
    Obtiene análisis y recomendaciones del último informe generado
    """
    if not INFORME_DISPONIBLE:
        return None, None
    
    try:
        ultimo_informe = InformeGenerado.objects.filter(
            parcela=parcela
        ).order_by('-fecha_generacion').first()
        
        if ultimo_informe:
            # Obtener análisis del informe
            analisis = ultimo_informe.contenido_json.get('analisis_ia', {})
            
            # Extraer texto de análisis
            analisis_texto = analisis.get('analisis_textual', '')
            if not analisis_texto:
                # Intentar con resumen ejecutivo
                analisis_texto = analisis.get('resumen_ejecutivo', '')
            
            # Extraer recomendaciones
            recomendaciones = analisis.get('recomendaciones_priorizadas', [])
            if recomendaciones:
                recomendaciones_texto = '\n'.join([f"- {r.get('accion', '')}" for r in recomendaciones[:3]])
            else:
                recomendaciones_texto = analisis.get('recomendaciones_texto', '')
            
            logger.info(f"✅ Análisis y recomendaciones obtenidos del informe #{ultimo_informe.id}")
            return analisis_texto, recomendaciones_texto
        else:
            logger.warning("⚠️ No se encontró informe previo - video sin análisis/recomendaciones")
            return None, None
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo análisis: {e}")
        return None, None


def generar_video_multiscene(parcela_id: int, indice: str = 'ndvi', output_path: str = None):
    """
    Genera video multi-escena completo para una parcela
    """
    logger.info(f"🎬 Iniciando generación de video multi-escena")
    logger.info(f"   Parcela: #{parcela_id}")
    logger.info(f"   Índice: {indice.upper()}")
    
    # 1. Obtener parcela
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        logger.info(f"✅ Parcela encontrada: {parcela.nombre}")
    except Parcela.DoesNotExist:
        logger.error(f"❌ Parcela #{parcela_id} no existe")
        return None
    
    # 2. Obtener datos mensuales
    indices_mensuales = IndiceMensual.objects.filter(
        parcela=parcela
    ).order_by('año', 'mes')
    
    if not indices_mensuales.exists():
        logger.error(f"❌ No hay datos mensuales para la parcela #{parcela_id}")
        return None
    
    logger.info(f"📊 Encontrados {indices_mensuales.count()} meses de datos")
    
    # 3. Generar metadata de frames
    logger.info("🔄 Procesando timeline...")
    frames_data = []
    
    indices_list = list(indices_mensuales)
    for i, indice_mensual in enumerate(indices_list):
        mes_anterior = indices_list[i-1] if i > 0 else None
        frame_meta = TimelineProcessor.generar_metadata_frame(indice_mensual, mes_anterior)
        frames_data.append(frame_meta)
    
    logger.info(f"✅ Timeline procesado: {len(frames_data)} frames")
    
    # 4. Información completa de parcela
    parcela_info = {
        'nombre': parcela.nombre,
        'area_hectareas': float(parcela.area_hectareas) if parcela.area_hectareas else 0,
        'tipo_cultivo': parcela.tipo_cultivo or 'Sin especificar',
        'centro_lat': parcela.geometria.centroid.y if parcela.geometria else 0,
        'centro_lon': parcela.geometria.centroid.x if parcela.geometria else 0
    }
    
    # 5. Obtener análisis y recomendaciones del motor
    analisis_texto, recomendaciones_texto = obtener_analisis_y_recomendaciones(parcela)
    
    # 6. Generar video
    logger.info("🎥 Generando video multi-escena...")
    exporter = TimelineVideoExporterMultiScene()
    
    video_path = exporter.export_timeline(
        frames_data=frames_data,
        indice=indice,
        output_path=output_path,
        parcela_info=parcela_info,
        analisis_texto=analisis_texto,
        recomendaciones_texto=recomendaciones_texto
    )
    
    logger.info(f"✅ VIDEO GENERADO EXITOSAMENTE")
    logger.info(f"📁 Ruta: {video_path}")
    
    # Mostrar estadísticas
    if os.path.exists(video_path):
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        logger.info(f"📊 Tamaño: {size_mb:.2f} MB")
    
    return video_path


def main():
    parser = argparse.ArgumentParser(description='Generar video timeline multi-escena')
    parser.add_argument('--parcela', type=int, required=True, help='ID de la parcela')
    parser.add_argument('--indice', choices=['ndvi', 'ndmi', 'savi'], default='ndvi', help='Índice a visualizar')
    parser.add_argument('--output', type=str, help='Ruta de salida del video (opcional)')
    
    args = parser.parse_args()
    
    video_path = generar_video_multiscene(
        parcela_id=args.parcela,
        indice=args.indice,
        output_path=args.output
    )
    
    if video_path:
        print(f"\n✅ Video generado: {video_path}\n")
    else:
        print(f"\n❌ Error generando video\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
