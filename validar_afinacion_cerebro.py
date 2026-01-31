#!/usr/bin/env python
"""
Script de Validación Rápida - Afinación del Cerebro de Diagnóstico
====================================================================

Valida que las 4 mejoras críticas estén correctamente implementadas:
1. Detección de cicatrices (umbral NDMI -0.08)
2. Narrativa de justificación (campo nuevo)
3. Sincronización matemática (formato 2 decimales)
4. Sensibilidad proactiva (detección temprana)

Autor: AgroTech Engineering Team
Fecha: 21 de Enero de 2026
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

import numpy as np
from informes.motor_analisis.cerebro_diagnostico import CerebroDiagnosticoUnificado
from pathlib import Path

print("=" * 80)
print("🧪 VALIDACIÓN DE AFINACIÓN DEL CEREBRO DE DIAGNÓSTICO")
print("=" * 80)
print()

# Test 1: Validar umbral NDMI actualizado
print("📋 TEST 1: Validar umbral NDMI para déficit hídrico")
print("-" * 80)
umbrales = CerebroDiagnosticoUnificado.UMBRALES_CRITICOS
ndmi_umbral = umbrales['deficit_hidrico_recurrente']['ndmi_max']

print(f"Umbral NDMI configurado: {ndmi_umbral}")
if ndmi_umbral == -0.08:
    print("✅ CORRECTO: Umbral configurado en -0.08 (Mejora 4 - Sensibilidad Proactiva)")
else:
    print(f"❌ ERROR: Umbral debería ser -0.08, pero está en {ndmi_umbral}")
print()

# Test 2: Validar formato de área de parcela (2 decimales)
print("📋 TEST 2: Validar formato de área de parcela")
print("-" * 80)
area_original = 61.42378
cerebro = CerebroDiagnosticoUnificado(area_parcela_ha=area_original)
area_guardada = cerebro.area_parcela_ha

print(f"Área original:  {area_original}")
print(f"Área guardada:  {area_guardada}")
print(f"Decimales:      {len(str(area_guardada).split('.')[1]) if '.' in str(area_guardada) else 0}")

if area_guardada == 61.42:
    print("✅ CORRECTO: Área redondeada a 2 decimales (Mejora 3 - Sincronización Matemática)")
else:
    print(f"❌ ERROR: Área debería ser 61.42, pero está en {area_guardada}")
print()

# Test 3: Validar que eficiencia nunca sea 100% si hay área afectada
print("📋 TEST 3: Validar regla de oro (eficiencia < 100% si área_afectada > 0)")
print("-" * 80)

# Crear arrays de prueba con vegetación casi perfecta
ndvi_test = np.full((100, 100), 0.85)  # NDVI muy alto
savi_test = np.full((100, 100), 0.75)  # SAVI muy alto

# Simular área afectada pequeña
area_afectada_test = 0.2  # 0.2 hectáreas

eficiencia_sin_area = cerebro._calcular_eficiencia_lote(ndvi_test, savi_test, area_afectada=0.0)
eficiencia_con_area = cerebro._calcular_eficiencia_lote(ndvi_test, savi_test, area_afectada=area_afectada_test)

print(f"Eficiencia sin área afectada:  {eficiencia_sin_area}%")
print(f"Eficiencia con área afectada:  {eficiencia_con_area}%")

if eficiencia_con_area < 100.0 and area_afectada_test > 0:
    print("✅ CORRECTO: Eficiencia ajustada a < 100% (Mejora 3 - Regla de Oro)")
else:
    print(f"❌ ERROR: Eficiencia debería ser < 100% cuando hay área afectada")
print()

# Test 4: Validar que la función de narrativa existe
print("📋 TEST 4: Validar existencia de función de narrativa")
print("-" * 80)

if hasattr(cerebro, '_generar_justificacion_narrativa'):
    print("✅ CORRECTO: Función _generar_justificacion_narrativa() existe")
    
    # Probar la función
    desglose_test = {'critica': 0.15, 'moderada': 0.05, 'leve': 0.00}
    narrativa = cerebro._generar_justificacion_narrativa(
        eficiencia=98.3,
        pct_afectado=1.7,
        desglose_severidad=desglose_test,
        zona_prioritaria=None
    )
    
    print(f"\nNarrativa generada (ejemplo):")
    print(f"  {narrativa[:150]}...")
    
    if len(narrativa) > 50:
        print("✅ CORRECTO: Narrativa generada exitosamente (Mejora 2)")
    else:
        print("❌ ERROR: Narrativa muy corta o vacía")
else:
    print("❌ ERROR: Función _generar_justificacion_narrativa() NO existe")
print()

# Test 5: Validar redondeo en desglose de severidad
print("📋 TEST 5: Validar redondeo a 2 decimales en desglose")
print("-" * 80)

# Crear datos de prueba para desglose
from informes.motor_analisis.cerebro_diagnostico import ZonaCritica
zona_test = ZonaCritica(
    tipo_diagnostico='deficit_hidrico_recurrente',
    etiqueta_comercial='Déficit Hídrico',
    severidad=0.8,
    area_hectareas=0.123456,
    area_pixeles=123,
    centroide_pixel=(50, 50),
    centroide_geo=(4.5, -75.5),
    bbox=(0, 0, 100, 100),
    valores_indices={'ndvi': 0.3, 'ndmi': -0.1, 'savi': 0.25},
    confianza=0.85,
    recomendaciones=[]
)

zonas_por_severidad_test = {
    'critica': [zona_test],
    'moderada': [],
    'leve': []
}

desglose = cerebro._calcular_desglose_severidad_union(
    zonas_por_severidad_test,
    shape=(100, 100)
)

print(f"Área crítica calculada: {desglose['critica']} ha")
print(f"Decimales: {len(str(desglose['critica']).split('.')[1]) if '.' in str(desglose['critica']) else 0}")

# Verificar que todas las áreas tienen 2 decimales
todas_con_2_decimales = all(
    len(str(valor).split('.')[1]) == 2 if '.' in str(valor) and valor > 0 else True
    for valor in desglose.values()
)

if todas_con_2_decimales:
    print("✅ CORRECTO: Todas las áreas con 2 decimales (Mejora 3)")
else:
    print("❌ ERROR: Algunas áreas no tienen 2 decimales")
print()

# RESUMEN FINAL
print("=" * 80)
print("📊 RESUMEN DE VALIDACIÓN")
print("=" * 80)

tests_pasados = 0
total_tests = 5

if ndmi_umbral == -0.08:
    tests_pasados += 1
if area_guardada == 61.42:
    tests_pasados += 1
if eficiencia_con_area < 100.0:
    tests_pasados += 1
if hasattr(cerebro, '_generar_justificacion_narrativa'):
    tests_pasados += 1
if todas_con_2_decimales:
    tests_pasados += 1

print(f"Tests pasados: {tests_pasados}/{total_tests}")
print(f"Porcentaje:    {(tests_pasados/total_tests)*100:.1f}%")
print()

if tests_pasados == total_tests:
    print("✅ ¡TODAS LAS MEJORAS IMPLEMENTADAS CORRECTAMENTE!")
    print()
    print("Próximos pasos:")
    print("  1. Generar PDF de prueba con parcela real")
    print("  2. Validar visualmente el formato y narrativa")
    print("  3. Verificar que justificacion_narrativa aparezca en PDF")
    print()
    sys.exit(0)
else:
    print(f"⚠️  Hay {total_tests - tests_pasados} mejora(s) con problemas")
    print("   Revise los detalles arriba para corregir")
    print()
    sys.exit(1)
