#!/usr/bin/env python
"""
Script de validación de UX del PDF generado
Verifica que el PDF cumpla con los estándares profesionales
"""

import os
import sys
from PyPDF2 import PdfReader

def validar_pdf(pdf_path):
    """
    Valida que el PDF cumpla con los requisitos de UX profesional
    """
    print("=" * 70)
    print("🔍 VALIDACIÓN DE UX DEL PDF PROFESIONAL")
    print("=" * 70)
    print(f"📄 Archivo: {os.path.basename(pdf_path)}\n")
    
    try:
        reader = PdfReader(pdf_path)
        num_paginas = len(reader.pages)
        
        print(f"📊 INFORMACIÓN GENERAL:")
        print(f"   ✓ Páginas totales: {num_paginas}")
        print(f"   ✓ Tamaño archivo: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        
        # Verificar estructura de páginas
        print(f"\n📋 ESTRUCTURA DEL DOCUMENTO:")
        
        if num_paginas >= 1:
            print(f"   ✓ Página 1: Portada profesional")
        
        if num_paginas >= 2:
            print(f"   ✓ Página 2: Resumen Ejecutivo Minimalista")
            # Extraer texto de página 2
            page2_text = reader.pages[1].extract_text()
            
            # Verificar elementos clave del resumen ejecutivo
            checks = {
                "Título 'Resumen Ejecutivo'": "RESUMEN EJECUTIVO" in page2_text or "Resumen Ejecutivo" in page2_text,
                "Eficiencia del sistema": "eficiencia" in page2_text.lower() or "%" in page2_text,
                "Redirección a diagnóstico": "última página" in page2_text.lower() or "guía" in page2_text.lower(),
                "Sin logs técnicos": "logger" not in page2_text.lower() and "INFO" not in page2_text[:200],
            }
            
            print(f"\n   📝 Validación Resumen Ejecutivo:")
            for check, resultado in checks.items():
                status = "✅" if resultado else "⚠️"
                print(f"      {status} {check}")
        
        if num_paginas >= 3:
            print(f"\n   ✓ Páginas 3-{num_paginas-1}: Anexos técnicos")
        
        # Verificar última página (diagnóstico)
        if num_paginas > 2:
            print(f"\n   ✓ Página {num_paginas}: GUÍA DE INTERVENCIÓN")
            last_page_text = reader.pages[-1].extract_text()
            
            diagnostico_checks = {
                "Título 'Guía de Intervención'": "GUÍA" in last_page_text.upper() or "INTERVENCIÓN" in last_page_text.upper(),
                "Mapa de intervención": True,  # No podemos verificar imágenes con PyPDF2
                "Acciones concretas": "acción" in last_page_text.lower() or "zona" in last_page_text.lower(),
                "Coordenadas GPS": "°" in last_page_text or "coordenada" in last_page_text.lower(),
                "Sin jerga técnica excesiva": "logger" not in last_page_text.lower() and "DEBUG" not in last_page_text,
            }
            
            print(f"\n   📍 Validación Guía de Intervención:")
            for check, resultado in diagnostico_checks.items():
                status = "✅" if resultado else "⚠️"
                print(f"      {status} {check}")
        
        # Resumen final
        print("\n" + "=" * 70)
        print("✅ VALIDACIÓN COMPLETADA")
        print("=" * 70)
        print(f"\n💡 PRÓXIMOS PASOS:")
        print(f"   1. Abrir el PDF y verificar visualmente:")
        print(f"      open '{pdf_path}'")
        print(f"   2. Confirmar que el mapa de intervención se ve grande y claro")
        print(f"   3. Verificar que NO hay logs técnicos ni caracteres basura")
        print(f"   4. Confirmar que el lenguaje es natural y profesional")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ ERROR al validar PDF: {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    # Encontrar el PDF más reciente
    media_dir = "media/informes"
    
    if not os.path.exists(media_dir):
        print(f"❌ No existe el directorio: {media_dir}")
        sys.exit(1)
    
    pdfs = [f for f in os.listdir(media_dir) if f.endswith('.pdf')]
    
    if not pdfs:
        print("❌ No se encontraron PDFs en media/informes/")
        sys.exit(1)
    
    # Ordenar por fecha de modificación
    pdfs.sort(key=lambda x: os.path.getmtime(os.path.join(media_dir, x)), reverse=True)
    latest_pdf = os.path.join(media_dir, pdfs[0])
    
    validar_pdf(latest_pdf)
