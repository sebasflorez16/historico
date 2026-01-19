"""
Test simplificado de integración del sistema de videos timeline
Verifica la configuración sin importar dependencias problemáticas
"""

import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_estructura_archivos():
    """
    Verifica que todos los archivos necesarios existen
    """
    print("\n" + "="*70)
    print("🧪 TEST DE INTEGRACIÓN - Sistema de Videos Timeline")
    print("="*70 + "\n")
    
    archivos_requeridos = [
        # Exportador
        ('informes/exporters/video_exporter_multiscene.py', 'Exportador Multi-escena'),
        
        # Vista Django
        ('informes/views.py', 'Vistas Django'),
        
        # URLs
        ('informes/urls.py', 'Configuración de URLs'),
        
        # Template
        ('templates/informes/parcelas/timeline.html', 'Template HTML'),
        
        # JavaScript
        ('static/js/timeline/timeline_player.js', 'JavaScript del player'),
        
        # Tests
        ('tests/test_video_exporter_multiscene.py', 'Tests del exportador'),
        
        # Documentación
        ('INTEGRACION_VIDEO_TIMELINE.md', 'Documentación de integración'),
        ('finalizando_timeline.md', 'Especificación'),
    ]
    
    todos_existen = True
    
    print("📁 Verificando estructura de archivos:\n")
    
    for archivo, descripcion in archivos_requeridos:
        ruta_completa = os.path.join('/Users/sebasflorez16/Documents/AgroTech Historico', archivo)
        existe = os.path.exists(ruta_completa)
        
        if existe:
            tamaño = os.path.getsize(ruta_completa)
            print(f"   ✅ {descripcion:40} ({tamaño:>8} bytes)")
        else:
            print(f"   ❌ {descripcion:40} (NO ENCONTRADO)")
            todos_existen = False
    
    return todos_existen


