#!/usr/bin/env python
"""
🎯 VALIDACIÓN FINAL: Generar PDF Completo con Mapa Georeferenciado
Parcela #6 - Validación en producción
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Genera PDF completo para validación final"""
    
    logger.info("=" * 80)
    logger.info("🎯 VALIDACIÓN FINAL - PDF CON MAPA GEOREFERENCIADO")
    logger.info("=" * 80)
    
    try:
        # Obtener Parcela #6
        parcela = Parcela.objects.get(id=6)
        logger.info(f"\n✅ Parcela: {parcela.nombre}")
        logger.info(f"   Área: {parcela.area_hectareas:.2f} ha")
        logger.info(f"   Geometría: {'✅ SÍ' if parcela.geometria else '❌ NO'}")
        
        if parcela.geometria:
            bbox = parcela.geometria.extent
            logger.info(f"   BBox: [{bbox[0]:.6f}, {bbox[1]:.6f}, {bbox[2]:.6f}, {bbox[3]:.6f}]")
        
        # Generar PDF
        logger.info("\n📄 Generando PDF técnico completo...")
        logger.info("   ✓ Con diagnóstico unificado")
        logger.info("   ✓ Con mapa georeferenciado")
        logger.info("   ✓ Con análisis temporal")
        logger.info("   ✓ Con todos los índices")
        
        generador = GeneradorPDFProfesional()
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=12
        )
        
        if pdf_path and os.path.exists(pdf_path):
            size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            logger.info(f"\n✅ PDF GENERADO EXITOSAMENTE")
            logger.info(f"📂 Ubicación: {pdf_path}")
            logger.info(f"📦 Tamaño: {size_mb:.2f} MB")
            
            logger.info("\n🔍 VALIDACIONES A REALIZAR:")
            logger.info("   1. Abrir el PDF generado")
            logger.info("   2. Buscar sección 'Diagnóstico Detallado y Plan de Acción'")
            logger.info("   3. Verificar que aparezca 'Mapa Georeferenciado de Intervención'")
            logger.info("   4. Confirmar que muestra:")
            logger.info("      ✓ Contorno real de la parcela")
            logger.info("      ✓ Coordenadas GPS en las esquinas")
            logger.info("      ✓ Zonas de intervención (si hay)")
            logger.info("      ✓ Leyenda de severidad")
            
            logger.info(f"\n🚀 Comando para abrir:")
            logger.info(f"   open '{pdf_path}'")
            
            return pdf_path
        else:
            logger.error("❌ Error: PDF no fue generado")
            return None
            
    except Parcela.DoesNotExist:
        logger.error("❌ Parcela #6 no encontrada")
        return None
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        return None

if __name__ == '__main__':
    pdf_path = main()
    sys.exit(0 if pdf_path else 1)
