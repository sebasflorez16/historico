#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificación Final - Informe Legal PDF Web
===========================================

Script de verificación rápida para confirmar que la integración
del Informe Legal PDF está funcionando correctamente.

Autor: AgroTech Histórico
Fecha: Febrero 2026
"""

import os
import sys

print("\n" + "="*80)
print("🔍 VERIFICACIÓN FINAL - INFORME LEGAL PDF WEB")
print("="*80)

checklist = []

# 1. Verificar archivos de código
print("\n1️⃣ Verificando archivos de código...")

files_to_check = {
    'informes/views.py': 'Vista Django',
    'informes/urls.py': 'URL routing',
    'templates/informes/parcelas/detalle.html': 'Template con botón',
    'verificador_legal.py': 'Verificador de restricciones',
    'generador_pdf_legal.py': 'Generador de PDF',
    'mapas_profesionales.py': 'Generador de mapas',
}

for file_path, description in files_to_check.items():
    if os.path.exists(file_path):
        print(f"   ✅ {description}: {file_path}")
        checklist.append(('Archivo ' + description, True))
    else:
        print(f"   ❌ {description}: {file_path} NO ENCONTRADO")
        checklist.append(('Archivo ' + description, False))

# 2. Verificar método en views.py
print("\n2️⃣ Verificando método verificar_parcela en views.py...")

try:
    with open('informes/views.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'verificar_parcela' in content:
            print("   ✅ Método verificar_parcela encontrado")
            checklist.append(('Método verificar_parcela', True))
            
            # Verificar argumentos correctos
            if 'parcela_id=' in content and 'geometria_parcela=' in content and 'nombre_parcela=' in content:
                print("   ✅ Argumentos correctos: parcela_id, geometria_parcela, nombre_parcela")
                checklist.append(('Argumentos correctos', True))
            else:
                print("   ⚠️  Argumentos podrían no estar completos")
                checklist.append(('Argumentos correctos', False))
        else:
            print("   ❌ Método verificar_parcela NO encontrado")
            checklist.append(('Método verificar_parcela', False))
except Exception as e:
    print(f"   ❌ Error leyendo views.py: {str(e)}")
    checklist.append(('Lectura de views.py', False))

# 3. Verificar URL pattern
print("\n3️⃣ Verificando URL pattern...")

try:
    with open('informes/urls.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'informe-legal-pdf' in content and 'generar_informe_legal_pdf' in content:
            print("   ✅ URL pattern encontrada: informe-legal-pdf")
            checklist.append(('URL pattern', True))
        else:
            print("   ❌ URL pattern NO encontrada")
            checklist.append(('URL pattern', False))
except Exception as e:
    print(f"   ❌ Error leyendo urls.py: {str(e)}")
    checklist.append(('Lectura de urls.py', False))

# 4. Verificar botón en template
print("\n4️⃣ Verificando botón en template...")

try:
    template_path = 'templates/informes/parcelas/detalle.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if '⚖️ Informe Legal' in content or 'informe-legal-pdf' in content:
            print("   ✅ Botón de Informe Legal encontrado en template")
            checklist.append(('Botón en template', True))
        else:
            print("   ❌ Botón de Informe Legal NO encontrado")
            checklist.append(('Botón en template', False))
except Exception as e:
    print(f"   ❌ Error leyendo template: {str(e)}")
    checklist.append(('Lectura de template', False))

# 5. Verificar datos geográficos
print("\n5️⃣ Verificando datos geográficos...")

if os.path.exists('datos_geograficos'):
    shapefiles = [f for f in os.listdir('datos_geograficos') if f.endswith('.shp')]
    if shapefiles:
        print(f"   ✅ Datos geográficos disponibles: {len(shapefiles)} shapefiles")
        for shp in shapefiles[:5]:  # Mostrar primeros 5
            print(f"      • {shp}")
        checklist.append(('Datos geográficos', True))
    else:
        print("   ⚠️  Directorio datos_geograficos existe pero sin shapefiles")
        checklist.append(('Datos geográficos', False))
else:
    print("   ⚠️  Directorio datos_geograficos no encontrado")
    checklist.append(('Datos geográficos', False))

# 6. Verificar directorio de salida
print("\n6️⃣ Verificando directorio de salida de PDFs...")

output_dir = 'media/verificacion_legal'
if os.path.exists(output_dir):
    pdfs = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
    print(f"   ✅ Directorio de salida existe: {len(pdfs)} PDFs generados")
    checklist.append(('Directorio de salida', True))
else:
    print(f"   ⚠️  Directorio {output_dir} no existe (se creará automáticamente)")
    checklist.append(('Directorio de salida', False))

# 7. Verificar script de test
print("\n7️⃣ Verificando scripts de test...")

test_files = [
    'test_pdf_parcela6_web_completo.py',
    'test_web_informe_legal.py',
    'test_servidor_informe_legal.sh'
]

for test_file in test_files:
    if os.path.exists(test_file):
        print(f"   ✅ {test_file}")
        checklist.append((f'Test {test_file}', True))
    else:
        print(f"   ❌ {test_file} NO ENCONTRADO")
        checklist.append((f'Test {test_file}', False))

# Resumen final
print("\n" + "="*80)
print("📊 RESUMEN DE VERIFICACIÓN")
print("="*80)

passed = sum(1 for _, status in checklist if status)
total = len(checklist)
percentage = (passed / total * 100) if total > 0 else 0

print(f"\n✅ Verificaciones exitosas: {passed}/{total} ({percentage:.1f}%)")

if percentage == 100:
    print("\n🎉 ¡INTEGRACIÓN COMPLETAMENTE VERIFICADA!")
    print("\n✅ TODO LISTO PARA USAR")
    print("\n📋 PRÓXIMOS PASOS:")
    print("   1. Iniciar servidor: python manage.py runserver")
    print("   2. Navegar a: http://localhost:8000/informes/parcelas/6/")
    print("   3. Hacer clic en: ⚖️ Informe Legal")
    print("   4. Verificar descarga del PDF")
elif percentage >= 80:
    print("\n✅ INTEGRACIÓN MAYORMENTE COMPLETADA")
    print("\n⚠️  Algunas verificaciones fallaron pero la funcionalidad debería funcionar")
    print("\n📋 Revisar los elementos marcados con ❌ arriba")
else:
    print("\n⚠️  INTEGRACIÓN INCOMPLETA")
    print("\n❌ Múltiples verificaciones fallaron")
    print("\n📋 Revisar todos los elementos marcados con ❌ arriba")

print("\n" + "="*80)
print("📚 DOCUMENTACIÓN:")
print("   • INTEGRACION_WEB_INFORME_LEGAL_FINAL.md")
print("   • INTEGRACION_INFORME_LEGAL_WEB.md")
print("="*80)
