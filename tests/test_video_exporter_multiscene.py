#!/usr/bin/env python3
"""
Test completo del TimelineVideoExporterMultiScene
Verifica todas las funcionalidades antes de integrar con Django

@author: AgroTech Team
@date: 19 de enero de 2026
"""

import os
import sys
import django
import logging
from pathlib import Path

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.exporters.video_exporter_multiscene import TimelineVideoExporterMultiScene
from informes.models import Parcela, IndiceMensual
from informes.processors.timeline_processor import TimelineProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_1_verificar_ffmpeg():
    """Test 1: Verificar que FFmpeg está instalado"""
    print("\n" + "="*80)
    print("TEST 1: Verificación de FFmpeg")
    print("="*80)
    
    try:
        exporter = TimelineVideoExporterMultiScene()
        print("✅ FFmpeg disponible")
        print(f"   Configuración: {exporter.width}x{exporter.height} @ {exporter.fps}fps")
        return True
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("   Instala FFmpeg: brew install ffmpeg (macOS)")
        return False


def test_2_funciones_auxiliares():
    """Test 2: Verificar funciones de limpieza de texto"""
    print("\n" + "="*80)
    print("TEST 2: Funciones Auxiliares")
    print("="*80)
    
    exporter = TimelineVideoExporterMultiScene()
    
    # Test limpieza de análisis
    texto_analisis = """
    Este es un análisis muy largo con muchos tecnicismos innecesarios.
    La vegetación muestra síntomas de estrés hídrico moderado según el NDVI.
    Se recomienda incrementar la frecuencia de riego en las próximas semanas.
    Esto es una cuarta frase que debería eliminarse.
    """
    
    resultado = exporter._limpiar_analisis_texto(texto_analisis, max_frases=3)
    frases = resultado.split('.')
    num_frases = len([f for f in frases if f.strip()])
    
    print(f"\n📝 Análisis original: {len(texto_analisis)} caracteres")
    print(f"   Análisis limpio: {len(resultado)} caracteres")
    print(f"   Frases: {num_frases}")
    print(f"   Resultado: {resultado[:100]}...")
    
    if num_frases <= 3:
        print("✅ Limpieza de análisis OK")
    else:
        print(f"❌ ERROR: Se esperaban máx 3 frases, se obtuvieron {num_frases}")
        return False
    
    # Test parseo de recomendaciones
    texto_recomendaciones = """
    - Incrementar frecuencia de riego en zonas norte y este
    - Aplicar fertilizante nitrogenado en próximos 15 días
    - Monitorear plagas en sector sur del lote
    - Esta cuarta recomendación debería eliminarse
    - Y esta quinta también
    """
    
    recos = exporter._parsear_recomendaciones(texto_recomendaciones, max_recos=3)
    
    print(f"\n💡 Recomendaciones parseadas: {len(recos)}")
    for i, reco in enumerate(recos, 1):
        print(f"   {i}. {reco[:60]}...")
    
    if len(recos) <= 3:
        print("✅ Parseo de recomendaciones OK")
        return True
    else:
        print(f"❌ ERROR: Se esperaban máx 3 recos, se obtuvieron {len(recos)}")
        return False


def test_3_datos_reales_parcela():
    """Test 3: Verificar datos de parcela real"""
    print("\n" + "="*80)
    print("TEST 3: Datos Reales de Parcela")
    print("="*80)
    
    # Buscar parcela con datos (corregido: indices_mensuales en plural)
    parcela = Parcela.objects.filter(
        indices_mensuales__isnull=False
    ).first()
    
    if not parcela:
        print("⚠️  No hay parcelas con datos históricos")
        return False
    
    print(f"📍 Parcela encontrada: {parcela.nombre} (ID: {parcela.id})")
    print(f"   Propietario: {parcela.propietario}")
    print(f"   Cultivo: {parcela.tipo_cultivo}")
    
    # Contar registros mensuales
    registros = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
    print(f"\n📊 Registros mensuales: {registros.count()}")
    
    # Verificar imágenes NDVI
    con_ndvi = registros.exclude(imagen_ndvi='').exclude(imagen_ndvi__isnull=True).count()
    con_ndmi = registros.exclude(imagen_ndmi='').exclude(imagen_ndmi__isnull=True).count()
    con_savi = registros.exclude(imagen_savi='').exclude(imagen_savi__isnull=True).count()
    
    print(f"   Con NDVI: {con_ndvi}")
    print(f"   Con NDMI: {con_ndmi}")
    print(f"   Con SAVI: {con_savi}")
    
    if con_ndvi > 0:
        print(f"✅ Parcela {parcela.id} tiene datos suficientes para video")
        return parcela.id
    else:
        print("⚠️  Parcela sin imágenes NDVI")
        return False


