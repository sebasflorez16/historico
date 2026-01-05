#!/usr/bin/env python
"""Verifica qué campos ve Django en el modelo Informe"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Informe

print("✅ Campos del modelo Informe en Django:")
print("=" * 60)

campos = sorted(Informe._meta.get_fields(), key=lambda x: x.name)
for f in campos:
    print(f"  - {f.name} ({type(f).__name__})")

print(f"\n📊 Total de campos: {len(campos)}")

# Verificar si existen los campos de pago
campos_pago = ['precio_base', 'descuento_porcentaje', 'precio_final', 'estado_pago', 
               'monto_pagado', 'saldo_pendiente', 'fecha_pago', 'fecha_vencimiento',
               'metodo_pago', 'referencia_pago', 'notas_pago', 'cliente']

print("\n💰 Campos de pago:")
for campo in campos_pago:
    existe = hasattr(Informe, campo)
    print(f"  {'✅' if existe else '❌'} {campo}")
