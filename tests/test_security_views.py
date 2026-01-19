#!/usr/bin/env python3
"""
Auditoría de Seguridad - Sistema de Autorización en Views
Verifica que todas las vistas críticas tengan los decoradores de seguridad correctos

CRÍTICO: Solo superusuarios pueden acceder a:
- Dashboard admin
- Gestión de usuarios
- Informes de todas las parcelas
- Configuraciones del sistema

@author: AgroTech Team
@date: 19 de enero de 2026
"""

import os
import sys
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple

# Colores para terminal
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def analizar_vista(funcion_codigo: str, nombre_funcion: str) -> Dict:
    """
    Analiza una función de vista para detectar decoradores de seguridad
    """
    resultado = {
        'nombre': nombre_funcion,
        'tiene_login_required': False,
        'tiene_superuser_required': False,
        'tiene_user_passes_test': False,
        'decoradores': [],
        'es_clase': False,
        'nivel_riesgo': 'BAJO'
    }
    
    # Detectar decoradores
    decoradores_pattern = r'@(\w+(?:\.\w+)?(?:\([^)]*\))?)'
    decoradores = re.findall(decoradores_pattern, funcion_codigo)
    resultado['decoradores'] = decoradores
    
    # Verificar tipos de decoradores
    for dec in decoradores:
        if 'login_required' in dec:
            resultado['tiene_login_required'] = True
        if 'user_passes_test' in dec and 'is_superuser' in funcion_codigo:
            resultado['tiene_superuser_required'] = True
            resultado['tiene_user_passes_test'] = True
        if 'user_passes_test' in dec:
            resultado['tiene_user_passes_test'] = True
    
    # Detectar si es clase (CBV)
    if 'class ' in funcion_codigo and 'View' in funcion_codigo:
        resultado['es_clase'] = True
    
    return resultado


def clasificar_vista(nombre: str, codigo: str) -> str:
    """
    Clasifica el nivel de criticidad de una vista
    
    PÚBLICO - No requiere autenticación (registro, login, etc)
    BAJO - Usuario autenticado (sus propios recursos)
    ALTO - Usuario autenticado (recursos sensibles)
    CRÍTICO - Solo superusuarios (admin, sistema, eliminaciones)
    """
    # Vistas PÚBLICAS (NO requieren login - son intencionales)
    vistas_publicas = [
        'registro_cliente', 'login', 'logout', 'password_reset',
        'mapa_parcela',  # Usuario dibuja su parcela al registrarse
    ]
    
    # Vistas CRÍTICAS (solo superusuario)
    vistas_criticas = [
        'admin_dashboard', 'dashboard',  # Si muestran TODAS las parcelas
        'eliminar_informe', 'eliminar_parcela', 'delete',
        'estado_sistema', 'estado_sincronizacion',
        'crear_usuario', 'eliminar_usuario', 'listar_usuarios',
        'configuracion', 'settings'
    ]
    
    # Vistas ALTAS (requieren login - recursos propios)
    vistas_altas = [
        'crear_parcela', 'editar', 'modificar', 'generar_informe',
        'sincronizar', 'actualizar', 'detalle_informe', 'lista_informes',
        'procesar_datos', 'analisis', 'api_datos'
    ]
    
    nombre_lower = nombre.lower()
    
    # 1. Verificar si es pública (intencional)
    for palabra in vistas_publicas:
        if palabra in nombre_lower:
            return 'PÚBLICO'
    
    # 2. Verificar vistas críticas
    for palabra in vistas_criticas:
        if palabra in nombre_lower:
            return 'CRÍTICO'
    
    # 3. Verificar si accede a TODAS las parcelas (CRÍTICO)
    if 'Parcela.objects.all()' in codigo:
        # Si NO filtra por propietario = request.user, es CRÍTICO
        if 'filter(propietario=' not in codigo and 'request.user' not in codigo:
            return 'CRÍTICO'
    
    # 4. Verificar vistas altas
    for palabra in vistas_altas:
        if palabra in nombre_lower:
            return 'ALTO'
    
    return 'BAJO'


