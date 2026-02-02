#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generar PDF Legal para Bio Energy (300+ ha)
============================================
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal

print("="*80)
print("📄 GENERANDO INFORME LEGAL - BIO ENERGY (300+ ha)")
print("="*80)

# 1. Cargar parcela Bio Energy
print("\n1️⃣ Cargando parcela Bio Energy...")
parcela = Parcela.objects.get(id=11)
print(f"✅ Parcela: {parcela.nombre}")
print(f"   Propietario: {parcela.propietario}")
print(f"   Área: {parcela.area_hectareas} ha")
print(f"   Cultivo: {parcela.tipo_cultivo}")

# 2. Crear verificador
print("\n2️⃣ Inicializando verificador legal...")
verificador = VerificadorRestriccionesLegales()
print("✅ Verificador inicializado")

# 3. Ejecutar verificación
print("\n3️⃣ Ejecutando verificación legal...")
resultado = verificador.verificar_parcela(
    parcela_id=parcela.id,
    geometria_parcela=parcela.geometria,
    nombre_parcela=parcela.nombre
)
print(f"✅ Verificación completada")
print(f"   Cumple normativa: {resultado.cumple_normativa}")
print(f"   Restricciones: {len(resultado.restricciones_encontradas)}")
print(f"   Área total: {resultado.area_total_ha} ha")

# 4. Generar PDF
print("\n4️⃣ Generando PDF...")
generador = GeneradorPDFLegal()

output_path = f'informe_legal_bio_energy_300ha.pdf'
ruta_pdf = generador.generar_pdf(
    parcela=parcela,
    resultado=resultado,
    verificador=verificador,
    output_path=output_path,
    departamento='Casanare'
)

print(f"\n✅ PDF generado: {ruta_pdf}")
print(f"   Tamaño: {os.path.getsize(ruta_pdf) / 1024 / 1024:.2f} MB")

print(f"\n🔍 Abriendo PDF...")
os.system(f"open {ruta_pdf}")

print("\n" + "="*80)
print("✅ COMPLETADO - Revisa el PDF generado")
print("="*80)
