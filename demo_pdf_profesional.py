#!/usr/bin/env python
"""
Script de Demostración: Sistema de PDFs Profesionales v2.0
===========================================================

Este script muestra cómo usar el nuevo sistema de generación de PDFs
con todas las mejoras UX/UI implementadas.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional
from datetime import datetime, timedelta


def demo_generar_pdf_profesional():
    """Demuestra la generación de un PDF con el nuevo diseño"""
    print("=" * 70)
    print("🎨 DEMO: Generación de PDF Profesional v2.0")
    print("=" * 70)
    
    # 1. Seleccionar parcela
    print("\n📍 Paso 1: Seleccionar parcela")
    parcela = Parcela.objects.first()
    
    if not parcela:
        print("❌ No hay parcelas en la base de datos")
        return
    
    print(f"   ✓ Parcela seleccionada: {parcela.nombre}")
    print(f"   ✓ Área: {parcela.area_hectareas:.2f} ha")
    print(f"   ✓ Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
    
    # 2. Configurar fechas
    print("\n📅 Paso 2: Configurar período de análisis")
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=180)  # 6 meses
    
    print(f"   ✓ Desde: {fecha_inicio.strftime('%d/%m/%Y')}")
    print(f"   ✓ Hasta: {fecha_fin.strftime('%d/%m/%Y')}")
    
    # 3. Generar PDF
    print("\n🔨 Paso 3: Generar PDF con diseño profesional")
    print("   (Esto puede tomar 30-60 segundos...)")
    
    try:
        generador = GeneradorPDFProfesional()
        pdf_path = generador.generar(
            parcela_id=parcela.id,
            tipo_informe='rapido',
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        print(f"\n✅ ¡PDF generado exitosamente!")
        print(f"   Ubicación: {pdf_path}")
        
        # Mostrar características del PDF
        if os.path.exists(pdf_path):
            size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            print(f"   Tamaño: {size_mb:.2f} MB")
        
        # 4. Validar automáticamente
        print("\n🔍 Paso 4: Validar calidad UX del PDF")
        validar_pdf(pdf_path)
        
        # 5. Abrir PDF
        print("\n📄 Paso 5: Abrir PDF generado")
        print("   Ejecute:")
        print(f"   open {pdf_path}")
        
        return pdf_path
        
    except Exception as e:
        print(f"\n❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


def validar_pdf(pdf_path):
    """Valida el PDF usando el script de validación"""
    import subprocess
    
    validador = "validar_ux_pdf_profesional.py"
    
    if not os.path.exists(validador):
        print(f"   ⚠️  Validador no encontrado: {validador}")
        return
    
    try:
        resultado = subprocess.run(
            ['python', validador, pdf_path],
            capture_output=True,
            text=True
        )
        
        print(resultado.stdout)
        
        if resultado.returncode == 0:
            print("   ✅ PDF validado correctamente")
        else:
            print("   ⚠️  PDF tiene advertencias menores")
            
    except Exception as e:
        print(f"   ⚠️  No se pudo ejecutar validador: {e}")


def demo_personalizar_colores():
    """Demuestra cómo personalizar los colores del banner"""
    print("\n" + "=" * 70)
    print("🎨 DEMO: Personalización de Colores")
    print("=" * 70)
    
    print("""
Para personalizar los colores del banner ejecutivo, edite el archivo:
informes/generador_pdf.py

En el método _crear_resumen_ejecutivo(), modifique:

# Umbrales de eficiencia
if eficiencia >= 85:  # Cambiar de 80 a 85
    color_fondo = '#27AE60'  # Verde
    estado = 'EXCELENTE'
elif eficiencia >= 65:  # Cambiar de 60 a 65
    color_fondo = '#F39C12'  # Amber
    estado = 'REQUIERE ATENCIÓN'
else:
    color_fondo = '#E67E22'  # Soft red
    estado = 'CRÍTICO'

# Paleta de colores completa en:
# REFACTORIZACION_UX_PDF_PROFESIONAL.md
""")


def demo_agregar_seccion_compacta():
    """Demuestra cómo agregar una sección sin fragmentar el documento"""
    print("\n" + "=" * 70)
    print("📋 DEMO: Agregar Sección Compacta")
    print("=" * 70)
    
    print("""
Para agregar una nueva sección SIN crear saltos de página innecesarios:

