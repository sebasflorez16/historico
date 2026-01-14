#!/usr/bin/env python3
"""
Verificador de Configuración Responsive del Timeline Player
Valida que el CSS y JavaScript estén correctamente configurados
"""

import re
from pathlib import Path

def verificar_css_responsive(archivo_html):
    """Verifica que el CSS responsive esté correctamente configurado"""
    print(f"\n🎨 Verificando CSS Responsive...")
    
    with open(archivo_html, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    checks = {
        'canvas-wrapper con aspect-ratio': r'\.canvas-wrapper\s*\{[^}]*aspect-ratio:\s*16\s*/\s*9',
        'aspect-ratio en tablet': r'@media.*max-width:\s*768px.*aspect-ratio:\s*4\s*/\s*3',
        'aspect-ratio en móvil': r'@media.*max-width:\s*480px.*aspect-ratio:\s*1\s*/\s*1',
        'canvas position absolute': r'#timeline-canvas\s*\{[^}]*position:\s*absolute',
        'canvas width 100%': r'#timeline-canvas\s*\{[^}]*width:\s*100%',
        'canvas height 100%': r'#timeline-canvas\s*\{[^}]*height:\s*100%',
    }
    
    resultados = []
    for nombre, patron in checks.items():
        if re.search(patron, contenido, re.MULTILINE | re.DOTALL):
            resultados.append(f"  ✅ {nombre}")
        else:
            resultados.append(f"  ❌ {nombre} - NO ENCONTRADO")
    
    for r in resultados:
        print(r)
    
    return all('✅' in r for r in resultados)


def verificar_js_responsive(archivo_js):
    """Verifica que el JavaScript responsive esté correctamente configurado"""
    print(f"\n💻 Verificando JavaScript Responsive...")
    
    with open(archivo_js, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    checks = {
        'Función resizeCanvas existe': r'const resizeCanvas\s*=\s*\(\)\s*=>\s*\{',
        'Listener window.resize': r'window\.addEventListener\([\'"]resize[\'"]\s*,',
        'Debounce en resize': r'clearTimeout\(resizeTimeout\)',
        'Device Pixel Ratio (DPR)': r'const dpr\s*=\s*window\.devicePixelRatio',
        'Canvas width con DPR': r'this\.canvas\.width\s*=\s*\w+\s*\*\s*dpr',
        'Canvas height con DPR': r'this\.canvas\.height\s*=\s*\w+\s*\*\s*dpr',
        'Context scale con DPR': r'this\.ctx\.scale\(dpr,\s*dpr\)',
        'Re-renderizado en resize': r'if\s*\(this\.frames\.length\s*>\s*0.*this\.drawImage',
        'Tamaños de fuente dinámicos (overlay)': r'const\s+baseFontSize\s*=\s*Math\.max\(\d+,\s*canvasWidth\s*/\s*\d+\)',
        'Tamaños de fuente dinámicos (placeholder)': r'const\s+iconSize\s*=\s*Math\.max\(\d+,\s*canvasWidth\s*/\s*\d+\)',
        'Overlay altura adaptativa': r'const\s+overlayHeight\s*=\s*Math\.min\(',
        'Padding adaptativo': r'const\s+padding\s*=\s*Math\.max\(',
    }
    
    resultados = []
    for nombre, patron in checks.items():
        if re.search(patron, contenido, re.MULTILINE | re.DOTALL):
            resultados.append(f"  ✅ {nombre}")
        else:
            resultados.append(f"  ❌ {nombre} - NO ENCONTRADO")
    
    for r in resultados:
        print(r)
    
    return all('✅' in r for r in resultados)


def verificar_html_estructura(archivo_html):
    """Verifica que la estructura HTML sea correcta"""
    print(f"\n🏗️  Verificando Estructura HTML...")
    
    with open(archivo_html, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    checks = {
        'div.canvas-wrapper existe': r'<div\s+class=["\']canvas-wrapper["\']',
        'canvas dentro de wrapper': r'<div\s+class=["\']canvas-wrapper["\']>[\s\S]*?<canvas\s+id=["\']timeline-canvas["\']',
        'canvas sin style inline de altura': r'<canvas\s+id=["\']timeline-canvas["\'](?![^>]*style=["\'][^"\']*height)',
    }
    
    resultados = []
    for nombre, patron in checks.items():
        if re.search(patron, contenido, re.MULTILINE):
            resultados.append(f"  ✅ {nombre}")
        else:
            resultados.append(f"  ❌ {nombre} - NO ENCONTRADO")
    
    for r in resultados:
        print(r)
    
    return all('✅' in r for r in resultados)


def main():
    print("=" * 70)
    print("📱 VERIFICADOR DE RESPONSIVE - TIMELINE PLAYER")
    print("=" * 70)
    
    base_dir = Path(__file__).parent
    
    # Archivos a verificar
    html_file = base_dir / 'templates/informes/parcelas/timeline.html'
    js_file = base_dir / 'static/js/timeline/timeline_player.js'
    
    todo_ok = True
    
    # Verificar HTML
    if html_file.exists():
        html_ok = verificar_html_estructura(html_file)
        css_ok = verificar_css_responsive(html_file)
        todo_ok = todo_ok and html_ok and css_ok
    else:
        print(f"\n❌ No encontrado: {html_file}")
        todo_ok = False
    
    # Verificar JavaScript
    if js_file.exists():
        js_ok = verificar_js_responsive(js_file)
        todo_ok = todo_ok and js_ok
    else:
        print(f"\n❌ No encontrado: {js_file}")
        todo_ok = False
    
    # Resumen
    print("\n" + "=" * 70)
    if todo_ok:
        print("✅✅✅ RESPONSIVE COMPLETAMENTE CONFIGURADO ✅✅✅")
        print("\n📱 Breakpoints configurados:")
        print("  • Desktop (>768px):  aspect-ratio 16:9")
        print("  • Tablet (≤768px):   aspect-ratio 4:3")
        print("  • Móvil (≤480px):    aspect-ratio 1:1")
        print("\n🎨 Tamaños dinámicos:")
        print("  • Fuentes:    12px - 24px (basado en canvasWidth)")
        print("  • Padding:    10px - 20px (adaptativo)")
        print("  • Overlay:    60px - 120px (adaptativo)")
        print("\n💻 Device Pixel Ratio:")
        print("  • Retina/4K:  Soporte completo (DPR 2x-3x)")
        print("  • Re-render:  Automático al redimensionar")
        print("\n🚀 Próximos pasos:")
        print("  1. Recargar navegador (Ctrl+Shift+R)")
        print("  2. Abrir DevTools (F12) → Toggle device toolbar (Ctrl+Shift+M)")
        print("  3. Probar dispositivos: iPhone 12, iPad, Desktop")
        print("  4. Verificar que canvas se adapta correctamente")
    else:
        print("❌❌❌ CONFIGURACIÓN RESPONSIVE INCOMPLETA ❌❌❌")
        print("\nRevisar los checks marcados con ❌ arriba")
    print("=" * 70)
    
    return 0 if todo_ok else 1


if __name__ == '__main__':
    exit(main())
