#!/usr/bin/env python
"""
Script para actualizar datos climáticos de todas las parcelas con caché antiguo
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, CacheDatosEOSDA, IndiceMensual
from django.contrib.auth.models import User
from informes.services.eosda_api import eosda_service
from datetime import date, datetime, timedelta

print("=" * 80)
print("ACTUALIZAR DATOS CLIMÁTICOS - TODAS LAS PARCELAS")
print("=" * 80)

# Obtener todas las parcelas con field_id
parcelas = Parcela.objects.exclude(eosda_field_id__isnull=True).exclude(eosda_field_id='')
usuario = User.objects.first()

print(f"\n📊 Total de parcelas: {parcelas.count()}")
print(f"👤 Usuario: {usuario.username}")

# Opción 1: Actualizar caché existente agregando datos climáticos
print("\n" + "=" * 80)
print("OPCIÓN 1: Actualizar cachés existentes (más rápido)")
print("=" * 80)

caches_actualizados = 0
for cache in CacheDatosEOSDA.objects.all():
    tiene_clima = cache.datos_json.get('datos_clima') and len(cache.datos_json.get('datos_clima', [])) > 0
    
    if not tiene_clima:
        print(f"\n🔄 Actualizando caché para field {cache.field_id}...")
        print(f"   Rango: {cache.fecha_inicio} a {cache.fecha_fin}")
        
        try:
            # Obtener datos climáticos
            datos_clima = eosda_service._obtener_datos_climaticos_por_field_id(
                field_id=cache.field_id,
                fecha_inicio=cache.fecha_inicio,
                fecha_fin=cache.fecha_fin
            )
            
            if datos_clima:
                # Convertir fechas a string
                datos_clima_serializables = []
                for dato in datos_clima:
                    dato_serializable = dato.copy()
                    if isinstance(dato_serializable.get('fecha'), date):
                        dato_serializable['fecha'] = dato_serializable['fecha'].isoformat()
                    datos_clima_serializables.append(dato_serializable)
                
                # Actualizar caché
                cache.datos_json['datos_clima'] = datos_clima_serializables
                cache.save()
                
                caches_actualizados += 1
                print(f"   ✅ {len(datos_clima)} días de datos climáticos agregados")
            else:
                print(f"   ⚠️ No se obtuvieron datos climáticos")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    else:
        print(f"\n✓ Field {cache.field_id} ya tiene datos climáticos ({len(cache.datos_json.get('datos_clima', []))} días)")

print(f"\n📊 Total de cachés actualizados: {caches_actualizados}")

# Opción 2: Actualizar IndiceMensual de todas las parcelas
print("\n" + "=" * 80)
print("OPCIÓN 2: Actualizar registros mensuales con datos climáticos")
print("=" * 80)

from collections import defaultdict

parcelas_actualizadas = 0
for parcela in parcelas:
    print(f"\n🌱 Procesando {parcela.nombre} (field {parcela.eosda_field_id})...")
    
    # Obtener caché actualizado
    # Buscar cualquier caché que tenga datos climáticos
    cache = CacheDatosEOSDA.objects.filter(
        field_id=parcela.eosda_field_id
    ).order_by('-creado_en').first()
    
    if not cache:
        print(f"   ⚠️ Sin caché - necesita actualizar datos EOSDA primero")
        continue
    
    datos_clima = cache.datos_json.get('datos_clima', [])
    if not datos_clima:
        print(f"   ⚠️ Caché sin datos climáticos")
        continue
    
    # Agrupar datos climáticos por mes
    datos_clima_por_mes = defaultdict(lambda: {
        'temp_promedio': [], 'temp_max': [], 'temp_min': [], 'precipitacion': []
    })
    
    for dato in datos_clima:
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
    
    # Actualizar registros mensuales
    registros_actualizados = 0
    for (year, month), datos in datos_clima_por_mes.items():
        temp_prom = sum(datos['temp_promedio']) / len(datos['temp_promedio']) if datos['temp_promedio'] else None
        temp_max = max(datos['temp_max']) if datos['temp_max'] else None
        temp_min = min(datos['temp_min']) if datos['temp_min'] else None
        precip_total = sum(datos['precipitacion']) if datos['precipitacion'] else None
        
        count = IndiceMensual.objects.filter(
            parcela=parcela,
            año=year,
            mes=month
        ).update(
            temperatura_promedio=temp_prom,
            temperatura_maxima=temp_max,
            temperatura_minima=temp_min,
            precipitacion_total=precip_total
        )
        
        if count > 0:
            registros_actualizados += count
            temp_str = f"{temp_prom:.1f}" if temp_prom else "N/A"
            precip_str = f"{precip_total:.1f}" if precip_total else "0"
            print(f"   ✅ {month:02d}/{year}: Temp={temp_str}°C, Precip={precip_str}mm")
    
    if registros_actualizados > 0:
        parcelas_actualizadas += 1
        print(f"   📊 {registros_actualizados} registros actualizados")
    else:
        print(f"   ⚠️ No hay registros mensuales para actualizar")

print("\n" + "=" * 80)
print("RESUMEN")
print("=" * 80)
print(f"\n✅ Cachés actualizados: {caches_actualizados}")
print(f"✅ Parcelas actualizadas: {parcelas_actualizadas}/{parcelas.count()}")
print("\n✓ Proceso completado")
