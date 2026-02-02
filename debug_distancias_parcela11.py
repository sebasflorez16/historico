#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug de distancias para parcela 11 (Bio Energy - 308 ha)
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal
import json

print("\n" + "="*80)
print("🔍 DEBUG - Análisis de Distancias Parcela #11 (Bio Energy)")
print("="*80)

# Cargar parcela
parcela = Parcela.objects.get(id=11)
print(f"\n✅ Parcela cargada: {parcela.nombre}")
print(f"   Área: {parcela.area_hectareas} ha")
print(f"   Propietario: {parcela.propietario}")
print(f"   Cultivo: {parcela.tipo_cultivo}")

# Inicializar verificador
print("\n🔍 Inicializando verificador...")
verificador = VerificadorRestriccionesLegales()

# Inicializar generador
print("🔍 Inicializando generador PDF...")
generador = GeneradorPDFLegal()

# Calcular distancias
print("\n🔍 Calculando distancias...")
distancias = generador._calcular_distancias_minimas(parcela, verificador, "Casanare")

print("\n📊 RESULTADO DEL CÁLCULO DE DISTANCIAS:")
print("="*80)
print(json.dumps(distancias, indent=2, ensure_ascii=False))

print("\n🔍 ANÁLISIS DE CADA CAPA:")
print("="*80)

# Áreas protegidas
if 'areas_protegidas' in distancias:
    print("\n✅ Áreas Protegidas:")
    print(json.dumps(distancias['areas_protegidas'], indent=2, ensure_ascii=False))
else:
    print("\n❌ Áreas Protegidas: NO ENCONTRADA EN DICCIONARIO")

# Resguardos
if 'resguardos_indigenas' in distancias:
    print("\n✅ Resguardos Indígenas:")
    print(json.dumps(distancias['resguardos_indigenas'], indent=2, ensure_ascii=False))
else:
    print("\n❌ Resguardos Indígenas: NO ENCONTRADA EN DICCIONARIO")

# Red hídrica
if 'red_hidrica' in distancias:
    print("\n✅ Red Hídrica:")
    print(json.dumps(distancias['red_hidrica'], indent=2, ensure_ascii=False))
else:
    print("\n❌ Red Hídrica: NO ENCONTRADA EN DICCIONARIO")

# Páramos
if 'paramos' in distancias:
    print("\n✅ Páramos:")
    print(json.dumps(distancias['paramos'], indent=2, ensure_ascii=False))
else:
    print("\n❌ Páramos: NO ENCONTRADA EN DICCIONARIO")

print("\n" + "="*80)
print("✅ FIN DEL DEBUG")
print("="*80)
