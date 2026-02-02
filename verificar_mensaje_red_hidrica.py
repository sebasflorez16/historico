#!/usr/bin/env python3
"""
Verificar el mensaje de red hídrica en el PDF generado
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from PyPDF2 import PdfReader

def verificar_mensaje_red_hidrica():
    """
    Extrae y muestra el contenido del PDF relacionado con red hídrica
    """
    pdf_path = "informe_legal_bio_energy_300ha.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ No se encontró el archivo: {pdf_path}")
        return
    
    print("="*80)
    print("📄 VERIFICANDO MENSAJE DE RED HÍDRICA EN PDF")
    print("="*80)
    
    try:
        reader = PdfReader(pdf_path)
        
        # Buscar contenido relacionado con red hídrica
        texto_completo = ""
        for i, page in enumerate(reader.pages, 1):
            texto = page.extract_text()
            texto_completo += texto
            
            # Buscar menciones de red hídrica
            if "Red Hídrica" in texto or "red hídrica" in texto or "RED HÍDRICA" in texto:
                print(f"\n📍 Página {i}:")
                print("-" * 80)
                
                # Extraer líneas relevantes (contexto)
                lineas = texto.split('\n')
                for j, linea in enumerate(lineas):
                    if any(keyword in linea.lower() for keyword in ['red hídrica', 'red hidrica', 'cauces', 'ríos']):
                        # Mostrar contexto (3 líneas antes y después)
                        inicio = max(0, j-3)
                        fin = min(len(lineas), j+4)
                        print("\n".join(lineas[inicio:fin]))
                        print("-" * 40)
        
        # Estadísticas
        print("\n" + "="*80)
        print("📊 ESTADÍSTICAS DEL PDF")
        print("="*80)
        print(f"Total de páginas: {len(reader.pages)}")
        print(f"Menciones de 'red hídrica': {texto_completo.lower().count('red hídrica') + texto_completo.lower().count('red hidrica')}")
        print(f"Menciones de 'NO DETERMINABLE': {texto_completo.count('NO DETERMINABLE')}")
        print(f"Menciones de 'Sin cauces': {texto_completo.count('Sin cauces')}")
        print(f"Menciones de '> 5 km': {texto_completo.count('> 5 km')}")
        
        # Verificar si hay advertencia de dato no concluyente
        if "DATO NO CONCLUYENTE" in texto_completo:
            print("\n⚠️  ADVERTENCIA: Se detectó mensaje 'DATO NO CONCLUYENTE'")
            print("   Esto significa que hay limitaciones técnicas reales")
        elif "Sin cauces registrados" in texto_completo or "> 5 km" in texto_completo:
            print("\n✅ RESULTADO POSITIVO: 'Sin cauces registrados en la región'")
            print("   Esto es un dato REAL y válido (no alarmante)")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ Error al leer PDF: {e}")

if __name__ == "__main__":
    verificar_mensaje_red_hidrica()
