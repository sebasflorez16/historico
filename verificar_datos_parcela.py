#!/usr/bin/env python
"""
Script para verificar los datos de la parcela y generar informe completo
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/Users/sebastianflorez/Documents/Historico Agrotech/historico')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual

# Obtener la parcela 1
parcela = Parcela.objects.get(id=1)
print(f"\n{'='*80}")
print(f"PARCELA: {parcela.nombre}")
print(f"{'='*80}\n")

# Obtener todos los índices mensuales
indices = IndiceMensual.objects.filter(parcela=parcela).order_by('-año', '-mes')

print(f"Total de índices: {indices.count()}\n")

# Mostrar los últimos 5
print("Últimos 5 índices mensuales:")
print(f"{'Fecha':<12} {'NDVI':<10} {'NDMI':<10} {'SAVI':<10}")
print(f"{'-'*45}")

for idx in indices[:5]:
    fecha = f"{idx.año}-{idx.mes:02d}"
    ndvi = f"{idx.ndvi_promedio:.3f}" if idx.ndvi_promedio is not None else "None"
    ndmi = f"{idx.ndmi_promedio:.3f}" if idx.ndmi_promedio is not None else "None"
    savi = f"{idx.savi_promedio:.3f}" if idx.savi_promedio is not None else "None"
    print(f"{fecha:<12} {ndvi:<10} {ndmi:<10} {savi:<10}")

# Verificar el último índice
ultimo = indices.first()
print(f"\n{'='*80}")
print(f"ÚLTIMO ÍNDICE MENSUAL ({ultimo.año}-{ultimo.mes:02d})")
print(f"{'='*80}")
print(f"NDVI promedio: {ultimo.ndvi_promedio}")
print(f"NDMI promedio: {ultimo.ndmi_promedio}")
print(f"SAVI promedio: {ultimo.savi_promedio}")
print(f"Imagen NDVI: {ultimo.imagen_ndvi}")
print(f"Imagen NDMI: {ultimo.imagen_ndmi}")
print(f"Imagen SAVI: {ultimo.imagen_savi}")

# Verificar geometría
print(f"\n{'='*80}")
print(f"GEOMETRÍA DE LA PARCELA")
print(f"{'='*80}")
print(f"Tiene geometría: {parcela.geometria is not None}")
if parcela.geometria:
    print(f"Tipo: {type(parcela.geometria)}")
    print(f"SRID: {parcela.geometria.srid}")
    print(f"Área calculada: {parcela.area_hectareas} ha")
    print(f"Extensión (bbox): {parcela.geometria.extent}")
