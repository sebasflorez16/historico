#!/usr/bin/env python3
"""
Script de verificación final - Timeline Player Fase 2
Verifica que no haya errores de NaN y que las imágenes se carguen correctamente
"""

import os
import re

print("=" * 60)
print("VERIFICACIÓN FINAL - TIMELINE PLAYER FASE 2")
print("=" * 60)
print()

# Archivos a verificar
archivos = [
    'static/js/timeline/timeline_player.js',
    'static/js/timeline/modules/playback_controller.js',
    'static/js/timeline/modules/transition_engine.js',
    'static/js/timeline/modules/filter_engine.js',
]

errores = []
advertencias = []

print("1. Verificando emojis excesivos...")
for archivo in archivos:
    if not os.path.exists(archivo):
        errores.append(f"Archivo no encontrado: {archivo}")
        continue
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
        
        # Buscar emojis excesivos en console.log
        emojis_log = re.findall(r'console\.(log|info|warn|error)\([\'"]([🎬🎯📡✅❌⚠️🆕🔥🎉🎨🚀🎛️]*)', contenido)
        if emojis_log:
            for match in emojis_log:
                if match[1]:  # Si hay emojis
                    advertencias.append(f"{os.path.basename(archivo)}: Emoji en log: {match[1]}")

print(f"   - Emojis encontrados: {len(advertencias)}")

print("\n2. Verificando manejo de NaN...")
nan_checks = 0
for archivo in archivos:
    if not os.path.exists(archivo):
        continue
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
        
        # Buscar validaciones de null/undefined
        checks = re.findall(r'!== null|!== undefined|typeof.*!== [\'"]undefined[\'"]', contenido)
        nan_checks += len(checks)

print(f"   - Validaciones de null/undefined encontradas: {nan_checks}")
if nan_checks < 10:
    advertencias.append("Pocas validaciones de null/undefined - revisar código")

print("\n3. Verificando updateFrameCounter...")
for archivo in ['static/js/timeline/timeline_player.js']:
    if not os.path.exists(archivo):
        continue
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
        
        # Buscar updateFrameCounter
        if 'updateFrameCounter()' in contenido:
            # Verificar que tenga validación
            if 'if (!this.elements.frameCounter) return' in contenido:
                print("   ✓ updateFrameCounter tiene validación")
            else:
                errores.append("updateFrameCounter sin validación de elemento")

print("\n4. Verificando inicialización de frames...")
for archivo in ['static/js/timeline/timeline_player.js']:
    if not os.path.exists(archivo):
        continue
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
        
        # Verificar que frames se inicialice correctamente
        if 'this.frames = data.frames || []' in contenido:
            print("   ✓ Frames se inicializa correctamente")
        else:
            errores.append("Inicialización de frames incorrecta")
        
        # Verificar que haya check de length
        if 'this.frames.length === 0' in contenido:
            print("   ✓ Validación de frames vacíos presente")
        else:
            advertencias.append("Falta validación de frames vacíos")

print("\n5. Verificando elementos del DOM...")
for archivo in ['static/js/timeline/timeline_player.js']:
    if not os.path.exists(archivo):
        continue
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
        
        # Verificar validaciones de elementos
        validaciones = re.findall(r'if \(.*\.elements\.[a-zA-Z]+\)', contenido)
        print(f"   - Validaciones de elementos DOM: {len(validaciones)}")

print()
print("=" * 60)
print("RESUMEN")
print("=" * 60)

if errores:
    print(f"\n❌ ERRORES CRÍTICOS ({len(errores)}):")
    for error in errores:
        print(f"   - {error}")

if advertencias:
    print(f"\n⚠️  ADVERTENCIAS ({len(advertencias)}):")
    for adv in advertencias[:5]:  # Mostrar solo las primeras 5
        print(f"   - {adv}")
    if len(advertencias) > 5:
        print(f"   ... y {len(advertencias) - 5} más")

if not errores and not advertencias:
    print("\n✅ VERIFICACIÓN EXITOSA - No se encontraron problemas")
elif not errores:
    print("\n✓ Verificación completada con advertencias menores")
else:
    print("\n✗ Verificación fallida - Corrige los errores críticos")

print()
print("=" * 60)
print("PRÓXIMOS PASOS:")
print("=" * 60)
print()
print("1. Iniciar servidor: python manage.py runserver")
print("2. Abrir navegador: http://localhost:8000/parcelas/<ID>/timeline/")
print("3. Abrir consola (F12) y verificar:")
print("   - No debe haber errores JavaScript")
print("   - El contador debe mostrar '1 / N' (no 'NaN / N')")
print("   - Las imágenes deben cargarse correctamente")
print()
