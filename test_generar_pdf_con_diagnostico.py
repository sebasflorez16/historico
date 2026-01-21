"""
Script de prueba para generar PDF con diagnóstico unificado
===========================================================

Este script genera un informe PDF completo usando la parcela 6
para verificar que el diagnóstico unificado esté correctamente integrado.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.services.generador_pdf import GeneradorInformePDF
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generar_pdf_prueba():
    """Genera un PDF de prueba con la parcela 6"""
    
    print("="*80)
    print("🧪 TEST: GENERACIÓN DE PDF CON DIAGNÓSTICO UNIFICADO")
    print("="*80)
    print()
    
    # 1. Obtener parcela
    try:
        parcela = Parcela.objects.get(id=6)
        logger.info(f"✅ Parcela encontrada: {parcela.nombre}")
        logger.info(f"   Área: {parcela.area_hectareas:.2f} ha")
        logger.info(f"   Cultivo: {parcela.tipo_cultivo}")
    except Parcela.DoesNotExist:
        logger.error("❌ Parcela 6 no encontrada")
        logger.info("📋 Parcelas disponibles:")
        for p in Parcela.objects.all()[:5]:
            logger.info(f"   ID: {p.id} - {p.nombre}")
        return
    
    # 2. Obtener usuario
    try:
        usuario = User.objects.first()
        if not usuario:
            logger.warning("⚠️ No hay usuarios, creando uno de prueba...")
            usuario = User.objects.create_user(
                username='test_pdf',
                email='test@agrotech.com',
                password='test123'
            )
        logger.info(f"✅ Usuario: {usuario.username}")
    except Exception as e:
        logger.error(f"❌ Error obteniendo usuario: {str(e)}")
        return
    
    # 3. Definir período de análisis
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=90)  # 3 meses
    
    logger.info(f"📅 Período de análisis:")
    logger.info(f"   Inicio: {fecha_inicio.strftime('%Y-%m-%d')}")
    logger.info(f"   Fin: {fecha_fin.strftime('%Y-%m-%d')}")
    print()
    
    # 4. Generar PDF
    try:
        logger.info("🚀 Iniciando generación de PDF...")
        print()
        
        generador = GeneradorInformePDF()
        resultado = generador.generar_informe_optimizado(
            parcela=parcela,
            usuario=usuario,
            periodo_meses=3  # 3 meses de análisis
        )
        
        resultado = generador.generar_informe_optimizado(
            parcela=parcela,
            usuario=usuario,
            periodo_meses=3  # 3 meses de análisis
        )
        
        if resultado.get('success'):
            logger.info("✅ ¡PDF GENERADO EXITOSAMENTE!")
            print()
            logger.info(f"📄 Archivo PDF: {resultado.get('archivo_pdf')}")
            logger.info(f"📊 Informe ID: {resultado.get('informe_id')}")
            print()
            
            # Verificar que el PDF existe
            pdf_path = resultado.get('archivo_pdf')
            if pdf_path and os.path.exists(pdf_path):
                size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
                logger.info(f"✅ Archivo verificado: {size_mb:.2f} MB")
                
                # Abrir el PDF automáticamente
                logger.info("🖥️  Abriendo PDF...")
                os.system(f'open "{pdf_path}"')
            else:
                logger.error(f"❌ Archivo no encontrado: {pdf_path}")
            
            print()
            logger.info("="*80)
            logger.info("VERIFICAR EN EL PDF:")
            logger.info("="*80)
            logger.info("✓ Sección 'DIAGNÓSTICO UNIFICADO - MAPA DE SEVERIDAD'")
            logger.info("✓ Tabla de desglose por severidad (Rojo/Naranja/Amarillo)")
            logger.info("✓ Mapa consolidado con zonas marcadas")
            logger.info("✓ Información de zona prioritaria")
            logger.info("✓ Sección 'DIAGNÓSTICO TÉCNICO DETALLADO'")
            logger.info("✓ Narrativas mencionando 'ZONA ROJA' como prioridad")
            logger.info("="*80)
            
        else:
            logger.error(f"❌ Error generando PDF: {resultado.get('error', 'Error desconocido')}")
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando generador: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    print()
    logger.info("🏁 Test completado")
    print()


if __name__ == '__main__':
    generar_pdf_prueba()
