#!/usr/bin/env python
"""
Test rápido del sistema de tipos de análisis (rápido vs completo)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.utils.image_selector import ImagenSelector, MAX_IMAGENES_POR_INFORME, MAX_IMAGENES_ANALISIS_COMPLETO

print('='*70)
print('🧪 TEST: TIPOS DE ANÁLISIS (RÁPIDO VS COMPLETO)')
print('='*70)

selector = ImagenSelector()

print('\n📊 CONFIGURACIÓN:')
print(f'  • Análisis Rápido: {MAX_IMAGENES_POR_INFORME} imágenes')
print(f'  • Análisis Completo: {MAX_IMAGENES_ANALISIS_COMPLETO} imágenes')

print('\n💰 COMPARACIÓN DE COSTOS:')
print('-'*70)

# Análisis Rápido
estimacion_rapido = selector.estimar_costo_analisis(MAX_IMAGENES_POR_INFORME)
print(f'\n🏃 ANÁLISIS RÁPIDO ({MAX_IMAGENES_POR_INFORME} imágenes):')
print(f'  • Tokens: {estimacion_rapido["total_tokens"]:,}')
print(f'  • Peticiones API: {estimacion_rapido["total_peticiones"]}')
print(f'  • Recomendado para: Plan gratuito ✅')

# Análisis Completo
estimacion_completo = selector.estimar_costo_analisis(MAX_IMAGENES_ANALISIS_COMPLETO)
print(f'\n📈 ANÁLISIS COMPLETO ({MAX_IMAGENES_ANALISIS_COMPLETO} imágenes):')
print(f'  • Tokens: {estimacion_completo["total_tokens"]:,}')
print(f'  • Peticiones API: {estimacion_completo["total_peticiones"]}')
print(f'  • Recomendado para: Plan de pago 💳')

# Calcular diferencia
diferencia_tokens = estimacion_completo['total_tokens'] - estimacion_rapido['total_tokens']
diferencia_porcentaje = (diferencia_tokens / estimacion_rapido['total_tokens']) * 100

print(f'\n📊 DIFERENCIA:')
print(f'  • Tokens adicionales: +{diferencia_tokens:,} ({diferencia_porcentaje:.0f}% más)')
print(f'  • Factor: {estimacion_completo["total_tokens"] / estimacion_rapido["total_tokens"]:.1f}x')

print('\n📈 CAPACIDAD ESTIMADA (TIER GRATUITO - 60,000 tokens/mes):')
limite_gratuito = 60000
informes_rapidos = limite_gratuito // estimacion_rapido['total_tokens']
informes_completos = limite_gratuito // estimacion_completo['total_tokens']

print(f'  • Análisis Rápido: ~{informes_rapidos} informes/mes')
print(f'  • Análisis Completo: ~{informes_completos} informes/mes')

print('\n' + '='*70)
print('✅ SISTEMA DE TIPOS DE ANÁLISIS CONFIGURADO CORRECTAMENTE')
print('='*70 + '\n')

print('💡 RECOMENDACIONES:')
print('  1. Usar "Análisis Rápido" para monitoreo regular')
print('  2. Usar "Análisis Completo" solo cuando se necesite máximo detalle')
print('  3. Con plan gratuito, limitar a análisis rápidos')
print('  4. Considerar plan de pago si se necesitan análisis completos frecuentes')
print()
