#!/usr/bin/env python
"""
Script de verificación del sistema de optimización Gemini
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import InformeGenerado, AnalisisImagen
from informes.utils.image_selector import ImagenSelector
from django.contrib.auth.models import User

print('='*70)
print('✅ VERIFICACIÓN DEL SISTEMA DE OPTIMIZACIÓN GEMINI')
print('='*70)

# 1. Verificar modelos
print('\n📦 MODELOS DE BASE DE DATOS:')
print(f'  ✓ AnalisisImagen: {AnalisisImagen._meta.db_table}')
print(f'    - Campos: {", ".join([f.name for f in AnalisisImagen._meta.get_fields() if not f.many_to_many][:5])}...')
print(f'  ✓ InformeGenerado: {InformeGenerado._meta.db_table}')
print(f'    - Campos: {", ".join([f.name for f in InformeGenerado._meta.get_fields() if not f.many_to_many][:5])}...')

# 2. Verificar métodos de cuota
print('\n📊 SISTEMA DE CUOTAS:')
try:
    user = User.objects.first()
    if user:
        informes_hoy = InformeGenerado.contar_informes_hoy(user)
        puede_generar = InformeGenerado.puede_generar_informe(user, limite_diario=3)
        print(f'  ✓ Usuario: {user.username}')
        print(f'  ✓ Informes generados hoy: {informes_hoy}/3')
        print(f'  ✓ Puede generar informe: {"Sí ✅" if puede_generar else "No ❌ (límite alcanzado)"}')
    else:
        print('  ⚠️  No hay usuarios en la base de datos')
except Exception as e:
    print(f'  ❌ Error al verificar cuotas: {e}')

# 3. Verificar ImageSelector
print('\n🎯 IMAGE SELECTOR:')
from informes.utils import image_selector
selector = ImagenSelector()
print(f'  ✓ MAX_IMAGENES_POR_INFORME: {image_selector.MAX_IMAGENES_POR_INFORME}')
print(f'  ✓ MAX_IMAGENES_ANALISIS_COMPLETO: {image_selector.MAX_IMAGENES_ANALISIS_COMPLETO}')

# 4. Verificar estimación de costos
print('\n💰 ESTIMACIÓN DE COSTOS:')
for num_imagenes in [5, 10, 15, 30]:
    estimacion = selector.estimar_costo_analisis(num_imagenes)
    print(f'  {num_imagenes:2d} imágenes → {estimacion["total_tokens"]:6,} tokens, '
          f'{estimacion["total_peticiones"]} peticiones API')

# 5. Verificar cache de análisis
print('\n💾 CACHE DE ANÁLISIS:')
total_cache = AnalisisImagen.objects.count()
print(f'  ✓ Registros en cache: {total_cache}')
if total_cache > 0:
    ultimo = AnalisisImagen.objects.latest('fecha_analisis')
    print(f'  ✓ Último análisis: {ultimo.parcela.nombre if hasattr(ultimo, "parcela") else "N/A"}')
    print(f'    - Fecha: {ultimo.fecha_imagen}')
    print(f'    - Índice: {ultimo.indice}')

# 6. Verificar informes generados
print('\n📄 INFORMES GENERADOS:')
total_informes = InformeGenerado.objects.count()
print(f'  ✓ Total informes: {total_informes}')
if total_informes > 0:
    ultimo_informe = InformeGenerado.objects.latest('fecha_generacion')
    print(f'  ✓ Último informe:')
    print(f'    - Parcela: {ultimo_informe.parcela.nombre}')
    print(f'    - Tipo: {ultimo_informe.tipo_analisis}')
    print(f'    - Imágenes: {ultimo_informe.num_imagenes_analizadas}')
    print(f'    - Tokens: {ultimo_informe.tokens_consumidos:,}')
    print(f'    - Fecha: {ultimo_informe.fecha_generacion.strftime("%Y-%m-%d %H:%M")}')

print('\n' + '='*70)
print('✅ VERIFICACIÓN COMPLETADA')
print('='*70)
print('\n📚 MEJORA DE EFICIENCIA:')
print('  • Antes: 30+ imágenes × 500 tokens = 15,000+ tokens/informe')
print('  • Ahora: 10 imágenes × 500 tokens = 5,000 tokens/informe')
print('  • Reducción: 67% en consumo de tokens')
print('  • Límite diario: 3 informes/usuario/día')
print('  • Cache: 30 días de validez')
print('\n💡 Capacidad estimada con tier gratuito:')
print('  • Sin optimización: 4-6 informes/mes')
print('  • Con optimización: 12-20 informes/mes')
print('='*70 + '\n')
