#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug: Verificar datos de red hídrica para Bio Energy
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
import json

print("="*80)
print("🔍 DEBUG: DATOS DE RED HÍDRICA - BIO ENERGY")
print("="*80)

# Cargar parcela
parcela = Parcela.objects.get(id=11)
print(f"\n📍 Parcela: {parcela.nombre} ({parcela.area_hectareas} ha)")

# Crear verificador
verificador = VerificadorRestriccionesLegales()

# PRIMERO: Ejecutar verificar_parcela para que cargue las capas
print("\n🔄 Ejecutando verificar_parcela() (carga automática de capas)...")
resultado = verificador.verificar_parcela(
    parcela_id=parcela.id,
    geometria_parcela=parcela.geometria,
    nombre_parcela=parcela.nombre
)
print(f"✅ Verificación completada")

# SEGUNDO: Ejecutar verificación de retiros hídricos
print("\n🌊 Ejecutando verificar_retiros_hidricos()...")
restricciones_hidricos, area_restringida = verificador.verificar_retiros_hidricos(
    geometria_parcela=parcela.geometria,
    distancia_maxima_km=5.0
)

print(f"\n✅ Restricciones hídricas encontradas: {len(restricciones_hidricos)}")
print(f"   Área restringida: {area_restringida} ha")

if restricciones_hidricos:
    print(f"\n📋 DETALLES DE RESTRICCIONES HÍDRICAS:")
    for i, rest in enumerate(restricciones_hidricos, 1):
        print(f"\n   {i}. {rest.get('nombre', 'Sin nombre')}")
        print(f"      • Tipo: {rest.get('subtipo', 'N/A')}")
        print(f"      • Distancia real: {rest.get('distancia_real_m', 0):.2f} m")
        print(f"      • Retiro mínimo: {rest.get('retiro_minimo_m', 30)} m")
        print(f"      • Área afectada: {rest.get('area_afectada_ha', 0):.4f} ha")
        print(f"      • Geometría: {rest.get('tipo_geometria', 'N/A')}")
else:
    print("\n⚠️  NO SE ENCONTRARON RESTRICCIONES HÍDRICAS")
    print("   Esto puede significar:")
    print("   - No hay cuerpos de agua dentro de 5 km")
    print("   - La red hídrica no está cargada")
    print("   - Error en el proceso de verificación")

# Verificar si red hídrica está cargada
print(f"\n🔍 Estado del verificador:")
print(f"   Red hídrica cargada: {verificador.stats['red_hidrica_loaded']}")
if verificador.red_hidrica is not None:
    print(f"   Elementos en red hídrica: {len(verificador.red_hidrica)}")
else:
    print(f"   ⚠️  Red hídrica es None")

print("\n" + "="*80)
