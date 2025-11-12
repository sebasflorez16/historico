#!/usr/bin/env python
"""
Test directo del Weather API de EOSDA
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.services.eosda_api import eosda_service
from datetime import date

print("=" * 80)
print("TEST DIRECTO: Weather API de EOSDA")
print("=" * 80)

field_id = "10800473"
fecha_inicio = date(2025, 10, 1)
fecha_fin = date(2025, 11, 11)

print(f"\n📍 Field ID: {field_id}")
print(f"📅 Rango: {fecha_inicio} a {fecha_fin}")

# Llamar directamente al método de datos climáticos
print("\n🌡️ Llamando a Weather API...")
datos_clima = eosda_service._obtener_datos_climaticos_por_field_id(
    field_id=field_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin
)

print(f"\n✅ Resultado: {len(datos_clima)} días de datos")

if datos_clima:
    print("\n📊 Primeros 10 días:")
    for i, dato in enumerate(datos_clima[:10]):
        temp_prom = dato.get('temperatura_promedio')
        temp_min = dato.get('temperatura_minima')
        temp_max = dato.get('temperatura_maxima')
        precip = dato.get('precipitacion_total', 0)
        
        temp_prom_str = f"{temp_prom:.1f}" if temp_prom is not None else "N/A"
        temp_min_str = f"{temp_min:.1f}" if temp_min is not None else "N/A"
        temp_max_str = f"{temp_max:.1f}" if temp_max is not None else "N/A"
        precip_str = f"{precip:.1f}" if precip is not None else "0"
        
        print(f"   {i+1}. {dato['fecha']}: "
              f"Temp={temp_prom_str}°C "
              f"(min={temp_min_str}°C, "
              f"max={temp_max_str}°C), "
              f"Precip={precip_str}mm")
else:
    print("\n⚠️ No se obtuvieron datos climáticos")
    print("   Posibles razones:")
    print("   - API key sin acceso a Weather API")
    print("   - Field ID inválido")
    print("   - Rango de fechas fuera de cobertura")

print("\n" + "=" * 80)
