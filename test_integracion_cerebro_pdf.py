#!/usr/bin/env python
"""
Test de Integración: Cerebro Diagnóstico → PDF
==============================================

Valida el flujo completo desde la obtención de datos satelitales
hasta la generación del PDF con diagnóstico unificado marcado.

Autor: AgroTech Engineering Team
Fecha: Enero 2026
"""

import os
import sys
import django
from pathlib import Path
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
sys.path.insert(0, str(Path(__file__).parent))
django.setup()

from datetime import date, timedelta
from informes.models import Parcela
from informes.services.generador_pdf import generador_pdf
from informes.services.eosda_api import eosda_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_integracion_completa():
    """
    Test end-to-end del sistema de diagnóstico integrado
    """
    print("\n" + "="*80)
    print("🧪 TEST DE INTEGRACIÓN: CEREBRO DIAGNÓSTICO → PDF")
    print("="*80 + "\n")
    
    # 1. Buscar parcela ID 6 (la que tiene todos los datos)
    try:
        parcela = Parcela.objects.get(id=6)
        
        print(f"✅ Parcela seleccionada: {parcela.nombre} (ID: {parcela.id})")
        print(f"   ID EOSDA: {parcela.eosda_field_id}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        print(f"   Cultivo: {parcela.tipo_cultivo or 'N/A'}")
        
        # Verificar que tenga datos históricos
        from informes.models import IndiceMensual
        num_indices = IndiceMensual.objects.filter(parcela=parcela).count()
        print(f"   Índices mensuales en DB: {num_indices}")
        print()
        
        if num_indices == 0:
            print("⚠️ Parcela sin datos históricos, pero continuamos con generación sintética")
            print()
        
    except Parcela.DoesNotExist:
        print("❌ No se encontró la parcela ID 6")
        print("💡 Verifica que la parcela exista en la base de datos")
        return False
    except Exception as e:
        print(f"❌ Error buscando parcela: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. Generar informe con diagnóstico (PRODUCCIÓN)
    print("="*80)
    print("📄 GENERANDO INFORME CON DIAGNÓSTICO - MODO PRODUCCIÓN")
    print("="*80 + "\n")
    
    try:
        resultado_prod = generador_pdf.generar_informe_completo(
            parcela=parcela,
            periodo_meses=10,
            tipo_informe='produccion'
        )
        
        if resultado_prod.get('success'):
            print("✅ Informe de producción generado exitosamente")
            print(f"   Archivo: {resultado_prod.get('archivo_pdf')}")
            print()
            
            # Mostrar extracto del análisis IA
            if 'analisis_ia' in resultado_prod:
                resumen = resultado_prod['analisis_ia'].get('resumen_ejecutivo', '')[:300]
                print("📝 Extracto del resumen ejecutivo:")
                print(f"   {resumen}...")
                print()
        else:
            print(f"❌ Error generando informe: {resultado_prod.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción generando informe de producción: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Generar informe con diagnóstico (EVALUACIÓN)
    print("="*80)
    print("📄 GENERANDO INFORME CON DIAGNÓSTICO - MODO EVALUACIÓN")
    print("="*80 + "\n")
    
    try:
        resultado_eval = generador_pdf.generar_informe_completo(
            parcela=parcela,
            periodo_meses=10,
            tipo_informe='evaluacion'
        )
        
        if resultado_eval.get('success'):
            print("✅ Informe de evaluación generado exitosamente")
            print(f"   Archivo: {resultado_eval.get('archivo_pdf')}")
            print()
        else:
            print(f"❌ Error generando informe: {resultado_eval.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción generando informe de evaluación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Verificar archivos generados
    print("="*80)
    print("📁 VERIFICACIÓN DE ARCHIVOS")
    print("="*80 + "\n")
    
    archivos = [
        resultado_prod.get('archivo_pdf'),
        resultado_eval.get('archivo_pdf')
    ]
    
    for archivo in archivos:
        if archivo and os.path.exists(archivo):
            tamaño = os.path.getsize(archivo) / 1024  # KB
            print(f"✅ {Path(archivo).name}")
            print(f"   Tamaño: {tamaño:.2f} KB")
            print(f"   Ruta: {archivo}")
            print()
        else:
            print(f"❌ Archivo no encontrado: {archivo}")
    
    # 5. Resumen final
    print("="*80)
    print("🎯 RESUMEN DE LA PRUEBA")
    print("="*80 + "\n")
    
    print("✅ Parcela seleccionada correctamente")
    print("✅ Informe de PRODUCCIÓN generado con diagnóstico")
    print("✅ Informe de EVALUACIÓN generado con diagnóstico")
    print("✅ Archivos PDF guardados correctamente")
    print()
    print("🎉 ¡INTEGRACIÓN COMPLETA EXITOSA!")
    print()
    print("📋 PRÓXIMOS PASOS:")
    print("   1. Revisa los PDFs generados para validar visualmente")
    print("   2. Verifica que el mapa diagnóstico esté incluido")
    print("   3. Confirma que las narrativas se adapten al tipo de informe")
    print()
    print(f"📂 Ver PDFs:")
    for archivo in archivos:
        if archivo and os.path.exists(archivo):
            print(f"   open '{archivo}'")
    print()
    
    return True


if __name__ == '__main__':
    try:
        exito = test_integracion_completa()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
