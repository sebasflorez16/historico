#!/usr/bin/env python
"""
Script para generar PDF con las correcciones aplicadas
- Tabla de índices espectrales corregida (sin HTML mal renderizado)
- Mensajes claros sobre imágenes satelitales faltantes
- Debug logging para identificar problemas
"""
import os
import sys
import django
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configurar Django
sys.path.append('/Users/sebasflorez16/Documents/AgroTech Historico/historical')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.generador_pdf import GeneradorPDFProfesional

def main():
    print("=" * 100)
    print("GENERADOR DE PDF CON CORRECCIONES - PARCELA 6")
    print("=" * 100)
    print()
    
    print("✅ CORRECCIONES APLICADAS:")
    print("   1. Eliminación de emojis")
    print("   2. Reemplazo de referencias a IA/Gemini por 'Motor de Análisis Automatizado AgroTech'")
    print("   3. Impacto productivo y nivel de riesgo al final de cada mes")
    print("   4. Precipitación clarificada como 'total mensual'")
    print("   5. LAI y cobertura como estimaciones indirectas")
    print("   6. Lenguaje inclusivo para terrenos en evaluación y cultivos establecidos")
    print()
    
    try:
        # Obtener parcela 6
        parcela = Parcela.objects.get(id=6, activa=True)
        print(f"📍 Parcela encontrada: {parcela.nombre}")
        print(f"   - Propietario: {parcela.propietario}")
        print(f"   - Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
        print(f"   - Área: {parcela.area_hectareas:.2f} hectáreas")
        print()
        
        # Verificar datos disponibles
        indices_count = parcela.indices_mensuales.count()
        print(f"📊 Datos disponibles: {indices_count} registros mensuales")
        
        # Verificar si hay imágenes
        indices = parcela.indices_mensuales.all()[:5]
        total_imagenes = 0
        for idx in indices:
            if idx.imagen_ndvi:
                print(f"   ✅ {idx.periodo_texto}: Tiene NDVI imagen")
                total_imagenes += 1
            if idx.imagen_ndmi:
                print(f"   ✅ {idx.periodo_texto}: Tiene NDMI imagen")
                total_imagenes += 1
            if idx.imagen_savi:
                print(f"   ✅ {idx.periodo_texto}: Tiene SAVI imagen")
                total_imagenes += 1
        
        if total_imagenes == 0:
            print("   ⚠️  NO hay imágenes satelitales en la BD (solo datos numéricos)")
            print("   ℹ️  El PDF mostrará un mensaje explicativo sobre imágenes faltantes")
        else:
            print(f"   ✅ Total: {total_imagenes} imágenes disponibles")
        print()
        
        if indices_count == 0:
            print("❌ No hay datos para generar el informe")
            return
        
        # Generar PDF
        print("🔄 Generando informe PDF...")
        print("   (Revisa los logs de DEBUG para ver el procesamiento de imágenes)")
        print()
        
        generador = GeneradorPDFProfesional()
        pdf_path = generador.generar_informe_completo(
            parcela_id=6,
            meses_atras=12
        )
        
        print("=" * 100)
        print("✅ PDF GENERADO EXITOSAMENTE")
        print("=" * 100)
        print(f"📁 Ubicación: {pdf_path}")
        print()
        print("🔍 POR FAVOR REVISA:")
        print("   1. ✓ Tabla de índices espectrales: ¿Se ve correctamente formateada?")
        print("   2. ✓ Sección de imágenes satelitales: ¿Muestra el mensaje explicativo?")
        print("   3. ✓ Layout general: ¿Todo está ordenado y legible?")
        print()
        print("📋 PRÓXIMOS PASOS (si no hay imágenes):")
        print("   - Ejecutar script de sincronización EOSDA para descargar imágenes")
        print("   - Verificar que la API de EOSDA esté configurada correctamente")
        print("   - Revisar si las imágenes están en la carpeta media/imagenes_satelitales/")
        print()
        
    except Parcela.DoesNotExist:
        print("❌ ERROR: Parcela 2 no encontrada en la base de datos")
        print("   Parcelas disponibles:")
        for p in Parcela.objects.filter(activa=True):
            print(f"   - ID {p.id}: {p.nombre}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