def extraer_vistas_de_archivo(ruta_archivo: Path) -> List[Dict]:
    """
    Extrae todas las vistas de un archivo views.py
    """
    vistas = []
    
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Buscar funciones de vista (FBV)
        funciones_pattern = r'(@[\w\.\(\)]+\s+)*def\s+(\w+)\s*\([^)]*request[^)]*\):((?:\n(?!def |class ).*)*)'
        matches = re.finditer(funciones_pattern, contenido, re.MULTILINE)
        
        for match in matches:
            decoradores_texto = match.group(1) or ''
            nombre_funcion = match.group(2)
            codigo_funcion = decoradores_texto + match.group(0)
            
            # Evitar funciones privadas
            if nombre_funcion.startswith('_'):
                continue
            
            vista_info = analizar_vista(codigo_funcion, nombre_funcion)
            vista_info['tipo'] = 'FBV'
            vista_info['nivel_criticidad'] = clasificar_vista(nombre_funcion, codigo_funcion)
            vista_info['archivo'] = ruta_archivo.name
            
            vistas.append(vista_info)
        
        # Buscar vistas basadas en clase (CBV)
        clases_pattern = r'class\s+(\w+)\s*\([^)]*View[^)]*\):((?:\n(?!class ).*)*)'
        matches_clases = re.finditer(clases_pattern, contenido, re.MULTILINE)
        
        for match in matches_clases:
            nombre_clase = match.group(1)
            codigo_clase = match.group(0)
            
            vista_info = analizar_vista(codigo_clase, nombre_clase)
            vista_info['tipo'] = 'CBV'
            vista_info['nivel_criticidad'] = clasificar_vista(nombre_clase, codigo_clase)
            vista_info['archivo'] = ruta_archivo.name
            vista_info['es_clase'] = True
            
            vistas.append(vista_info)
        
    except Exception as e:
        print(f"{Colors.RED}❌ Error leyendo {ruta_archivo}: {e}{Colors.RESET}")
    
    return vistas


def evaluar_seguridad_vista(vista: Dict) -> Tuple[str, str]:
    """
    Evalúa si una vista tiene el nivel de seguridad adecuado
    Retorna (estado, mensaje)
    """
    nombre = vista['nombre']
    criticidad = vista['nivel_criticidad']
    
    # Vistas PÚBLICAS están bien sin decoradores (intencional)
    if criticidad == 'PÚBLICO':
        return ('SEGURO', 'Vista pública intencional (registro, login, etc)')
    
    # Vistas CRÍTICAS deben tener @user_passes_test(is_superuser)
    if criticidad == 'CRÍTICO':
        if not vista['tiene_superuser_required']:
            return ('VULNERABLE', f'Vista CRÍTICA sin protección de superusuario')
        else:
            return ('SEGURO', 'Protección de superusuario OK')
    
    # Vistas ALTAS y BAJAS deben tener al menos @login_required
    elif criticidad in ['ALTO', 'BAJO']:
        if not vista['tiene_login_required'] and not vista['tiene_superuser_required']:
            return ('VULNERABLE', 'Vista sin @login_required')
        else:
            return ('SEGURO', 'Autenticación básica OK')
    
    return ('REVISAR', 'Nivel de seguridad no clasificado')


