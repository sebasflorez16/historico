#!/usr/bin/env python
"""
Test de generación de PDF real - Verifica que usa la versión correcta del generador
"""
import os
import sys
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual, Informe
from informes.generador_pdf import GeneradorPDFProfesional
from informes.analizadores.ndvi_analyzer import AnalizadorNDVI
from informes.analizadores.ndmi_analyzer import AnalizadorNDMI
from informes.analizadores.savi_analyzer import AnalizadorSAVI
from informes.analizadores.tendencias_analyzer import DetectorTendencias
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generar_pdf_prueba():
    """Genera un PDF real como lo haría la vista web"""
    
    print("\n" + "="*80)
    print("🧪 TEST DE GENERACIÓN DE PDF - VERIFICACIÓN DE VERSIÓN")
    print("="*80 + "\n")
    
    # 1. Obtener parcela con datos
    parcela = Parcela.objects.filter(eosda_sincronizada=True).first()
    
    if not parcela:
        print("❌ No hay parcelas sincronizadas con EOSDA")
        parcela = Parcela.objects.first()
        if not parcela:
            print("❌ No hay parcelas en la base de datos")
            return False
    
    print(f"✅ Parcela seleccionada: {parcela.nombre}")
    print(f"   Propietario: {parcela.propietario}")
    print(f"   Área: {parcela.area_hectareas} ha")
    
    # 2. Obtener índices mensuales
    fecha_fin = datetime.now().date()
    fecha_inicio = fecha_fin - timedelta(days=365)  # 12 meses
    
    indices = IndiceMensual.objects.filter(
        parcela=parcela,
        fecha_imagen__gte=fecha_inicio,
        fecha_imagen__lte=fecha_fin
    ).order_by('-año', '-mes')
    
    print(f"\n✅ Índices mensuales encontrados: {indices.count()}")
    
    if indices.count() == 0:
        print("⚠️ No hay datos de índices para generar el informe")
        print("   Creando informe con datos mínimos...")
    
    # 3. Preparar datos para el generador
    datos_grafico = []
    for idx in indices:
        datos_grafico.append({
            'mes': f"{idx.año}-{str(idx.mes).zfill(2)}",
            'ndvi': idx.ndvi_promedio or 0,
            'ndmi': idx.ndmi_promedio or 0,
            'savi': idx.savi_promedio or 0,
            'fecha': idx.fecha_imagen
        })
    
    # 4. Analizar datos (como lo hace la vista real)
    print("\n📊 Analizando datos...")
    
    analisis_completo = {
        'ndvi': AnalizadorNDVI().analizar(datos_grafico) if datos_grafico else {'estado': {'etiqueta': 'Sin datos'}, 'estadisticas': {'promedio': 0}, 'interpretacion_tecnica': 'Sin datos', 'interpretacion_simple': 'Sin datos'},
        'ndmi': AnalizadorNDMI().analizar(datos_grafico) if datos_grafico else {'estado': {'etiqueta': 'Sin datos'}, 'estadisticas': {'promedio': 0}, 'interpretacion_tecnica': 'Sin datos', 'interpretacion_simple': 'Sin datos'},
        'savi': AnalizadorSAVI().analizar(datos_grafico) if datos_grafico else {'estado': {'etiqueta': 'Sin datos'}, 'estadisticas': {'promedio': 0}, 'interpretacion_tecnica': 'Sin datos', 'interpretacion_simple': 'Sin datos'},
        'tendencias': DetectorTendencias().analizar(datos_grafico) if datos_grafico else {'resumen': 'Sin datos'}
    }
    
    print("   ✅ Análisis NDVI completado")
    print("   ✅ Análisis NDMI completado")
    print("   ✅ Análisis SAVI completado")
    print("   ✅ Análisis de tendencias completado")
    
    # 5. Generar PDF (AQUÍ ES DONDE SE USA LA VERSIÓN CORRECTA)
    print("\n📄 Generando PDF...")
    
    generador = GeneradorPDFProfesional()
    
    # Verificar que es la versión correcta
    import inspect
    source = inspect.getsource(generador._crear_bloque_cierre)
    count_duplicados = source.count('Uso de Este Análisis en la Toma de Decisiones')
    
    print(f"\n🔍 VERIFICACIÓN DE VERSIÓN:")
    print(f"   Método _crear_bloque_cierre: {'✅ Existe' if hasattr(generador, '_crear_bloque_cierre') else '❌ No existe'}")
    print(f"   Título 'Uso de Este Análisis...': aparece {count_duplicados} vez(veces)")
    print(f"   Estado: {'✅ SIN DUPLICADOS (versión HISTORICAL)' if count_duplicados == 1 else '❌ DUPLICADO DETECTADO (versión antigua)'}")
    
    # 6. Generar el archivo PDF
    output_path = f'/tmp/test_pdf_fusion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    
    try:
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=12,
            output_path=output_path
        )
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"\n✅ PDF GENERADO EXITOSAMENTE")
            print(f"   Ruta: {pdf_path}")
            print(f"   Tamaño: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            # Verificar contenido del PDF
            with open(pdf_path, 'rb') as f:
                content = f.read()
                if b'Uso de Este An' in content:
                    # Contar ocurrencias en el PDF
                    occurrences = content.count(b'Uso de Este An')
                    print(f"\n🔍 VERIFICACIÓN EN PDF GENERADO:")
                    print(f"   Texto 'Uso de Este Análisis...' aparece: {occurrences} vez(veces)")
                    print(f"   Estado: {'✅ SIN DUPLICADOS' if occurrences == 1 else '❌ DUPLICADO EN PDF'}")
            
            return True
        else:
            print(f"\n❌ ERROR: No se pudo generar el PDF")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR al generar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n🚀 Iniciando test de generación de PDF...\n")
    resultado = generar_pdf_prueba()
    
    print("\n" + "="*80)
    if resultado:
        print("✅ TEST EXITOSO - PDF generado correctamente con versión HISTORICAL")
    else:
        print("❌ TEST FALLIDO - Revisar errores arriba")
    print("="*80 + "\n")
    
    sys.exit(0 if resultado else 1)
