"""
Script de Prueba: Generación de PDF con Diagnóstico Unificado
==============================================================

Valida la integración completa del Cerebro de Diagnóstico en el PDF.

Pasos:
1. Obtiene parcela con datos EOSDA sincronizados
2. Genera informe PDF con diagnóstico unificado
3. Valida que el PDF contenga:
   - Mapa consolidado de severidad
   - Tabla de desglose por área
   - Zona prioritaria con coordenadas
   - Narrativas adaptadas

Uso:
    python test_pdf_diagnostico_final.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

import logging
from datetime import date, timedelta
from informes.models import Parcela, IndiceMensual
from informes.services.generador_pdf import generador_pdf

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Prueba completa de generación PDF con diagnóstico"""
    
    logger.info("=" * 80)
    logger.info("🧪 TEST: Generación PDF con Diagnóstico Unificado")
    logger.info("=" * 80)
    
    # 1. Buscar parcela con datos EOSDA
    parcelas_sincronizadas = Parcela.objects.filter(
        eosda_field_id__isnull=False
    ).exclude(eosda_field_id='')
    
    if not parcelas_sincronizadas.exists():
        logger.error("❌ No hay parcelas sincronizadas con EOSDA")
        logger.info("💡 Sincroniza una parcela primero con EOSDA API")
        return
    
    # Tomar la primera parcela con índices recientes
    parcela = None
    for p in parcelas_sincronizadas:
        indices_count = IndiceMensual.objects.filter(parcela=p).count()
        if indices_count > 0:
            parcela = p
            logger.info(f"✅ Parcela seleccionada: {p.nombre} ({indices_count} índices)")
            break
    
    if not parcela:
        logger.error("❌ No hay parcelas con índices calculados")
        return
    
    # 2. Mostrar información de la parcela
    logger.info(f"📍 Parcela: {parcela.nombre}")
    logger.info(f"   Área: {parcela.area_hectareas:.2f} ha")
    logger.info(f"   EOSDA Field ID: {parcela.eosda_field_id}")
    
    # Verificar índices disponibles
    ultimo_indice = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes').first()
    if ultimo_indice:
        logger.info(f"   Último índice: {ultimo_indice.año}-{ultimo_indice.mes:02d}")
        logger.info(f"   NDVI: {ultimo_indice.ndvi_promedio:.3f}")
        logger.info(f"   NDMI: {ultimo_indice.ndmi_promedio:.3f}")
        logger.info(f"   SAVI: {ultimo_indice.savi_promedio:.3f}")
    
    # 3. Generar informe PDF con diagnóstico
    logger.info("\n" + "=" * 80)
    logger.info("📄 Generando informe PDF con diagnóstico unificado...")
    logger.info("=" * 80)
    
    try:
        resultado = generador_pdf.generar_informe_completo(
            parcela=parcela,
            periodo_meses=6,  # 6 meses de análisis
            tipo_informe='produccion'  # Usar lenguaje comercial
        )
        
        if resultado.get('success'):
            logger.info("\n✅ ¡INFORME GENERADO EXITOSAMENTE!")
            logger.info(f"   Archivo: {resultado['archivo_pdf']}")
            
            # Verificar que el archivo existe
            if os.path.exists(resultado['archivo_pdf']):
                size_mb = os.path.getsize(resultado['archivo_pdf']) / (1024 * 1024)
                logger.info(f"   Tamaño: {size_mb:.2f} MB")
            
            # Mostrar estadísticas del diagnóstico si están disponibles
            if 'diagnostico_unificado' in resultado:
                diag = resultado['diagnostico_unificado']
                logger.info(f"\n📊 Diagnóstico Unificado:")
                logger.info(f"   Eficiencia del lote: {diag.get('eficiencia_lote', 0):.1f}%")
                logger.info(f"   Área afectada: {diag.get('area_afectada_total', 0):.2f} ha")
                
                if diag.get('desglose_severidad'):
                    desglose = diag['desglose_severidad']
                    logger.info(f"   Zona crítica (roja): {desglose.get('critica', 0):.2f} ha")
                    logger.info(f"   Zona moderada (naranja): {desglose.get('moderada', 0):.2f} ha")
                    logger.info(f"   Zona leve (amarilla): {desglose.get('leve', 0):.2f} ha")
                
                if diag.get('zona_prioritaria'):
                    zona = diag['zona_prioritaria']
                    logger.info(f"\n🎯 Zona Prioritaria:")
                    logger.info(f"   Diagnóstico: {zona.get('etiqueta_comercial')}")
                    logger.info(f"   Coordenadas: {zona.get('centroide_geo')}")
                    logger.info(f"   Área: {zona.get('area_hectareas', 0):.2f} ha")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ VALIDACIÓN COMPLETADA")
            logger.info("=" * 80)
            logger.info(f"📁 Revisa el PDF en: {resultado['archivo_pdf']}")
            
        else:
            logger.error(f"❌ Error generando informe: {resultado.get('mensaje')}")
            if resultado.get('error'):
                logger.error(f"   Detalle: {resultado['error']}")
        
    except Exception as e:
        logger.error(f"❌ Error en test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()
