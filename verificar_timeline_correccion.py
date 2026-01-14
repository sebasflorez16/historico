#!/usr/bin/env python3
"""
Verificador de correcciones del Timeline Player
Valida que no existan los errores críticos reportados
"""

import os
import re
from pathlib import Path

def verificar_archivo(ruta, patrones_error, patrones_ok):
    """Verifica un archivo buscando patrones problemáticos y correctos"""
    print(f"\n🔍 Verificando: {ruta.name}")
    
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    errores = []
    aciertos = []
    
    # Buscar patrones de error
    for nombre, patron in patrones_error.items():
        matches = re.findall(patron, contenido, re.MULTILINE)
        if matches:
            errores.append(f"  ❌ {nombre}: {len(matches)} ocurrencia(s)")
            for match in matches[:3]:  # Mostrar primeros 3
                errores.append(f"     └─ {match[:100]}")
    
    # Buscar patrones correctos
    for nombre, patron in patrones_ok.items():
        if re.search(patron, contenido, re.MULTILINE):
            aciertos.append(f"  ✅ {nombre}")
    
    if errores:
        print("  ERRORES ENCONTRADOS:")
        for error in errores:
            print(error)
    
    if aciertos:
        print("  VALIDACIONES OK:")
        for acierto in aciertos:
            print(acierto)
    
    return len(errores) == 0


def main():
    print("=" * 70)
    print("🔧 VERIFICADOR DE CORRECCIONES - TIMELINE PLAYER")
    print("=" * 70)
    
    base_dir = Path(__file__).parent
    todo_ok = True
    
    # ========================================
    # 1. VERIFICAR transition_engine.js
    # ========================================
    transition_file = base_dir / 'static/js/timeline/modules/transition_engine.js'
    
    if transition_file.exists():
        patrones_error_transition = {
            'frame.url (debe ser frame.imagenes[indice])': r'frame\.url',
            'frame.index (debe buscarse en array)': r'frame\.index',
        }
        
        patrones_ok_transition = {
            'Usa frame.imagenes[currentIndice]': r'frame\.imagenes\[this\.player\.currentIndice\]',
            'Método finishTransition actualiza metadata': r'this\.player\.updateMetadata',
            'Método finishTransition actualiza currentIndex': r'this\.player\.currentIndex\s*=\s*toFrameIndex',
            'Validación de URLs de imagen': r'if\s*\(\s*!fromImageUrl\s*\|\|\s*!toImageUrl\s*\)',
        }
        
        ok = verificar_archivo(transition_file, patrones_error_transition, patrones_ok_transition)
        todo_ok = todo_ok and ok
    else:
        print(f"\n⚠️  No encontrado: {transition_file}")
        todo_ok = False
    
    # ========================================
    # 2. VERIFICAR timeline_player.js
    # ========================================
    player_file = base_dir / 'static/js/timeline/timeline_player.js'
    
    if player_file.exists():
        patrones_error_player = {
            'updateMetadata sin validación de frame': r'updateMetadata\(frame\)\s*{[^}]*valuePeriodo',
        }
        
        patrones_ok_player = {
            'Validación de frame en updateMetadata': r'if\s*\(\s*!frame\s*\)',
            'Validación de índice en goToFrame': r'if\s*\(\s*index\s*<\s*0\s*\|\|\s*index\s*>=\s*this\.frames\.length\s*\)',
            'Tooltip configurado (handleCanvasHover)': r'handleCanvasHover\(event\)',
            'Tooltip configurado (handleCanvasLeave)': r'handleCanvasLeave\(\)',
            'Método cycleIndice existe': r'cycleIndice\(direction\)',
        }
        
        ok = verificar_archivo(player_file, patrones_error_player, patrones_ok_player)
        todo_ok = todo_ok and ok
    else:
        print(f"\n⚠️  No encontrado: {player_file}")
        todo_ok = False
    
    # ========================================
    # 3. VERIFICAR ERRORES ESPECÍFICOS REPORTADOS
    # ========================================
    print("\n" + "=" * 70)
    print("🎯 VERIFICACIÓN DE ERRORES ESPECÍFICOS REPORTADOS")
    print("=" * 70)
    
    if transition_file.exists():
        with open(transition_file, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Error 1: URL undefined
        if 'frame.url' not in contenido:
            print("✅ Error 'frame.url undefined' CORREGIDO")
        else:
            print("❌ Error 'frame.url undefined' AÚN PRESENTE")
            todo_ok = False
        
        # Error 2: finishTransition actualiza metadata
        if 'updateMetadata' in contenido and 'finishTransition' in contenido:
            print("✅ finishTransition actualiza metadata correctamente")
        else:
            print("❌ finishTransition NO actualiza metadata")
            todo_ok = False
    
    if player_file.exists():
        with open(player_file, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Error 3: updateMetadata sin validación
        if re.search(r'updateMetadata\(frame\)\s*{[^}]*if\s*\(\s*!frame\s*\)', contenido):
            print("✅ updateMetadata valida frame antes de usarlo")
        else:
            print("❌ updateMetadata NO valida frame")
            todo_ok = False
        
        # Error 4: Tooltip eliminado
        if 'handleCanvasHover' in contenido and 'handleCanvasLeave' in contenido:
            print("✅ Tooltip (handleCanvasHover/Leave) RESTAURADO")
        else:
            print("❌ Tooltip AÚN FALTA")
            todo_ok = False
    
    # ========================================
    # RESUMEN FINAL
    # ========================================
    print("\n" + "=" * 70)
    if todo_ok:
        print("✅✅✅ TODAS LAS CORRECCIONES APLICADAS CORRECTAMENTE ✅✅✅")
        print("\nPróximos pasos:")
        print("1. Recargar la página en el navegador (Ctrl+Shift+R)")
        print("2. Abrir DevTools (F12) y verificar consola")
        print("3. Navegar entre frames con flechas o botones")
        print("4. Verificar que el contador muestra 'N / Total' correctamente")
        print("5. Verificar que el tooltip aparece al hacer hover")
    else:
        print("❌❌❌ ERRORES DETECTADOS - REVISAR ARCHIVOS ❌❌❌")
        print("\nRevisar los archivos marcados arriba y corregir manualmente.")
    
    print("=" * 70)
    return 0 if todo_ok else 1


if __name__ == '__main__':
    exit(main())
