"""
Script de Prueba: Informe Profesional Original + Diagnóstico Unificado
=======================================================================

Genera el informe profesional completo (el bueno de 645KB) 
y le agrega al final la sección de diagnóstico unificado.

Uso:
    python test_informe_profesional_con_diagnostico.py
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
from informes.generador_pdf import GeneradorPDFProfesional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Generar informe profesional con diagnóstico unificado"""
    
    logger.info("=" * 80)
    logger.info("📄 GENERANDO INFORME PROFESIONAL + DIAGNÓSTICO UNIFICADO")
    logger.info("=" * 80)
    
    # ID de la parcela (Parcela #2 tiene ID 6)
    parcela_id = 6
    
    try:
        # Instanciar generador
        generador = GeneradorPDFProfesional()
        
        logger.info(f"🚀 Generando informe para Parcela ID {parcela_id}...")
        
        # Generar informe completo
        ruta_pdf = generador.generar_informe_completo(
            parcela_id=parcela_id,
            meses_atras=12
        )
        
        logger.info("\n✅ ¡INFORME GENERADO EXITOSAMENTE!")
        logger.info(f"📂 Ubicación: {ruta_pdf}")
        
        # Verificar tamaño
        if os.path.exists(ruta_pdf):
            size_mb = os.path.getsize(ruta_pdf) / (1024 * 1024)
            logger.info(f"📊 Tamaño: {size_mb:.2f} MB")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ CONTENIDO DEL INFORME:")
            logger.info("=" * 80)
            logger.info("  1. Portada con logo AgroTech")
            logger.info("  2. Metodología de análisis")
            logger.info("  3. Resumen ejecutivo")
            logger.info("  4. Información de la parcela")
            logger.info("  5. Análisis NDVI (gráficos + interpretación)")
            logger.info("  6. Análisis NDMI (gráficos + interpretación)")
            logger.info("  7. Análisis SAVI (gráficos + interpretación)")
            logger.info("  8. Análisis de tendencias")
            logger.info("  9. Recomendaciones agronómicas")
            logger.info(" 10. Tabla de datos históricos")
            logger.info(" 11. Galería de imágenes satelitales")
            logger.info(" 12. 🆕 DIAGNÓSTICO UNIFICADO (Cerebro de Análisis)")
            logger.info("     • Mapa consolidado de severidad")
            logger.info("     • Desglose por área (Rojo/Naranja/Amarillo)")
            logger.info("     • Zona prioritaria con coordenadas")
            logger.info("     • Análisis técnico detallado")
            logger.info(" 13. Bloque de cierre")
            logger.info(" 14. Página de créditos")
            logger.info("\n" + "=" * 80)
            logger.info(f"🎉 Abre el PDF para ver el informe completo:")
            logger.info(f"   {ruta_pdf}")
            logger.info("=" * 80)
        else:
            logger.error(f"❌ Archivo no encontrado: {ruta_pdf}")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()
