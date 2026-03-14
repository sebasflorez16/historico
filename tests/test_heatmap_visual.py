#!/usr/bin/env python
"""
Test visual rápido del generador de heatmaps mejorado.
Genera 3 imágenes PNG de prueba para verificar que la distribución 
de colores se ve realista (zonas verdes, amarillas, rojas diferenciadas).

Uso: python tests/test_heatmap_visual.py
"""
import sys
import os
import time

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')

import django
django.setup()

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
import numpy as np
from pathlib import Path

# Importar la función del módulo
from informes.views_demo import _generar_un_heatmap

# Coordenadas de prueba: polígono irregular (simula parcela real en Colombia)
coords_poligono = [
    (-75.510, 6.230),
    (-75.505, 6.235),
    (-75.498, 6.234),
    (-75.495, 6.228),
    (-75.497, 6.222),
    (-75.503, 6.220),
    (-75.508, 6.222),
    (-75.510, 6.226),
    (-75.510, 6.230),  # Cerrar polígono
]

lons = [c[0] for c in coords_poligono]
lats = [c[1] for c in coords_poligono]

# Directorio de salida
dir_test = Path('tests/output_heatmap_test')
dir_test.mkdir(parents=True, exist_ok=True)

# Configuraciones de prueba
tests = [
    {
        'nombre': 'NDVI',
        'mean': 0.55, 'std': 0.18, 'vmin_real': 0.20, 'vmax_real': 0.85,
        'cmap': 'RdYlGn', 'vmin_d': 0.0, 'vmax_d': 1.0,
        'titulo': 'Salud del Cultivo (NDVI)', 'label': 'NDVI',
    },
    {
        'nombre': 'NDMI',
        'mean': 0.10, 'std': 0.15, 'vmin_real': -0.20, 'vmax_real': 0.40,
        'cmap': 'RdBu', 'vmin_d': -0.5, 'vmax_d': 0.5,
        'titulo': 'Nivel de Humedad (NDMI)', 'label': 'NDMI',
    },
    {
        'nombre': 'SAVI',
        'mean': 0.42, 'std': 0.16, 'vmin_real': 0.12, 'vmax_real': 0.70,
        'cmap': 'YlGn', 'vmin_d': 0.0, 'vmax_d': 0.8,
        'titulo': 'Vegetación del Suelo (SAVI)', 'label': 'SAVI',
    },
]

from datetime import date
fecha_test = date(2026, 3, 9)

print("🧪 Generando imágenes de prueba con distribución MEJORADA...")
print(f"   📂 Salida: {dir_test.absolute()}")
print()

for t in tests:
    ruta = dir_test / f'{t["nombre"].lower()}_test.png'
    inicio = time.time()
    
    _generar_un_heatmap(
        lons, lats, coords_poligono,
        t['mean'], t['std'], t['vmin_real'], t['vmax_real'],
        t['cmap'], t['vmin_d'], t['vmax_d'],
        t['titulo'], t['label'],
        ruta, 25.3, fecha_test,
    )
    
    elapsed = time.time() - inicio
    
    if ruta.exists():
        size_kb = ruta.stat().st_size / 1024
        print(f"   ✅ {t['nombre']}: {size_kb:.0f} KB — {elapsed:.2f}s — {ruta}")
    else:
        print(f"   ❌ {t['nombre']}: NO SE GENERÓ")

print()
print("🎉 Listo. Abre las imágenes en tests/output_heatmap_test/ para verificar visualmente.")
