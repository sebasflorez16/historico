#!/usr/bin/env python
"""
Script para crear umbrales iniciales en la base de datos
Estos valores reemplazan los que estaban hardcodeados en cerebro_diagnostico.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import UmbralesCultivo

def crear_umbrales_iniciales():
    """Crea los umbrales iniciales basados en los valores que estaban hardcodeados"""
    
    print("🌾 Creando umbrales iniciales para cultivos...")
    
    # Umbrales genéricos (fallback para cualquier cultivo)
    generico, created = UmbralesCultivo.objects.get_or_create(
        tipo_cultivo='generico',
        fase_fenologica='general',
        defaults={
            # NDVI
            'ndvi_critico_max': 0.30,
            'ndvi_moderado_max': 0.45,
            'ndvi_optimo_min': 0.70,
            # NDMI
            'ndmi_estres_severo_max': -0.08,
            'ndmi_estres_moderado_max': 0.08,
            'ndmi_optimo_min': 0.20,
            # SAVI
            'savi_exposicion_severa_max': 0.25,
            'savi_exposicion_moderada_max': 0.40,
            'savi_optimo_min': 0.60,
            # Penalización
            'factor_penalizacion_crisis': 80.0,
            'penalizacion_maxima': 50.0,
            # Área
            'area_minima_absoluta_ha': 0.05,
            'area_minima_porcentaje_lote': 0.5,
            # Metadata
            'fuente_bibliografia': 'Valores de referencia estándar para cultivos tropicales',
            'validado_por': 'Sistema AgroTech - Valores iniciales',
        }
    )
    if created:
        print(f"  ✅ Creado: {generico.tipo_cultivo} - {generico.fase_fenologica}")
    else:
        print(f"  ⏭️  Ya existe: {generico.tipo_cultivo} - {generico.fase_fenologica}")
    
    # Umbrales específicos para Arroz (fase general)
    arroz, created = UmbralesCultivo.objects.get_or_create(
        tipo_cultivo='Arroz',
        fase_fenologica='general',
        defaults={
            # NDVI - Arroz es sensible al exceso de agua
            'ndvi_critico_max': 0.28,
            'ndvi_moderado_max': 0.42,
            'ndvi_optimo_min': 0.68,
            # NDMI - Arroz tolera más humedad
            'ndmi_estres_severo_max': -0.05,
            'ndmi_estres_moderado_max': 0.10,
            'ndmi_optimo_min': 0.25,
            # SAVI
            'savi_exposicion_severa_max': 0.23,
            'savi_exposicion_moderada_max': 0.38,
            'savi_optimo_min': 0.58,
            # Penalización
            'factor_penalizacion_crisis': 80.0,
            'penalizacion_maxima': 50.0,
            # Área
            'area_minima_absoluta_ha': 0.05,
            'area_minima_porcentaje_lote': 0.5,
            # Metadata
            'fuente_bibliografia': 'FAO Rice Cultivation Guidelines 2024; Índices espectrales para arroz inundado',
            'validado_por': 'Sistema AgroTech - Adaptado para arroz',
        }
    )
    if created:
        print(f"  ✅ Creado: {arroz.tipo_cultivo} - {arroz.fase_fenologica}")
    else:
        print(f"  ⏭️  Ya existe: {arroz.tipo_cultivo} - {arroz.fase_fenologica}")
    
    # Umbrales específicos para Maíz (fase general)
    maiz, created = UmbralesCultivo.objects.get_or_create(
        tipo_cultivo='Maíz',
        fase_fenologica='general',
        defaults={
            # NDVI - Maíz tiene alto vigor vegetativo
            'ndvi_critico_max': 0.32,
            'ndvi_moderado_max': 0.48,
            'ndvi_optimo_min': 0.75,
            # NDMI - Maíz es sensible al estrés hídrico
            'ndmi_estres_severo_max': -0.10,
            'ndmi_estres_moderado_max': 0.05,
            'ndmi_optimo_min': 0.18,
            # SAVI
            'savi_exposicion_severa_max': 0.27,
            'savi_exposicion_moderada_max': 0.43,
            'savi_optimo_min': 0.65,
            # Penalización
            'factor_penalizacion_crisis': 80.0,
            'penalizacion_maxima': 50.0,
            # Área
            'area_minima_absoluta_ha': 0.05,
            'area_minima_porcentaje_lote': 0.5,
            # Metadata
            'fuente_bibliografia': 'USDA Corn Production Guide; Spectral indices for maize health monitoring',
            'validado_por': 'Sistema AgroTech - Adaptado para maíz',
        }
    )
    if created:
        print(f"  ✅ Creado: {maiz.tipo_cultivo} - {maiz.fase_fenologica}")
    else:
        print(f"  ⏭️  Ya existe: {maiz.tipo_cultivo} - {maiz.fase_fenologica}")
    
    # Umbrales específicos para Café (fase general)
    cafe, created = UmbralesCultivo.objects.get_or_create(
        tipo_cultivo='Café',
        fase_fenologica='general',
        defaults={
            # NDVI - Café es cultivo perenne con valores más estables
            'ndvi_critico_max': 0.35,
            'ndvi_moderado_max': 0.50,
            'ndvi_optimo_min': 0.72,
            # NDMI - Café requiere humedad constante
            'ndmi_estres_severo_max': -0.06,
            'ndmi_estres_moderado_max': 0.12,
            'ndmi_optimo_min': 0.22,
            # SAVI
            'savi_exposicion_severa_max': 0.30,
            'savi_exposicion_moderada_max': 0.45,
            'savi_optimo_min': 0.62,
            # Penalización
            'factor_penalizacion_crisis': 80.0,
            'penalizacion_maxima': 50.0,
            # Área
            'area_minima_absoluta_ha': 0.05,
            'area_minima_porcentaje_lote': 0.5,
            # Metadata
            'fuente_bibliografia': 'ICAFE Guía Técnica de Caficultura; Remote sensing for coffee plantations',
            'validado_por': 'Sistema AgroTech - Adaptado para café',
        }
    )
    if created:
        print(f"  ✅ Creado: {cafe.tipo_cultivo} - {cafe.fase_fenologica}")
    else:
        print(f"  ⏭️  Ya existe: {cafe.tipo_cultivo} - {cafe.fase_fenologica}")
    
    print("\n✨ Umbrales iniciales creados exitosamente!")
    print(f"📊 Total de configuraciones: {UmbralesCultivo.objects.count()}")

if __name__ == '__main__':
    crear_umbrales_iniciales()
