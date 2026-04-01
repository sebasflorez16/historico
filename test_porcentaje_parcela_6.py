#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test del porcentaje de salud de la parcela ID=6
Verifica que el cálculo del Índice de Salud del Lote sea correcto
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.motor_analisis.cerebro_diagnostico import CerebroDiagnosticoUnificado
import numpy as np


def test_porcentaje_parcela_6():
    """
    Testea el cálculo del Índice de Salud del Lote para una parcela
    """
    print("=" * 70)
    print("🧪 TEST: Verificación del Índice de Salud del Lote")
    print("=" * 70)
    
    try:
        # 1. Obtener la parcela (probamos con ID=1)
        parcela = Parcela.objects.get(id=1)
        print(f"\n✅ Parcela encontrada: {parcela.nombre}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        
        # 2. Obtener todos los índices mensuales
        indices = IndiceMensual.objects.filter(
            parcela=parcela
        ).order_by('fecha_imagen')
        
        print(f"\n📊 Índices mensuales disponibles: {indices.count()}")
        
        if indices.count() == 0:
            print("❌ No hay datos de índices mensuales para esta parcela")
            return
        
        # 3. Mostrar datos de los índices
        print("\n📈 DATOS DE ÍNDICES MES A MES:")
        print("-" * 70)
        crisis_detectadas = []
        
        for idx, indice in enumerate(indices, 1):
            ndvi = indice.ndvi_promedio
            savi = indice.savi_promedio
            ndmi = indice.ndmi_promedio
            
            # Validar valores None
            if ndvi is None or ndmi is None or savi is None:
                print(f"Mes {idx:2d} | Fecha: {indice.fecha_imagen} | ⚠️ Datos incompletos (valores None)")
                continue
            
            # Detección de crisis (según la lógica del sistema)
            es_crisis = ndvi < 0.45 or ndmi < 0.0
            
            status = "⚠️ CRISIS" if es_crisis else "✅ Normal"
            
            print(f"Mes {idx:2d} | Fecha: {indice.fecha_imagen} | "
                  f"NDVI: {ndvi:.3f} | SAVI: {savi:.3f} | NDMI: {ndmi:.3f} | {status}")
            
            if es_crisis:
                crisis_detectadas.append({
                    'mes': idx,
                    'fecha': indice.fecha_imagen,
                    'ndvi': ndvi,
                    'ndmi': ndmi
                })
        
        # 4. Ejecutar diagnóstico con CerebroDiagnosticoUnificado
        print("\n🧠 EJECUTANDO CEREBRO DIAGNÓSTICO...")
        print("-" * 70)
        
        cerebro = CerebroDiagnosticoUnificado(area_parcela_ha=parcela.area_hectareas)
        
        # Obtener el último índice para triangulación
        ultimo_indice = indices.last()
        
        resultado = cerebro.triangular_y_diagnosticar(
            ndvi=ultimo_indice.ndvi_promedio,
            savi=ultimo_indice.savi_promedio,
            ndmi=ultimo_indice.ndmi_promedio,
            parcela=parcela,
            contexto_temporal=None  # El cerebro debería usar los índices históricos
        )
        
        # 5. Mostrar resultados
        print("\n📊 RESULTADOS DEL DIAGNÓSTICO:")
        print("-" * 70)
        print(f"Estado del Lote: {resultado.get('estado', 'N/A')}")
        print(f"Índice de Salud: {resultado.get('indice_salud', 'N/A')}")
        print(f"Eficiencia del Lote: {resultado.get('eficiencia_lote', 'N/A'):.1f}%")
        print(f"Nivel de Confianza: {resultado.get('nivel_confianza', 'N/A')}")
        
        # 6. Análisis de crisis detectadas
        print(f"\n⚠️ CRISIS DETECTADAS: {len(crisis_detectadas)}")
        if crisis_detectadas:
            for crisis in crisis_detectadas:
                print(f"   - Mes {crisis['mes']} ({crisis['fecha']}): "
                      f"NDVI={crisis['ndvi']:.3f}, NDMI={crisis['ndmi']:.3f}")
        
        # 7. Calcular penalización histórica esperada
        total_meses = indices.count()
        meses_crisis = len(crisis_detectadas)
        
        if meses_crisis > 0:
            penalizacion_esperada = (meses_crisis / total_meses) * 15.0
            print(f"\n📉 ANÁLISIS DE PENALIZACIÓN HISTÓRICA:")
            print(f"   Total de meses analizados: {total_meses}")
            print(f"   Meses en crisis: {meses_crisis}")
            print(f"   Penalización esperada: -{penalizacion_esperada:.1f}%")
            print(f"   Eficiencia esperada: ~{100 - penalizacion_esperada:.1f}%")
        
        # 8. Comparar con el valor mostrado en el PDF (37%)
        porcentaje_pdf = 37.0
        eficiencia_calculada = resultado.get('eficiencia_lote', 0)
        
        print("\n🎯 COMPARACIÓN CON PDF:")
        print(f"   Porcentaje mostrado en PDF: {porcentaje_pdf}%")
        print(f"   Eficiencia calculada: {eficiencia_calculada:.1f}%")
        
        # Nota: El "Índice de Salud" puede ser diferente a "Eficiencia del Lote"
        indice_salud = resultado.get('indice_salud', 'N/A')
        print(f"   Índice de Salud: {indice_salud}")
        
        diferencia = abs(porcentaje_pdf - eficiencia_calculada)
        if diferencia < 5:
            print(f"\n✅ VERIFICACIÓN EXITOSA: Diferencia de {diferencia:.1f}% (dentro del rango aceptable)")
        else:
            print(f"\n⚠️ DIFERENCIA SIGNIFICATIVA: {diferencia:.1f}%")
            print("   Puede indicar que el PDF usa un cálculo diferente o datos diferentes")
        
        print("\n" + "=" * 70)
        print("✅ Test completado")
        print("=" * 70)
        
    except Parcela.DoesNotExist:
        print("❌ ERROR: No se encontró la parcela")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_porcentaje_parcela_6()
