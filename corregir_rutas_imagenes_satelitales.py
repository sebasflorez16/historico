#!/usr/bin/env python
"""
Script para corregir rutas de imágenes satelitales que están en carpetas incorrectas
Las imágenes se guardaron con la fecha del servidor, no del registro
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual
from django.conf import settings
import shutil

def analizar_imagenes():
    """Analiza todas las imágenes y detecta rutas incorrectas"""
    print("=" * 80)
    print("ANÁLISIS DE RUTAS DE IMÁGENES SATELITALES")
    print("=" * 80)
    
    registros = IndiceMensual.objects.exclude(
        imagen_ndvi__isnull=True,
        imagen_ndmi__isnull=True,
        imagen_savi__isnull=True
    ).order_by('año', 'mes')
    
    total = registros.count()
    print(f"\nTotal de registros con imágenes: {total}\n")
    
    incorrectas = []
    
    for r in registros:
        problemas = []
        
        # Verificar NDVI
        if r.imagen_ndvi:
            ruta_actual = r.imagen_ndvi.name
            ruta_esperada = f'imagenes_satelitales/{r.año}/{r.mes:02d}/ndvi/'
            
            if not ruta_actual.startswith(ruta_esperada):
                problemas.append({
                    'tipo': 'NDVI',
                    'campo': 'imagen_ndvi',
                    'ruta_actual': ruta_actual,
                    'ruta_esperada': ruta_esperada,
                    'archivo': os.path.basename(ruta_actual)
                })
        
        # Verificar NDMI
        if r.imagen_ndmi:
            ruta_actual = r.imagen_ndmi.name
            ruta_esperada = f'imagenes_satelitales/{r.año}/{r.mes:02d}/ndmi/'
            
            if not ruta_actual.startswith(ruta_esperada):
                problemas.append({
                    'tipo': 'NDMI',
                    'campo': 'imagen_ndmi',
                    'ruta_actual': ruta_actual,
                    'ruta_esperada': ruta_esperada,
                    'archivo': os.path.basename(ruta_actual)
                })
        
        # Verificar SAVI
        if r.imagen_savi:
            ruta_actual = r.imagen_savi.name
            ruta_esperada = f'imagenes_satelitales/{r.año}/{r.mes:02d}/savi/'
            
            if not ruta_actual.startswith(ruta_esperada):
                problemas.append({
                    'tipo': 'SAVI',
                    'campo': 'imagen_savi',
                    'ruta_actual': ruta_actual,
                    'ruta_esperada': ruta_esperada,
                    'archivo': os.path.basename(ruta_actual)
                })
        
        if problemas:
            incorrectas.append({
                'registro': r,
                'problemas': problemas
            })
    
    print(f"Registros con rutas incorrectas: {len(incorrectas)}\n")
    
    for item in incorrectas:
        r = item['registro']
        print(f"Registro ID {r.id} - {r.año}/{r.mes:02d} ({r.parcela.nombre})")
        for p in item['problemas']:
            print(f"  {p['tipo']}: {p['ruta_actual']}")
            print(f"         → {p['ruta_esperada']}{p['archivo']}")
        print()
    
    return incorrectas


def corregir_imagenes(incorrectas, dry_run=True):
    """Mueve las imágenes a sus rutas correctas"""
    
    if dry_run:
        print("\n" + "=" * 80)
        print("MODO DRY-RUN: No se harán cambios reales")
        print("=" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print("CORRIGIENDO RUTAS DE IMÁGENES")
        print("=" * 80 + "\n")
    
    media_root = Path(settings.MEDIA_ROOT)
    corregidas = 0
    errores = 0
    
    for item in incorrectas:
        r = item['registro']
        registro_modificado = False
        
        for p in item['problemas']:
            origen = media_root / p['ruta_actual']
            destino = media_root / (p['ruta_esperada'] + p['archivo'])
            
            if not origen.exists():
                print(f"❌ No existe: {origen}")
                errores += 1
                continue
            
            if dry_run:
                print(f"✓ Se movería: {origen.name}")
                print(f"  Desde: {p['ruta_actual']}")
                print(f"  Hacia: {p['ruta_esperada']}{p['archivo']}")
                corregidas += 1
            else:
                try:
                    # Crear directorio destino
                    destino.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Mover archivo
                    shutil.move(str(origen), str(destino))
                    
                    # Actualizar registro en BD
                    setattr(r, p['campo'], str(p['ruta_esperada'] + p['archivo']))
                    registro_modificado = True
                    
                    print(f"✅ Movido: {p['archivo']}")
                    print(f"   → {p['ruta_esperada']}")
                    corregidas += 1
                    
                except Exception as e:
                    print(f"❌ Error moviendo {p['archivo']}: {e}")
                    errores += 1
        
        if registro_modificado and not dry_run:
            r.save()
            print(f"   💾 Registro {r.id} actualizado\n")
    
    print("\n" + "=" * 80)
    print(f"Imágenes corregidas: {corregidas}")
    print(f"Errores: {errores}")
    print("=" * 80)


if __name__ == '__main__':
    import sys
    
    # Analizar
    incorrectas = analizar_imagenes()
    
    if not incorrectas:
        print("✅ Todas las imágenes están en las rutas correctas")
        sys.exit(0)
    
    # Por defecto hacer dry-run
    dry_run = '--ejecutar' not in sys.argv
    
    corregir_imagenes(incorrectas, dry_run=dry_run)
    
    if dry_run:
        print("\n💡 Para ejecutar los cambios reales, usa: python corregir_rutas_imagenes_satelitales.py --ejecutar")
