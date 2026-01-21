#!/usr/bin/env python
"""
Script para generar informe PDF de una parcela específica
Incluye todas las mejoras y correcciones aplicadas al sistema

Uso:
    python generar_informe_parcela.py --parcela 6 --tipo completo
    python generar_informe_parcela.py --parcela 6 --tipo rapido
"""

import os
import sys
import django
import argparse
from datetime import datetime, timedelta
import logging

# Configurar path para Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

# Imports después de setup Django
from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def generar_informe_parcela(parcela_id: int, tipo_analisis: str = 'completo'):
    """
    Genera informe PDF profesional para una parcela
    
    Args:
        parcela_id: ID de la parcela
        tipo_analisis: 'rapido' (10 imágenes) o 'completo' (30 imágenes)
    """
    print(f"\n{'='*60}")
    print(f"📄 GENERACIÓN DE INFORME PDF PROFESIONAL")
    print(f"{'='*60}\n")
    
    try:
        # 1. Obtener parcela
        print(f"🔍 Buscando parcela #{parcela_id}...")
        parcela = Parcela.objects.get(id=parcela_id)
        
        print(f"✅ Parcela encontrada: {parcela.nombre}")
        print(f"    Área: {parcela.area_hectareas:.2f} hectáreas")
        print(f"   🌾 Cultivo: {parcela.tipo_cultivo or 'Sin especificar'}")
        
        # 2. Configurar período de análisis
        fecha_fin = datetime.now()
        if tipo_analisis == 'rapido':
            fecha_inicio = fecha_fin - timedelta(days=300)  # ~10 meses
            max_imagenes = 10
            print(f"\n📊 Tipo de análisis: RÁPIDO (últimos 10 meses)")
        else:
            fecha_inicio = fecha_fin - timedelta(days=900)  # ~30 meses
            max_imagenes = 30
            print(f"\n📊 Tipo de análisis: COMPLETO (últimos 30 meses)")
        
        print(f"   📅 Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")
        print(f"   🖼️ Max imágenes: {max_imagenes}")
        
        # 3. Inicializar generador PDF
        print(f"\n🔧 Inicializando generador PDF...")
        generador = GeneradorPDFProfesional()
        
        # 4. Generar informe
        print(f"\n🚀 Generando informe PDF...")
        print(f"   ⏱️  Este proceso puede tomar varios minutos...")
        print(f"   📡 Descargando imágenes satelitales...")
        print(f"   🤖 Generando análisis con IA...")
        print(f"   📈 Creando gráficos y visualizaciones...")
        
        # Calcular meses según el tipo
        meses_atras = 10 if tipo_analisis == 'rapido' else 24
        
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela_id,
            meses_atras=meses_atras
        )
        
        # 5. Verificar resultado
        if not pdf_path or not os.path.exists(pdf_path):
            print(f"\n❌ ERROR: No se pudo generar el PDF")
            return False
        
        # 6. Mostrar resultados
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        
        print(f"\n{'='*60}")
        print(f"✅ INFORME GENERADO EXITOSAMENTE")
        print(f"{'='*60}")
        print(f"\n📁 Archivo PDF:")
        print(f"   {pdf_path}")
        
        # Verificar que el archivo existe
        if os.path.exists(pdf_path):
            size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            print(f"\n📊 Tamaño: {size_mb:.2f} MB")
        
        print(f"\n{'='*60}\n")
        
        return True
        
    except Parcela.DoesNotExist:
        print(f"\n❌ ERROR: No existe parcela con ID {parcela_id}")
        return False
    
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Genera informe PDF profesional para una parcela',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python generar_informe_parcela.py --parcela 6 --tipo completo
  python generar_informe_parcela.py --parcela 6 --tipo rapido
  python generar_informe_parcela.py -p 6 -t rapido
        """
    )
    
    parser.add_argument(
        '-p', '--parcela',
        type=int,
        required=True,
        help='ID de la parcela (requerido)'
    )
    
    parser.add_argument(
        '-t', '--tipo',
        choices=['rapido', 'completo'],
        default='completo',
        help='Tipo de análisis: rapido (10 meses) o completo (30 meses). Default: completo'
    )
    
    args = parser.parse_args()
    
    # Generar informe
    exito = generar_informe_parcela(
        parcela_id=args.parcela,
        tipo_analisis=args.tipo
    )
    
    # Salir con código apropiado
    sys.exit(0 if exito else 1)


if __name__ == '__main__':
    main()
