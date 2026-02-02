#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Rápido - PDF con Logos de AgroTech
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal

print("\n🧪 TEST: PDF CON LOGOS DE AGROTECH")
print("="*60)

# 1. Cargar parcela
parcela = Parcela.objects.get(id=6)
print(f"✅ Parcela: {parcela.nombre}")

# 2. Verificador
verificador = VerificadorRestriccionesLegales()
print("✅ Verificador inicializado")

# 3. Verificación
resultado = verificador.verificar_parcela(
    parcela_id=parcela.id,
    geometria_parcela=parcela.geometria,
    nombre_parcela=parcela.nombre
)
print("✅ Verificación completada")

# 4. Generar PDF
generador = GeneradorPDFLegal()
output_path = 'test_pdf_con_logos.pdf'

print(f"\n📄 Generando PDF con logos...")
ruta_pdf = generador.generar_pdf(
    parcela=parcela,
    resultado=resultado,
    verificador=verificador,
    output_path=output_path,
    departamento='Casanare'
)

print(f"\n✅ PDF generado: {ruta_pdf}")
print(f"   Tamaño: {os.path.getsize(ruta_pdf) / (1024*1024):.2f} MB")

print(f"\n🔍 Abriendo PDF...")
os.system(f"open {ruta_pdf}")

print("\n" + "="*60)
print("✅ TEST COMPLETADO")
print("="*60)
