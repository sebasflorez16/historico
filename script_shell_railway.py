# ============================================================
# SCRIPT PARA COPIAR Y PEGAR EN EL SHELL DE DJANGO (Railway)
# ============================================================

from informes.models import Parcela, IndiceMensual
import os

parcela = Parcela.objects.get(id=3)
print("=" * 60)
print(f"Parcela: {parcela.nombre}")
print(f"Propietario: {parcela.propietario}")
print(f"Total índices: {parcela.indices_mensuales.count()}")
print("=" * 60)

print("\n=== RUTAS DE IMÁGENES (primeros 10 meses) ===\n")

total_ndvi = 0
total_ndmi = 0
total_savi = 0

for indice in parcela.indices_mensuales.all()[:10]:
    print(f"\n📅 {indice.periodo_texto} (ID: {indice.id})")
    
    # NDVI
    if indice.imagen_ndvi:
        total_ndvi += 1
        print(f"  ✅ NDVI: {indice.imagen_ndvi.name}")
        ruta = f"media/{indice.imagen_ndvi.name}"
        existe = os.path.exists(ruta)
        print(f"     Existe: {'✅ SÍ' if existe else '❌ NO'} ({ruta})")
    else:
        print(f"  ❌ NDVI: --- (campo vacío en BD)")
    
    # NDMI
    if indice.imagen_ndmi:
        total_ndmi += 1
        print(f"  ✅ NDMI: {indice.imagen_ndmi.name}")
        ruta = f"media/{indice.imagen_ndmi.name}"
        existe = os.path.exists(ruta)
        print(f"     Existe: {'✅ SÍ' if existe else '❌ NO'} ({ruta})")
    else:
        print(f"  ❌ NDMI: --- (campo vacío en BD)")
    
    # SAVI
    if indice.imagen_savi:
        total_savi += 1
        print(f"  ✅ SAVI: {indice.imagen_savi.name}")
        ruta = f"media/{indice.imagen_savi.name}"
        existe = os.path.exists(ruta)
        print(f"     Existe: {'✅ SÍ' if existe else '❌ NO'} ({ruta})")
    else:
        print(f"  ❌ SAVI: --- (campo vacío en BD)")

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)
print(f"Imágenes NDVI en BD: {total_ndvi}/10")
print(f"Imágenes NDMI en BD: {total_ndmi}/10")
print(f"Imágenes SAVI en BD: {total_savi}/10")

# Verificar directorio
print("\n=== VERIFICACIÓN DEL DIRECTORIO ===")
media_dir = "media/imagenes_satelitales"
if os.path.exists(media_dir):
    archivos = os.listdir(media_dir)
    print(f"✅ Directorio existe: {len(archivos)} archivos")
    print("Primeros 10 archivos:")
    for i, archivo in enumerate(archivos[:10], 1):
        print(f"  {i}. {archivo}")
else:
    print(f"❌ Directorio NO existe: {media_dir}")