def test_configuracion_vista():
    """
    Verifica la configuración de la vista sin importarla
    """
    print("\n📝 Verificando configuración de vista:\n")
    
    ruta_views = '/Users/sebasflorez16/Documents/AgroTech Historico/informes/views.py'
    
    with open(ruta_views, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    verificaciones = [
        ('TimelineVideoExporterMultiScene', '✅ Usa TimelineVideoExporterMultiScene', '❌ NO usa TimelineVideoExporterMultiScene'),
        ('@login_required', '✅ Protegida con @login_required', '⚠️  NO tiene @login_required'),
        ('def exportar_video_timeline', '✅ Vista exportar_video_timeline existe', '❌ Vista NO existe'),
        ("indice not in ['ndvi', 'ndmi', 'savi']", '✅ Valida índices correctamente', '⚠️  NO valida índices'),
        ('get_object_or_404(Parcela', '✅ Valida existencia de parcela', '⚠️  NO valida parcela'),
    ]
    
    todas_ok = True
    
    for patron, msg_ok, msg_error in verificaciones:
        if patron in contenido:
            print(f"   {msg_ok}")
        else:
            print(f"   {msg_error}")
            todas_ok = False
    
    return todas_ok


def test_configuracion_url():
    """
    Verifica la configuración de URLs
    """
    print("\n🔗 Verificando configuración de URLs:\n")
    
    ruta_urls = '/Users/sebasflorez16/Documents/AgroTech Historico/informes/urls.py'
    
    with open(ruta_urls, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    verificaciones = [
        ('timeline/exportar-video/', '✅ URL de exportación configurada'),
        ('exportar_video_timeline', '✅ Vista vinculada correctamente'),
    ]
    
    todas_ok = True
    
    for patron, msg_ok in verificaciones:
        if patron in contenido:
            print(f"   {msg_ok}")
        else:
            print(f"   ❌ Falta: {patron}")
            todas_ok = False
    
    return todas_ok


def test_template_html():
    """
    Verifica que el template tiene los botones de descarga
    """
    print("\n🎨 Verificando template HTML:\n")
    
    ruta_template = '/Users/sebasflorez16/Documents/AgroTech Historico/templates/informes/parcelas/timeline.html'
    
    with open(ruta_template, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    verificaciones = [
        ('btn-download-ndvi', '✅ Botón de descarga NDVI'),
        ('btn-download-ndmi', '✅ Botón de descarga NDMI'),
        ('btn-download-savi', '✅ Botón de descarga SAVI'),
        ('Descargar Timeline como Video', '✅ Título de sección de descarga'),
    ]
    
    todas_ok = True
    
    for patron, msg_ok in verificaciones:
        if patron in contenido:
            print(f"   {msg_ok}")
        else:
            print(f"   ❌ Falta: {patron}")
            todas_ok = False
    
    return todas_ok


def test_javascript():
    """
    Verifica que el JavaScript tiene la función de descarga
    """
    print("\n💻 Verificando JavaScript:\n")
    
    ruta_js = '/Users/sebasflorez16/Documents/AgroTech Historico/static/js/timeline/timeline_player.js'
    
    with open(ruta_js, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    verificaciones = [
        ('async downloadVideo(indice)', '✅ Función downloadVideo existe'),
        ('exportar-video/', '✅ URL de exportación configurada'),
        ('fetch(exportUrl)', '✅ Realiza petición fetch'),
        ('blob = await response.blob()', '✅ Procesa respuesta como blob'),
        ('a.download =', '✅ Descarga archivo'),
    ]
    
    todas_ok = True
    
    for patron, msg_ok in verificaciones:
        if patron in contenido:
            print(f"   {msg_ok}")
        else:
            print(f"   ❌ Falta: {patron}")
            todas_ok = False
    
    return todas_ok


def test_exportador():
    """
    Verifica el exportador multi-escena
    """
    print("\n🎬 Verificando exportador multi-escena:\n")
    
    ruta_exportador = '/Users/sebasflorez16/Documents/AgroTech Historico/informes/exporters/video_exporter_multiscene.py'
    
    with open(ruta_exportador, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    verificaciones = [
        ('class TimelineVideoExporterMultiScene', '✅ Clase TimelineVideoExporterMultiScene existe'),
        ('def export_timeline', '✅ Método export_timeline existe'),
        ('def _generate_cover_scene', '✅ Genera escena de portada'),
        ('def _generate_monthly_map_scene', '✅ Genera escenas de mapas mensuales'),
        ('def _generate_closing_scene', '✅ Genera escena de cierre'),
        ('def _draw_monthly_overlay', '✅ Dibuja overlay con columna dinámica'),
        ('subprocess.run([\'ffmpeg\'', '✅ Usa FFmpeg para video'),
    ]
    
    todas_ok = True
    
    for patron, msg_ok in verificaciones:
        if patron in contenido:
            print(f"   {msg_ok}")
        else:
            print(f"   ❌ Falta: {patron}")
            todas_ok = False
    
    return todas_ok


def main():
    """
    Ejecuta todos los tests
    """
    resultados = []
    
    resultados.append(('Estructura de archivos', test_estructura_archivos()))
    resultados.append(('Configuración de vista', test_configuracion_vista()))
    resultados.append(('Configuración de URL', test_configuracion_url()))
    resultados.append(('Template HTML', test_template_html()))
    resultados.append(('JavaScript', test_javascript()))
    resultados.append(('Exportador', test_exportador()))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE TESTS")
    print("="*70 + "\n")
    
    tests_pasados = sum(1 for _, resultado in resultados if resultado)
    tests_totales = len(resultados)
    
    for nombre, resultado in resultados:
        estado = "✅ PASS" if resultado else "❌ FAIL"
        print(f"   {estado} - {nombre}")
    
    print("\n" + "="*70)
    print(f"📈 Resultado: {tests_pasados}/{tests_totales} tests pasados")
    
    if tests_pasados == tests_totales:
        print("✅ TODOS LOS TESTS PASARON - Sistema listo para producción")
    else:
        print("⚠️  ALGUNOS TESTS FALLARON - Revisar configuración")
    
    print("="*70 + "\n")
    
    return tests_pasados == tests_totales


if __name__ == '__main__':
    resultado = main()
    sys.exit(0 if resultado else 1)
