#!/usr/bin/env python
"""
Script para generar PDF del lote 1 - USA EL MISMO GENERADOR QUE LA INTERFAZ
Ejecutar desde la raíz del proyecto: python generar_pdf_lote_1.py
"""

import os
import sys
import django

# Configurar Django (proyecto principal en /historico)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')

# Inicializar Django
django.setup()

# Importar desde el MISMO lugar que usa la interfaz
from informes.generador_pdf import GeneradorPDFProfesional

def main():
    print("=" * 60)
    print("📄 GENERADOR DE PDF - LOTE 1")
    print("=" * 60)
    
    try:
        # Crear instancia del generador
        print("\n🔧 Inicializando generador de PDF...")
        generador = GeneradorPDFProfesional()
        
        # Generar el informe para el lote 1 (ID=1)
        print("📊 Generando informe para lote 1 (ID=1)...")
        ruta_pdf = generador.generar_informe_completo(parcela_id=1)
        
        print("\n" + "=" * 60)
        print("✅ PDF GENERADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\n📁 Ubicación del archivo: {ruta_pdf}")
        print("\n💡 Puedes abrir el PDF con el siguiente comando:")
        print(f"   open \"{ruta_pdf}\"")
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR AL GENERAR PDF")
        print("=" * 60)
        print(f"\n{type(e).__name__}: {str(e)}")
        
        # Mostrar traceback completo para debugging
        print("\n📋 Detalles del error:")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        
        return 1

if __name__ == '__main__':
    sys.exit(main())
