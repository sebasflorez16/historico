#!/usr/bin/env python
"""
Script de prueba para verificar la refactorización del generador de videos del timeline

Verifica que:
1. El exportador se inicializa correctamente
2. FFmpeg está disponible
3. La configuración de calidad es correcta
4. No hay emojis en el código
5. Las transiciones están configuradas

@author: AgroTech Team
@date: 15 de enero de 2026
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.exporters.video_exporter import TimelineVideoExporter


def test_exporter_initialization():
    """Test 1: Inicialización del exportador"""
    print("🧪 Test 1: Inicialización del exportador")
    
    try:
        exporter = TimelineVideoExporter()
        
        # Verificar configuración de calidad profesional
        assert exporter.width == 1920, f"❌ Ancho incorrecto: {exporter.width}"
        assert exporter.height == 1080, f"❌ Alto incorrecto: {exporter.height}"
        assert exporter.fps == 24, f"❌ FPS incorrecto: {exporter.fps}"
        assert exporter.bitrate == '10000k', f"❌ Bitrate incorrecto: {exporter.bitrate}"
        assert exporter.crf == 18, f"❌ CRF incorrecto: {exporter.crf}"
        assert exporter.FRAME_DURATION == 2.5, f"❌ Duración de frame incorrecta: {exporter.FRAME_DURATION}"
        
        print("✅ Configuración de calidad correcta")
        print(f"   - Resolución: {exporter.width}x{exporter.height}")
        print(f"   - FPS: {exporter.fps}")
        print(f"   - Bitrate: {exporter.bitrate}")
        print(f"   - CRF: {exporter.crf}")
        print(f"   - Duración por frame: {exporter.FRAME_DURATION}s")
        
        return True
    except Exception as e:
        print(f"❌ Error en inicialización: {e}")
        return False


def test_ffmpeg_availability():
    """Test 2: Verificar que FFmpeg está disponible"""
    print("\n🧪 Test 2: Disponibilidad de FFmpeg")
    
    try:
        exporter = TimelineVideoExporter()
        print("✅ FFmpeg está disponible")
        return True
    except RuntimeError as e:
        print(f"❌ FFmpeg no disponible: {e}")
        print("   Instalar con: brew install ffmpeg (macOS)")
        return False


def test_no_emojis_in_code():
    """Test 3: Verificar que no hay emojis en el código"""
    print("\n🧪 Test 3: Verificación de emojis en código")
    
    # Emojis prohibidos
    emojis_prohibidos = ['📈', '📉', '➡️', '📋', '🌡️', '💧', '⭐', '🌱']
    
    # Leer el código fuente
    exporter_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'informes/exporters/video_exporter.py'
    )
    
    with open(exporter_path, 'r', encoding='utf-8') as f:
        codigo = f.read()
    
    emojis_encontrados = []
    for emoji in emojis_prohibidos:
        if emoji in codigo:
            emojis_encontrados.append(emoji)
    
    if emojis_encontrados:
        print(f"❌ Emojis encontrados en código: {emojis_encontrados}")
        return False
    else:
        print("✅ No hay emojis en el código")
        return True


def test_professional_structure_exists():
    """Test 4: Verificar que existe la estructura profesional"""
    print("\n🧪 Test 4: Estructura profesional")
    
    try:
        exporter = TimelineVideoExporter()
        
        # Verificar que existen los métodos críticos
        assert hasattr(exporter, '_draw_professional_structure'), "❌ Falta método _draw_professional_structure"
        assert hasattr(exporter, '_get_rangos_agronomicos'), "❌ Falta método _get_rangos_agronomicos"
        assert hasattr(exporter, '_generar_texto_interpretativo'), "❌ Falta método _generar_texto_interpretativo"
        assert hasattr(exporter, '_draw_multiline_text'), "❌ Falta método _draw_multiline_text"
        
        print("✅ Todos los métodos de estructura profesional existen")
        return True
    except AssertionError as e:
        print(f"❌ {e}")
        return False


def test_subtitle_texts():
    """Test 5: Verificar subtítulos educativos"""
    print("\n🧪 Test 5: Subtítulos educativos (sin tecnicismos)")
    
    # Subtítulos esperados (actualizados según ajustes de diseño)
    subtitulos_esperados = {
        'ndvi': 'Evaluacion de la salud de la vegetacion',
        'ndmi': 'Evaluacion del nivel de humedad',
        'savi': 'Evaluacion del desarrollo vegetal'
    }
    
    # Leer el código fuente
    exporter_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'informes/exporters/video_exporter.py'
    )
    
    with open(exporter_path, 'r', encoding='utf-8') as f:
        codigo = f.read()
    
    todos_encontrados = True
    for indice, subtitulo in subtitulos_esperados.items():
        if subtitulo not in codigo:
            print(f"❌ Subtítulo no encontrado para {indice}: {subtitulo}")
            todos_encontrados = False
    
    if todos_encontrados:
        print("✅ Todos los subtítulos educativos están presentes")
        for indice, subtitulo in subtitulos_esperados.items():
            print(f"   - {indice.upper()}: {subtitulo}")
        return True
    else:
        return False


def test_fade_transitions():
    """Test 6: Verificar que las transiciones fade están configuradas"""
    print("\n🧪 Test 6: Transiciones fade in/out")
    
    # Leer el código fuente
    exporter_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'informes/exporters/video_exporter.py'
    )
    
    with open(exporter_path, 'r', encoding='utf-8') as f:
        codigo = f.read()
    
    # Verificar que existen las instrucciones de fade
    tiene_fade_in = 'fade=t=in' in codigo
    tiene_fade_out = 'fade=t=out' in codigo
    tiene_fade_duration = 'fade_duration' in codigo
    
    if tiene_fade_in and tiene_fade_out and tiene_fade_duration:
        print("✅ Transiciones fade in/out configuradas")
        print("   - Fade in al inicio")
        print("   - Fade out al final")
        return True
    else:
        print("❌ Transiciones fade no configuradas correctamente")
        if not tiene_fade_in:
            print("   - Falta fade in")
        if not tiene_fade_out:
            print("   - Falta fade out")
        return False


def main():
    """Ejecutar todos los tests"""
    print("=" * 70)
    print("VERIFICACIÓN DE REFACTORIZACIÓN DEL GENERADOR DE VIDEOS DEL TIMELINE")
    print("=" * 70)
    
    tests = [
        test_exporter_initialization,
        test_ffmpeg_availability,
        test_no_emojis_in_code,
        test_professional_structure_exists,
        test_subtitle_texts,
        test_fade_transitions
    ]
    
    resultados = []
    for test in tests:
        resultado = test()
        resultados.append(resultado)
    
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)
    
    tests_exitosos = sum(resultados)
    tests_totales = len(resultados)
    
    print(f"Tests exitosos: {tests_exitosos}/{tests_totales}")
    
    if tests_exitosos == tests_totales:
        print("\n🎉 TODOS LOS TESTS PASARON")
        print("✅ El generador de videos está listo para producción")
        return 0
    else:
        print(f"\n⚠️  {tests_totales - tests_exitosos} test(s) fallaron")
        print("❌ Revisar los errores antes de usar en producción")
        return 1


if __name__ == '__main__':
    sys.exit(main())
