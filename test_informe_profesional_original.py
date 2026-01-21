"""
Script de Prueba: Generación del Informe Profesional Original
==============================================================

Genera el informe completo mes a mes con:
- Gráficos de tendencias
- Resumen ejecutivo IA
- Recomendaciones agronómicas
- Análisis técnico completo

Este es el informe que ya funcionaba antes del diagnóstico unificado.

Uso:
    python test_informe_profesional_original.py
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
from informes.models import Parcela, IndiceMensual, User
from informes.services.generador_pdf import generador_pdf

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Prueba del informe profesional original"""
    
    logger.info("=" * 80)
    logger.info("📄 TEST: Informe Profesional Original (Mes a Mes)")
    logger.info("=" * 80)
    
    # 1. Buscar parcela con datos
    try:
        parcela = Parcela.objects.get(id=6)  # Parcela #2
        logger.info(f"✅ Parcela seleccionada: {parcela.nombre}")
    except Parcela.DoesNotExist:
        logger.error("❌ Parcela #6 no encontrada")
        return
    
    # Verificar índices disponibles
    indices_count = IndiceMensual.objects.filter(parcela=parcela).count()
    logger.info(f"   Índices disponibles: {indices_count}")
    
    if indices_count == 0:
        logger.error("❌ No hay índices calculados para esta parcela")
        return
    
    # Mostrar último índice
    ultimo_indice = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes').first()
    if ultimo_indice:
        logger.info(f"   Último índice: {ultimo_indice.año}-{ultimo_indice.mes:02d}")
        logger.info(f"   NDVI: {ultimo_indice.ndvi_promedio:.3f}")
        logger.info(f"   NDMI: {ultimo_indice.ndmi_promedio:.3f}")
        logger.info(f"   SAVI: {ultimo_indice.savi_promedio:.3f}")
    
    # 2. Obtener o crear usuario de prueba
    try:
        usuario = User.objects.get(username='admin')
        logger.info(f"✅ Usuario: {usuario.username}")
    except User.DoesNotExist:
        logger.error("❌ Usuario 'admin' no encontrado")
        logger.info("💡 Crea un superusuario primero: python manage.py createsuperuser")
        return
    
    # 3. Generar informe profesional optimizado
    logger.info("\n" + "=" * 80)
    logger.info("📊 Generando Informe Profesional Mes a Mes...")
    logger.info("=" * 80)
    
    try:
        # Usar el método que funciona 100% con datos del caché (IndiceMensual)
        # Este genera el informe profesional completo sin llamar a EOSDA API
        logger.info("📝 Generando informe usando datos del caché local...")
        
        resultado = generador_pdf.generar_informe_completo(
            parcela=parcela,
            periodo_meses=12,
            tipo_informe='produccion'
        )
        
        if resultado.get('success'):
            logger.info("\n✅ ¡INFORME GENERADO EXITOSAMENTE!")
            logger.info(f"   Archivo: {resultado['archivo_pdf']}")
            
            # Verificar tamaño del archivo
            archivo_path = resultado['archivo_pdf']
            if isinstance(archivo_path, str) and os.path.exists(archivo_path):
                size_mb = os.path.getsize(archivo_path) / (1024 * 1024)
                logger.info(f"   Tamaño: {size_mb:.2f} MB")
                
                logger.info("\n" + "=" * 80)
                logger.info("✅ VALIDACIÓN COMPLETADA")
                logger.info("=" * 80)
                logger.info(f"📁 Abre el PDF para ver:")
                logger.info(f"   • Gráficos de tendencias mes a mes")
                logger.info(f"   • Resumen ejecutivo con análisis IA")
                logger.info(f"   • Recomendaciones agronómicas")
                logger.info(f"   • Datos técnicos completos")
                logger.info(f"\n📂 Ubicación: {archivo_path}")
            else:
                logger.warning(f"⚠️ Archivo no accesible: {archivo_path}")
        else:
            logger.error(f"❌ Error: {resultado.get('error', 'Desconocido')}")
            
    except Exception as e:
        logger.error(f"❌ Error en test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()
