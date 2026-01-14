#!/usr/bin/env python
"""
Script de diagnóstico para verificar rutas de imágenes satelitales
Parcela 3 - Javier Rodriguez
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings_production')
django.setup()

from informes.models import Parcela, IndiceMensual

def main():
    print("=" * 60)
    print("DIAGNÓSTICO DE RUTAS DE IMÁGENES SATELITALES")
    print("=" * 60)
    
    # Obtener parcela
    try:
        parcela = Parcela.objects.get(id=3)
        print(f"\n✅ Parcela encontrada:")
        print(f"   Nombre: {parcela.nombre}")
        print(f"   Propietario: {parcela.propietario}")
        print(f"   Total índices: {parcela.indices_mensuales.count()}")
    except Parcela.DoesNotExist:
        print("\n❌ ERROR: Parcela con ID=3 no encontrada")
        return
    
    print("\n" + "=" * 60)
    print("RUTAS DE IMÁGENES (primeros 10 meses)")
    print("=" * 60)
    
    indices = parcela.indices_mensuales.all()[:10]
    
    if not indices:
        print("\n⚠️  No hay índices mensuales para esta parcela")
        return
    
    total_ndvi = 0
    total_ndmi = 0
    total_savi = 0
    
    for indice in indices:
        print(f"\n📅 {indice.periodo_texto} (ID: {indice.id})")
        print(f"   Fecha: {indice.fecha_imagen.strftime('%d/%m/%Y') if indice.fecha_imagen else 'N/A'}")
        
        # NDVI
        if indice.imagen_ndvi:
            total_ndvi += 1
            print(f"   ✅ NDVI: {indice.imagen_ndvi.name}")
            # Verificar si el archivo existe físicamente
            ruta_completa = indice.imagen_ndvi.path if hasattr(indice.imagen_ndvi, 'path') else f"media/{indice.imagen_ndvi.name}"
            existe = os.path.exists(ruta_completa)
            print(f"      Archivo existe: {'✅ SÍ' if existe else '❌ NO'}")
            if not existe:
                print(f"      Ruta buscada: {ruta_completa}")
        else:
            print(f"   ❌ NDVI: ---")
        
        # NDMI
        if indice.imagen_ndmi:
            total_ndmi += 1
            print(f"   ✅ NDMI: {indice.imagen_ndmi.name}")
            ruta_completa = indice.imagen_ndmi.path if hasattr(indice.imagen_ndmi, 'path') else f"media/{indice.imagen_ndmi.name}"
            existe = os.path.exists(ruta_completa)
            print(f"      Archivo existe: {'✅ SÍ' if existe else '❌ NO'}")
            if not existe:
                print(f"      Ruta buscada: {ruta_completa}")
        else:
            print(f"   ❌ NDMI: ---")
        
        # SAVI
        if indice.imagen_savi:
            total_savi += 1
            print(f"   ✅ SAVI: {indice.imagen_savi.name}")
            ruta_completa = indice.imagen_savi.path if hasattr(indice.imagen_savi, 'path') else f"media/{indice.imagen_savi.name}"
            existe = os.path.exists(ruta_completa)
            print(f"      Archivo existe: {'✅ SÍ' if existe else '❌ NO'}")
            if not existe:
                print(f"      Ruta buscada: {ruta_completa}")
        else:
            print(f"   ❌ SAVI: ---")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total meses analizados: {len(indices)}")
    print(f"Imágenes NDVI con ruta: {total_ndvi}/{len(indices)}")
    print(f"Imágenes NDMI con ruta: {total_ndmi}/{len(indices)}")
    print(f"Imágenes SAVI con ruta: {total_savi}/{len(indices)}")
    
    # Verificar directorio de imágenes
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE DIRECTORIO")
    print("=" * 60)
    
    media_dir = "media/imagenes_satelitales"
    if os.path.exists(media_dir):
        archivos = os.listdir(media_dir)
        print(f"✅ Directorio existe: {media_dir}")
        print(f"   Total archivos: {len(archivos)}")
        if archivos:
            print(f"   Primeros 5 archivos:")
            for archivo in archivos[:5]:
                print(f"   - {archivo}")
    else:
        print(f"❌ Directorio NO existe: {media_dir}")

if __name__ == '__main__':
    main()
