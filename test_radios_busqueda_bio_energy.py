#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug: Probar diferentes radios de búsqueda para Bio Energy
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales

print("="*80)
print("🔍 TEST: RADIOS DE BÚSQUEDA - BIO ENERGY")
print("="*80)

# Cargar parcela
parcela = Parcela.objects.get(id=11)
print(f"\n📍 Parcela: {parcela.nombre} ({parcela.area_hectareas} ha)")

# Crear verificador y cargar capas
verificador = VerificadorRestriccionesLegales()
print("\n📥 Cargando capas...")
verificador.cargar_red_hidrica()
verificador.cargar_areas_protegidas()
verificador.cargar_resguardos_indigenas()
verificador.cargar_paramos()
print(f"✅ Capas cargadas: {len(verificador.red_hidrica)} elementos en red hídrica")

# Probar diferentes radios
radios_km = [1, 2, 5, 10, 20, 50]

for radio in radios_km:
    print(f"\n{'='*60}")
    print(f"🔍 Probando radio de {radio} km...")
    
    restricciones, area = verificador.verificar_retiros_hidricos(
        geometria_parcela=parcela.geometria,
        distancia_maxima_km=radio
    )
    
    if restricciones:
        print(f"   ✅ {len(restricciones)} restricciones encontradas")
        # Mostrar solo la primera (la más cercana)
        r = restricciones[0]
        print(f"   📍 Más cercano: {r.get('nombre', 'Sin nombre')}")
        print(f"      • Distancia: {r.get('distancia_real_m', 0):.0f} m ({r.get('distancia_real_m', 0)/1000:.2f} km)")
        print(f"      • Tipo: {r.get('subtipo', 'N/A')}")
        break
    else:
        print(f"   ❌ No se encontraron cauces dentro de {radio} km")

print("\n" + "="*80)
