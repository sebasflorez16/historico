#!/usr/bin/env python3
"""
Test de Umbrales de Nubosidad - AgroTech Histórico

Objetivo:
    Validar el comportamiento del sistema con diferentes niveles de nubosidad
    y demostrar la necesidad de implementar umbrales escalonados.

Uso:
    python tests/test_umbrales_nubosidad.py --parcela-id 1 --mes 2025-01

Autor: Sistema de Testing
Fecha: 2025-01-21
"""

import os
import sys
import django
import argparse
from datetime import datetime, timedelta
import logging

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.services.eosda_api import EosdaAPIService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_umbral_nubosidad(parcela_id: int, fecha_inicio: str, umbral: int):
    """
    Prueba obtención de imágenes con un umbral específico de nubosidad.
    
    Args:
        parcela_id: ID de la parcela a analizar
        fecha_inicio: Fecha inicio en formato 'YYYY-MM-DD'
        umbral: Umbral máximo de nubosidad (0-100)
    
    Returns:
        dict: Resultados del test
    """
    try:
        # Obtener parcela
        parcela = Parcela.objects.get(id=parcela_id)
        logger.info(f"📍 Parcela: {parcela.nombre} ({parcela.area_hectareas} ha)")
        
        # Calcular rango de fechas (1 mes)
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = fecha_inicio_dt + timedelta(days=30)
        
        logger.info(f"📅 Período: {fecha_inicio_dt.date()} a {fecha_fin_dt.date()}")
        logger.info(f"☁️ Umbral de nubosidad: {umbral}%\n")
        
        # Inicializar servicio EOSDA
        servicio = EosdaAPIService()
        
        # Probar con NDVI
        logger.info("🛰️ Buscando imágenes NDVI...")
        resultado = servicio.obtener_imagenes_indice(
            parcela=parcela,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            indice='NDVI',
            max_nubosidad=umbral
        )
        
        if resultado.get('error'):
            logger.error(f"❌ Error: {resultado['error']}")
            return {
                'umbral': umbral,
                'imagenes_encontradas': 0,
                'error': resultado['error']
            }
        
        imagenes = resultado.get('datos', [])
        num_imagenes = len(imagenes)
        
        if num_imagenes == 0:
            logger.warning(f"⚠️ No se encontraron imágenes con umbral {umbral}%")
            return {
                'umbral': umbral,
                'imagenes_encontradas': 0,
                'nubosidad_promedio': None,
                'nubosidad_min': None,
                'nubosidad_max': None
            }
        
        # Analizar nubosidad de las imágenes encontradas
        nubosidades = [img.get('nubosidad', 0) for img in imagenes]
        nubosidad_promedio = sum(nubosidades) / len(nubosidades)
        nubosidad_min = min(nubosidades)
        nubosidad_max = max(nubosidades)
        
        logger.info(f"✅ {num_imagenes} imágenes encontradas")
        logger.info(f"   - Nubosidad promedio: {nubosidad_promedio:.1f}%")
        logger.info(f"   - Nubosidad mínima: {nubosidad_min:.1f}%")
        logger.info(f"   - Nubosidad máxima: {nubosidad_max:.1f}%")
        
        # Clasificar calidad
        if nubosidad_promedio <= 20:
            calidad = "✅ CONFIABLE"
        elif nubosidad_promedio <= 50:
            calidad = "⚠️ ACEPTABLE"
        elif nubosidad_promedio <= 80:
            calidad = "🚫 BAJA CALIDAD"
        else:
            calidad = "❌ NO CONFIABLE"
        
        logger.info(f"   - Calidad: {calidad}\n")
        
        return {
            'umbral': umbral,
            'imagenes_encontradas': num_imagenes,
            'nubosidad_promedio': nubosidad_promedio,
            'nubosidad_min': nubosidad_min,
            'nubosidad_max': nubosidad_max,
            'calidad': calidad,
            'imagenes': imagenes[:3]  # Solo primeras 3 para muestra
        }
        
    except Parcela.DoesNotExist:
        logger.error(f"❌ Parcela {parcela_id} no existe")
        return {'error': 'Parcela no encontrada'}
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return {'error': str(e)}


