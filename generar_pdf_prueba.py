#!/usr/bin/env python
"""
Script para generar PDF de prueba de la parcela 6
Validar los cambios implementados en el generador de informes
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/sebasflorez16/Documents/AgroTech Historico')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional

def main():
    print("=" * 80)
    print("GENERADOR DE PDF DE PRUEBA - PARCELA 6")
    print("=" * 80)
    print()
    
    try:
        # Obtener parcela 6
        parcela = Parcela.objects.get(id=6, activa=True)
        print(f"✓ Parcela encontrada: {parcela.nombre}")
        print(f"  - Propietario: {parcela.propietario}")
        print(f"  - Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
        print(f"  - Área: {parcela.area_hectareas:.2f} hectáreas")
        print()
        
        # Verificar datos disponibles
        indices_count = parcela.indices_mensuales.count()
        print(f"✓ Datos disponibles: {indices_count} registros mensuales")
        print()
        
        if indices_count == 0:
            print("❌ No hay datos para generar el informe")
            return
        
        # Generar PDF
        print("Generando informe PDF...")
        print("Cambios implementados:")
        print("  ✓ Motor técnico determinístico (sin IA)")
        print("  ✓ Sección de Metodología de Análisis")
        print("  ✓ Análisis cruzado de índices con diagnósticos")
        print("  ✓ Layout corregido de galería de imágenes")
        print("  ✓ Justificación de recomendaciones")
        print("  ✓ Resumen técnico transparente")
        print()
        
        generador = GeneradorPDFProfesional()
        pdf_path = generador.generar_informe_completo(
            parcela_id=6,
            meses_atras=12
        )
        
        print("=" * 80)
        print("✅ PDF GENERADO EXITOSAMENTE")
        print("=" * 80)
        print(f"Ubicación: {pdf_path}")
        print()
        print("Secciones incluidas:")
        print("  1. Portada profesional")
        print("  2. Metodología de Análisis (NUEVO)")
        print("  3. Resumen Ejecutivo con análisis cruzado (MEJORADO)")
        print("  4. Información de la parcela")
        print("  5. Análisis NDVI")
        print("  6. Análisis NDMI")
        print("  7. Análisis SAVI (si disponible)")
        print("  8. Tendencias temporales")
        print("  9. Recomendaciones agronómicas")
        print(" 10. Tabla de datos mensuales")
        print(" 11. Galería de imágenes satelitales (LAYOUT CORREGIDO)")
        print(" 12. Créditos")
        print()
        print("Por favor, revise el PDF para validar:")
        print("  • Las imágenes ya no se superponen en la galería")
        print("  • La metodología explica claramente el proceso técnico")
        print("  • El resumen ejecutivo incluye diagnósticos cruzados")
        print("  • No hay referencias a IA/Gemini")
        print("  • Todas las conclusiones están justificadas")
        print()
        
    except Parcela.DoesNotExist:
        print("❌ ERROR: Parcela 6 no encontrada en la base de datos")
        print("   Parcelas disponibles:")
        for p in Parcela.objects.filter(activa=True):
            print(f"   - ID {p.id}: {p.nombre}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
