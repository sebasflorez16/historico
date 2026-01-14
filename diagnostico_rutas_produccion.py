#!/usr/bin/env python
"""
Script para diagnosticar y corregir rutas de imágenes satelitales en producción
Parcela ID 3 - Javier Rodriguez
Ejecutar dentro de Railway shell
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings_production')
django.setup()

from informes.models import IndiceMensual, Parcela
from django.conf import settings
from pathlib import Path

def diagnosticar_parcela_3():
    """Diagnostica el estado de las imágenes de la parcela 3"""
    
    print("\n" + "="*80)
    print("🔍 DIAGNÓSTICO DE RUTAS - PARCELA JAVIER RODRIGUEZ (ID: 3)")
    print("="*80 + "\n")
    
    # 1. Verificar que existe la parcela
    try:
        parcela = Parcela.objects.get(id=3)
        print(f"✅ Parcela encontrada: {parcela.nombre} - {parcela.propietario}")
        print(f"   EOSDA Field ID: {parcela.eosda_field_id}")
        print(f"   Sincronizada: {parcela.eosda_sincronizada}\n")
    except Parcela.DoesNotExist:
        print("❌ ERROR: No existe la parcela con ID 3")
        return
    
    # 2. Obtener todos los índices mensuales
    indices = IndiceMensual.objects.filter(parcela_id=3).order_by('año', 'mes')
    print(f"📊 Total de índices mensuales: {indices.count()}\n")
    
    if indices.count() == 0:
        print("⚠️  No hay índices mensuales registrados para esta parcela")
        return
    
    # 3. Verificar MEDIA_ROOT
    print(f"📁 MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"   Existe: {os.path.exists(settings.MEDIA_ROOT)}\n")
    
    # 4. Analizar cada índice mensual
    print("="*80)
    print("ANÁLISIS DETALLADO POR MES:")
    print("="*80 + "\n")
    
    imagenes_ok = 0
    imagenes_faltantes = 0
    rutas_incorrectas = []
    
    for indice in indices:
        print(f"\n📅 {indice.periodo_texto} (ID: {indice.id})")
        print("-" * 60)
        
        # Verificar cada tipo de imagen
        for tipo in ['ndvi', 'ndmi', 'savi']:
            campo_imagen = f'imagen_{tipo}'
            imagen_field = getattr(indice, campo_imagen)
            
            if imagen_field:
                # Ruta almacenada en la DB
                ruta_db = imagen_field.name
                print(f"\n  {tipo.upper()}:")
                print(f"    Ruta en DB: {ruta_db}")
                
                # Ruta completa esperada
                ruta_completa = os.path.join(settings.MEDIA_ROOT, ruta_db)
                print(f"    Ruta completa: {ruta_completa}")
                
                # Verificar si existe
                existe = os.path.exists(ruta_completa)
                print(f"    Existe: {'✅' if existe else '❌'}")
                
                if existe:
                    # Obtener tamaño del archivo
                    size = os.path.getsize(ruta_completa)
                    print(f"    Tamaño: {size:,} bytes ({size/1024:.2f} KB)")
                    imagenes_ok += 1
                else:
                    imagenes_faltantes += 1
                    rutas_incorrectas.append({
                        'indice_id': indice.id,
                        'periodo': indice.periodo_texto,
                        'tipo': tipo,
                        'ruta_db': ruta_db,
                        'ruta_completa': ruta_completa
                    })
                    
                    # Buscar archivo en otras ubicaciones
                    print(f"    🔍 Buscando en ubicaciones alternativas...")
                    
                    # Buscar en media/
                    nombre_archivo = os.path.basename(ruta_db)
                    for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                        if nombre_archivo in files:
                            ruta_encontrada = os.path.join(root, nombre_archivo)
                            print(f"       ✅ ENCONTRADO EN: {ruta_encontrada}")
            else:
                print(f"\n  {tipo.upper()}: ⚠️  No registrada en DB")
    
    # 5. Resumen final
    print("\n" + "="*80)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("="*80)
    print(f"\n✅ Imágenes OK: {imagenes_ok}")
    print(f"❌ Imágenes faltantes: {imagenes_faltantes}")
    print(f"📝 Total verificadas: {imagenes_ok + imagenes_faltantes}")
    
    # 6. Listar estructura de directorios
    print("\n" + "="*80)
    print("📁 ESTRUCTURA DE DIRECTORIOS EN MEDIA/")
    print("="*80 + "\n")
    
    if os.path.exists(settings.MEDIA_ROOT):
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            nivel = root.replace(settings.MEDIA_ROOT, '').count(os.sep)
            indent = ' ' * 2 * nivel
            print(f'{indent}{os.path.basename(root)}/')
            
            sub_indent = ' ' * 2 * (nivel + 1)
            for archivo in files:
                if archivo.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                    ruta_completa = os.path.join(root, archivo)
                    size = os.path.getsize(ruta_completa)
                    print(f'{sub_indent}{archivo} ({size:,} bytes)')
    
    # 7. Si hay rutas incorrectas, generar script de corrección
    if rutas_incorrectas:
        print("\n" + "="*80)
        print("⚠️  RUTAS INCORRECTAS DETECTADAS")
        print("="*80 + "\n")
        
        for item in rutas_incorrectas:
            print(f"ID {item['indice_id']} - {item['periodo']} - {item['tipo'].upper()}")
            print(f"  Ruta DB: {item['ruta_db']}")
            print(f"  Esperada: {item['ruta_completa']}\n")

if __name__ == '__main__':
    diagnosticar_parcela_3()
