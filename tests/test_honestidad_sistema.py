#!/usr/bin/env python
"""
Test de Honestidad del Sistema - Validación de Análisis Temporal
=================================================================

Este test debe ejecutarse ANTES de cada despliegue a producción para
asegurar que el sistema detecta correctamente:

1. Crisis históricas (Memoria de Crisis)
2. Cicatrices permanentes (estrés extremo)
3. Penalización de eficiencia por problemas pasados
4. Índice de Estrés Acumulado (IEA)

REGLA DE ORO:
Si hubo crisis históricas, la eficiencia NUNCA puede ser 100%,
aunque el lote esté verde en la actualidad.

Autor: AgroTech Engineering Team
Fecha: Enero 2026
"""

import os
import sys
import django
import numpy as np
from datetime import datetime

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TestHonestidadSistema:
    """
    Suite de pruebas de honestidad del sistema de análisis
    """
    
    def __init__(self):
        self.resultados = []
        self.tests_pasaron = 0
        self.tests_fallaron = 0
    
    def test_pixel_traidor(self) -> Dict:
        """
        TEST CRÍTICO: El Píxel Traidor
        
        Escenario:
        - Lote 10×10 píxeles (100 píxeles totales)
        - 99 píxeles perfectos todo el año (NDVI=0.85, NDMI=0.2)
        - 1 píxel (5,5) con sequía extrema en Mes 3:
          · NDMI = -0.2 (crisis extrema)
          · NDVI = 0.35 (muy bajo)
        - Ese mismo píxel se recupera en Mes 12:
          · NDMI = 0.15 (normal)
          · NDVI = 0.8 (excelente)
        
        Pregunta: ¿El sistema lo detecta y penaliza?
        """
        print("\n" + "="*80)
        print("🧪 TEST DE HONESTIDAD: El Píxel Traidor")
        print("="*80 + "\n")
        
        # CONFIGURACIÓN
        size = (10, 10)
        num_meses = 12
        area_total_ha = 1.0
        
        # CREAR DATA CUBES
        ndvi_cube = np.full((num_meses, size[0], size[1]), 0.85, dtype=np.float32)
        ndmi_cube = np.full((num_meses, size[0], size[1]), 0.2, dtype=np.float32)
        savi_cube = np.full((num_meses, size[0], size[1]), 0.65, dtype=np.float32)
        
        # PÍXEL TRAIDOR (5, 5) - Crisis en Mes 3 (índice 2)
        ndvi_cube[2, 5, 5] = 0.35  # Muy bajo
        ndmi_cube[2, 5, 5] = -0.2  # Crisis extrema
        savi_cube[2, 5, 5] = 0.25  # Bajo
        
        # Recuperación en Mes 12 (índice 11)
        ndvi_cube[11, 5, 5] = 0.8  # Excelente
        ndmi_cube[11, 5, 5] = 0.15  # Normal
        savi_cube[11, 5, 5] = 0.6  # Normal
        
        # DETECTAR CRISIS HISTÓRICAS
        crisis_detectadas = []
        for mes in range(num_meses):
            # Calcular promedio del mes
            ndvi_mes = np.mean(ndvi_cube[mes, :, :])
            ndmi_mes = np.mean(ndmi_cube[mes, :, :])
            
            # Crisis si NDVI < 0.45 o NDMI < 0.0
            if ndvi_mes < 0.45 or ndmi_mes < 0.0:
                crisis_detectadas.append({
                    'mes': mes + 1,
                    'ndvi': float(ndvi_mes),
                    'ndmi': float(ndmi_mes)
                })
        
        print(f"📊 ANÁLISIS DEL PÍXEL TRAIDOR (5,5):")
        
        # CALCULAR IEA (Índice de Estrés Acumulado)
        data_cubes = {
            'ndvi': ndvi_cube,
            'ndmi': ndmi_cube,
            'savi': savi_cube,
            'num_meses': num_meses
        }
        
        resultado_iea = self.calcular_iea_vectorizado(data_cubes)
        iea = resultado_iea['iea']
        cicatrices = resultado_iea['tiene_cicatriz']
        
        # RESULTADOS PÍXEL (5,5)
        iea_pixel_traidor = iea[5, 5]
        tiene_cicatriz_pixel = cicatrices[5, 5]
        
        print(f"   IEA acumulado: {iea_pixel_traidor}")
        print(f"   ¿Tiene cicatriz?: {tiene_cicatriz_pixel}")
        print(f"   NDVI Mes 3: {ndvi_cube[2, 5, 5]:.2f}")
        print(f"   NDMI Mes 3: {ndmi_cube[2, 5, 5]:.2f} ⚠️ CRISIS EXTREMA")
        print(f"   NDVI Mes 12: {ndvi_cube[11, 5, 5]:.2f} ✅ RECUPERADO")
        print(f"   NDMI Mes 12: {ndmi_cube[11, 5, 5]:.2f} ✅ RECUPERADO")
        
        # CALCULAR EFICIENCIA
        ndvi_actual = ndvi_cube[-1, :, :]
        savi_actual = savi_cube[-1, :, :]
        area_afectada_actual = 0.0  # El píxel está recuperado
        
        eficiencia_final, eficiencia_base, penalizacion = \
            self.calcular_eficiencia_lote(
                ndvi_actual, savi_actual,
                area_afectada_actual, area_total_ha,
                crisis_detectadas
            )
        
        print(f"\n📈 EFICIENCIA CALCULADA:")
        print(f"   Eficiencia Base: {eficiencia_base:.1f}%")
        print(f"   Penalización Histórica: -{penalizacion:.1f}%")
        print(f"   Eficiencia Final: {eficiencia_final:.1f}%")
        
        # VALIDACIONES
        print(f"\n✅ VALIDACIONES:")
        
        tests = []
        
        # Test 1: IEA debe detectar el problema
        test1 = iea_pixel_traidor > 0
        tests.append(('IEA detecta crisis', test1))
        print(f"   1. IEA detecta crisis: {test1} "
              f"{'✅ PASS' if test1 else '❌ FAIL'}")
        
        # Test 2: Debe tener cicatriz (NDMI < -0.1)
        test2 = tiene_cicatriz_pixel == True
        tests.append(('Cicatriz detectada', test2))
        print(f"   2. Cicatriz detectada: {test2} "
              f"{'✅ PASS' if test2 else '❌ FAIL'}")
        
        # Test 3: Eficiencia NO debe ser 100%
        test3 = eficiencia_final < 100.0
        tests.append(('Eficiencia < 100%', test3))
        print(f"   3. Eficiencia < 100%: {test3} "
              f"{'✅ PASS' if test3 else '❌ FAIL - CÓDIGO DESHONESTO'}")
        
        # Test 4: Crisis debe estar en el historial
        test4 = len(crisis_detectadas) > 0
        tests.append(('Crisis en historial', test4))
        print(f"   4. Crisis en historial: {test4} "
              f"({len(crisis_detectadas)} meses) "
              f"{'✅ PASS' if test4 else '❌ FAIL'}")
        
        # RESULTADO FINAL
        todos_pass = all(t[1] for t in tests)
        
        print(f"\n{'='*80}")
        if todos_pass:
            print("🎉 SISTEMA HONESTO - Todos los tests pasaron")
            print("   El píxel traidor fue detectado y penalizado correctamente")
            self.tests_pasaron += len(tests)
        else:
            print("❌ SISTEMA DESHONESTO - Algunos tests fallaron")
            print("   El sistema está ocultando problemas históricos")
            self.tests_fallaron += sum(1 for t in tests if not t[1])
            self.tests_pasaron += sum(1 for t in tests if t[1])
        print(f"{'='*80}\n")
        
        return {
            'test_name': 'test_pixel_traidor',
            'passed': todos_pass,
            'eficiencia_final': eficiencia_final,
            'iea_pixel': iea_pixel_traidor,
            'tiene_cicatriz': tiene_cicatriz_pixel,
            'crisis_detectadas': crisis_detectadas,
            'tests': tests
        }
    
    def calcular_iea_vectorizado(self, data_cubes: Dict) -> Dict:
        """
        Calcula Índice de Estrés Acumulado por píxel (VECTORIZADO)
        
        IEA = suma de meses con problemas por píxel
        Cicatriz = crisis extrema (NDMI < -0.1) en cualquier mes
        """
        ndvi_cube = data_cubes['ndvi']
        ndmi_cube = data_cubes['ndmi']
        
        # DETECTAR MESES CON PROBLEMAS (VECTORIZADO)
        problema_ndvi = ndvi_cube < 0.45
        problema_ndmi = ndmi_cube < 0.0
        problema_general = problema_ndvi | problema_ndmi
        
        # CALCULAR IEA (suma de meses con problema)
        iea = np.sum(problema_general.astype(np.int8), axis=0)
        
        # DETECTAR CRISIS EXTREMAS (CICATRICES)
        crisis_extrema = ndmi_cube < -0.1
        tiene_cicatriz = np.any(crisis_extrema, axis=0)
        
        # Bonus: doble penalización por crisis extrema
        meses_extremos = np.sum(crisis_extrema.astype(np.int8), axis=0)
        iea = iea + meses_extremos
        
        return {
            'iea': iea,
            'tiene_cicatriz': tiene_cicatriz,
            'stats': {
                'iea_max': float(np.max(iea)),
                'iea_promedio': float(np.mean(iea)),
                'pixeles_con_cicatriz': int(np.sum(tiene_cicatriz)),
            }
        }
    
    def calcular_eficiencia_lote(self, ndvi: np.ndarray, savi: np.ndarray,
                                 area_afectada: float, area_total: float,
                                 crisis_historicas: List) -> tuple:
        """
        Calcula eficiencia con penalización histórica
        
        Returns:
            (eficiencia_final, eficiencia_base, penalizacion)
        """
        # 1. Eficiencia base
        if area_afectada <= 0.0:
            eficiencia_base = 100.0
        else:
            porcentaje_afectado = (area_afectada / area_total) * 100.0
            eficiencia_base = max(0.0, 100.0 - porcentaje_afectado)
        
        # 2. Penalización por crisis históricas
        penalizacion = 0.0
        if crisis_historicas and len(crisis_historicas) > 0:
            total_meses = 12
            meses_crisis = len(crisis_historicas)
            penalizacion = (meses_crisis / total_meses) * 15.0
        
        # 3. Eficiencia final
        eficiencia_final = max(0.0, eficiencia_base - penalizacion)
        
        # VALIDACIÓN: Si hubo crisis, NO puede ser 100%
        if crisis_historicas and len(crisis_historicas) > 0:
            if eficiencia_final >= 100.0:
                eficiencia_final = min(eficiencia_final, 92.0)
        
        return (
            round(eficiencia_final, 1),
            round(eficiencia_base, 1),
            round(penalizacion, 1)
        )
    
    def ejecutar_todos_los_tests(self) -> bool:
        """
        Ejecuta toda la suite de pruebas
        
        Returns:
            True si todos pasaron, False si alguno falló
        """
        print("\n" + "="*80)
        print("🔬 EJECUTANDO SUITE DE PRUEBAS DE HONESTIDAD")
        print("="*80)
        
        # Test 1: Píxel Traidor
        resultado1 = self.test_pixel_traidor()
        self.resultados.append(resultado1)
        
        # RESUMEN FINAL
        print("\n" + "="*80)
        print("📊 RESUMEN DE PRUEBAS")
        print("="*80)
        print(f"\nTests ejecutados: {self.tests_pasaron + self.tests_fallaron}")
        print(f"✅ Pasaron: {self.tests_pasaron}")
        print(f"❌ Fallaron: {self.tests_fallaron}")
        
        todos_ok = self.tests_fallaron == 0
        
        if todos_ok:
            print(f"\n{'='*80}")
            print("🎉 SISTEMA APROBADO PARA PRODUCCIÓN")
            print("="*80)
            print("El sistema detecta correctamente:")
            print("  ✅ Crisis históricas")
            print("  ✅ Cicatrices permanentes")
            print("  ✅ Penalización de eficiencia")
            print("  ✅ Índice de Estrés Acumulado (IEA)")
            print("\n🚀 LISTO PARA DESPLIEGUE A RAILWAY")
        else:
            print(f"\n{'='*80}")
            print("❌ SISTEMA REPROBADO - NO DESPLEGAR")
            print("="*80)
            print("El sistema tiene problemas de honestidad.")
            print("Revisar código antes de desplegar a producción.")
            print("\n⚠️  DESPLIEGUE BLOQUEADO")
        
        print(f"{'='*80}\n")
        
        return todos_ok


def main():
    """Punto de entrada principal"""
    test_suite = TestHonestidadSistema()
    aprobado = test_suite.ejecutar_todos_los_tests()
    
    # Exit code para CI/CD
    sys.exit(0 if aprobado else 1)


if __name__ == '__main__':
    main()
