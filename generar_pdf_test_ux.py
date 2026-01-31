#!/usr/bin/env python
"""
Generador Simple de PDF con Correcciones UX
===========================================

Genera un PDF de prueba para validar las correcciones de UX aplicadas.

Autor: AgroTech Team
Fecha: 21 enero 2025
"""

import os
import sys
import django
import logging
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.generador_pdf import GeneradorPDFProfesional

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def generar_pdf_test():
    """Genera PDF de prueba para Parcela #6"""
    logger.info("=" * 80)
    logger.info(" GENERACIÓN DE PDF CON CORRECCIONES UX")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        generador = GeneradorPDFProfesional()
        
        logger.info("📄 Generando PDF para Parcela #6 (últimos 6 meses)...")
        logger.info("")
        
        pdf_path = generador.generar_informe_completo(
            parcela_id=6,
            meses_atras=6
        )
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ PDF GENERADO EXITOSAMENTE")
        logger.info("=" * 80)
        logger.info(f"📁 Archivo: {pdf_path}")
        logger.info("")
        
        logger.info("📋 CORRECCIONES APLICADAS EN ESTE PDF:")
        logger.info("")
        logger.info("  ✅ 1. Banner sin asumir 'cultivo'")
        logger.info("       • Antes: 'ESTADO DEL CULTIVO: CRÍTICO'")
        logger.info("       • Ahora: 'ESTADO DEL LOTE: ÓPTIMO/REQUIERE ATENCIÓN/...'")
        logger.info("")
        
        logger.info("  ✅ 2. Explicación clara del porcentaje")
        logger.info("       • Etiqueta: 'Índice de Salud del Lote: XX%'")
        logger.info("       • Explicación integrada en el texto")
        logger.info("")
        
        logger.info("  ✅ 3. Mensajes coherentes (sin contradicciones)")
        logger.info("       • Si área afectada = 0: Banner ÓPTIMO")
        logger.info("       • Si área afectada > 0: Banner con área específica")
        logger.info("")
        
        logger.info("  ✅ 4. Tabla clara")
        logger.info("       • 'Sin zonas críticas durante todo el período analizado'")
        logger.info("       • Observaciones detalladas")
        logger.info("")
        
        logger.info("  ✅ 5. Contexto adaptado")
        logger.info("       • Sin zonas: Menciona 'primera siembra' como opción")
        logger.info("       • Con zonas: Dirige a 'Diagnóstico Detallado'")
        logger.info("")
        
        logger.info("=" * 80)
        logger.info("🔍 PRÓXIMO PASO: Abrir y revisar el PDF")
        logger.info("=" * 80)
        logger.info(f"   open \"{pdf_path}\"")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        exito = generar_pdf_test()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrumpido")
        sys.exit(1)