from reportlab.platypus import Spacer, Paragraph

def _crear_mi_seccion(self):
    elements = []
    
    # Título de sección
    titulo = Paragraph(
        '<font size="12" color="#2C3E50"><b>Mi Nueva Sección</b></font>',
        self.estilos['TituloSeccion']
    )
    elements.append(titulo)
    elements.append(Spacer(1, 0.5*cm))  # ← Usar Spacer, NO PageBreak
    
    # Contenido
    contenido = Paragraph(
        "Contenido de la sección...",
        self.estilos['TextoNormal']
    )
    elements.append(contenido)
    elements.append(Spacer(1, 0.8*cm))  # ← Permitir flujo natural
    
    return elements

# En generar():
story.extend(self._crear_mi_seccion())
# NO agregar PageBreak aquí - dejar que fluya

# Solo usar PageBreak en puntos estratégicos:
# - Fin de portada
# - Inicio de anexos
# - Inicio de diagnóstico final
""")


def demo_crear_tabla_profesional():
    """Demuestra cómo crear una tabla con diseño profesional"""
    print("\n" + "=" * 70)
    print("📊 DEMO: Crear Tabla Profesional")
    print("=" * 70)
    
    print("""
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# Datos
data = [
    ['Parámetro', 'Valor'],
    ['NDVI promedio', '0.67'],
    ['NDMI promedio', '0.12'],
    ['SAVI promedio', '0.54'],
]

# Crear tabla
tabla = Table(data, colWidths=[10*cm, 5*cm])

# Estilo PROFESIONAL (colores suaves)
tabla.setStyle(TableStyle([
    # Encabezado
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    
    # Contenido
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    
    # Colores alternados SUAVES
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
     [colors.white, colors.HexColor('#F8F9FA')]),
    
    # Bordes redondeados
    ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#BDC3C7')),
    ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    
    # Padding generoso
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
]))

story.append(tabla)
""")


def mostrar_menu():
    """Muestra el menú de opciones"""
    print("\n" + "=" * 70)
    print("🎨 Sistema de PDFs Profesionales v2.0 - DEMO")
    print("=" * 70)
    print("\nOpciones:")
    print("  1. Generar PDF con nuevo diseño")
    print("  2. Ver cómo personalizar colores")
    print("  3. Ver cómo agregar sección compacta")
    print("  4. Ver cómo crear tabla profesional")
    print("  5. Ver documentación completa")
    print("  0. Salir")
    print("=" * 70)
    
    return input("\nSeleccione una opción: ")


def mostrar_documentacion():
    """Muestra la ubicación de la documentación"""
    print("\n" + "=" * 70)
    print("📚 Documentación del Sistema")
    print("=" * 70)
    
    documentos = [
        ("REFACTORIZACION_UX_PDF_PROFESIONAL.md", "Documentación completa de la refactorización"),
        ("GUIA_RAPIDA_PDF_v2.md", "Guía de uso rápido para desarrolladores"),
        ("RESUMEN_REFACTORIZACION_UX_FINAL.md", "Resumen ejecutivo de cambios"),
        ("EJEMPLO_VISUAL_NUEVO_DISENO.py", "Ejemplos visuales del nuevo diseño"),
        ("validar_ux_pdf_profesional.py", "Validador automático de calidad UX"),
    ]
    
    print("\nArchivos disponibles:")
    for archivo, descripcion in documentos:
        if os.path.exists(archivo):
            print(f"  ✓ {archivo}")
            print(f"    {descripcion}")
        else:
            print(f"  ✗ {archivo} (no encontrado)")
    
    print("\nPara leer la documentación completa:")
    print("  cat REFACTORIZACION_UX_PDF_PROFESIONAL.md")


def main():
    """Función principal del script de demo"""
    while True:
        opcion = mostrar_menu()
        
        if opcion == '1':
            demo_generar_pdf_profesional()
        elif opcion == '2':
            demo_personalizar_colores()
        elif opcion == '3':
            demo_agregar_seccion_compacta()
        elif opcion == '4':
            demo_crear_tabla_profesional()
        elif opcion == '5':
            mostrar_documentacion()
        elif opcion == '0':
            print("\n¡Hasta luego! 👋")
            break
        else:
            print("\n❌ Opción inválida")
        
        input("\nPresione Enter para continuar...")


if __name__ == "__main__":
    main()
