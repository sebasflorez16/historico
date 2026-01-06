#!/usr/bin/env python
"""
Script para generar PDF de la parcela con ID 6
Ejecutar desde la raíz del proyecto: python generar_pdf_parcela_6.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'historical'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')

# Inicializar Django
django.setup()

# Ahora importar los modelos y generador
from informes.generador_pdf import GeneradorPDFProfesional

def main():
    print("=" * 60)
    print("📄 GENERADOR DE PDF - PARCELA 6")
    print("=" * 60)
    
    try:
        # Crear instancia del generador
        print("\n🔧 Inicializando generador de PDF...")
        generador = GeneradorPDFProfesional()
        
        # Generar el informe para la parcela 6
        print("📊 Generando informe para la parcela con ID 6...")
        ruta_pdf = generador.generar_informe_completo(parcela_id=6)
        
        print("\n" + "=" * 60)
        print("✅ PDF GENERADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\n📁 Ubicación del archivo: {ruta_pdf}")
        print("\n💡 Puedes abrir el PDF con el siguiente comando:")
        print(f"   open \"{ruta_pdf}\"")
        print("=" * 60)
        
        return ruta_pdf
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR AL GENERAR PDF")
        print("=" * 60)
        print(f"\n{type(e).__name__}: {str(e)}")
        print("\n📋 Detalles del error:")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
