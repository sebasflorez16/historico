#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Verificador de Mejoras UX/UI en Timeline Visual
Verifica que las correcciones de tooltips y responsive estén aplicadas correctamente
"""

import os
import re

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def verificar_archivo_existe(ruta):
    """Verifica que el archivo exista"""
    if os.path.exists(ruta):
        print(f"{GREEN}✅ Archivo encontrado:{RESET} {ruta}")
        return True
    else:
        print(f"{RED}❌ Archivo NO encontrado:{RESET} {ruta}")
        return False

def verificar_contenido(ruta, patrones_requeridos, nombre_seccion):
    """Verifica que ciertos patrones existan en el archivo"""
    print(f"\n{BLUE}🔍 Verificando {nombre_seccion}...{RESET}")
    
    if not verificar_archivo_existe(ruta):
        return False
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    errores = []
    for descripcion, patron in patrones_requeridos:
        if re.search(patron, contenido, re.MULTILINE | re.DOTALL):
            print(f"{GREEN}  ✅ {descripcion}{RESET}")
        else:
            print(f"{RED}  ❌ {descripcion}{RESET}")
            errores.append(descripcion)
    
    return len(errores) == 0

def main():
    print(f"{BLUE}{'='*70}")
    print("🔍 VERIFICACIÓN DE MEJORAS UX/UI - TIMELINE VISUAL")
    print(f"{'='*70}{RESET}\n")
    
    base_dir = "/Users/sebasflorez16/Documents/AgroTech Historico"
    
    # ========================================
    # 1️⃣ Verificar JavaScript (tooltips)
    # ========================================
    js_file = os.path.join(base_dir, "static/js/timeline/timeline_player.js")
    
    patrones_js = [
        ("Variables hayTemperatura/hayPrecipitacion", 
         r"const hayTemperatura = frame\.temperatura !== null"),
        
        ("Validación condicional de clima",
         r"if \(hayTemperatura \|\| hayPrecipitacion\)"),
        
        ("Separador | entre temperatura y precipitación",
         r"\$\{hayTemperatura \? ' \| ' : ''\}"),
        
        ("Texto 'Sin datos' en lugar de N/A",
         r"'Sin datos'"),
        
        ("Solo agregar <br> si hay datos climáticos",
         r"climaHTML = '<br>';")
    ]
    
    js_ok = verificar_contenido(js_file, patrones_js, "JavaScript (Tooltips)")
    
    # ========================================
    # 2️⃣ Verificar CSS (responsive)
    # ========================================
    html_file = os.path.join(base_dir, "templates/informes/parcelas/timeline.html")
    
    patrones_css_768 = [
        ("Media query @768px presente",
         r"@media \(max-width: 768px\)"),
        
        ("Controles en flex-direction: row",
         r"\.timeline-controls.*?flex-direction:\s*row"),
        
        ("Botones táctiles 48x48px",
         r"width:\s*48px.*?height:\s*48px"),
        
        ("Metadata en grid 2 columnas",
         r"\.metadata-panel \.row.*?grid-template-columns:\s*1fr 1fr"),
        
        ("Metadata-item flex-direction: row",
         r"\.metadata-item.*?flex-direction:\s*row"),
        
        ("Leyenda en grid 3 columnas",
         r"\.color-legend \.row.*?grid-template-columns:\s*repeat\(3,\s*1fr\)"),
        
        ("Index-selector sin wrap",
         r"\.index-selector.*?flex-wrap:\s*nowrap"),
        
        ("Index-btn flex: 1 con min-width: 0",
         r"\.index-btn.*?flex:\s*1.*?min-width:\s*0")
    ]
    
    css_768_ok = verificar_contenido(html_file, patrones_css_768, "CSS Responsive @768px")
    
    patrones_css_480 = [
        ("Media query @480px presente",
         r"@media \(max-width: 480px\)"),
        
        ("Canvas 220px de alto",
         r"#timeline-canvas.*?height:\s*220px"),
        
        ("Botones táctiles 44x44px en móvil pequeño",
         r"\.control-btn.*?width:\s*44px.*?height:\s*44px"),
        
        ("Metadata en 1 columna en móvil pequeño",
         r"\.metadata-panel \.row.*?grid-template-columns:\s*1fr !important"),
        
        ("Leyenda en 2 columnas en móvil pequeño",
         r"\.color-legend \.row.*?grid-template-columns:\s*repeat\(2,\s*1fr\) !important")
    ]
    
    css_480_ok = verificar_contenido(html_file, patrones_css_480, "CSS Responsive @480px")
    
    # ========================================
    # 3️⃣ Resumen Final
    # ========================================
    print(f"\n{BLUE}{'='*70}")
    print("📊 RESUMEN DE VERIFICACIÓN")
    print(f"{'='*70}{RESET}\n")
    
    resultados = {
        "Tooltips (JavaScript)": js_ok,
        "Responsive @768px (CSS)": css_768_ok,
        "Responsive @480px (CSS)": css_480_ok
    }
    
    todos_ok = all(resultados.values())
    
    for nombre, ok in resultados.items():
        status = f"{GREEN}✅ CORRECTO{RESET}" if ok else f"{RED}❌ FALTAN CORRECCIONES{RESET}"
        print(f"  {nombre}: {status}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    if todos_ok:
        print(f"{GREEN}🎉 TODAS LAS CORRECCIONES VERIFICADAS CORRECTAMENTE{RESET}")
        print(f"{GREEN}✅ Timeline listo para pruebas en navegador{RESET}")
    else:
        print(f"{YELLOW}⚠️  Algunas verificaciones fallaron{RESET}")
        print(f"{YELLOW}Revisa los archivos modificados manualmente{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

if __name__ == "__main__":
    main()
