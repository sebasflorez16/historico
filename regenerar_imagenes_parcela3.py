#!/usr/bin/env python
"""
Script para regenerar imágenes satelitales de Parcela 3
Ejecutar en Railway shell: railway run python regenerar_imagenes_parcela3.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings_production')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.services.eosda_api import EosdaAPIService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerar_imagenes():
    """Regenera las imágenes satelitales desde EOSDA API"""
    
    parcela = Parcela.objects.get(id=3)
    logger.info(f"📦 Procesando: {parcela.nombre} ({parcela.propietario})")
    
    # Obtener índices que tienen rutas pero sin archivos
    indices = parcela.indices_mensuales.exclude(imagen_ndvi='').exclude(imagen_ndvi__isnull=True)
    
    logger.info(f"📊 Total índices con rutas: {indices.count()}")
    
    # Inicializar servicio EOSDA
    eosda_service = EosdaAPIService()
    
    for indice in indices:
        logger.info(f"\n🔄 Procesando {indice.periodo_texto}...")
        
        # Verificar si los archivos existen
        ndvi_existe = os.path.exists(indice.imagen_ndvi.path) if indice.imagen_ndvi else False
        ndmi_existe = os.path.exists(indice.imagen_ndmi.path) if indice.imagen_ndmi else False
        savi_existe = os.path.exists(indice.imagen_savi.path) if indice.imagen_savi else False
        
        if ndvi_existe and ndmi_existe and savi_existe:
            logger.info(f"✅ Imágenes ya existen, saltando...")
            continue
        
        logger.info(f"❌ Imágenes faltantes, descargando desde EOSDA...")
        
        # Aquí llamarías al método que descarga las imágenes
        # eosda_service.obtener_imagenes_mes(parcela, indice.año, indice.mes)
        
        logger.warning("⚠️  PENDIENTE: Implementar descarga desde EOSDA")

if __name__ == '__main__':
    try:
        regenerar_imagenes()
        logger.info("\n✅ Proceso completado")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        sys.exit(1)
