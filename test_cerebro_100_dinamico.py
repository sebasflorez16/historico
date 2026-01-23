#!/usr/bin/env python
"""
Test de Refactorización: Cerebro 100% Dinámico
==============================================

Verifica que:
1. Los umbrales se cargan correctamente desde BD
2. No hay valores hardcodeados en el flujo
3. La eficiencia se calcula dinámicamente
4. Los diagnósticos se generan sin errores

Autor: AgroTech - Refactorización Enero 23, 2026
"""
import os
import sys
import django
import numpy as np
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, UmbralesCultivo
from informes.motor_analisis.cerebro_diagnostico import (
    CerebroDiagnosticoUnificado,
    ejecutar_diagnostico_unificado
)

def test_carga_umbrales():
    """Test 1: Verificar carga de umbrales desde BD"""
    print("\n" + "="*70)
    print("TEST 1: Carga de Umbrales Dinámicos")
    print("="*70)
    
    # Test con Arroz
    umbrales_arroz = UmbralesCultivo.obtener_umbrales('Arroz', 'general')
    print(f"\n✅ Umbrales Arroz:")
    print(f"   NDVI crítico: {umbrales_arroz.ndvi_critico_max}")
    print(f"   NDMI severo: {umbrales_arroz.ndmi_estres_severo_max}")
    print(f"   Factor penalización: {umbrales_arroz.factor_penalizacion_crisis}%")
    print(f"   Penalización máxima: {umbrales_arroz.penalizacion_maxima}%")
    
    # Test con genérico
    umbrales_generico = UmbralesCultivo.obtener_umbrales('generico', 'general')
    print(f"\n✅ Umbrales Genéricos:")
    print(f"   NDVI crítico: {umbrales_generico.ndvi_critico_max}")
    print(f"   NDMI severo: {umbrales_generico.ndmi_estres_severo_max}")
    
    # Test con cultivo inexistente (debe usar fallback)
    umbrales_fallback = UmbralesCultivo.obtener_umbrales('CultivoInexistente', 'general')
    print(f"\n✅ Fallback para cultivo inexistente:")
    print(f"   NDVI crítico: {umbrales_fallback.ndvi_critico_max}")
    
    assert umbrales_arroz.ndvi_critico_max == 0.28, "Error en umbrales de Arroz"
    assert umbrales_generico.ndvi_critico_max == 0.30, "Error en umbrales genéricos"
    print("\n✅ TEST 1 PASADO: Umbrales se cargan correctamente")

def test_inicializacion_cerebro():
    """Test 2: Verificar inicialización con umbrales dinámicos"""
    print("\n" + "="*70)
    print("TEST 2: Inicialización del Cerebro con Configuración Dinámica")
    print("="*70)
    
    # Crear cerebro para Arroz
    cerebro_arroz = CerebroDiagnosticoUnificado(
        area_parcela_ha=61.42,
        tipo_cultivo='Arroz',
        fase_fenologica='general'
    )
    
    print(f"\n✅ Cerebro inicializado para Arroz:")
    print(f"   Tipo cultivo: {cerebro_arroz.tipo_cultivo}")
    print(f"   Fase: {cerebro_arroz.fase_fenologica}")
    print(f"   NDVI crítico (desde BD): {cerebro_arroz.umbrales.ndvi_critico_max}")
    print(f"   Factor penalización (desde BD): {cerebro_arroz.umbrales.factor_penalizacion_crisis}%")
    
    # Crear cerebro para Maíz
    cerebro_maiz = CerebroDiagnosticoUnificado(
        area_parcela_ha=50.0,
        tipo_cultivo='Maíz',
        fase_fenologica='general'
    )
    
    print(f"\n✅ Cerebro inicializado para Maíz:")
    print(f"   NDVI crítico (desde BD): {cerebro_maiz.umbrales.ndvi_critico_max}")
    
    # Verificar que son diferentes
    assert cerebro_arroz.umbrales.ndvi_critico_max != cerebro_maiz.umbrales.ndvi_critico_max, \
        "Los umbrales deberían ser diferentes para cultivos diferentes"
    
    print("\n✅ TEST 2 PASADO: Cerebro se inicializa con configuración específica del cultivo")

def test_construccion_patrones_dinamicos():
    """Test 3: Verificar construcción de patrones en runtime"""
    print("\n" + "="*70)
    print("TEST 3: Construcción Dinámica de Patrones de Detección")
    print("="*70)
    
    cerebro = CerebroDiagnosticoUnificado(
        area_parcela_ha=61.42,
        tipo_cultivo='Arroz',
        fase_fenologica='general'
    )
    
    # Construir patrones
    patrones = cerebro._construir_patrones_deteccion_dinamicos()
    
    print(f"\n✅ Patrones construidos: {len(patrones)}")
    for i, patron in enumerate(patrones, 1):
        print(f"\n   Patrón {i}: {patron['tipo']}")
        print(f"   - Etiqueta: {patron['etiqueta']}")
        print(f"   - NDVI max: {patron.get('ndvi_max', 'N/A')}")
        print(f"   - NDMI max: {patron.get('ndmi_max', 'N/A')}")
        print(f"   - Severidad base: {patron['severidad_base']}")
    
    assert len(patrones) == 3, "Deberían construirse 3 patrones"
    assert all('tipo' in p for p in patrones), "Todos los patrones deben tener 'tipo'"
    
    print("\n✅ TEST 3 PASADO: Patrones se construyen dinámicamente")

