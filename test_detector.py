#!/usr/bin/env python
"""Test del detector geográfico"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from detector_geografico import DetectorGeografico

parcela = Parcela.objects.get(pk=6)
detector = DetectorGeografico()
resultado = detector.proceso_completo(parcela.geometria)

print(f"\n📍 Resultado:")
print(f"   Departamento: {resultado['departamento']}")
print(f"   Municipio: {resultado['municipio']}")
print(f"   Red hídrica: {len(resultado['red_hidrica']) if resultado.get('red_hidrica') is not None else 0} elementos")
