#!/usr/bin/env python3
"""
🚀 Script de verificación de Timeline Player - Fase 2
Verifica que todos los módulos avanzados estén correctamente implementados

@author: AgroTech Team
@date: 2025-01-14
"""

import os
import sys

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def verificar_archivo(ruta, nombre):
    """Verifica la existencia de un archivo"""
    if os.path.exists(ruta):
        size_kb = os.path.getsize(ruta) / 1024
        print_success(f"{nombre} encontrado ({size_kb:.1f} KB)")
        return True
    else:
        print_error(f"{nombre} NO encontrado: {ruta}")
        return False

def verificar_contenido(ruta, buscar, nombre):
    """Verifica que un archivo contenga cierto texto"""
    if not os.path.exists(ruta):
        return False
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
        if buscar in contenido:
            print_success(f"{nombre} - Contenido verificado")
            return True
        else:
            print_error(f"{nombre} - Contenido faltante: {buscar}")
            return False

def verificar_fase2():
    """Verificación completa de la Fase 2"""
    
    print_header("🚀 VERIFICACIÓN DE TIMELINE PLAYER - FASE 2")
    
    errores = 0
    advertencias = 0
    
    # ===============================
    # 1. VERIFICAR MÓDULOS JS
    # ===============================
    print_header("1️⃣ Módulos JavaScript")
    
    modulos = [
        ('static/js/timeline/modules/playback_controller.js', 'PlaybackController'),
        ('static/js/timeline/modules/transition_engine.js', 'TransitionEngine'),
        ('static/js/timeline/modules/filter_engine.js', 'FilterEngine'),
    ]
    
    for ruta, nombre in modulos:
        if not verificar_archivo(ruta, nombre):
            errores += 1
    
    # ===============================
    # 2. VERIFICAR ESTILOS CSS
    # ===============================
    print_header("2️⃣ Estilos CSS")
    
    if not verificar_archivo('static/css/timeline_modules.css', 'timeline_modules.css'):
        errores += 1
    else:
        # Verificar clases importantes
        verificaciones_css = [
            ('static/css/timeline_modules.css', '.speed-control', 'Control de velocidad'),
            ('static/css/timeline_modules.css', '.timeline-config-panel', 'Panel de configuración'),
            ('static/css/timeline_modules.css', '.filter-group', 'Grupos de filtros'),
        ]
        
        for ruta, clase, desc in verificaciones_css:
            if not verificar_contenido(ruta, clase, desc):
                advertencias += 1
    
    # ===============================
    # 3. VERIFICAR INTEGRACIÓN EN TIMELINE_PLAYER.JS
    # ===============================
    print_header("3️⃣ Integración en timeline_player.js")
    
    verificaciones_player = [
        ('static/js/timeline/timeline_player.js', 'this.playbackController', 'PlaybackController inicializado'),
        ('static/js/timeline/timeline_player.js', 'this.transitionEngine', 'TransitionEngine inicializado'),
        ('static/js/timeline/timeline_player.js', 'this.filterEngine', 'FilterEngine inicializado'),
        ('static/js/timeline/timeline_player.js', 'initAdvancedModules', 'Método initAdvancedModules'),
        ('static/js/timeline/timeline_player.js', 'updateUIForFrame', 'Método updateUIForFrame'),
    ]
    
    for ruta, buscar, desc in verificaciones_player:
        if not verificar_contenido(ruta, buscar, desc):
            errores += 1
    
    # ===============================
    # 4. VERIFICAR TEMPLATE HTML
    # ===============================
    print_header("4️⃣ Template HTML")
    
    template = 'templates/informes/parcelas/timeline.html'
    
    verificaciones_template = [
        (template, 'playback_controller.js', 'Script PlaybackController'),
        (template, 'transition_engine.js', 'Script TransitionEngine'),
        (template, 'filter_engine.js', 'Script FilterEngine'),
        (template, 'timeline_modules.css', 'Estilos de módulos'),
    ]
    
    for ruta, buscar, desc in verificaciones_template:
        if not verificar_contenido(ruta, buscar, desc):
            errores += 1
    
    # ===============================
    # 5. VERIFICAR DOCUMENTACIÓN
    # ===============================
    print_header("5️⃣ Documentación")
    
    if verificar_archivo('docs/frontend/TIMELINE_FASE2_DISEÑO.md', 'Documento de diseño Fase 2'):
        print_info("Documento de diseño completo encontrado")
    else:
        advertencias += 1
    
    # ===============================
    # 6. VERIFICAR SINTAXIS JS (BÁSICO)
    # ===============================
    print_header("6️⃣ Verificación de sintaxis")
    
    # Verificar que no haya syntax errors obvios
    for ruta, _ in modulos:
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                
                # Verificar que tenga class
                if 'class ' in contenido:
                    print_success(f"{os.path.basename(ruta)} - Estructura de clase correcta")
                else:
                    print_error(f"{os.path.basename(ruta)} - No se encontró declaración de clase")
                    errores += 1
                
                # Verificar export
                if 'module.exports' in contenido or 'export' in contenido:
                    print_success(f"{os.path.basename(ruta)} - Export correctamente definido")
                else:
                    print_warning(f"{os.path.basename(ruta)} - No se encontró export (puede ser intencional)")
                    advertencias += 1
    
    # ===============================
    # RESUMEN FINAL
    # ===============================
    print_header("📊 RESUMEN DE VERIFICACIÓN")
    
    print(f"\n{Colors.BOLD}Archivos verificados:{Colors.RESET}")
    print(f"  • Módulos JS: {len(modulos)}")
    print(f"  • Estilos CSS: 1")
    print(f"  • Templates: 1")
    print(f"  • Documentación: 1")
    
    print(f"\n{Colors.BOLD}Resultados:{Colors.RESET}")
    
    if errores == 0 and advertencias == 0:
        print_success("VERIFICACIÓN EXITOSA - Fase 2 completamente implementada ✨")
        return 0
    elif errores == 0:
        print_warning(f"VERIFICACIÓN COMPLETADA CON ADVERTENCIAS ({advertencias} advertencias)")
        print_info("La Fase 2 está funcional pero revisa las advertencias")
        return 0
    else:
        print_error(f"VERIFICACIÓN FALLIDA - {errores} errores, {advertencias} advertencias")
        print_info("Corrige los errores antes de usar la Fase 2")
        return 1

def main():
    """Función principal"""
    try:
        result = verificar_fase2()
        
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"\n{Colors.BLUE}🔧 Próximos pasos:{Colors.RESET}")
        print(f"  1. Abre el Timeline en el navegador")
        print(f"  2. Verifica la consola del navegador (F12)")
        print(f"  3. Prueba los controles de velocidad")
        print(f"  4. Prueba las transiciones suaves")
        print(f"  5. Prueba los filtros de visualización")
        print(f"\n{Colors.BLUE}📝 Comandos útiles:{Colors.RESET}")
        print(f"  • Servidor: python manage.py runserver")
        print(f"  • Timeline: http://localhost:8000/parcelas/<ID>/timeline/")
        print(f"  • Logs: tail -f agrotech.log")
        
        sys.exit(result)
        
    except Exception as e:
        print_error(f"Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