def test_4_generar_metadata_timeline(parcela_id):
    """Test 4: Generar metadata del timeline"""
    print("\n" + "="*80)
    print("TEST 4: Generación de Metadata Timeline")
    print("="*80)
    
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        
        # Generar metadata
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
        frames_data = []
        
        indices_list = list(indices)
        for i, indice_mensual in enumerate(indices_list):
            mes_anterior = indices_list[i-1] if i > 0 else None
            frame_meta = TimelineProcessor.generar_metadata_frame(indice_mensual, mes_anterior)
            frames_data.append(frame_meta)
        
        print(f"✅ Metadata generada: {len(frames_data)} frames")
        
        # Verificar estructura del primer frame
        if frames_data:
            primer_frame = frames_data[0]
            print(f"\n📋 Estructura del primer frame:")
            print(f"   Periodo: {primer_frame.get('periodo_texto')}")
            print(f"   NDVI promedio: {primer_frame.get('ndvi', {}).get('promedio')}")
            print(f"   Temperatura: {primer_frame.get('temperatura')}")
            print(f"   Precipitación: {primer_frame.get('precipitacion')}")
            print(f"   Imagen NDVI: {'✓' if primer_frame.get('imagenes', {}).get('ndvi') else '✗'}")
        
        return frames_data
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_5_generar_video_completo(parcela_id, frames_data):
    """Test 5: Generar video completo multi-escena"""
    print("\n" + "="*80)
    print("TEST 5: Generación de Video Multi-Escena")
    print("="*80)
    
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        
        # Información de parcela
        parcela_info = {
            'nombre': parcela.nombre,
            'area': float(parcela.area_hectareas) if parcela.area_hectareas else None,
            'cultivo': parcela.tipo_cultivo or 'No especificado'
        }
        
        # Análisis y recomendaciones de prueba
        analisis_texto = """
        La parcela muestra un desarrollo vegetativo moderado durante el periodo analizado.
        Se observan variaciones estacionales normales en los índices de vegetación.
        El estado general del cultivo es satisfactorio.
        """
        
        recomendaciones_texto = """
        - Mantener el programa de riego actual
        - Monitorear áreas con menor vigor en el sector norte
        - Planificar aplicación de nutrientes para el próximo ciclo
        """
        
        # Inicializar exportador
        exporter = TimelineVideoExporterMultiScene()
        
        # Generar video
        print("\n🎬 Generando video multi-escena...")
        print(f"   Frames totales: {len(frames_data)}")
        print(f"   Análisis: {'✓' if analisis_texto else '✗'}")
        print(f"   Recomendaciones: {'✓' if recomendaciones_texto else '✗'}")
        
        video_path = exporter.export_timeline(
            frames_data=frames_data,
            indice='ndvi',
            parcela_info=parcela_info,
            analisis_texto=analisis_texto,
            recomendaciones_texto=recomendaciones_texto
        )
        
        # Verificar resultado
        if os.path.exists(video_path):
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"\n✅ VIDEO GENERADO EXITOSAMENTE")
            print(f"   📁 Ruta: {video_path}")
            print(f"   💾 Tamaño: {size_mb:.2f} MB")
            print(f"\n💡 Reproducir con: open '{video_path}'")
            return video_path
        else:
            print("❌ ERROR: Video no encontrado")
            return None
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def ejecutar_todos_los_tests():
    """Ejecuta todos los tests en secuencia"""
    print("\n" + "🔬"*40)
    print("SUITE DE TESTS - TimelineVideoExporterMultiScene")
    print("🔬"*40)
    
    resultados = {
        'total': 5,
        'exitosos': 0,
        'fallidos': 0
    }
    
    # Test 1: FFmpeg
    if test_1_verificar_ffmpeg():
        resultados['exitosos'] += 1
    else:
        resultados['fallidos'] += 1
        print("\n⚠️  FFmpeg no disponible - tests restantes se saltarán")
        return resultados
    
    # Test 2: Funciones auxiliares
    if test_2_funciones_auxiliares():
        resultados['exitosos'] += 1
    else:
        resultados['fallidos'] += 1
    
    # Test 3: Datos reales
    parcela_id = test_3_datos_reales_parcela()
    if parcela_id:
        resultados['exitosos'] += 1
    else:
        resultados['fallidos'] += 1
        print("\n⚠️  No hay datos para tests de video - saltando tests 4 y 5")
        return resultados
    
    # Test 4: Metadata
    frames_data = test_4_generar_metadata_timeline(parcela_id)
    if frames_data:
        resultados['exitosos'] += 1
    else:
        resultados['fallidos'] += 1
        return resultados
    
    # Test 5: Video completo
    video_path = test_5_generar_video_completo(parcela_id, frames_data)
    if video_path:
        resultados['exitosos'] += 1
    else:
        resultados['fallidos'] += 1
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)
    print(f"Total de tests: {resultados['total']}")
    print(f"✅ Exitosos: {resultados['exitosos']}")
    print(f"❌ Fallidos: {resultados['fallidos']}")
    
    porcentaje = (resultados['exitosos'] / resultados['total']) * 100
    print(f"\n📊 Tasa de éxito: {porcentaje:.1f}%")
    
    if resultados['exitosos'] == resultados['total']:
        print("\n🎉 TODOS LOS TESTS PASARON - Sistema listo para producción")
    elif resultados['exitosos'] > resultados['fallidos']:
        print("\n⚠️  Mayoría de tests pasaron - Revisar fallos antes de producción")
    else:
        print("\n❌ TESTS FALLARON - Sistema necesita correcciones")
    
    return resultados


if __name__ == '__main__':
    resultados = ejecutar_todos_los_tests()
    
    # Exit code según resultados
    sys.exit(0 if resultados['exitosos'] == resultados['total'] else 1)
