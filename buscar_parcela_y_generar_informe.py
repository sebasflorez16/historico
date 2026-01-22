#!/usr/bin/env python
"""
Entry Point de Línea de Comandos - Sistema AgroTech
====================================================

Script para generar informes PDF desde terminal.
Utiliza la misma lógica que la interfaz web para garantizar consistencia.

REFACTORIZADO (Enero 2026):
- Dinamismo total: Sin valores hardcoded
- Mismo motor de análisis que la web (Data Cubes 3D + IEA)
- Optimización RAM: np.float32
- Limpieza automática de archivos temporales

Uso:
    python buscar_parcela_y_generar_informe.py [parcela_id]
"""
import os
import sys
import django
from datetime import datetime
from pathlib import Path

# Configurar Django (dinámico)
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.generador_pdf import GeneradorPDFProfesional
from django.db.models import Count, Q
from django.conf import settings

import logging
logger = logging.getLogger(__name__)


def buscar_parcela_con_datos():
    """
    Busca parcelas con datos satelitales completos (NDVI, NDMI, SAVI e imágenes)
    """
    print("\n" + "="*80)
    print("BUSCANDO PARCELAS CON DATOS COMPLETOS")
    print("="*80 + "\n")
    
    # Buscar parcelas activas con índices mensuales
    parcelas_con_datos = Parcela.objects.filter(
        activa=True
    ).annotate(
        total_indices=Count('indices_mensuales'),
        imagenes_ndvi=Count('indices_mensuales', filter=Q(indices_mensuales__imagen_ndvi__isnull=False)),
        imagenes_ndmi=Count('indices_mensuales', filter=Q(indices_mensuales__imagen_ndmi__isnull=False)),
        imagenes_savi=Count('indices_mensuales', filter=Q(indices_mensuales__imagen_savi__isnull=False))
    ).filter(
        total_indices__gte=3  # Al menos 3 meses de datos
    ).order_by('-total_indices')
    
    print(f"Total de parcelas activas con datos: {parcelas_con_datos.count()}\n")
    
    # Mostrar información de cada parcela
    for idx, parcela in enumerate(parcelas_con_datos[:10], 1):  # Mostrar las primeras 10
        print(f"{idx}. Parcela: {parcela.nombre}")
        print(f"   - Propietario: {parcela.propietario}")
        print(f"   - Área: {parcela.area_hectareas:.2f} ha" if parcela.area_hectareas else "   - Área: No definida")
        print(f"   - Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
        print(f"   - Índices mensuales: {parcela.total_indices}")
        print(f"   - Imágenes NDVI: {parcela.imagenes_ndvi}")
        print(f"   - Imágenes NDMI: {parcela.imagenes_ndmi}")
        print(f"   - Imágenes SAVI: {parcela.imagenes_savi}")
        print(f"   - ID EOSDA: {parcela.eosda_field_id or 'No sincronizada'}")
        
        # Verificar si tiene geometría
        if parcela.geometria:
            print(f"   - ✓ Geometría PostGIS disponible")
        
        # Mostrar rango de fechas de datos
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
        if indices.exists():
            primer_indice = indices.first()
            ultimo_indice = indices.last()
            print(f"   - Datos desde: {primer_indice.año}-{primer_indice.mes:02d}")
            print(f"   - Datos hasta: {ultimo_indice.año}-{ultimo_indice.mes:02d}")
        
        print()
    
    return parcelas_con_datos


def generar_informe_parcela(parcela_id=None):
    """
    Genera un informe PDF para una parcela específica
    
    REFACTORIZADO:
    - Dinamismo total (sin hardcoded paths)
    - Usa la misma lógica que views.generar_informe_pdf()
    - Análisis temporal con Data Cubes 3D
    - Limpieza automática de archivos temporales
    
    Args:
        parcela_id: ID de la parcela (None = auto-selección)
    
    Returns:
        Path del PDF generado o None si falla
    """
    try:
        # 1. OBTENER PARCELA DINÁMICAMENTE
        if parcela_id:
            parcela = Parcela.objects.get(id=parcela_id, activa=True)
            logger.info(f"Parcela seleccionada manualmente: {parcela.nombre} (ID: {parcela.id})")
        else:
            # Auto-selección: parcela con más datos
            parcelas = Parcela.objects.filter(activa=True).annotate(
                total_indices=Count('indices_mensuales')
            ).filter(total_indices__gte=3).order_by('-total_indices')
            
            if not parcelas.exists():
                print("❌ No se encontraron parcelas con datos suficientes (mínimo 3 meses)")
                return None
            
            parcela = parcelas.first()
            logger.info(f"Auto-seleccionada: {parcela.nombre} ({parcela.total_indices} meses)")
        
        print(f"\n{'='*80}")
        print(f"GENERANDO INFORME PARA: {parcela.nombre}")
        print(f"ID: {parcela.id} | Propietario: {parcela.propietario}")
        print(f"{'='*80}\n")
        
        # 2. VALIDAR DATOS DISPONIBLES
        total_indices = IndiceMensual.objects.filter(parcela=parcela).count()
        
        if total_indices == 0:
            print("❌ Esta parcela no tiene datos históricos.")
            print("   Ejecuta primero: 'Obtener Datos Históricos' desde la web")
            return None
        
        # Estadísticas
        total_imagenes_ndvi = IndiceMensual.objects.filter(
            parcela=parcela, imagen_ndvi__isnull=False
        ).count()
        total_imagenes_ndmi = IndiceMensual.objects.filter(
            parcela=parcela, imagen_ndmi__isnull=False
        ).count()
        total_imagenes_savi = IndiceMensual.objects.filter(
            parcela=parcela, imagen_savi__isnull=False
        ).count()
        
        print(f"📊 Datos disponibles:")
        print(f"   - Índices mensuales: {total_indices}")
        print(f"   - Imágenes NDVI: {total_imagenes_ndvi}")
        print(f"   - Imágenes NDMI: {total_imagenes_ndmi}")
        print(f"   - Imágenes SAVI: {total_imagenes_savi}")
        print(f"   - Área: {parcela.area_hectareas:.2f} ha")
        print(f"   - Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
        print(f"   - Geometría: {'✓ PostGIS' if parcela.geometria else '✗ Sin geometría'}\n")
        
        # 3. CONFIGURAR DIRECTORIO DE SALIDA (DINÁMICO)
        if hasattr(settings, 'MEDIA_ROOT'):
            output_dir = Path(settings.MEDIA_ROOT) / 'informes'
        else:
            output_dir = BASE_DIR / 'media' / 'informes'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. GENERAR PDF (MISMA LÓGICA QUE LA WEB)
        print("⏳ Generando informe PDF con análisis temporal...")
        print("   - Construyendo Data Cubes 3D...")
        print("   - Calculando Índice de Estrés Acumulado (IEA)...")
        print("   - Detectando crisis históricas...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"Informe_{parcela.nombre.replace(' ', '_')}_{timestamp}.pdf"
        ruta_salida = output_dir / nombre_archivo
        
        # Instanciar generador (mismo que la web)
        generador = GeneradorPDFProfesional()
        pdf_path = generador.generar_informe_completo(
            parcela_id=parcela.id,
            output_path=str(ruta_salida)
        )
        
        # 5. VALIDAR RESULTADO
        if not Path(pdf_path).exists():
            print("❌ Error: El PDF no se generó correctamente")
            return None
        
        tamaño_kb = Path(pdf_path).stat().st_size / 1024
        
        print(f"\n✅ INFORME GENERADO EXITOSAMENTE")
        print(f"📄 Archivo: {pdf_path}")
        print(f"📦 Tamaño: {tamaño_kb:.2f} KB")
        print(f"🧠 Motor: Cerebro Diagnóstico Unificado v2.0")
        print(f"📊 Análisis: Temporal con Memoria de Crisis\n")
        
        # 6. LIMPIEZA AUTOMÁTICA (si está configurado)
        limpiar_archivos_temporales(exclude_pdf=pdf_path)
        
        return pdf_path
        
    except Parcela.DoesNotExist:
        print(f"❌ Error: No se encontró la parcela con ID {parcela_id}")
        return None
    except Exception as e:
        print(f"❌ Error al generar informe: {str(e)}")
        logger.exception("Error completo:")
        return None


def limpiar_archivos_temporales(exclude_pdf=None, max_age_days=7):
    """
    Limpia archivos temporales antiguos para no saturar el almacenamiento
    
    Args:
        exclude_pdf: Path del PDF recién generado (no eliminar)
        max_age_days: Eliminar archivos más antiguos que X días
    """
    try:
        from datetime import timedelta
        import time
        
        # Directorios a limpiar
        if hasattr(settings, 'MEDIA_ROOT'):
            media_root = Path(settings.MEDIA_ROOT)
        else:
            media_root = BASE_DIR / 'media'
        
        directorios = [
            media_root / 'diagnosticos',
            media_root / 'mapas',
            media_root / 'temp',
        ]
        
        archivos_eliminados = 0
        espacio_liberado = 0
        
        for directorio in directorios:
            if not directorio.exists():
                continue
            
            for archivo in directorio.glob('*'):
                # No eliminar el PDF recién generado
                if exclude_pdf and archivo == Path(exclude_pdf):
                    continue
                
                # Verificar antigüedad
                edad = time.time() - archivo.stat().st_mtime
                dias = edad / (24 * 3600)
                
                if dias > max_age_days:
                    tamaño = archivo.stat().st_size
                    archivo.unlink()
                    archivos_eliminados += 1
                    espacio_liberado += tamaño
        
        if archivos_eliminados > 0:
            mb_liberados = espacio_liberado / (1024 * 1024)
            print(f"🧹 Limpieza automática: {archivos_eliminados} archivos "
                  f"({mb_liberados:.2f} MB liberados)")
        
    except Exception as e:
        logger.warning(f"Error en limpieza automática: {str(e)}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🌾 SISTEMA AGROTECH - GENERADOR DE INFORMES PDF")
    print("="*80)
    
    # 1. Verificar argumentos
    parcela_id_arg = None
    if len(sys.argv) > 1:
        try:
            parcela_id_arg = int(sys.argv[1])
            print(f"\n📍 Parcela especificada: ID {parcela_id_arg}")
        except ValueError:
            print(f"\n⚠️  Argumento inválido: '{sys.argv[1]}'. Usa: python script.py [ID]")
            sys.exit(1)
    
    # 2. Buscar parcelas disponibles
    if not parcela_id_arg:
        print("\n🔍 Buscando parcelas con datos...")
        parcelas = buscar_parcela_con_datos()
        
        if not parcelas.exists():
            print("\n❌ No se encontraron parcelas con datos suficientes")
            print("   Ejecuta primero: 'Obtener Datos Históricos' desde la interfaz web")
            sys.exit(1)
        
        mejor_parcela = parcelas.first()
        parcela_id_arg = mejor_parcela.id
        
        print(f"\n🎯 Auto-seleccionada: {mejor_parcela.nombre} (ID: {mejor_parcela.id})")
        print(f"   {mejor_parcela.total_indices} índices mensuales | "
              f"{mejor_parcela.area_hectareas:.2f} ha")
    
    # 3. Generar informe
    print(f"\n{'='*80}")
    print("INICIANDO GENERACIÓN DE INFORME")
    print(f"{'='*80}")
    
    resultado = generar_informe_parcela(parcela_id_arg)
    
    # 4. Resultado final
    if resultado:
        print("\n" + "="*80)
        print("✨ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*80)
        print(f"\n📂 Ubicación: {resultado}")
        print("\n💡 Características del informe:")
        print("   ✅ Análisis Temporal Pixel-por-Píxel (Data Cubes 3D)")
        print("   ✅ Índice de Estrés Acumulado (IEA)")
        print("   ✅ Memoria de Crisis Históricas")
        print("   ✅ Mapas Georeferenciados con GPS")
        print("   ✅ Diagnóstico con Visión Artificial (OpenCV)")
        print("\n🚀 Sistema validado para producción Railway")
        print(f"{'='*80}\n")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ ERROR EN LA GENERACIÓN")
        print("="*80)
        print("\n💡 Soluciones:")
        print("   1. Verifica que la parcela tenga datos históricos")
        print("   2. Ejecuta 'Obtener Datos Históricos' desde la web")
        print("   3. Revisa los logs para más detalles")
        print(f"\n{'='*80}\n")
        sys.exit(1)
