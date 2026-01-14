"""
Script para verificar que el timeline de la Parcela 6 puede generarse
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.processors.timeline_processor import TimelineProcessor

print("=" * 60)
print("🎬 DIAGNÓSTICO DE TIMELINE - PARCELA 6")
print("=" * 60)

try:
    # 1. Verificar parcela
    parcela = Parcela.objects.get(id=6)
    print(f"\n✅ Parcela encontrada: {parcela.nombre}")
    print(f"   Propietario: {parcela.propietario}")
    print(f"   Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
    
    # 2. Verificar índices mensuales
    indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
    print(f"\n✅ Índices mensuales: {indices.count()} meses registrados")
    
    # 3. Verificar imágenes disponibles
    indices_con_imagenes = 0
    total_imagenes = 0
    
    for idx in indices:
        tiene_img = False
        if idx.imagen_ndvi:
            total_imagenes += 1
            tiene_img = True
        if idx.imagen_ndmi:
            total_imagenes += 1
            tiene_img = True
        if idx.imagen_savi:
            total_imagenes += 1
            tiene_img = True
        
        if tiene_img:
            indices_con_imagenes += 1
    
    print(f"   - Meses con imágenes: {indices_con_imagenes}/{indices.count()}")
    print(f"   - Total de imágenes: {total_imagenes}")
    
    # 4. Verificar que podemos generar metadata
    if indices.exists():
        print(f"\n✅ Probando TimelineProcessor...")
        primer_indice = indices.first()
        metadata = TimelineProcessor.generar_metadata_frame(primer_indice)
        
        print(f"   - Metadata generada para: {metadata['periodo_texto']}")
        print(f"   - NDVI promedio: {metadata['ndvi']['promedio']}")
        print(f"   - Imágenes disponibles:")
        if metadata.get('imagenes'):
            for img_tipo, img_data in metadata['imagenes'].items():
                if img_data and img_data.get('url'):
                    print(f"     ✅ {img_tipo}: {img_data['url']}")
                else:
                    print(f"     ❌ {img_tipo}: No disponible")
    
    # 5. Verificar ruta de salida para video
    from django.conf import settings
    video_dir = os.path.join(settings.MEDIA_ROOT, 'timelines', f'parcela_{parcela.id}')
    print(f"\n✅ Directorio para video: {video_dir}")
    
    if not os.path.exists(video_dir):
        print(f"   ⚠️  El directorio no existe, se creará al generar el timeline")
    else:
        # Buscar videos existentes
        videos = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
        if videos:
            print(f"   ✅ Videos existentes: {len(videos)}")
            for v in videos:
                print(f"      - {v}")
        else:
            print(f"   ℹ️  No hay videos generados aún")
    
    print("\n" + "=" * 60)
    print("✅ TODO LISTO PARA GENERAR TIMELINE")
    print("=" * 60)
    print("\n💡 Para generar el timeline desde la web:")
    print("   1. Ve a http://localhost:8000/informes/parcelas/6/")
    print("   2. Busca el botón 'Ver Timeline' o 'Generar Video'")
    print("   3. El video se generará en segundo plano")
    
except Parcela.DoesNotExist:
    print("\n❌ ERROR: La parcela 6 no existe en la base de datos")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
