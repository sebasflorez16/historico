#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Comparativo de Lotes - Sistema AgroTech
Analiza y compara todos los lotes disponibles en la base de datos
"""

import os
import sys
import django
from pathlib import Path
from datetime import datetime

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual


def analizar_lote(parcela_id):
    """
    Analiza un lote específico y retorna estadísticas completas
    """
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        
        # Obtener índices mensuales
        indices = IndiceMensual.objects.filter(
            parcela=parcela
        ).order_by('fecha_imagen')
        
        if indices.count() == 0:
            return None
        
        # Análisis de crisis mes a mes
        crisis_detectadas = []
        meses_normales = 0
        
        for idx, indice in enumerate(indices, 1):
            ndvi = indice.ndvi_promedio
            savi = indice.savi_promedio
            ndmi = indice.ndmi_promedio
            
            # Validar valores None
            if ndvi is None or ndmi is None or savi is None:
                continue
            
            # Detección de crisis (lógica del sistema)
            es_crisis = ndvi < 0.45 or ndmi < 0.0
            
            if es_crisis:
                tipos_crisis = []
                if ndvi < 0.45:
                    tipos_crisis.append("baja densidad vegetal")
                if ndmi < 0.0:
                    tipos_crisis.append("estrés hídrico")
                if savi < 0.30:
                    tipos_crisis.append("exposición de suelo")
                
                crisis_detectadas.append({
                    'mes': idx,
                    'fecha': indice.fecha_imagen,
                    'ndvi': ndvi,
                    'ndmi': ndmi,
                    'savi': savi,
                    'tipos': tipos_crisis
                })
            else:
                meses_normales += 1
        
        # Calcular estadísticas
        total_meses = indices.count()
        num_crisis = len(crisis_detectadas)
        porcentaje_crisis = (num_crisis / total_meses * 100) if total_meses > 0 else 0
        
        # Calcular penalización histórica esperada
        penalizacion_esperada = (num_crisis / total_meses) * 15.0 if num_crisis > 0 else 0.0
        eficiencia_esperada = max(0.0, 100.0 - penalizacion_esperada)
        
        # Promedios de índices
        ndvi_promedio_general = sum([i.ndvi_promedio for i in indices if i.ndvi_promedio is not None]) / total_meses
        ndmi_promedio_general = sum([i.ndmi_promedio for i in indices if i.ndmi_promedio is not None]) / total_meses
        savi_promedio_general = sum([i.savi_promedio for i in indices if i.savi_promedio is not None]) / total_meses
        
        return {
            'parcela': parcela,
            'total_meses': total_meses,
            'meses_normales': meses_normales,
            'num_crisis': num_crisis,
            'porcentaje_crisis': porcentaje_crisis,
            'crisis_detectadas': crisis_detectadas,
            'penalizacion_esperada': penalizacion_esperada,
            'eficiencia_esperada': eficiencia_esperada,
            'ndvi_promedio': ndvi_promedio_general,
            'ndmi_promedio': ndmi_promedio_general,
            'savi_promedio': savi_promedio_general,
            'primer_mes': indices.first().fecha_imagen if indices.first() else None,
            'ultimo_mes': indices.last().fecha_imagen if indices.last() else None
        }
        
    except Parcela.DoesNotExist:
        return None
    except Exception as e:
        print(f"❌ Error analizando lote {parcela_id}: {str(e)}")
        return None


def imprimir_resultado(resultado, numero):
    """
    Imprime el resultado de análisis de un lote de forma formateada
    """
    if not resultado:
        print(f"❌ No se pudo analizar el lote {numero}")
        return
    
    p = resultado['parcela']
    
    print("=" * 80)
    print(f"📊 LOTE {numero}: {p.nombre}")
    print("=" * 80)
    
    print(f"\n📍 INFORMACIÓN BÁSICA:")
    print(f"   ID: {p.id}")
    print(f"   Nombre: {p.nombre}")
    print(f"   Propietario: {p.propietario}")
    print(f"   Área: {p.area_hectareas:.2f} hectáreas")
    
    print(f"\n📅 PERÍODO DE ANÁLISIS:")
    print(f"   Primer registro: {resultado['primer_mes']}")
    print(f"   Último registro: {resultado['ultimo_mes']}")
    print(f"   Total meses analizados: {resultado['total_meses']}")
    
    print(f"\n📈 ÍNDICES PROMEDIO GENERALES:")
    print(f"   NDVI: {resultado['ndvi_promedio']:.3f}")
    print(f"   NDMI: {resultado['ndmi_promedio']:.3f}")
    print(f"   SAVI: {resultado['savi_promedio']:.3f}")
    
    print(f"\n⚠️  ANÁLISIS DE CRISIS:")
    print(f"   Meses con crisis detectadas: {resultado['num_crisis']} de {resultado['total_meses']}")
    print(f"   Porcentaje de crisis: {resultado['porcentaje_crisis']:.1f}%")
    print(f"   Meses normales: {resultado['meses_normales']}")
    
    if resultado['crisis_detectadas']:
        print(f"\n🔴 DETALLE DE CRISIS:")
        for crisis in resultado['crisis_detectadas']:
            tipos = ", ".join(crisis['tipos'])
            print(f"      • {crisis['fecha']} (Mes {crisis['mes']}): {tipos}")
            print(f"        NDVI: {crisis['ndvi']:.3f} | NDMI: {crisis['ndmi']:.3f} | SAVI: {crisis['savi']:.3f}")
    
    print(f"\n💯 CÁLCULO DE EFICIENCIA:")
    print(f"   Penalización histórica esperada: -{resultado['penalizacion_esperada']:.1f}%")
    print(f"   Eficiencia esperada (con penalización): {resultado['eficiencia_esperada']:.1f}%")
    print(f"   Eficiencia actual del sistema: 100.0% ⚠️  (SIN PENALIZACIÓN - PENDIENTE)")
    
    # Determinar estado esperado
    if resultado['num_crisis'] == 0:
        estado_esperado = "ÓPTIMO ✅"
        color_estado = "VERDE"
    elif resultado['eficiencia_esperada'] >= 90:
        estado_esperado = "ESTABLE CON OBSERVACIONES ⚠️"
        color_estado = "NARANJA"
    elif resultado['eficiencia_esperada'] >= 70:
        estado_esperado = "REQUIERE ATENCIÓN ⚠️"
        color_estado = "NARANJA OSCURO"
    else:
        estado_esperado = "ACCIÓN PRIORITARIA REQUERIDA 🔴"
        color_estado = "ROJO"
    
    print(f"\n🎯 ESTADO ESPERADO DEL LOTE:")
    print(f"   {estado_esperado} ({color_estado})")
    print("\n")


def main():
    """
    Ejecuta el test comparativo para todos los lotes
    """
    print("=" * 80)
    print("🧪 TEST COMPARATIVO DE LOTES - SISTEMA AGROTECH")
    print("=" * 80)
    print(f"Fecha del test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Obtener todos los lotes
    parcelas = Parcela.objects.all()
    
    if parcelas.count() == 0:
        print("❌ No hay parcelas en la base de datos")
        return
    
    print(f"📊 Total de lotes en la base de datos: {parcelas.count()}\n")
    
    # Analizar cada lote
    resultados = []
    for idx, parcela in enumerate(parcelas, 1):
        resultado = analizar_lote(parcela.id)
        if resultado:
            resultados.append(resultado)
            imprimir_resultado(resultado, idx)
    
    # Tabla comparativa final
    if len(resultados) > 1:
        print("=" * 80)
        print("📊 TABLA COMPARATIVA")
        print("=" * 80)
        print()
        
        # Header
        print(f"{'LOTE':<20} {'ÁREA (ha)':<12} {'CRISIS':<10} {'% CRISIS':<12} {'EFICIENCIA ESPERADA':<20}")
        print("-" * 80)
        
        # Datos
        for r in resultados:
            nombre = r['parcela'].nombre[:18]
            area = f"{r['parcela'].area_hectareas:.2f}"
            crisis = f"{r['num_crisis']}/{r['total_meses']}"
            pct_crisis = f"{r['porcentaje_crisis']:.1f}%"
            eficiencia = f"{r['eficiencia_esperada']:.1f}%"
            
            print(f"{nombre:<20} {area:<12} {crisis:<10} {pct_crisis:<12} {eficiencia:<20}")
        
        print()
    
    # Resumen final
    print("=" * 80)
    print("📋 RESUMEN EJECUTIVO")
    print("=" * 80)
    
    total_crisis = sum([r['num_crisis'] for r in resultados])
    total_meses_todos = sum([r['total_meses'] for r in resultados])
    promedio_eficiencia = sum([r['eficiencia_esperada'] for r in resultados]) / len(resultados)
    
    print(f"\n✅ Lotes analizados: {len(resultados)}")
    print(f"📅 Total meses-lote procesados: {total_meses_todos}")
    print(f"⚠️  Total crisis detectadas: {total_crisis}")
    print(f"📊 Eficiencia promedio esperada: {promedio_eficiencia:.1f}%")
    
    print("\n🔧 ESTADO DE IMPLEMENTACIÓN:")
    print("   ✅ Detección de crisis: FUNCIONAL")
    print("   ✅ Cálculo de penalización: DOCUMENTADO")
    print("   ⚠️  Aplicación de penalización: PENDIENTE")
    print("   ⚠️  Sistema actual muestra: 100% para todos (DESHONESTO)")
    
    print("\n💡 ACCIÓN REQUERIDA:")
    print("   Implementar penalización histórica en cerebro_diagnostico.py")
    print("   para que la eficiencia refleje la memoria de crisis")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETADO")
    print("=" * 80)


if __name__ == '__main__':
    main()
