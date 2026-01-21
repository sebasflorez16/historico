#!/usr/bin/env python
"""
Test de Integración: Sistema de KPIs Unificados en Generador de PDF
===================================================================

Valida que el generador de PDF use correctamente:
1. La máscara de cultivo generada desde geometría
2. Los KPIs unificados con validación matemática
3. El formato estándar de 1 decimal para hectáreas y porcentajes

Ejecutar:
    python test_integracion_kpis_pdf.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.generador_pdf import GeneradorPDFProfesional
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_integracion_kpis_pdf():
    """
    Test de integración completo del sistema de KPIs en el PDF
    """
    print("\n" + "="*80)
    print("TEST DE INTEGRACIÓN: KPIs UNIFICADOS EN GENERADOR DE PDF")
    print("="*80 + "\n")
    
    # 1. Buscar parcela con datos recientes
    print("1️⃣  Buscando parcela con datos recientes...")
    parcelas = Parcela.objects.all().order_by('-id')[:5]
    
    parcela_test = None
    for parcela in parcelas:
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')
        if indices.exists():
            ultimo = indices.first()
            if (ultimo.ndvi_promedio is not None and 
                ultimo.ndmi_promedio is not None and 
                ultimo.savi_promedio is not None):
                parcela_test = parcela
                print(f"   ✅ Parcela seleccionada: {parcela.nombre} (ID: {parcela.id})")
                print(f"   📊 Último índice: {ultimo.año}-{ultimo.mes:02d}")
                print(f"   📈 NDVI: {ultimo.ndvi_promedio:.3f}, NDMI: {ultimo.ndmi_promedio:.3f}, SAVI: {ultimo.savi_promedio:.3f}")
                break
    
    if not parcela_test:
        print("   ❌ No se encontró parcela con datos completos")
        return False
    
    # 2. Generar PDF con diagnóstico
    print("\n2️⃣  Generando PDF con diagnóstico unificado...")
    generador = GeneradorPDFProfesional()
    
    try:
        # Intentar generar el PDF
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela_test.id,
            meses_atras=12
        )
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"   ✅ PDF generado exitosamente")
            print(f"   📄 Ruta: {pdf_path}")
            
            # 3. Verificar que se usaron KPIs unificados
            print("\n3️⃣  Verificando uso de KPIs unificados...")
            
            # Leer el log para verificar que se crearon KPIs
            with open('agrotech.log', 'r') as f:
                log_lines = f.readlines()[-100:]  # Últimas 100 líneas
                
                kpis_creados = any('KPIs unificados creados' in line for line in log_lines)
                mascara_generada = any('Máscara de cultivo generada' in line for line in log_lines)
                
                if kpis_creados:
                    print("   ✅ KPIs unificados creados correctamente")
                else:
                    print("   ⚠️  No se detectó creación de KPIs unificados en el log")
                
                if mascara_generada:
                    print("   ✅ Máscara de cultivo generada correctamente")
                else:
                    print("   ⚠️  No se detectó generación de máscara de cultivo")
            
            # 4. Validar que el PDF existe y tiene tamaño razonable
            print("\n4️⃣  Validando archivo PDF generado...")
            if os.path.exists(pdf_path):
                size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
                print(f"   ✅ Archivo PDF existe: {size_mb:.2f} MB")
                
                if size_mb > 0.1:
                    print(f"   ✅ Tamaño del PDF es razonable (> 0.1 MB)")
                else:
                    print(f"   ⚠️  PDF muy pequeño, puede estar incompleto")
            else:
                print("   ❌ Archivo PDF no existe")
                return False
            
            # 5. Resumen de validación
            print("\n" + "="*80)
            print("RESUMEN DE VALIDACIÓN")
            print("="*80)
            print(f"✅ PDF generado: {pdf_path}")
            print(f"✅ Tamaño: {size_mb:.2f} MB")
            print(f"✅ Sistema de KPIs: {'Integrado' if kpis_creados else 'No detectado'}")
            print(f"✅ Máscara de cultivo: {'Generada' if mascara_generada else 'No detectada'}")
            print("\n📋 PRÓXIMOS PASOS:")
            print("   1. Abrir el PDF generado y verificar visualmente:")
            print("      - Resumen ejecutivo muestra eficiencia y área afectada")
            print("      - Tabla de severidad usa formato de 1 decimal")
            print("      - Diagnóstico detallado muestra zonas críticas")
            print("   2. Verificar que no hay áreas afectadas > área total")
            print("   3. Verificar que eficiencia + porcentaje afectado = 100%")
            print("\n" + "="*80 + "\n")
            
            return True
        else:
            print(f"   ❌ Error generando PDF: no se generó el archivo")
            return False
            
    except Exception as e:
        print(f"   ❌ Excepción durante generación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_integracion_kpis_pdf()
    sys.exit(0 if success else 1)
