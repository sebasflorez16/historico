#!/usr/bin/env python
"""
Script para corregir los paths de las imágenes satelitales en la base de datos
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'historical'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')

# Inicializar Django
django.setup()

from informes.models import IndiceMensual

def main():
    print("=" * 60)
    print("🔧 CORRECCIÓN DE PATHS DE IMÁGENES SATELITALES")
    print("=" * 60)
    
    # Obtener todos los índices con imágenes
    indices = IndiceMensual.objects.all()
    
    actualizados = 0
    errores = 0
    
    for idx in indices:
        updated = False
        
        # Verificar y corregir imagen_ndvi
        if idx.imagen_ndvi:
            old_path = str(idx.imagen_ndvi)
            # Reemplazar historical/media por media
            new_path = old_path.replace('historical/media/', 'media/')
            
            if old_path != new_path:
                # Verificar si el nuevo path existe
                full_path = os.path.join('/Users/sebastianflorez/Documents/Historico Agrotech/historico', new_path)
                if os.path.exists(full_path):
                    idx.imagen_ndvi = new_path
                    updated = True
                    print(f"✓ NDVI: {idx.periodo_texto}")
                else:
                    print(f"✗ NDVI no encontrado: {full_path}")
                    errores += 1
        
        # Verificar y corregir imagen_ndmi
        if idx.imagen_ndmi:
            old_path = str(idx.imagen_ndmi)
            new_path = old_path.replace('historical/media/', 'media/')
            
            if old_path != new_path:
                full_path = os.path.join('/Users/sebastianflorez/Documents/Historico Agrotech/historico', new_path)
                if os.path.exists(full_path):
                    idx.imagen_ndmi = new_path
                    updated = True
                    print(f"✓ NDMI: {idx.periodo_texto}")
                else:
                    print(f"✗ NDMI no encontrado: {full_path}")
                    errores += 1
        
        # Verificar y corregir imagen_savi
        if idx.imagen_savi:
            old_path = str(idx.imagen_savi)
            new_path = old_path.replace('historical/media/', 'media/')
            
            if old_path != new_path:
                full_path = os.path.join('/Users/sebastianflorez/Documents/Historico Agrotech/historico', new_path)
                if os.path.exists(full_path):
                    idx.imagen_savi = new_path
                    updated = True
                    print(f"✓ SAVI: {idx.periodo_texto}")
                else:
                    print(f"✗ SAVI no encontrado: {full_path}")
                    errores += 1
        
        if updated:
            idx.save()
            actualizados += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Índices actualizados: {actualizados}")
    print(f"❌ Errores: {errores}")
    print("=" * 60)

if __name__ == '__main__':
    main()
