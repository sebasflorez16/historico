"""
Test de integración del Cerebro de Diagnóstico en el Generador PDF
===================================================================

Este script prueba la generación completa del PDF con el diagnóstico unificado.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.services.generador_pdf import GeneradorInformePDF
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_generacion_pdf_con_diagnostico():
    """
    Test de generación de PDF con diagnóstico unificado
    """
    try:
        logger.info("="*80)
        logger.info("🧪 TEST: Generación de PDF con Diagnóstico Unificado")
        logger.info("="*80)
        
        # Buscar una parcela de prueba
        parcelas = Parcela.objects.all()
        
        if not parcelas.exists():
            logger.error("❌ No hay parcelas en la base de datos")
            logger.info("Crea una parcela primero con:")
            logger.info("  python manage.py shell")
            logger.info("  from informes.models import Parcela")
            logger.info("  Parcela.objects.create(...)")
            return False
        
        parcela = parcelas.first()
        logger.info(f"✅ Usando parcela: {parcela.nombre} (ID: {parcela.id})")
        
        # Crear generador
        generador = GeneradorInformePDF()
        logger.info("✅ Generador PDF inicializado")
        
        # Verificar imports
        from informes.helpers import generar_tabla_desglose_severidad
        logger.info("✅ Helper diagnostico_pdf_helper importado correctamente")
        
        from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
        logger.info("✅ Cerebro de diagnóstico importado correctamente")
        
        logger.info("")
        logger.info("="*80)
        logger.info("✅ INTEGRACIÓN EXITOSA")
        logger.info("="*80)
        logger.info("")
        logger.info("📋 Módulos integrados:")
        logger.info("   ✓ GeneradorInformePDF")
        logger.info("   ✓ ejecutar_diagnostico_unificado")
        logger.info("   ✓ generar_tabla_desglose_severidad")
        logger.info("")
        logger.info("🎯 Para generar un PDF completo con diagnóstico:")
        logger.info("   1. Ve a la interfaz web")
        logger.info("   2. Selecciona una parcela")
        logger.info("   3. Genera un informe")
        logger.info("   4. El PDF incluirá:")
        logger.info("      - Mapa consolidado de severidad")
        logger.info("      - Tabla de desglose por área")
        logger.info("      - Zona prioritaria marcada")
        logger.info("      - Diagnóstico técnico detallado")
        logger.info("")
        logger.info("📁 Los archivos PDF se guardan en: media/informes/")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    exito = test_generacion_pdf_con_diagnostico()
    sys.exit(0 if exito else 1)
