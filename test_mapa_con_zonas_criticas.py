#!/usr/bin/env python
"""
Test: Mapa Georeferenciado CON Zonas Críticas Visibles
=======================================================

Genera un mapa con zonas claramente críticas para validación visual completa.

Autor: AgroTech Team
Fecha: 21 enero 2026
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

from informes.models import Parcela
from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
from informes.motor_analisis.mascara_cultivo import generar_mascara_desde_geometria
from django.conf import settings
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_mapa_con_zonas_criticas():
    """
    Test del mapa georeferenciado con zonas críticas visibles
    """
    logger.info("=" * 80)
    logger.info("🗺️  TEST: MAPA CON ZONAS CRÍTICAS BIEN DEFINIDAS")
    logger.info("=" * 80)
    logger.info("")
    
    # 1. Obtener parcela
    parcela = Parcela.objects.get(id=6)
    logger.info(f"✅ Parcela: {parcela.nombre} ({parcela.area_hectareas:.2f} ha)")
    
    # 2. Generar datos sintéticos CON zonas claramente problemáticas
    logger.info("")
    logger.info("📊 Generando datos sintéticos con ZONAS CLARAMENTE CRÍTICAS...")
    
    size = (120, 120)
    np.random.seed(123)  # Nueva semilla para diferentes zonas
    
    # Base: Lote saludable (NDVI alto)
    ndvi = np.full(size, 0.75, dtype=float)
    ndvi += np.random.normal(0, 0.05, size)  # Variabilidad natural
    
    # ZONA CRÍTICA 1: Esquina superior izquierda (stress hídrico severo)
    ndvi[10:35, 10:35] = 0.18  # NDVI crítico
    ndvi[10:35, 10:35] += np.random.normal(0, 0.03, (25, 25))
    
    # ZONA CRÍTICA 2: Centro (déficit nutricional)
    ndvi[50:70, 50:70] = 0.22  # NDVI muy bajo
    ndvi[50:70, 50:70] += np.random.normal(0, 0.02, (20, 20))
    
    # ZONA MODERADA 1: Lado derecho (stress leve)
    ndvi[30:60, 85:110] = 0.38  # NDVI moderado
    ndvi[30:60, 85:110] += np.random.normal(0, 0.04, (30, 25))
    
    # ZONA MODERADA 2: Esquina inferior izquierda
    ndvi[90:110, 15:40] = 0.42  # NDVI moderado-bajo
    ndvi[90:110, 15:40] += np.random.normal(0, 0.03, (20, 25))
    
    # ZONA LEVE: Centro-derecha
    ndvi[65:85, 60:85] = 0.50  # NDVI leve
    ndvi[65:85, 60:85] += np.random.normal(0, 0.03, (20, 25))
    
    # Clip final
    ndvi = np.clip(ndvi, -0.2, 1.0)
    
    # NDMI correlacionado con NDVI (zonas críticas tienen menos humedad)
    ndmi = ndvi * 0.6 - 0.1
    ndmi[10:35, 10:35] -= 0.3  # Zona 1: Déficit hídrico severo
    ndmi[50:70, 50:70] -= 0.2  # Zona 2: Déficit hídrico moderado
    ndmi = np.clip(ndmi, -0.5, 0.8)
    
    # SAVI correlacionado
    savi = ndvi * 1.5 / (1 + 0.5)
    savi = np.clip(savi, -0.2, 1.0)
    
    logger.info(f"✅ Arrays generados: {ndvi.shape}")
    logger.info(f"   NDVI rango: [{np.min(ndvi):.3f}, {np.max(ndvi):.3f}]")
    logger.info(f"   Zonas críticas insertadas:")
    logger.info(f"      - Esquina superior izq (10:35, 10:35) NDVI ~0.18")
    logger.info(f"      - Centro (50:70, 50:70) NDVI ~0.22")
    logger.info(f"      - Lado derecho (30:60, 85:110) NDVI ~0.38")
    logger.info(f"      - Esquina inferior izq (90:110, 15:40) NDVI ~0.42")
    logger.info(f"      - Centro-derecha (65:85, 60:85) NDVI ~0.50")
    
    # 3. GeoTransform realista
    if parcela.centroide:
        lat, lon = parcela.centroide.y, parcela.centroide.x
    else:
        lat, lon = 4.6097, -74.0817
    
    pixel_size = 10.0 / 111320.0
    geo_transform = (
        lon - (ndvi.shape[1] / 2) * pixel_size,
        pixel_size,
        0,
        lat + (ndvi.shape[0] / 2) * pixel_size,
        0,
        -pixel_size
    )
    
    # 4. Generar máscara
    logger.info("")
    logger.info("🗺️  Generando máscara de cultivo...")
    mascara = generar_mascara_desde_geometria(
        parcela.geometria,
        geo_transform,
        shape=ndvi.shape
    )
    logger.info(f"✅ Máscara: {np.sum(mascara)} píxeles válidos")
    
    # 5. Ejecutar diagnóstico
    logger.info("")
    logger.info("🧠 Ejecutando diagnóstico unificado...")
    
    output_dir = Path(settings.MEDIA_ROOT) / 'diagnosticos' / f'parcela_{parcela.id}_test_criticas'
    
    diagnostico = ejecutar_diagnostico_unificado(
        datos_indices={
            'ndvi': ndvi,
            'ndmi': ndmi,
            'savi': savi
        },
        geo_transform=geo_transform,
        area_parcela_ha=parcela.area_hectareas,
        output_dir=output_dir,
        tipo_informe='produccion',
        mascara_cultivo=mascara,
        geometria_parcela=parcela.geometria
    )
    
    # 6. Resultados
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ DIAGNÓSTICO COMPLETADO")
    logger.info("=" * 80)
    logger.info(f"📊 Eficiencia del lote: {diagnostico.eficiencia_lote:.1f}%")
    logger.info(f"📍 Área afectada total: {diagnostico.area_afectada_total:.2f} ha")
    logger.info(f"🔴 Zonas críticas detectadas: {len([z for z in diagnostico.zonas_criticas if z.severidad >= 0.7])}")
    logger.info(f"🟠 Zonas moderadas detectadas: {len([z for z in diagnostico.zonas_criticas if 0.4 <= z.severidad < 0.7])}")
    logger.info(f"🟡 Zonas leves detectadas: {len([z for z in diagnostico.zonas_criticas if z.severidad < 0.4])}")
    logger.info(f"🗺️  Mapa generado: {diagnostico.mapa_diagnostico_path}")
    logger.info("")
    
    if os.path.exists(diagnostico.mapa_diagnostico_path):
        logger.info("=" * 80)
        logger.info("🔍 VALIDACIÓN VISUAL DEL MAPA")
        logger.info("=" * 80)
        logger.info("")
        logger.info("✅ Archivo de mapa generado exitosamente")
        logger.info("")
        logger.info("📋 El mapa DEBE mostrar:")
        logger.info("   1. ✅ Contorno negro de la parcela (polígono real)")
        logger.info("   2. ✅ Fondo limpio (gris claro #F5F5F5)")
        logger.info("   3. ✅ Coordenadas GPS en las 4 esquinas")
        logger.info("   4. ✅ Zonas críticas (círculos ROJOS)")
        logger.info("   5. ✅ Zonas moderadas (círculos NARANJAS)")
        logger.info("   6. ✅ Zonas leves (círculos AMARILLOS)")
        logger.info("   7. ✅ Zona prioritaria con etiqueta 'ZONA PRIORITARIA'")
        logger.info("   8. ✅ Título: 'MAPA DE INTERVENCIÓN - RESUMEN DE TODO EL PERÍODO ANALIZADO'")
        logger.info("   9. ✅ Leyenda con áreas por severidad")
        logger.info("")
        logger.info("🔍 ABRIR MAPA PARA VALIDACIÓN VISUAL:")
        logger.info(f"   open \"{diagnostico.mapa_diagnostico_path}\"")
        logger.info("")
        
        return True
    else:
        logger.error(f"❌ El mapa no se generó")
        return False


if __name__ == "__main__":
    try:
        exito = test_mapa_con_zonas_criticas()
        sys.exit(0 if exito else 1)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
