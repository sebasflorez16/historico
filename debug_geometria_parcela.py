#!/usr/bin/env python
"""
Debug: Verificar Geometría de Parcela
=====================================

Investiga qué tipo de geometría tiene la parcela y cómo convertirla correctamente.

Autor: AgroTech Team
Fecha: 21 enero 2026
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela

# Obtener parcela
parcela = Parcela.objects.get(id=6)

print("=" * 80)
print("🔍 DEBUG: GEOMETRÍA DE PARCELA")
print("=" * 80)
print()
print(f"Parcela: {parcela.nombre}")
print(f"Área: {parcela.area_hectareas:.2f} ha")
print()

if parcela.geometria:
    geom = parcela.geometria
    print(f"✅ Tiene geometría")
    print(f"   Tipo de objeto Python: {type(geom)}")
    print(f"   Tipo geométrico: {geom.geom_type}")
    print(f"   SRID: {geom.srid}")
    print(f"   Número de coordenadas: {geom.num_coords}")
    print()
    
    # Verificar interfaces disponibles
    print("Interfaces disponibles:")
    print(f"   __geo_interface__: {hasattr(geom, '__geo_interface__')}")
    if hasattr(geom, '__geo_interface__'):
        print(f"   __geo_interface__ keys: {geom.__geo_interface__.keys()}")
        print(f"   type: {geom.__geo_interface__['type']}")
    print()
    
    # Intentar conversión a shapely
    try:
        from shapely.geometry import shape, Polygon, MultiPolygon
        
        # Opción 1: Usar __geo_interface__
        if hasattr(geom, '__geo_interface__'):
            shapely_geom = shape(geom.__geo_interface__)
            print(f"✅ Conversión exitosa via __geo_interface__")
            print(f"   Tipo shapely: {type(shapely_geom)}")
            print(f"   Es Polygon: {isinstance(shapely_geom, Polygon)}")
            print(f"   Es MultiPolygon: {isinstance(shapely_geom, MultiPolygon)}")
            
            # Obtener coordenadas
            if isinstance(shapely_geom, Polygon):
                coords = list(shapely_geom.exterior.coords)
                print(f"   Número de vértices: {len(coords)}")
                print(f"   Primera coordenada: {coords[0]}")
                print(f"   Última coordenada: {coords[-1]}")
            print()
    except Exception as e:
        print(f"❌ Error en conversión shapely: {e}")
        import traceback
        traceback.print_exc()
    
    # Verificar si ya es shapely
    try:
        from shapely.geometry import Polygon, MultiPolygon
        if isinstance(geom, (Polygon, MultiPolygon)):
            print("✅ La geometría YA ES de tipo shapely")
        else:
            print("❌ La geometría NO es de tipo shapely")
    except Exception as e:
        print(f"Error verificando tipo: {e}")
    
else:
    print("❌ No tiene geometría")
