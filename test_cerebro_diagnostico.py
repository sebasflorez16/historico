#!/usr/bin/env python
"""
Test del Cerebro de Diagnóstico Unificado
=========================================

Script de validación funcional y visual del módulo de diagnóstico.
Genera datos sintéticos realistas y valida la detección de zonas críticas.

Autor: AgroTech Team
Fecha: Enero 2026
"""

import os
import sys
import numpy as np
from pathlib import Path
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
django.setup()

from informes.motor_analisis.cerebro_diagnostico import (
    CerebroDiagnosticoUnificado,
    ejecutar_diagnostico_unificado
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generar_datos_sinteticos_realistas(shape=(100, 100)):
    """
    Genera arrays sintéticos de NDVI, NDMI, SAVI con zonas críticas simuladas
    
    Simula una parcela con:
    - Área mayormente saludable (NDVI >0.6, NDMI >0.2, SAVI >0.5)
    - Zona con déficit hídrico (esquina superior izquierda)
    - Zona con baja densidad/suelo degradado (zona central-inferior)
    """
    logger.info("📊 Generando datos sintéticos realistas...")
    
    # Base saludable
    np.random.seed(42)
    
    # NDVI: Base alta con variación
    ndvi = np.random.normal(0.65, 0.10, shape)
    ndvi = np.clip(ndvi, -1.0, 1.0)
    
    # NDMI: Base media-alta con variación
    ndmi = np.random.normal(0.25, 0.08, shape)
    ndmi = np.clip(ndmi, -1.0, 1.0)
    
    # SAVI: Similar a NDVI pero ligeramente menor
    savi = np.random.normal(0.55, 0.12, shape)
    savi = np.clip(savi, -1.0, 1.0)
    
    # ZONA CRÍTICA 1: Déficit hídrico recurrente (esquina superior izquierda)
    # NDVI < 0.45 AND NDMI < 0.05
    y1, x1 = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), indexing='ij')
    mascara_deficit = (x1 < 25) & (y1 < 30)
    
    ndvi[mascara_deficit] = np.random.uniform(0.20, 0.42, size=np.sum(mascara_deficit))
    ndmi[mascara_deficit] = np.random.uniform(-0.15, 0.03, size=np.sum(mascara_deficit))
    savi[mascara_deficit] = np.random.uniform(0.15, 0.38, size=np.sum(mascara_deficit))
    
    # ZONA CRÍTICA 2: Baja densidad/suelo degradado (zona central-inferior)
    # NDVI < 0.45 AND SAVI < 0.35
    mascara_baja_densidad = (x1 > 40) & (x1 < 65) & (y1 > 60) & (y1 < 85)
    
    ndvi[mascara_baja_densidad] = np.random.uniform(0.25, 0.43, size=np.sum(mascara_baja_densidad))
    ndmi[mascara_baja_densidad] = np.random.uniform(0.10, 0.25, size=np.sum(mascara_baja_densidad))  # Humedad OK
    savi[mascara_baja_densidad] = np.random.uniform(0.18, 0.33, size=np.sum(mascara_baja_densidad))
    
    # ZONA CRÍTICA 3 (menor): Estrés nutricional (esquina derecha)
    mascara_nutricional = (x1 > 80) & (y1 > 15) & (y1 < 35)
    
    ndvi[mascara_nutricional] = np.random.uniform(0.35, 0.48, size=np.sum(mascara_nutricional))
    ndmi[mascara_nutricional] = np.random.uniform(0.20, 0.35, size=np.sum(mascara_nutricional))  # Humedad buena
    savi[mascara_nutricional] = np.random.uniform(0.30, 0.44, size=np.sum(mascara_nutricional))
    
    logger.info(f"✅ Datos generados: {shape}")
    logger.info(f"   NDVI rango: {ndvi.min():.3f} - {ndvi.max():.3f}")
    logger.info(f"   NDMI rango: {ndmi.min():.3f} - {ndmi.max():.3f}")
    logger.info(f"   SAVI rango: {savi.min():.3f} - {savi.max():.3f}")
    
    return ndvi, ndmi, savi


