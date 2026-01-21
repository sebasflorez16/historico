#!/usr/bin/env python
"""
Test de Validación Completa de Correcciones Matemáticas
=======================================================

Script que valida todas las correcciones aplicadas al sistema de diagnóstico:
1. Área afectada <= Área total (SIEMPRE)
2. KPIs coherentes (Eficiencia = 100 - Porcentaje Afectado)
3. Desglose suma al total
4. Umbrales realistas (no 100% crítico)
5. Formato consistente (1 decimal)

Uso:
    python test_validacion_completa_correcciones.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

import numpy as np
from pathlib import Path
from django.conf import settings

# Imports del sistema
from informes.models import Parcela, IndiceMensual
from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
from informes.motor_analisis.kpis_unificados import KPIsUnificados


def test_area_afectada_no_supera_total():
    """
    Test Crítico 1: Área afectada NUNCA debe superar área total
    """
    print("\n" + "="*70)
    print("🧪 TEST 1: Validar que Área Afectada <= Área Total")
    print("="*70)
    
    # Crear datos simulados con condiciones críticas (peor caso)
    size = (256, 256)
    
    # Caso extremo: Todo el lote con índices muy bajos
    ndvi = np.full(size, 0.2)  # NDVI muy bajo en todo el lote
    ndmi = np.full(size, -0.1)  # NDMI negativo (déficit hídrico)
    savi = np.full(size, 0.15)  # SAVI muy bajo
    
    datos_indices = {
        'ndvi': ndvi,
        'ndmi': ndmi,
        'savi': savi
    }
    
    # Transformación geográfica simple
    geo_transform = (-58.0, 0.0001, 0, -34.0, 0, -0.0001)
    area_parcela = 10.0  # 10 hectáreas
    
    output_dir = Path(settings.MEDIA_ROOT) / 'test_diagnosticos'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ejecutar diagnóstico
    diagnostico = ejecutar_diagnostico_unificado(
        datos_indices=datos_indices,
        geo_transform=geo_transform,
        area_parcela_ha=area_parcela,
        output_dir=str(output_dir),
        tipo_informe='produccion'
    )
    
    # Validar
    area_afectada = diagnostico.area_afectada_total
    
    print(f"\n📊 Resultados:")
    print(f"   Área total: {area_parcela:.1f} ha")
    print(f"   Área afectada: {area_afectada:.1f} ha")
    
    if area_afectada <= area_parcela:
        print(f"   ✅ PASÓ: Área afectada ({area_afectada:.1f}) <= Área total ({area_parcela:.1f})")
        return True
    else:
        print(f"   ❌ FALLÓ: Área afectada ({area_afectada:.1f}) > Área total ({area_parcela:.1f})")
        return False


def test_kpis_coherentes():
    """
    Test Crítico 2: Validar coherencia de KPIs
    """
    print("\n" + "="*70)
    print("🧪 TEST 2: Validar Coherencia de KPIs")
    print("="*70)
    
    # Usar Parcela #2 de la base de datos
    try:
        parcela = Parcela.objects.get(id=2)
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')[:1]
        
        if not indices:
            print("⚠️  No hay datos de índices para Parcela #2")
            return None
        
        indice = indices[0]
        
        # Crear arrays simulados
        size = (256, 256)
        ndvi = np.random.normal(indice.ndvi_promedio, 0.08, size)
        ndmi = np.random.normal(indice.ndmi_promedio, 0.08, size)
        savi = np.random.normal(indice.savi_promedio, 0.08, size)
        
        # Agregar zonas con problemas
        ndvi[50:100, 50:100] *= 0.6  # Zona con bajo NDVI
        ndmi[120:170, 120:170] *= 0.5  # Zona con bajo NDMI
        
        datos_indices = {'ndvi': ndvi, 'ndmi': ndmi, 'savi': savi}
        
        # Bbox de la parcela
        if parcela.geometria:
            bbox = parcela.geometria.extent
        else:
            bbox = (-58.5, -34.5, -58.4, -34.4)
        
        geo_transform = (
            bbox[0],
            (bbox[2] - bbox[0]) / 256,
            0,
            bbox[3],
            0,
            -(bbox[3] - bbox[1]) / 256
        )
        
        output_dir = Path(settings.MEDIA_ROOT) / 'test_diagnosticos'
        
        # Ejecutar diagnóstico
        diagnostico = ejecutar_diagnostico_unificado(
            datos_indices=datos_indices,
            geo_transform=geo_transform,
            area_parcela_ha=parcela.area_hectareas,
            output_dir=str(output_dir),
            tipo_informe='produccion'
        )
        
        # Crear KPIs Unificados
        kpis = KPIsUnificados.desde_diagnostico(
            diagnostico=diagnostico,
            area_total_ha=parcela.area_hectareas
        )
        
        print(f"\n📊 KPIs Calculados:")
        print(f"   Área total: {kpis.area_total_ha:.1f} ha")
        print(f"   Área afectada: {kpis.area_afectada_ha:.1f} ha")
        print(f"   Porcentaje afectado: {kpis.porcentaje_afectado:.1f}%")
        print(f"   Eficiencia: {kpis.eficiencia:.1f}%")
        print(f"   Área sana: {kpis.obtener_area_sana():.1f} ha")
        
        print(f"\n   Desglose:")
        print(f"     🔴 Crítica: {kpis.area_critica_ha:.1f} ha ({kpis.porcentaje_critico:.1f}%)")
        print(f"     🟠 Moderada: {kpis.area_moderada_ha:.1f} ha ({kpis.porcentaje_moderado:.1f}%)")
        print(f"     🟡 Leve: {kpis.area_leve_ha:.1f} ha ({kpis.porcentaje_leve:.1f}%)")
        
        # Validar coherencia
        try:
            kpis.validar_coherencia(tolerancia=0.2)
            print(f"\n   ✅ PASÓ: Todos los KPIs son coherentes")
            return True
        except AssertionError as e:
            print(f"\n   ❌ FALLÓ: {str(e)}")
            return False
            
    except Parcela.DoesNotExist:
        print("⚠️  Parcela #2 no existe en la base de datos")
        return None
    except Exception as e:
        print(f"❌ Error ejecutando test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_desglose_suma_al_total():
    """
    Test Crítico 3: Desglose de severidad debe sumar al total afectado
    """
    print("\n" + "="*70)
    print("🧪 TEST 3: Validar Desglose de Severidad")
    print("="*70)
    
    # Datos con variedad de severidades
    size = (256, 256)
    ndvi = np.random.uniform(0.1, 0.7, size)
    ndmi = np.random.uniform(-0.2, 0.4, size)
    savi = np.random.uniform(0.1, 0.6, size)
    
    # Crear 3 zonas con diferentes severidades
    # Zona crítica (esquina superior izquierda)
    ndvi[0:80, 0:80] = 0.15
    ndmi[0:80, 0:80] = -0.1
    savi[0:80, 0:80] = 0.10
    
    # Zona moderada (esquina superior derecha)
    ndvi[0:80, 176:256] = 0.28
    ndmi[0:80, 176:256] = -0.02
    savi[0:80, 176:256] = 0.22
    
    # Zona leve (esquina inferior izquierda)
    ndvi[176:256, 0:80] = 0.38
    ndmi[176:256, 0:80] = 0.08
    savi[176:256, 0:80] = 0.32
    
    datos_indices = {'ndvi': ndvi, 'ndmi': ndmi, 'savi': savi}
    geo_transform = (-58.0, 0.0001, 0, -34.0, 0, -0.0001)
    area_parcela = 12.0
    
    output_dir = Path(settings.MEDIA_ROOT) / 'test_diagnosticos'
    
    diagnostico = ejecutar_diagnostico_unificado(
        datos_indices=datos_indices,
        geo_transform=geo_transform,
        area_parcela_ha=area_parcela,
        output_dir=str(output_dir),
        tipo_informe='produccion'
    )
    
    # Validar desglose
    desglose = diagnostico.desglose_severidad
    total_desglose = desglose['critica'] + desglose['moderada'] + desglose['leve']
    area_afectada = diagnostico.area_afectada_total
    
    print(f"\n📊 Desglose de Severidad:")
    print(f"   🔴 Crítica: {desglose['critica']:.1f} ha")
    print(f"   🟠 Moderada: {desglose['moderada']:.1f} ha")
    print(f"   🟡 Leve: {desglose['leve']:.1f} ha")
    print(f"   📏 Total desglose: {total_desglose:.1f} ha")
    print(f"   📏 Área afectada: {area_afectada:.1f} ha")
    
    diferencia = abs(total_desglose - area_afectada)
    
    if diferencia < 0.2:  # Tolerancia 0.2 ha
        print(f"   ✅ PASÓ: Desglose coherente (diferencia {diferencia:.2f} ha)")
        return True
    else:
        print(f"   ❌ FALLÓ: Diferencia de {diferencia:.2f} ha supera tolerancia")
        return False


def test_umbrales_realistas():
    """
    Test Crítico 4: Umbrales no deben clasificar 100% como crítico
    """
    print("\n" + "="*70)
    print("🧪 TEST 4: Validar Umbrales Realistas")
    print("="*70)
    
    # Lote con condiciones NORMALES de producción
    size = (256, 256)
    ndvi = np.random.normal(0.55, 0.10, size)  # NDVI promedio normal
    ndmi = np.random.normal(0.25, 0.08, size)  # NDMI promedio normal
    savi = np.random.normal(0.50, 0.10, size)  # SAVI promedio normal
    
    # Clip a rangos válidos
    ndvi = np.clip(ndvi, -1, 1)
    ndmi = np.clip(ndmi, -1, 1)
    savi = np.clip(savi, -1, 1)
    
    datos_indices = {'ndvi': ndvi, 'ndmi': ndmi, 'savi': savi}
    geo_transform = (-58.0, 0.0001, 0, -34.0, 0, -0.0001)
    area_parcela = 10.0
    
    output_dir = Path(settings.MEDIA_ROOT) / 'test_diagnosticos'
    
    diagnostico = ejecutar_diagnostico_unificado(
        datos_indices=datos_indices,
        geo_transform=geo_transform,
        area_parcela_ha=area_parcela,
        output_dir=str(output_dir),
        tipo_informe='produccion'
    )
    
    eficiencia = diagnostico.eficiencia_lote
    area_afectada = diagnostico.area_afectada_total
    porcentaje_afectado = (area_afectada / area_parcela) * 100
    
    print(f"\n📊 Resultados para Lote Normal:")
    print(f"   Eficiencia: {eficiencia:.1f}%")
    print(f"   Área afectada: {area_afectada:.1f} ha ({porcentaje_afectado:.1f}%)")
    
    # Un lote normal NO debería tener más del 50% afectado
    if porcentaje_afectado < 50:
        print(f"   ✅ PASÓ: Umbrales realistas (< 50% afectado en lote normal)")
        return True
    else:
        print(f"   ❌ FALLÓ: {porcentaje_afectado:.1f}% afectado es excesivo para lote normal")
        return False


def test_formato_consistente():
    """
    Test Crítico 5: Validar formato consistente (1 decimal)
    """
    print("\n" + "="*70)
    print("🧪 TEST 5: Validar Formato Consistente (1 decimal)")
    print("="*70)
    
    # Crear KPIs de prueba
    from informes.motor_analisis.cerebro_diagnostico import DiagnosticoUnificado
    from datetime import datetime
    
    # Mock de diagnóstico
    class MockDiagnostico:
        area_afectada_total = 8.234567
        eficiencia_lote = 45.678901
        desglose_severidad = {
            'critica': 3.456789,
            'moderada': 2.345678,
            'leve': 2.432100
        }
        zonas_por_severidad = {
            'critica': [],
            'moderada': [],
            'leve': []
        }
    
    mock = MockDiagnostico()
    
    kpis = KPIsUnificados.desde_diagnostico(
        diagnostico=mock,
        area_total_ha=10.0
    )
    
    print(f"\n📊 Formatos Generados:")
    print(f"   Área total: {kpis.formatear_area_total()}")
    print(f"   Área afectada: {kpis.formatear_area_afectada()}")
    print(f"   Porcentaje afectado: {kpis.formatear_porcentaje_afectado()}")
    print(f"   Eficiencia: {kpis.formatear_eficiencia()}")
    print(f"   Área crítica: {kpis.formatear_area_critica()}")
    print(f"   Área moderada: {kpis.formatear_area_moderada()}")
    print(f"   Área leve: {kpis.formatear_area_leve()}")
    
    # Verificar que todos tienen 1 decimal
    formatos = [
        kpis.formatear_area_total(),
        kpis.formatear_area_afectada(),
        kpis.formatear_porcentaje_afectado(),
        kpis.formatear_eficiencia(),
        kpis.formatear_area_critica(),
        kpis.formatear_area_moderada(),
        kpis.formatear_area_leve()
    ]
    
    # Validar formato X.X
    import re
    patron = r'\d+\.\d ha|\d+\.\d%'
    
    todos_correctos = all(re.match(patron, fmt) for fmt in formatos)
    
    if todos_correctos:
        print(f"   ✅ PASÓ: Todos los formatos usan 1 decimal")
        return True
    else:
        print(f"   ❌ FALLÓ: Formatos inconsistentes detectados")
        return False


def ejecutar_suite_completa():
    """
    Ejecuta todos los tests y genera reporte
    """
    print("\n" + "🚀" + "="*68 + "🚀")
    print("   SUITE COMPLETA DE VALIDACIÓN - Correcciones Matemáticas")
    print("🚀" + "="*68 + "🚀")
    
    resultados = {
        'Test 1: Área Afectada <= Total': test_area_afectada_no_supera_total(),
        'Test 2: KPIs Coherentes': test_kpis_coherentes(),
        'Test 3: Desglose Suma al Total': test_desglose_suma_al_total(),
        'Test 4: Umbrales Realistas': test_umbrales_realistas(),
        'Test 5: Formato Consistente': test_formato_consistente()
    }
    
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)
    
    total = len(resultados)
    pasados = sum(1 for r in resultados.values() if r is True)
    fallidos = sum(1 for r in resultados.values() if r is False)
    omitidos = sum(1 for r in resultados.values() if r is None)
    
    for nombre, resultado in resultados.items():
        icono = "✅" if resultado is True else ("❌" if resultado is False else "⚠️ ")
        estado = "PASÓ" if resultado is True else ("FALLÓ" if resultado is False else "OMITIDO")
        print(f"{icono} {nombre}: {estado}")
    
    print(f"\n{'='*70}")
    print(f"Total de tests: {total}")
    print(f"✅ Pasados: {pasados}")
    print(f"❌ Fallidos: {fallidos}")
    print(f"⚠️  Omitidos: {omitidos}")
    
    tasa_exito = (pasados / (total - omitidos) * 100) if (total - omitidos) > 0 else 0
    print(f"\n🎯 Tasa de éxito: {tasa_exito:.1f}%")
    
    if fallidos == 0 and pasados > 0:
        print(f"\n🎉 ¡TODOS LOS TESTS PASARON! Sistema validado correctamente.")
    elif fallidos > 0:
        print(f"\n⚠️  Hay {fallidos} test(s) fallido(s). Revisar implementación.")
    
    return tasa_exito == 100.0


if __name__ == '__main__':
    try:
        exito = ejecutar_suite_completa()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ Error crítico ejecutando suite: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
