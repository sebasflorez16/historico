#!/usr/bin/env python
"""
🧪 TEST: Detector Geográfico Automático
========================================

Prueba el sistema de detección automática de departamento y municipio.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from detector_geografico import DetectorGeografico

print("=" * 80)
print("🧪 TEST: DETECTOR GEOGRÁFICO AUTOMÁTICO")
print("=" * 80)

# Cargar Parcela 6
try:
    parcela = Parcela.objects.get(pk=6)
    print(f"\n✅ Parcela cargada: {parcela.nombre}")
    print(f"   Área: {parcela.area_hectareas:.2f} ha")
except Parcela.DoesNotExist:
    print("\n❌ Parcela 6 no encontrada")
    sys.exit(1)

# Inicializar detector
print("\n📍 Inicializando detector geográfico...")
detector = DetectorGeografico()

# Detectar ubicación
print("\n🔍 Detectando ubicación geográfica...")
resultado = detector.detectar_ubicacion(parcela.geometria)

# Mostrar resultados
print("\n" + "=" * 80)
print("📊 RESULTADOS DE DETECCIÓN")
print("=" * 80)

if resultado['exito']:
    print(f"✅ Detección exitosa")
    print(f"\n🗺️  Ubicación administrativa:")
    print(f"   • Departamento: {resultado['departamento']}")
    print(f"   • Municipio: {resultado['municipio']}")
    print(f"   • Centroide: {resultado['centroide'].y:.6f}°N, {abs(resultado['centroide'].x):.6f}°W")
    
    # Cargar capas del departamento detectado
    print(f"\n📦 Cargando capas geográficas del departamento...")
    capas = detector.cargar_capas_departamento(resultado['departamento'])
    
    if capas['exito']:
        print(f"✅ Capas cargadas exitosamente")
        if capas['red_hidrica'] is not None:
            print(f"   • Red hídrica: {len(capas['red_hidrica'])} elementos")
        if capas['areas_protegidas'] is not None:
            print(f"   • Áreas protegidas: {len(capas['areas_protegidas'])} elementos")
    else:
        print(f"⚠️  Algunas capas no se pudieron cargar:")
        for error in capas['errores']:
            print(f"   • {error}")
    
    # Filtrar red hídrica al municipio
    if capas['red_hidrica'] is not None and resultado['municipio_gdf'] is not None:
        print(f"\n🎯 Filtrando red hídrica al municipio {resultado['municipio']}...")
        municipio_bounds = resultado['municipio_gdf'].total_bounds
        
        red_municipal = capas['red_hidrica'].cx[
            municipio_bounds[0]:municipio_bounds[2],
            municipio_bounds[1]:municipio_bounds[3]
        ]
        
        print(f"   ✅ Red hídrica municipal: {len(red_municipal)} elementos")
        
        # Contar ríos con nombre (buscar en varios campos posibles)
        rios_con_nombre = 0
        campo_nombre = None
        
        for posible_campo in ['name', 'NOMBRE_GEO', 'NOMBRE', 'nombre', 'NAME']:
            if posible_campo in red_municipal.columns:
                rios_con_nombre = red_municipal[posible_campo].notna().sum()
                if rios_con_nombre > 0:
                    campo_nombre = posible_campo
                    break
        
        print(f"   📛 Ríos con nombre: {rios_con_nombre} (campo: {campo_nombre})")
        
        if rios_con_nombre > 0 and campo_nombre:
            print(f"\n🏷️  Primeros ríos encontrados:")
            nombres_unicos = red_municipal[campo_nombre].dropna().unique()[:10]
            for i, nombre in enumerate(nombres_unicos, 1):
                print(f"      {i}. {nombre}")
    
else:
    print(f"❌ Error en detección: {resultado['error']}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO")
print("=" * 80)