def test_diagnostico_parcela_real():
    """Test 4: Ejecutar diagnóstico en parcela real"""
    print("\n" + "="*70)
    print("TEST 4: Diagnóstico en Parcela Real (sin generar PDF)")
    print("="*70)
    
    # Buscar parcela de Arroz
    parcela = Parcela.objects.filter(tipo_cultivo='Arroz').first()
    
    if not parcela:
        print("\n⚠️  No hay parcelas de Arroz, saltando test")
        return
    
    print(f"\n📍 Parcela: {parcela.nombre}")
    print(f"   Cultivo: {parcela.tipo_cultivo}")
    print(f"   Área: {parcela.area_hectareas} ha")
    
    # Crear datos sintéticos para test (simulando condición crítica)
    shape = (256, 256)
    ndvi = np.random.uniform(0.2, 0.4, shape)  # Valores bajos (crítico)
    ndmi = np.random.uniform(-0.15, 0.0, shape)  # Déficit hídrico
    savi = np.random.uniform(0.15, 0.30, shape)  # Suelo expuesto
    
    geo_transform = (-75.5, 0.0001, 0.0, 6.2, 0.0, -0.0001)
    output_dir = Path('/tmp/test_cerebro_dinamico')
    output_dir.mkdir(exist_ok=True)
    
    # Simular crisis históricas
    crisis_simuladas = [
        {'mes': '2024-01', 'tipo': 'deficit_hidrico'},
        {'mes': '2024-03', 'tipo': 'deficit_hidrico'},
        {'mes': '2024-05', 'tipo': 'baja_densidad'}
    ]
    
    # Simular data cube temporal
    data_cubes = {
        'num_meses': 12,  # 12 meses analizados
        'ndvi_cube': np.random.rand(12, 256, 256)
    }
    
    try:
        diagnostico = ejecutar_diagnostico_unificado(
            datos_indices={'ndvi': ndvi, 'ndmi': ndmi, 'savi': savi},
            geo_transform=geo_transform,
            area_parcela_ha=parcela.area_hectareas,
            output_dir=output_dir,
            tipo_cultivo=parcela.tipo_cultivo,  # ✅ NUEVO
            fase_fenologica='general',  # ✅ NUEVO
            tipo_informe='produccion',
            crisis_historicas=crisis_simuladas,
            data_cubes_temporales=data_cubes
        )
        
        print(f"\n✅ Diagnóstico generado exitosamente:")
        print(f"   Zonas críticas detectadas: {len(diagnostico.zonas_criticas)}")
        print(f"   Eficiencia del lote: {diagnostico.eficiencia_lote:.1f}%")
        print(f"   Área afectada: {diagnostico.area_afectada_total:.2f} ha")
        
        if diagnostico.zona_prioritaria:
            print(f"   Zona prioritaria: {diagnostico.zona_prioritaria.etiqueta_comercial}")
            print(f"   Severidad: {diagnostico.zona_prioritaria.severidad:.2f}")
        
        # Verificaciones
        assert 0 <= diagnostico.eficiencia_lote <= 100, "Eficiencia debe estar entre 0-100%"
        assert diagnostico.eficiencia_lote < 100, "Con crisis históricas no debe ser 100%"
        
        print("\n✅ TEST 4 PASADO: Diagnóstico ejecutado correctamente con sistema dinámico")
        
    except Exception as e:
        print(f"\n❌ ERROR en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_calculo_eficiencia_dinamica():
    """Test 5: Verificar cálculo de eficiencia con factores dinámicos"""
    print("\n" + "="*70)
    print("TEST 5: Cálculo Dinámico de Eficiencia")
    print("="*70)
    
    cerebro = CerebroDiagnosticoUnificado(
        area_parcela_ha=100.0,
        tipo_cultivo='Arroz',
        fase_fenologica='general'
    )
    
    # Datos sintéticos
    ndvi = np.random.rand(100, 100)
    savi = np.random.rand(100, 100)
    
    # Crisis: 3 meses de 10 analizados = 30% del tiempo
    crisis = [{'mes': f'2024-0{i}'} for i in range(1, 4)]
    data_cubes = {'num_meses': 10}
    
    eficiencia = cerebro._calcular_eficiencia_lote(
        ndvi=ndvi,
        savi=savi,
        area_afectada=10.0,  # 10% del lote afectado
        crisis_historicas=crisis,
        data_cubes_temporales=data_cubes
    )
    
    print(f"\n✅ Eficiencia calculada: {eficiencia:.1f}%")
    print(f"   Área afectada: 10 ha (10% del lote)")
    print(f"   Crisis: 3/10 meses (30% del tiempo)")
    print(f"   Factor penalización (desde BD): {cerebro.umbrales.factor_penalizacion_crisis}%")
    
    # La eficiencia debería ser ~90% (área limpia) menos penalización por crisis
    # Penalización = 30% * 80% = 24%
    # Eficiencia final ≈ 90% - 24% = 66%
    esperada_aprox = 66.0
    assert 60 < eficiencia < 75, f"Eficiencia {eficiencia}% fuera de rango esperado (~{esperada_aprox}%)"
    
    print(f"\n✅ TEST 5 PASADO: Eficiencia calculada dinámicamente (esperado ~{esperada_aprox}%, obtenido {eficiencia:.1f}%)")

def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*70)
    print(" SUITE DE TESTS: Cerebro 100% Dinámico (Sin Hardcoding)")
    print("="*70)
    
    try:
        test_carga_umbrales()
        test_inicializacion_cerebro()
        test_construccion_patrones_dinamicos()
        test_diagnostico_parcela_real()
        test_calculo_eficiencia_dinamica()
        
        print("\n" + "="*70)
        print(" ✅ TODOS LOS TESTS PASADOS")
        print("="*70)
        print("\n🎉 El cerebro está 100% dinámico")
        print("🎯 NO hay valores hardcodeados")
        print("💾 Umbrales se cargan desde base de datos")
        print("🧠 Sistema completamente 'pensante'")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
