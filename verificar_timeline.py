#!/usr/bin/env python3
"""
Script de verificación rápida para el Timeline Player
Verifica que todos los componentes estén correctamente configurados
"""

import os
import re

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file(filepath, checks):
    """Verifica que un archivo contenga ciertos patrones"""
    print(f"\n{BLUE}Verificando:{RESET} {filepath}")
    
    if not os.path.exists(filepath):
        print(f"{RED}❌ Archivo no encontrado{RESET}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_passed = True
    for check_name, pattern, is_regex in checks:
        if is_regex:
            found = bool(re.search(pattern, content, re.MULTILINE))
        else:
            found = pattern in content
        
        if found:
            print(f"{GREEN}✅{RESET} {check_name}")
        else:
            print(f"{RED}❌{RESET} {check_name}")
            all_passed = False
    
    return all_passed

# Verificaciones para timeline_player.js
js_checks = [
    ("Declaración de clase", r"^class TimelinePlayer \{", True),
    ("Constructor completo", "constructor(config) {", False),
    ("Sistema de loading", "this.loading = {", False),
    ("Sistema de tooltip", "this.tooltip = {", False),
    ("Método init()", "async init() {", False),
    ("Método changeIndice()", "changeIndice(indice) {", False),
    ("Método cycleIndice()", "cycleIndice(direction) {", False),
    ("Atajos de teclado", "addEventListener('keydown'", False),
    ("Handler de tooltip", "handleCanvasHover(event) {", False),
    ("Export global", "window.TimelinePlayer = TimelinePlayer;", False),
]

# Verificaciones para timeline.html
html_checks = [
    ("Script timeline_player.js", "timeline_player.js", False),
    ("Canvas element", "id=\"timeline-canvas\"", False),
    ("Loading overlay", "id=\"loading-overlay\"", False),
    ("Tooltip element", "id=\"canvas-tooltip\"", False),
    ("Color legend", "class=\"color-legend\"", False),
    ("Keyboard shortcuts guide", "Atajos de teclado", False),
    ("Instanciación de TimelinePlayer", "new TimelinePlayer({", False),
]

print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}🔍 VERIFICACIÓN DE TIMELINE PLAYER - FASE 1{RESET}")
print(f"{BLUE}{'='*60}{RESET}")

# Verificar archivos
base_path = "/Users/sebasflorez16/Documents/AgroTech Historico"
js_path = os.path.join(base_path, "static/js/timeline/timeline_player.js")
html_path = os.path.join(base_path, "templates/informes/parcelas/timeline.html")

js_ok = check_file(js_path, js_checks)
html_ok = check_file(html_path, html_checks)

# Resumen final
print(f"\n{BLUE}{'='*60}{RESET}")
print(f"\n{BLUE}📊 RESUMEN:{RESET}")
if js_ok and html_ok:
    print(f"{GREEN}✅ TODOS LOS COMPONENTES VERIFICADOS CORRECTAMENTE{RESET}")
    print(f"\n{YELLOW}🚀 Siguiente paso:{RESET}")
    print("   1. Recargar la página del timeline en el navegador")
    print("   2. Abrir la consola de desarrollador (F12)")
    print("   3. Verificar que no haya errores")
    print("   4. Probar todas las funcionalidades:")
    print("      - Reproducción (Espacio)")
    print("      - Navegación (Flechas)")
    print("      - Cambio de índice (1, 2, 3)")
    print("      - Tooltips (hover sobre canvas)")
    print("      - Barra de progreso")
else:
    print(f"{RED}❌ ALGUNOS COMPONENTES TIENEN ERRORES{RESET}")
    if not js_ok:
        print(f"{RED}   - timeline_player.js tiene problemas{RESET}")
    if not html_ok:
        print(f"{RED}   - timeline.html tiene problemas{RESET}")

print(f"\n{BLUE}{'='*60}{RESET}\n")