def generar_geotransform_ejemplo():
    """
    Genera un GeoTransform de ejemplo para una parcela en Colombia
    
    GeoTransform: (top_left_x, pixel_width, rotation_x,
                   top_left_y, rotation_y, pixel_height)
    """
    # Ejemplo: Parcela cerca de Bogotá
    # Coordenadas aproximadas: 4.5° N, -74.0° W
    top_left_lon = -74.0
    top_left_lat = 4.5
    
    # Resolución de 10m (Sentinel-2)
    # En grados (aproximado para latitud 4.5°):
    # 1 grado ≈ 111 km
    # 10m ≈ 0.00009 grados
    pixel_size_deg = 10.0 / 111000.0
    
    return (
        top_left_lon,       # top_left_x
        pixel_size_deg,     # pixel_width
        0,                  # rotation_x
        top_left_lat,       # top_left_y
        0,                  # rotation_y
        -pixel_size_deg     # pixel_height (negativo porque va hacia abajo)
    )


def test_cerebro_diagnostico():
    """Test principal del cerebro de diagnóstico"""
    print("\n" + "="*80)
    print("🧪 TEST DEL CEREBRO DE DIAGNÓSTICO UNIFICADO")
    print("="*80 + "\n")
    
    # 1. Configuración
    logger.info("⚙️ Configurando test...")
    output_dir = Path(__file__).parent / 'test_outputs' / 'cerebro_diagnostico'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    area_parcela_ha = 61.42  # Parcela #6 real
    shape = (100, 100)
    
    # 2. Generar datos sintéticos
    ndvi, ndmi, savi = generar_datos_sinteticos_realistas(shape)
    geo_transform = generar_geotransform_ejemplo()
    
    # 3. Ejecutar diagnóstico - PRODUCCIÓN
    logger.info("\n📋 Test 1: Informe de PRODUCCIÓN")
    logger.info("-" * 60)
    
    diagnostico_prod = ejecutar_diagnostico_unificado(
        datos_indices={
            'ndvi': ndvi,
            'ndmi': ndmi,
            'savi': savi
        },
        geo_transform=geo_transform,
        area_parcela_ha=area_parcela_ha,
        output_dir=output_dir / 'produccion',
        tipo_informe='produccion',
        resolucion_m=10.0
    )
    
    # 4. Mostrar resultados
    print("\n" + "="*80)
    print("📊 RESULTADOS DEL DIAGNÓSTICO - PRODUCCIÓN")
    print("="*80 + "\n")
    
    print(f"🎯 Eficiencia del Lote: {diagnostico_prod.eficiencia_lote}%")
    print(f"📍 Zonas Críticas Detectadas: {len(diagnostico_prod.zonas_criticas)}")
    print(f"⚠️  Área Total Afectada: {diagnostico_prod.area_afectada_total:.2f} ha\n")
    
    if diagnostico_prod.zona_prioritaria:
        zp = diagnostico_prod.zona_prioritaria
        print("🔴 ZONA PRIORITARIA:")
        print(f"   • Tipo: {zp.etiqueta_comercial}")
        print(f"   • Área: {zp.area_hectareas:.2f} ha ({zp.area_pixeles} píxeles)")
        print(f"   • Severidad: {zp.severidad*100:.0f}%")
        print(f"   • Confianza: {zp.confianza*100:.0f}%")
        print(f"   • Centroide Geo: {zp.centroide_geo[0]:.6f}, {zp.centroide_geo[1]:.6f}")
        print(f"   • Centroide Pixel: {zp.centroide_pixel}")
        print(f"\n   📈 Valores de Índices:")
        for idx, val in zp.valores_indices.items():
            print(f"      - {idx.upper()}: {val:.3f}")
        print(f"\n   💡 Recomendaciones:")
        for i, rec in enumerate(zp.recomendaciones[:3], 1):
            print(f"      {i}. {rec}")
    
    print("\n" + "="*80)
    print("📝 NARRATIVAS GENERADAS - PRODUCCIÓN")
    print("="*80 + "\n")
    
    print("📄 RESUMEN EJECUTIVO (inicio del informe):")
    print("-" * 60)
    print(diagnostico_prod.resumen_ejecutivo)
    
    print("\n📄 DIAGNÓSTICO DETALLADO (final del informe):")
    print("-" * 60)
    print(diagnostico_prod.diagnostico_detallado)
    
    print(f"\n🗺️  Mapa generado: {diagnostico_prod.mapa_diagnostico_path}")
    
    # 5. Ejecutar diagnóstico - EVALUACIÓN
    logger.info("\n📋 Test 2: Informe de EVALUACIÓN")
    logger.info("-" * 60)
    
    diagnostico_eval = ejecutar_diagnostico_unificado(
        datos_indices={
            'ndvi': ndvi,
            'ndmi': ndmi,
            'savi': savi
        },
        geo_transform=geo_transform,
        area_parcela_ha=area_parcela_ha,
        output_dir=output_dir / 'evaluacion',
        tipo_informe='evaluacion',
        resolucion_m=10.0
    )
    
    print("\n" + "="*80)
    print("📝 NARRATIVAS GENERADAS - EVALUACIÓN")
    print("="*80 + "\n")
    
    print("📄 RESUMEN EJECUTIVO (inicio del informe):")
    print("-" * 60)
    print(diagnostico_eval.resumen_ejecutivo)
    
    print("\n📄 DIAGNÓSTICO DETALLADO (final del informe):")
    print("-" * 60)
    print(diagnostico_eval.diagnostico_detallado)
    
    print(f"\n🗺️  Mapa generado: {diagnostico_eval.mapa_diagnostico_path}")
    
    # 6. Validación final
    print("\n" + "="*80)
    print("✅ VALIDACIÓN FINAL")
    print("="*80 + "\n")
    
    validaciones = []
    
    # Check 1: Zonas detectadas
    if len(diagnostico_prod.zonas_criticas) >= 2:
        validaciones.append("✅ Se detectaron múltiples zonas críticas")
    else:
        validaciones.append("❌ No se detectaron suficientes zonas críticas")
    
    # Check 2: Zona prioritaria
    if diagnostico_prod.zona_prioritaria:
        validaciones.append("✅ Se identificó zona prioritaria")
    else:
        validaciones.append("❌ No se identificó zona prioritaria")
    
    # Check 3: Eficiencia calculada
    if 0 <= diagnostico_prod.eficiencia_lote <= 100:
        validaciones.append(f"✅ Eficiencia del lote válida: {diagnostico_prod.eficiencia_lote}%")
    else:
        validaciones.append(f"❌ Eficiencia del lote inválida: {diagnostico_prod.eficiencia_lote}%")
    
    # Check 4: Mapa generado
    if Path(diagnostico_prod.mapa_diagnostico_path).exists():
        validaciones.append(f"✅ Mapa diagnóstico generado correctamente")
    else:
        validaciones.append(f"❌ Mapa diagnóstico NO generado")
    
    # Check 5: Narrativas diferentes según tipo
    if diagnostico_prod.resumen_ejecutivo != diagnostico_eval.resumen_ejecutivo:
        validaciones.append("✅ Narrativas adaptativas funcionando (producción vs evaluación)")
    else:
        validaciones.append("❌ Narrativas no se adaptan según tipo de informe")
    
    # Check 6: Coordenadas geográficas válidas
    if diagnostico_prod.zona_prioritaria:
        lat, lon = diagnostico_prod.zona_prioritaria.centroide_geo
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            validaciones.append(f"✅ Coordenadas geográficas válidas: {lat:.6f}, {lon:.6f}")
        else:
            validaciones.append(f"❌ Coordenadas geográficas inválidas: {lat:.6f}, {lon:.6f}")
    
    for val in validaciones:
        print(val)
    
    # Resultado final
    exitos = sum(1 for v in validaciones if v.startswith("✅"))
    total = len(validaciones)
    
    print(f"\n{'='*80}")
    print(f"🎯 RESULTADO FINAL: {exitos}/{total} validaciones exitosas")
    print(f"{'='*80}\n")
    
    if exitos == total:
        print("🎉 ¡TEST COMPLETADO EXITOSAMENTE!")
        print(f"\n📁 Revisa los mapas generados en: {output_dir}")
        return True
    else:
        print("⚠️  Algunas validaciones fallaron. Revisar logs.")
        return False


if __name__ == '__main__':
    try:
        exito = test_cerebro_diagnostico()
        sys.exit(0 if exito else 1)
    except Exception as e:
        logger.error(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
