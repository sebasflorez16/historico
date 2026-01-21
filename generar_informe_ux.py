#!/usr/bin/env python
"""
Script para generar informe PDF con nueva UX de diagnóstico
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/Users/sebasflorez16/Documents/AgroTech Historico')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.generador_pdf import GeneradorPDFProfesional
from datetime import date, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    print('🚀 Generando Informe PDF con Nueva UX de Diagnóstico...')
    print('=' * 70)
    
    try:
        # Obtener parcela
        parcela = Parcela.objects.get(id=6)
        print(f'📍 Parcela: {parcela.nombre}')
        print(f'   Propietario: {parcela.propietario}')
        print(f'   Área: {parcela.area_hectareas:.2f} ha')
        print(f'   Cultivo: {parcela.tipo_cultivo}')
        
        # Definir período
        fecha_fin = date.today()
        fecha_inicio = parcela.fecha_inicio_monitoreo or (fecha_fin - timedelta(days=180))
        
        print(f'📅 Período: {fecha_inicio} a {fecha_fin}')
        
        # Verificar índices
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
        print(f'📊 Índices disponibles: {indices.count()} meses')
        
        if indices.count() == 0:
            print('❌ No hay datos suficientes')
            return False
        
        print('\n📝 Generando PDF profesional...')
        print('-' * 70)
        
        # Generar informe (usa todos los meses disponibles)
        generador = GeneradorPDFProfesional()
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=12  # Usar últimos 12 meses o todos los disponibles
        )
        
        print('-' * 70)
        print(f'\n✅ ¡PDF GENERADO EXITOSAMENTE!')
        print(f'📄 Ruta: {pdf_path}')
        print(f'\n🎯 Elementos de la Nueva UX:')
        print(f'   ✓ Página 2: Cuadro de eficiencia destacado')
        print(f'   ✓ Última página: "GUÍA DE INTERVENCIÓN EN CAMPO"')
        print(f'   ✓ Mapa limpio con fondo gris')
        print(f'   ✓ Narrativa dual (técnica + campo)')
        print(f'   ✓ Coordenadas GPS y acciones')
        print('=' * 70)
        
        return True
        
    except Exception as e:
        logger.error(f'❌ Error: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