def auditar_vistas():
    """
    Audita todas las vistas del proyecto
    """
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}🔒 AUDITORÍA DE SEGURIDAD - SISTEMA DE AUTORIZACIÓN{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    # Buscar archivos views.py
    base_dir = Path(__file__).parent.parent
    archivos_views = list(base_dir.glob('**/views*.py'))
    
    print(f"{Colors.BLUE}📂 Archivos encontrados:{Colors.RESET}")
    for archivo in archivos_views:
        print(f"   • {archivo.relative_to(base_dir)}")
    print()
    
    # Analizar todas las vistas
    todas_vistas = []
    for archivo in archivos_views:
        vistas = extraer_vistas_de_archivo(archivo)
        todas_vistas.extend(vistas)
    
    print(f"{Colors.BLUE}📊 Total de vistas encontradas: {len(todas_vistas)}{Colors.RESET}\n")
    
    # Clasificar por nivel de seguridad
    vistas_vulnerables = []
    vistas_seguras = []
    vistas_revisar = []
    
    for vista in todas_vistas:
        estado, mensaje = evaluar_seguridad_vista(vista)
        vista['estado_seguridad'] = estado
        vista['mensaje_seguridad'] = mensaje
        
        if estado == 'VULNERABLE':
            vistas_vulnerables.append(vista)
        elif estado == 'SEGURO':
            vistas_seguras.append(vista)
        else:
            vistas_revisar.append(vista)
    
    # REPORTE: Vistas VULNERABLES (CRÍTICO)
    if vistas_vulnerables:
        print(f"{Colors.RED}{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}🚨 VISTAS VULNERABLES - ACCIÓN REQUERIDA{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}{'='*80}{Colors.RESET}\n")
        
        for vista in vistas_vulnerables:
            print(f"{Colors.RED}❌ {vista['nombre']}{Colors.RESET} ({vista['archivo']})")
            print(f"   Tipo: {vista['tipo']}")
            print(f"   Criticidad: {Colors.RED}{Colors.BOLD}{vista['nivel_criticidad']}{Colors.RESET}")
            print(f"   Problema: {vista['mensaje_seguridad']}")
            print(f"   Decoradores actuales: {vista['decoradores'] if vista['decoradores'] else 'NINGUNO'}")
            
            # Sugerencias de corrección
            if vista['nivel_criticidad'] == 'CRÍTICO':
                print(f"   {Colors.YELLOW}💡 Sugerencia: Agregar @user_passes_test(lambda u: u.is_superuser){Colors.RESET}")
            else:
                print(f"   {Colors.YELLOW}💡 Sugerencia: Agregar @login_required{Colors.RESET}")
            print()
    
    # REPORTE: Vistas que necesitan revisión
    if vistas_revisar:
        print(f"{Colors.YELLOW}{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  VISTAS PARA REVISAR{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}{'='*80}{Colors.RESET}\n")
        
        for vista in vistas_revisar:
            print(f"{Colors.YELLOW}⚠️  {vista['nombre']}{Colors.RESET} ({vista['archivo']})")
            print(f"   Decoradores: {vista['decoradores']}")
            print()
    
    # REPORTE: Vistas seguras (resumen)
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}✅ VISTAS SEGURAS{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.GREEN}Total: {len(vistas_seguras)} vistas con seguridad adecuada{Colors.RESET}\n")
    
    # RESUMEN FINAL
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}📊 RESUMEN DE AUDITORÍA{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.GREEN}✅ Vistas seguras: {len(vistas_seguras)}{Colors.RESET}")
    print(f"{Colors.YELLOW}⚠️  Vistas para revisar: {len(vistas_revisar)}{Colors.RESET}")
    print(f"{Colors.RED}❌ Vistas vulnerables: {len(vistas_vulnerables)}{Colors.RESET}")
    
    total = len(todas_vistas)
    porcentaje_seguro = (len(vistas_seguras) / total * 100) if total > 0 else 0
    
    print(f"\n{Colors.CYAN}Nivel de seguridad del sistema: {porcentaje_seguro:.1f}%{Colors.RESET}")
    
    if len(vistas_vulnerables) == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SISTEMA SEGURO - No se encontraron vulnerabilidades críticas{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  ACCIÓN REQUERIDA - Corregir {len(vistas_vulnerables)} vulnerabilidades{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    exit_code = auditar_vistas()
    sys.exit(exit_code)
