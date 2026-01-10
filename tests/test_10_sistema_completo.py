#!/usr/bin/env python
"""
Test Final - Verificación Completa del Sistema (SIMPLIFICADO)
Verifica componentes básicos sin PlantillaInforme (deprecado)
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.auth.models import User
from informes.models import Parcela, Informe

def test_1_modelos():
    """Test 1: Verificar que los modelos estén correctos"""
    print("\n" + "="*70)
    print("TEST 1: Verificación de Modelos")
    print("="*70)
    
    try:
        # Verificar que Parcela tenga campos básicos
        parcela_fields = [f.name for f in Parcela._meta.get_fields()]
        required_parcela = ['nombre', 'propietario', 'geometria', 'eosda_field_id']
        missing = [f for f in required_parcela if f not in parcela_fields]
        
        if not missing:
            print("✅ Modelo Parcela tiene todos los campos requeridos")
        else:
            print(f"❌ FAIL: Parcela falta campos: {missing}")
            return False
        
        # Verificar que Informe tenga campos básicos
        informe_fields = [f.name for f in Informe._meta.get_fields()]
        required_informe = ['parcela', 'fecha_generacion', 'titulo', 'archivo_pdf']
        missing_informe = [f for f in required_informe if f not in informe_fields]
        
        if not missing_informe:
            print("✅ Modelo Informe tiene todos los campos requeridos")
        else:
            print(f"❌ FAIL: Informe falta campos: {missing_informe}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error verificando modelos: {e}")
        return False


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n" + "="*70)
    print("🔍 TEST SIMPLIFICADO - VERIFICACIÓN DE MODELOS")
    print("="*70)
    
    resultado = test_1_modelos()
    
    print("\n" + "="*70)
    print("📊 RESULTADO")
    print("="*70)
    
    if resultado:
        print("✅ Test pasó correctamente")
        return 0
    else:
        print("❌ Test falló")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
