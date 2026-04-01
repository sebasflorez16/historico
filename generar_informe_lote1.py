#!/usr/bin/env python
"""
Genera informe profesional para LOTE 1 (tiene todas las imágenes)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.generador_pdf import GeneradorPDFProfesional
from datetime import datetime

print("\n" + "="*80)
print("🏢 GENERANDO INFORME PROFESIONAL - LOTE 1")
print("="*80)

print("\n📍 Lote seleccionado: LOTE 1 (70.81 ha)")
print("   Razón: Tiene todas las imágenes NDMI y SAVI disponibles")
print("\n🚀 Generando PDF profesional completo...\n")

generador = GeneradorPDFProfesional()
pdf_path = generador.generar_informe_completo(
    parcela_id=1,  # Lote 1
    meses_atras=14,
    output_path=None
)

if pdf_path and os.path.exists(pdf_path):
    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    
    print("\n" + "="*80)
    print("✅ INFORME GENERADO EXITOSAMENTE")
    print("="*80)
    print(f"\n📄 Archivo: {pdf_path}")
    print(f"💾 Tamaño: {size_mb:.2f} MB")
    print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    print("\n🎯 Contenido:")
    print("   ✅ Todas las imágenes satelitales (NDVI, NDMI, SAVI)")
    print("   ✅ Análisis temporal completo (14 meses)")
    print("   ✅ Diagnóstico con cerebro 100% dinámico")
    print("   ✅ Mapas georeferenciados")
    print("   ✅ Recomendaciones profesionales")
    
    print(f"\n🔍 Abriendo PDF...\n")
    os.system(f'open "{pdf_path}"')
else:
    print("\n❌ Error generando PDF")
