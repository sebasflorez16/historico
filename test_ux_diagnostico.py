"""
Script de Prueba Rápida - Reestructuración UX del Diagnóstico Unificado
=======================================================================

Valida que los cambios de UX estén correctamente implementados:
1. Cuadro de eficiencia en resumen ejecutivo
2. Sección "GUÍA DE INTERVENCIÓN EN CAMPO"
3. Narrativa dual (técnica + campo)
4. Mapa de intervención limpio (si está integrado)

Uso:
    python test_ux_diagnostico.py
"""

import sys
import os
from pathlib import Path

# Configurar path de Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')

import django
django.setup()

from datetime import date, timedelta
from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validar_pdf_generado(pdf_path):
    """
    Valida que el PDF generado tenga los elementos UX esperados
    """
    import PyPDF2
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            num_pages = len(pdf.pages)
            
            logger.info(f"📄 PDF generado con {num_pages} páginas")
            
            # Extraer texto de páginas clave
            page_2_text = pdf.pages[1].extract_text()  # Resumen ejecutivo
            ultima_page_text = pdf.pages[-2].extract_text()  # Última antes de créditos
            
            # Validaciones
            validaciones = {
                '✅ Cuadro de eficiencia': 'Eficiencia' in page_2_text or 'ESTADO GENERAL' in page_2_text,
                '✅ Área crítica mencionada': 'hectáreas' in page_2_text or 'crítica' in page_2_text.lower(),
                '✅ Guía de intervención': 'INTERVENCIÓN' in ultima_page_text or 'GUÍA' in ultima_page_text,
                '✅ Narrativa de campo': 'zona' in ultima_page_text.lower() and 'GPS' in ultima_page_text,
            }
            
            logger.info("\n🔍 Resultados de validación:")
            for check, passed in validaciones.items():
                status = "✅" if passed else "❌"
                logger.info(f"  {status} {check}")
            
            return all(validaciones.values())
            
    except Exception as e:
        logger.error(f"❌ Error validando PDF: {str(e)}")
        return False


def main():
    """
    Prueba principal de generación de PDF con UX mejorado
    """
    logger.info("🚀 Iniciando prueba de UX del Diagnóstico Unificado...")
    
    # Obtener parcela de prueba
    parcela = Parcela.objects.filter(propietario__isnull=False).first()
    
    if not parcela:
        logger.error("❌ No hay parcelas disponibles para prueba")
        return False
    
    logger.info(f"📍 Usando parcela: {parcela.nombre} ({parcela.area_hectareas:.2f} ha)")
    
    # Definir período de análisis
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=180)  # 6 meses
    
    logger.info(f"📅 Período: {fecha_inicio} a {fecha_fin}")
    
    # Generar PDF
    logger.info("📝 Generando PDF profesional con diagnóstico UX...")
    
    try:
        generador = GeneradorPDFProfesional()
        pdf_path = generador.generar(
            parcela=parcela,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        logger.info(f"✅ PDF generado: {pdf_path}")
        
        # Validar contenido
        logger.info("\n🔍 Validando contenido del PDF...")
        validacion_exitosa = validar_pdf_generado(pdf_path)
        
        if validacion_exitosa:
            logger.info("\n🎉 ¡Prueba EXITOSA! El PDF contiene todos los elementos UX esperados")
            logger.info(f"📄 Revisa el PDF en: {pdf_path}")
            return True
        else:
            logger.warning("\n⚠️ El PDF se generó pero falta algún elemento UX")
            logger.info("📝 Verifica manualmente si:")
            logger.info("  1. El cuadro de eficiencia está en página 2")
            logger.info("  2. La última sección es 'GUÍA DE INTERVENCIÓN EN CAMPO'")
            logger.info("  3. Hay narrativa dual (técnica + campo) por zona")
            logger.info("  4. El mapa tiene fondo gris y contornos claros")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error generando PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    exito = main()
    sys.exit(0 if exito else 1)
