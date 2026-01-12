#!/usr/bin/env python
"""
Script para mover imágenes satelitales de rutas incorrectas a correctas
Las imágenes se guardaron con fecha del servidor (2026/01) en lugar de fecha del registro (año/mes)
"""

import os
import sys
import django
from pathlib import Path
import shutil

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import IndiceMensual

def mover_imagenes():
    """Mueve las imágenes de rutas incorrectas a correctas"""
    
    print("=" * 80)
    print("🔄 MIGRACIÓN DE IMÁGENES SATELITALES")
    print("=" * 80)
    
    # Obtener MEDIA_ROOT
    from django.conf import settings
    MEDIA_ROOT = settings.MEDIA_ROOT
    
    print(f"\n📁 MEDIA_ROOT: {MEDIA_ROOT}")
    
    # Contar registros con imágenes
    registros_con_imagenes = IndiceMensual.objects.filter(
        imagen_ndvi__isnull=False
    ) | IndiceMensual.objects.filter(
        imagen_ndmi__isnull=False
    ) | IndiceMensual.objects.filter(
        imagen_savi__isnull=False
    )
    
    total = registros_con_imagenes.count()
    print(f"\n📊 Total registros con imágenes: {total}")
    
    if total == 0:
        print("\n⚠️ No hay registros con imágenes para migrar")
        return
    
    # Analizar primeros 5 registros
    print("\n🔍 ANÁLISIS DE RUTAS ACTUALES:")
    print("-" * 80)
    
    for registro in registros_con_imagenes[:5]:
        print(f"\n📌 Registro ID: {registro.id} | Año: {registro.año} | Mes: {registro.mes:02d}")
        
        if registro.imagen_ndvi:
            print(f"   NDVI actual: {registro.imagen_ndvi.name}")
            ruta_correcta = f"imagenes_satelitales/{registro.año}/{registro.mes:02d}/ndvi/{os.path.basename(registro.imagen_ndvi.name)}"
            print(f"   NDVI correcta: {ruta_correcta}")
            
            # Verificar si archivo existe
            ruta_completa = os.path.join(MEDIA_ROOT, registro.imagen_ndvi.name)
            existe = os.path.exists(ruta_completa)
            print(f"   Archivo existe: {'✅' if existe else '❌'} {ruta_completa}")
        
        if registro.imagen_ndmi:
            print(f"   NDMI actual: {registro.imagen_ndmi.name}")
        
        if registro.imagen_savi:
            print(f"   SAVI actual: {registro.imagen_savi.name}")
    
    # Preguntar confirmación
    print("\n" + "=" * 80)
    respuesta = input("\n¿Proceder con la migración de TODAS las imágenes? (si/no): ")
    
    if respuesta.lower() not in ['si', 's', 'yes', 'y']:
        print("\n❌ Migración cancelada")
        return
    
    # Migrar todas las imágenes
    print("\n" + "=" * 80)
    print("🚀 INICIANDO MIGRACIÓN...")
    print("=" * 80)
    
    movidos = 0
    errores = 0
    ya_correctos = 0
    
    for registro in registros_con_imagenes:
        print(f"\n📄 Procesando registro {registro.id} ({registro.año}/{registro.mes:02d})...")
        
        # Procesar cada tipo de imagen
        for campo, indice in [('imagen_ndvi', 'ndvi'), ('imagen_ndmi', 'ndmi'), ('imagen_savi', 'savi')]:
            imagen_field = getattr(registro, campo)
            
            if not imagen_field:
                continue
            
            ruta_actual = imagen_field.name
            nombre_archivo = os.path.basename(ruta_actual)
            ruta_correcta = f"imagenes_satelitales/{registro.año}/{registro.mes:02d}/{indice}/{nombre_archivo}"
            
            # Si ya está en la ruta correcta, skip
            if ruta_actual == ruta_correcta:
                print(f"   ✓ {indice.upper()}: Ya en ruta correcta")
                ya_correctos += 1
                continue
            
            # Rutas completas
            archivo_actual = os.path.join(MEDIA_ROOT, ruta_actual)
            archivo_nuevo = os.path.join(MEDIA_ROOT, ruta_correcta)
            
            # Verificar que archivo origen existe
            if not os.path.exists(archivo_actual):
                print(f"   ⚠️ {indice.upper()}: Archivo no existe en {archivo_actual}")
                errores += 1
                continue
            
            try:
                # Crear directorio destino si no existe
                os.makedirs(os.path.dirname(archivo_nuevo), exist_ok=True)
                
                # Mover archivo
                shutil.move(archivo_actual, archivo_nuevo)
                
                # Actualizar campo en BD
                setattr(registro, campo, ruta_correcta)
                
                print(f"   ✅ {indice.upper()}: Movido a {ruta_correcta}")
                movidos += 1
                
            except Exception as e:
                print(f"   ❌ {indice.upper()}: Error - {str(e)}")
                errores += 1
        
        # Guardar cambios en BD
        if movidos > 0:
            registro.save()
    
    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("=" * 80)
    print(f"✅ Imágenes movidas: {movidos}")
    print(f"✓ Ya correctas: {ya_correctos}")
    print(f"❌ Errores: {errores}")
    print(f"📁 Total procesado: {movidos + ya_correctos + errores}")
    
    if movidos > 0:
        print("\n🎉 ¡Migración completada exitosamente!")
        print("💡 Recarga la galería y timeline para ver las imágenes")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    mover_imagenes()
