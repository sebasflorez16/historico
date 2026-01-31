#!/usr/bin/env python
"""
Test: Generar PDF COMPLETO TÉCNICO para Parcela #6
Valida que el nuevo mapa georeferenciado se incluya en el informe técnico principal.
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.models_gemini import InformeGenerado
from informes.generador_pdf import GeneradorPDFProfesional
from django.contrib.auth.models import User
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Genera PDF completo técnico para Parcela #6"""
    
    try:
        # 1. Obtener parcela #6
        logger.info("=" * 80)
        logger.info("🚀 GENERANDO PDF COMPLETO TÉCNICO - PARCELA #6")
        logger.info("=" * 80)
        
        parcela = Parcela.objects.get(id=6)
        logger.info(f"✅ Parcela encontrada: {parcela.nombre} ({parcela.area_hectareas:.2f} ha)")
        logger.info(f"   🌾 Cultivo: {parcela.tipo_cultivo if hasattr(parcela, 'tipo_cultivo') else 'No especificado'}")
        
        # 2. Obtener o crear usuario
        usuario = User.objects.filter(is_superuser=True).first()
        if not usuario:
            usuario = User.objects.create_user(
                username='admin_test',
                email='admin@test.com',
                is_superuser=True
            )
            logger.info(f"✅ Usuario admin creado: {usuario.username}")
        else:
            logger.info(f"✅ Usuario encontrado: {usuario.username}")
        
        # 3. Configurar parámetros del informe
        logger.info("\n📊 Configurando parámetros del informe...")
        parametros = {
            'tipo_analisis': 'completo',  # Informe técnico completo
            'incluir_recomendaciones': True,
            'incluir_analisis_tendencias': True,
            'incluir_proyecciones': True,
            'generar_graficos': True
        }
        
        # 4. Generar PDF usando el generador principal
        logger.info("\n📄 Generando PDF técnico completo...")
        logger.info("   Esto incluirá:")
        logger.info("   ✓ Resumen ejecutivo")
        logger.info("   ✓ Análisis de índices mes a mes")
        logger.info("   ✓ Análisis de tendencias")
        logger.info("   ✓ Diagnóstico con MAPA GEOREFERENCIADO")
        logger.info("   ✓ Recomendaciones agronómicas")
        logger.info("   ✓ Proyecciones y anexos")
        
        generador = GeneradorPDFProfesional()
        
        # La función retorna directamente la ruta del PDF
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=12
        )
        
        # 5. Validar resultado
        if pdf_path and os.path.exists(pdf_path):
            logger.info(f"\n✅ PDF COMPLETO GENERADO EXITOSAMENTE")
            logger.info(f"📂 Ubicación: {pdf_path}")
            
            size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            logger.info(f"📦 Tamaño: {size_mb:.2f} MB")
            
            # Buscar registro en BD
            informe = InformeGenerado.objects.filter(parcela=parcela).order_by('-fecha_generacion').first()
            if informe:
                logger.info(f"💾 Registro en BD:")
                logger.info(f"   ID: {informe.id}")
                logger.info(f"   Fecha: {informe.fecha_generacion}")
                logger.info(f"   Imágenes analizadas: {informe.num_imagenes_analizadas}")
                logger.info(f"   Tokens consumidos: {informe.tokens_consumidos}")
            
            logger.info("\n🎯 VALIDACIONES A REALIZAR:")
            logger.info("   1. Abrir el PDF generado")
            logger.info("   2. Buscar la sección 'Mapa Georeferenciado de Intervención'")
            logger.info("   3. Verificar que muestre:")
            logger.info("      ✓ Contorno real de la parcela")
            logger.info("      ✓ Coordenadas GPS en las esquinas")
            logger.info("      ✓ Zonas de intervención clasificadas por color")
            logger.info("      ✓ Leyenda con severidad")
            logger.info("   4. Confirmar que el resto del informe está intacto")
            
            logger.info(f"\n🔍 Comando para abrir: open '{pdf_path}'")
            return pdf_path
        else:
            logger.error(f"❌ Error al generar PDF o archivo no encontrado")
            return None
            
    except Parcela.DoesNotExist:
        logger.error("❌ Parcela #6 no encontrada en la base de datos")
        logger.info("   Ejecuta: python manage.py migrate")
        return None
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return None

if __name__ == '__main__':
    pdf_path = main()
    if pdf_path:
        print(f"\n✅ ÉXITO: PDF generado en {pdf_path}")
        sys.exit(0)
    else:
        print("\n❌ FALLO: No se pudo generar el PDF")
        sys.exit(1)