def comparar_umbrales(parcela_id: int, fecha_inicio: str):
    """
    Compara resultados con diferentes umbrales de nubosidad.
    
    Demuestra cómo el sistema escalonado maximiza disponibilidad de datos.
    """
    logger.info("="*80)
    logger.info("COMPARACIÓN DE UMBRALES DE NUBOSIDAD")
    logger.info("="*80 + "\n")
    
    umbrales = [20, 50, 80]  # Umbrales propuestos: confiable, aceptable, máximo
    resultados = []
    
    for umbral in umbrales:
        logger.info(f"\n{'='*80}")
        logger.info(f"TEST CON UMBRAL: {umbral}%")
        logger.info(f"{'='*80}\n")
        
        resultado = test_umbral_nubosidad(parcela_id, fecha_inicio, umbral)
        resultados.append(resultado)
    
    # Resumen comparativo
    logger.info("\n" + "="*80)
    logger.info("RESUMEN COMPARATIVO")
    logger.info("="*80 + "\n")
    
    logger.info(f"{'Umbral':<10} {'Imágenes':<12} {'Nubosidad Prom.':<18} {'Calidad':<25}")
    logger.info("-"*80)
    
    for r in resultados:
        umbral = r['umbral']
        imagenes = r.get('imagenes_encontradas', 0)
        nubosidad = r.get('nubosidad_promedio')
        calidad = r.get('calidad', 'N/A')
        
        nubosidad_str = f"{nubosidad:.1f}%" if nubosidad else "N/A"
        logger.info(f"{umbral}%{' ':<7} {imagenes:<12} {nubosidad_str:<18} {calidad}")
    
    logger.info("\n" + "="*80)
    logger.info("ANÁLISIS Y RECOMENDACIONES")
    logger.info("="*80 + "\n")
    
    # Determinar estrategia recomendada
    r_20 = resultados[0]
    r_50 = resultados[1]
    r_80 = resultados[2]
    
    if r_20['imagenes_encontradas'] > 0:
        logger.info("✅ RECOMENDACIÓN: Usar umbral de 20% (CONFIABLE)")
        logger.info(f"   Se encontraron {r_20['imagenes_encontradas']} imágenes de alta calidad.")
        logger.info("   Los análisis serán precisos y confiables.")
    elif r_50['imagenes_encontradas'] > 0:
        logger.warning("⚠️ RECOMENDACIÓN: Usar umbral de 50% (ACEPTABLE)")
        logger.warning(f"   Se encontraron {r_50['imagenes_encontradas']} imágenes de calidad media.")
        logger.warning("   ADVERTIR al usuario sobre la nubosidad moderada.")
    elif r_80['imagenes_encontradas'] > 0:
        logger.error("🚫 RECOMENDACIÓN: Usar umbral de 80% (BAJA CALIDAD)")
        logger.error(f"   Se encontraron {r_80['imagenes_encontradas']} imágenes de baja calidad.")
        logger.error("   ADVERTIR FUERTEMENTE sobre la alta nubosidad.")
        logger.error("   Considerar no generar informe o marcar como 'no confiable'.")
    else:
        logger.error("❌ SITUACIÓN: Sin imágenes disponibles (>80% nubosidad)")
        logger.error("   Opciones:")
        logger.error("   1. Expandir rango de fechas")
        logger.error("   2. Usar datos de otro satélite (ej: Radar SAR)")
        logger.error("   3. Notificar al usuario que el mes no tiene datos disponibles")
    
    logger.info("\n" + "="*80)
    logger.info("CONCLUSIÓN")
    logger.info("="*80 + "\n")
    
    logger.info("El sistema de umbrales escalonados permite:")
    logger.info("1. ✅ Maximizar disponibilidad de datos")
    logger.info("2. ⚠️ Advertir sobre calidad cuando sea necesario")
    logger.info("3. 🚫 Evitar análisis con datos muy poco confiables")
    logger.info("4. 📊 Dar transparencia total al usuario")
    logger.info("\nVer documentación completa en: docs/sistema/FILTRADO_NUBOSIDAD_EOSDA.md\n")


def main():
    """Función principal del script de pruebas."""
    parser = argparse.ArgumentParser(
        description='Test de umbrales de nubosidad en imágenes satelitales'
    )
    parser.add_argument(
        '--parcela-id',
        type=int,
        required=True,
        help='ID de la parcela a analizar'
    )
    parser.add_argument(
        '--mes',
        type=str,
        required=True,
        help='Mes a analizar en formato YYYY-MM (ej: 2025-01)'
    )
    parser.add_argument(
        '--umbral',
        type=int,
        help='Probar un umbral específico (0-100). Si no se especifica, compara 20/50/80'
    )
    
    args = parser.parse_args()
    
    # Validar formato de mes
    try:
        fecha_inicio = datetime.strptime(args.mes + '-01', '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        logger.error("❌ Formato de mes inválido. Use YYYY-MM (ej: 2025-01)")
        return
    
    # Ejecutar tests
    if args.umbral:
        # Test individual
        test_umbral_nubosidad(args.parcela_id, fecha_inicio, args.umbral)
    else:
        # Comparación completa
        comparar_umbrales(args.parcela_id, fecha_inicio)


if __name__ == '__main__':
    main()
