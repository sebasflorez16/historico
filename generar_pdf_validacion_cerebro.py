#!/usr/bin/env python
"""
Script de Validación Visual - Generación PDF con Cerebro Diagnóstico Mejorado
============================================================================

Genera un PDF real usando el motor de diagnóstico mejorado para validar:
1. ✅ Detección de Cicatrices (umbral NDMI -0.08)
2. ✅ Justificación Narrativa en lenguaje natural
3. ✅ Sincronización Matemática Estricta (área 61.42 ha, redondeos)
4. ✅ Sensibilidad Proactiva (alertas tempranas)

VALIDACIÓN VISUAL:
- PDF debe mostrar la nueva narrativa en la sección de resumen
- Cálculos de eficiencia y área afectada deben ser consistentes
- Área de la parcela siempre 61.42 ha
- Redondeos: 2 decimales para hectáreas, 1 para porcentajes
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.models_gemini import InformeGenerado
from informes.generador_pdf import GeneradorPDFProfesional
from django.contrib.auth.models import User


def generar_pdf_validacion():
    """
    Genera un PDF de validación usando el cerebro diagnóstico mejorado
    NOTA: El GeneradorPDFProfesional ya integra el cerebro_diagnostico.py
          automáticamente con las 4 mejoras implementadas
    """
    print("🚀 GENERACIÓN PDF DE VALIDACIÓN - CEREBRO DIAGNÓSTICO MEJORADO")
    print("=" * 80)
    
    # Seleccionar parcela con datos
    try:
        parcela = Parcela.objects.get(id=6)  # Parcela #2 - 61.42 ha - 13 índices
        print(f"\n✅ Parcela seleccionada: {parcela.nombre}")
        print(f"   Cultivo: {parcela.tipo_cultivo}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        print(f"   Índices mensuales: {parcela.indices_mensuales.count()}")
    except Parcela.DoesNotExist:
        print("❌ ERROR: No se encontró la parcela ID=6")
        return None
    
    # Seleccionar usuario
    try:
        usuario = User.objects.get(username='admin')
        print(f"   Usuario: {usuario.username}")
    except User.DoesNotExist:
        print("⚠️  Usuario 'admin' no encontrado, usando el primero disponible")
        usuario = User.objects.first()
        if not usuario:
            print("❌ ERROR: No hay usuarios en el sistema")
            return None
        print(f"   Usuario: {usuario.username}")
    
    print("\n" + "=" * 80)
    print("� GENERANDO PDF PROFESIONAL CON CEREBRO DIAGNÓSTICO MEJORADO...")
    print("   Tipo de análisis: completo")
    print("   Mejoras incluidas:")
    print("   ✓ Detección de Cicatrices (umbral NDMI -0.08)")
    print("   ✓ Justificación Narrativa en lenguaje natural")
    print("   ✓ Sincronización Matemática Estricta (área 61.42 ha)")
    print("   ✓ Sensibilidad Proactiva (alertas tempranas)")
    print("\n" + "=" * 80)
    
    try:
        # El generador automáticamente usa cerebro_diagnostico.py mejorado
        generador = GeneradorPDFProfesional()
        
        # Generar informe completo usando el ID de la parcela
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=12
        )
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / 1024  # KB
            print(f"\n✅ PDF GENERADO EXITOSAMENTE")
            print(f"   📂 Ruta: {pdf_path}")
            print(f"   📊 Tamaño: {file_size:.1f} KB")
            
            # Verificar registro en BD
            try:
                ultimo_informe = InformeGenerado.objects.filter(
                    parcela=parcela,
                    usuario=usuario
                ).order_by('-fecha_generacion').first()
                
                if ultimo_informe:
                    print(f"\n📋 REGISTRO EN BASE DE DATOS:")
                    print(f"   ID: {ultimo_informe.id}")
                    print(f"   Fecha: {ultimo_informe.fecha_generacion.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   Imágenes analizadas: {ultimo_informe.num_imagenes_analizadas}")
            except Exception as e:
                print(f"\n⚠️  No se pudo verificar registro en BD: {str(e)}")
            
            # Mostrar instrucciones para validación visual
            print("\n" + "=" * 80)
            print("🔍 INSTRUCCIONES DE VALIDACIÓN VISUAL:")
            print("=" * 80)
            print("\n1. Abrir el PDF generado:")
            print(f"   open '{pdf_path}'")
            print("\n2. Verificar en el PDF las 4 MEJORAS IMPLEMENTADAS:")
            print("\n   ✓ MEJORA 1 - Detección de Cicatrices:")
            print("     • Buscar alertas de 'Estrés Hídrico Moderado' o 'Cicatriz de Sequía'")
            print("     • Umbral NDMI ajustado a -0.08 (antes -0.05)")
            print("\n   ✓ MEJORA 2 - Justificación Narrativa:")
            print("     • Buscar sección 'Justificación del Estado' o similar")
            print("     • Debe contener explicación en lenguaje natural")
            print("     • Formato: 'La eficiencia de X% se explica por...'")
            print("\n   ✓ MEJORA 3 - Sincronización Matemática:")
            print("     • Verificar: Eficiencia < 100% si Área Afectada > 0")
            print("     • Área de parcela: 61.42 ha (2 decimales)")
            print("     • Porcentajes: X.X% (1 decimal)")
            print("     • Hectáreas: X.XX ha (2 decimales)")
            print("\n   ✓ MEJORA 4 - Sensibilidad Proactiva:")
            print("     • Revisar detección temprana de problemas")
            print("     • Alertas preventivas antes de daño severo")
            
            print("\n" + "=" * 80)
            print("✅ VALIDACIÓN AUTOMATIZADA COMPLETADA")
            print("🔎 REVISIÓN VISUAL PENDIENTE - Abrir PDF y verificar mejoras")
            print("=" * 80)
            
            return pdf_path
            
        else:
            print("\n❌ ERROR: El PDF no se generó correctamente")
            return None
            
    except Exception as e:
        print(f"\n❌ ERROR GENERANDO PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    pdf_path = generar_pdf_validacion()
    
    if pdf_path:
        print(f"\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print(f"📄 PDF disponible en: {pdf_path}")
        sys.exit(0)
    else:
        print(f"\n❌ PROCESO FALLIDO - Revisar errores arriba")
        sys.exit(1)
