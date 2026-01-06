#!/usr/bin/env python
"""
Test del Weather API de EOSDA para datos climáticos históricos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from django.contrib.auth.models import User
from informes.services.eosda_api import eosda_service
from datetime import date

print("=" * 80)
print("TEST: Weather API - Datos Climáticos Históricos")
print("=" * 80)

# Obtener parcela
parcela = Parcela.objects.get(id=2)
usuario = User.objects.first()

print(f"\n📍 Parcela: {parcela.nombre}")
print(f"   Field ID: {parcela.eosda_field_id}")
print(f"👤 Usuario: {usuario.username}")

# Limpiar datos previos
registros_previos = IndiceMensual.objects.filter(parcela=parcela).count()
IndiceMensual.objects.filter(parcela=parcela).delete()
print(f"\n🗑️  Eliminados {registros_previos} registros previos")

# Obtener datos (incluye datos climáticos)
print("\n📡 Obteniendo datos de EOSDA (índices + clima)...")
datos_satelitales = eosda_service.obtener_datos_optimizado(
    parcela=parcela,
    fecha_inicio=date(2025, 10, 1),
    fecha_fin=date(2025, 11, 11),
    indices=['NDVI', 'NDMI', 'SAVI'],
    usuario=usuario,
    max_nubosidad=80
)

print(f"\n✅ Datos obtenidos:")
print(f"   - Escenas satelitales: {len(datos_satelitales.get('resultados', []))}")
print(f"   - Datos climáticos: {len(datos_satelitales.get('datos_clima', []))} días")

# Mostrar muestra de datos climáticos
datos_clima = datos_satelitales.get('datos_clima', [])
if datos_clima:
    print(f"\n🌡️ Muestra de datos climáticos (primeros 5 días):")
    for i, dato in enumerate(datos_clima[:5]):
        print(f"   {i+1}. {dato['fecha']}: "
              f"Temp={dato.get('temperatura_promedio', 'N/A')}°C "
              f"(min={dato.get('temperatura_minima', 'N/A')}°C, "
              f"max={dato.get('temperatura_maxima', 'N/A')}°C), "
              f"Precip={dato.get('precipitacion_total', 0)}mm")
else:
    print("\n⚠️ No se obtuvieron datos climáticos")

# Procesar datos (simular lo que hace views.py)
print("\n" + "=" * 80)
print("PROCESAMIENTO DE DATOS")
print("=" * 80)

from collections import defaultdict
from datetime import datetime

# 1. Procesar índices satelitales
indices_creados = 0
datos_por_mes = defaultdict(lambda: {
    'ndvi_valores': [], 'ndvi_max': [], 'ndvi_min': [],
    'ndmi_valores': [], 'ndmi_max': [], 'ndmi_min': [],
    'savi_valores': [], 'savi_max': [], 'savi_min': [],
    'nubosidad': []
})

for escena in datos_satelitales.get('resultados', []):
    fecha = datetime.fromisoformat(escena['date']).date()
    clave_mes = (fecha.year, fecha.month)
    
    indexes = escena.get('indexes', {})
    if 'NDVI' in indexes:
        datos_por_mes[clave_mes]['ndvi_valores'].append(indexes['NDVI']['average'])
        datos_por_mes[clave_mes]['ndvi_max'].append(indexes['NDVI']['max'])
        datos_por_mes[clave_mes]['ndvi_min'].append(indexes['NDVI']['min'])
    
    if 'NDMI' in indexes:
        datos_por_mes[clave_mes]['ndmi_valores'].append(indexes['NDMI']['average'])
        datos_por_mes[clave_mes]['ndmi_max'].append(indexes['NDMI']['max'])
        datos_por_mes[clave_mes]['ndmi_min'].append(indexes['NDMI']['min'])
    
    if 'SAVI' in indexes:
        datos_por_mes[clave_mes]['savi_valores'].append(indexes['SAVI']['average'])
        datos_por_mes[clave_mes]['savi_max'].append(indexes['SAVI']['max'])
        datos_por_mes[clave_mes]['savi_min'].append(indexes['SAVI']['min'])
    
    datos_por_mes[clave_mes]['nubosidad'].append(escena['cloud'])

# Guardar índices
for (year, month), datos in datos_por_mes.items():
    ndvi_prom = sum(datos['ndvi_valores']) / len(datos['ndvi_valores']) if datos['ndvi_valores'] else None
    ndmi_prom = sum(datos['ndmi_valores']) / len(datos['ndmi_valores']) if datos['ndmi_valores'] else None
    savi_prom = sum(datos['savi_valores']) / len(datos['savi_valores']) if datos['savi_valores'] else None
    nub_prom = sum(datos['nubosidad']) / len(datos['nubosidad']) if datos['nubosidad'] else 0
    
    indice, created = IndiceMensual.objects.update_or_create(
        parcela=parcela,
        año=year,
        mes=month,
        defaults={
            'ndvi_promedio': ndvi_prom,
            'ndvi_maximo': max(datos['ndvi_max']) if datos['ndvi_max'] else None,
            'ndvi_minimo': min(datos['ndvi_min']) if datos['ndvi_min'] else None,
            'ndmi_promedio': ndmi_prom,
            'ndmi_maximo': max(datos['ndmi_max']) if datos['ndmi_max'] else None,
            'ndmi_minimo': min(datos['ndmi_min']) if datos['ndmi_min'] else None,
            'savi_promedio': savi_prom,
            'savi_maximo': max(datos['savi_max']) if datos['savi_max'] else None,
            'savi_minimo': min(datos['savi_min']) if datos['savi_min'] else None,
            'nubosidad_promedio': nub_prom,
            'fuente_datos': 'EOSDA',
            'calidad_datos': 'buena' if nub_prom < 30 else 'regular'
        }
    )
    if created:
        indices_creados += 1

print(f"\n✅ Índices guardados: {indices_creados} registros mensuales")

# 2. Procesar datos climáticos
if datos_satelitales.get('datos_clima'):
    datos_clima_por_mes = defaultdict(lambda: {
        'temp_promedio': [], 'temp_max': [], 'temp_min': [], 'precipitacion': []
    })
    
    for dato in datos_satelitales.get('datos_clima', []):
        fecha_dato = dato.get('fecha')
        if isinstance(fecha_dato, str):
            fecha_dato = datetime.fromisoformat(fecha_dato).date()
        
        clave_mes = (fecha_dato.year, fecha_dato.month)
        
        if dato.get('temperatura_promedio') is not None:
            datos_clima_por_mes[clave_mes]['temp_promedio'].append(dato['temperatura_promedio'])
        if dato.get('temperatura_maxima') is not None:
            datos_clima_por_mes[clave_mes]['temp_max'].append(dato['temperatura_maxima'])
        if dato.get('temperatura_minima') is not None:
            datos_clima_por_mes[clave_mes]['temp_min'].append(dato['temperatura_minima'])
        if dato.get('precipitacion_total') is not None:
            datos_clima_por_mes[clave_mes]['precipitacion'].append(dato['precipitacion_total'])
    
    # Actualizar registros
    for (year, month), datos in datos_clima_por_mes.items():
        temp_prom = sum(datos['temp_promedio']) / len(datos['temp_promedio']) if datos['temp_promedio'] else None
        temp_max = max(datos['temp_max']) if datos['temp_max'] else None
        temp_min = min(datos['temp_min']) if datos['temp_min'] else None
        precip_total = sum(datos['precipitacion']) if datos['precipitacion'] else None
        
        registros_actualizados = IndiceMensual.objects.filter(
            parcela=parcela,
            año=year,
            mes=month
        ).update(
            temperatura_promedio=temp_prom,
            temperatura_maxima=temp_max,
            temperatura_minima=temp_min,
            precipitacion_total=precip_total
        )
        
        if registros_actualizados > 0:
            temp_str = f"{temp_prom:.1f}" if temp_prom is not None else "N/A"
            temp_min_str = f"{temp_min:.1f}" if temp_min is not None else "N/A"
            temp_max_str = f"{temp_max:.1f}" if temp_max is not None else "N/A"
            precip_str = f"{precip_total:.1f}" if precip_total is not None else "0"
            
            print(f"\n   🌡️ {month:02d}/{year}: "
                  f"Temp={temp_str}°C "
                  f"(min={temp_min_str}°C, "
                  f"max={temp_max_str}°C), "
                  f"Precip={precip_str}mm")

print("\n" + "=" * 80)
print("VERIFICACIÓN EN BASE DE DATOS")
print("=" * 80)

registros = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
print(f"\n📋 Total de registros: {registros.count()}")

for reg in registros:
    ndvi_str = f"{reg.ndvi_promedio:.3f}" if reg.ndvi_promedio else "N/A"
    temp_str = f"{reg.temperatura_promedio:.1f}°C" if reg.temperatura_promedio else "N/A"
    precip_str = f"{reg.precipitacion_total:.1f}mm" if reg.precipitacion_total else "N/A"
    
    print(f"\n   📅 {reg.mes:02d}/{reg.año}:")
    print(f"      🌱 NDVI: {ndvi_str}")
    print(f"      🌡️  Temp: {temp_str}")
    print(f"      💧 Precip: {precip_str}")
    print(f"      ☁️  Nubosidad: {reg.nubosidad_promedio:.1f}%")
    print(f"      ✓ Calidad: {reg.calidad_datos}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO")
print("=" * 80)
