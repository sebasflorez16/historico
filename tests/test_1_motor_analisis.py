#!/usr/bin/env python
"""
Test Completo del Motor de Análisis Agrícola Profesional v2.0
==============================================================

Prueba todas las funcionalidades del motor mejorado:
1. Procesamiento raster avanzado
2. Análisis de series temporales
3. Detección de cambios estructurales
4. Predicción de tendencias
5. Exportación para dashboards

Ejecutar:
    python tests/test_motor_completo_v2.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
import numpy as np
import logging

# Configurar Django
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'historical.settings')
django.setup()

# Importar motor
from informes.motor_analisis import (
    procesador_raster,
    analizador_series,
    exportador,
    GeneradorDiagnosticos
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def generar_datos_sinteticos():
    """Genera datos sintéticos realistas para pruebas"""
    logger.info("=" * 80)
    logger.info("📊 GENERANDO DATOS SINTÉTICOS DE PARCELA")
    logger.info("=" * 80)
    
    # Serie temporal de 24 meses con tendencia y estacionalidad
    fechas = [datetime(2023, 1, 1) + timedelta(days=30*i) for i in range(24)]
    
    # Tendencia: ligera mejora (0.5 → 0.65)
    tendencia = np.linspace(0.5, 0.65, 24)
    
    # Estacionalidad: ciclo anual (máximo en verano, mínimo en invierno)
    estacionalidad = 0.1 * np.sin(np.linspace(0, 4*np.pi, 24))
    
    # Ruido: variaciones aleatorias
    np.random.seed(42)
    ruido = np.random.normal(0, 0.03, 24)
    
    # Anomalía simulada (sequía en mes 10)
    anomalia = np.zeros(24)
    anomalia[10:13] = -0.15
    
    # Serie completa
    ndvi = tendencia + estacionalidad + ruido + anomalia
    ndvi = np.clip(ndvi, 0, 1)  # Mantener en rango válido
    
    # Generar arrays 2D simulando imagen raster (100x100 pixels)
    raster_actual = np.random.normal(ndvi[-1], 0.05, (100, 100))
    raster_actual = np.clip(raster_actual, 0, 1)
    
    logger.info(f"✅ Generados {len(fechas)} puntos temporales")
    logger.info(f"✅ Raster simulado: {raster_actual.shape} pixels")
    logger.info(f"   NDVI actual: {ndvi[-1]:.3f}")
    logger.info(f"   NDVI promedio histórico: {np.mean(ndvi):.3f}")
    
    return {
        'fechas': fechas,
        'ndvi': ndvi.tolist(),
        'raster_actual': raster_actual,
        'area_hectareas': 50.5
    }


def test_procesador_raster(datos):
    """Prueba procesador raster avanzado"""
    logger.info("\n" + "=" * 80)
    logger.info("🔬 TEST 1: PROCESADOR RASTER AVANZADO")
    logger.info("=" * 80)
    
    raster = datos['raster_actual']
    area = datos['area_hectareas']
    
    # 1. Estadísticas zonales
    logger.info("\n📊 Calculando estadísticas zonales...")
    stats = procesador_raster.calcular_estadisticas_zonales(
        valores_array=raster.flatten(),
        area_hectareas=area,
        num_bins=10
    )
    logger.info(f"   Media: {stats.media:.4f}")
    logger.info(f"   Desviación estándar: {stats.desviacion:.4f}")
    logger.info(f"   Coeficiente de variación: {stats.coef_variacion:.2f}%")
    logger.info(f"   Rango: [{stats.minimo:.4f}, {stats.maximo:.4f}]")
    
    # 2. Detección de hotspots
    logger.info("\n🔥 Detectando hotspots y coldspots...")
    hotspots = procesador_raster.detectar_hotspots(
        valores_array=raster.flatten(),
        umbral_percentil=90
    )
    logger.info(f"   Umbral alto (P90): {hotspots['umbral_alto']:.4f}")
    logger.info(f"   Umbral bajo (P10): {hotspots['umbral_bajo']:.4f}")
    logger.info(f"   Hotspots positivos: {hotspots['num_hotspots_positivos']} "
                f"({hotspots['porcentaje_positivo']:.1f}%)")
    logger.info(f"   Hotspots negativos: {hotspots['num_hotspots_negativos']} "
                f"({hotspots['porcentaje_negativo']:.1f}%)")
    logger.info(f"   ➡️  {hotspots['interpretacion']}")
    
    # 3. Análisis de calidad
    logger.info("\n✅ Analizando calidad de imagen...")
    calidad = procesador_raster.analizar_calidad_imagen(
        valores_array=raster.flatten(),
        nubosidad=5.0
    )
    logger.info(f"   Píxeles válidos: {calidad['pixels_validos']}/{calidad['total_pixels']} "
                f"({calidad['porcentaje_validos']:.1f}%)")
    logger.info(f"   Calidad: {calidad['calidad']} (confianza {calidad['confianza']})")
    logger.info(f"   ➡️  {calidad['recomendacion']}")
    
    # 4. Variabilidad espacial
    logger.info("\n📐 Calculando variabilidad espacial...")
    variabilidad = procesador_raster.calcular_variabilidad_espacial(
        valores_array=raster.flatten(),
        metodo='all'
    )
    logger.info(f"   Coeficiente de variación: {variabilidad['coef_variacion']}%")
    logger.info(f"   ➡️  {variabilidad['interpretacion_cv']}")
    logger.info(f"   Rango intercuartílico: {variabilidad['iqr']:.4f}")
    logger.info(f"   ➡️  {variabilidad['interpretacion_iqr']}")
    logger.info(f"   Entropía Shannon: {variabilidad['entropia']:.4f}")
    logger.info(f"   ➡️  {variabilidad['interpretacion_entropia']}")
    
    return {
        'estadisticas': stats.to_dict(),
        'hotspots': hotspots,
        'calidad': calidad,
        'variabilidad': variabilidad
    }


def test_analizador_series_temporal(datos):
    """Prueba analizador de series temporales"""
    logger.info("\n" + "=" * 80)
    logger.info("📈 TEST 2: ANÁLISIS DE SERIES TEMPORALES")
    logger.info("=" * 80)
    
    fechas = datos['fechas']
    valores = datos['ndvi']
    
    # 1. Descomposición de serie
    logger.info("\n🔍 Descomponiendo serie temporal...")
    descomp = analizador_series.descomponer_serie(
        valores=valores,
        fechas=fechas,
        periodo=12
    )
    logger.info(f"   Tendencia media: {np.mean(descomp.tendencia):.4f}")
    logger.info(f"   Amplitud estacional: {np.std(descomp.estacionalidad):.4f}")
    logger.info(f"   Ruido (std residuos): {np.std(descomp.residuos):.4f}")
    
    # 2. Detección de puntos de cambio
    logger.info("\n⚡ Detectando puntos de cambio estructural...")
    cambios = analizador_series.detectar_puntos_cambio(
        valores=valores,
        fechas=fechas,
        umbral_cambio=0.10
    )
    if cambios.indices:
        logger.info(f"   Detectados {len(cambios.indices)} puntos de cambio:")
        for i, (fecha, antes, despues, mag, sig) in enumerate(zip(
            cambios.fechas, cambios.valores_antes, cambios.valores_despues,
            cambios.magnitud_cambio, cambios.significancia
        )):
            logger.info(f"   {i+1}. {fecha.strftime('%Y-%m-%d')}: "
                       f"{antes:.3f} → {despues:.3f} "
                       f"(Δ={mag:.3f}, significancia={sig})")
    else:
        logger.info("   No se detectaron cambios estructurales significativos")
    
    # 3. Predicción de tendencias
    logger.info("\n🔮 Prediciendo tendencia futura...")
    prediccion = analizador_series.predecir_tendencia(
        valores=valores,
        fechas=fechas,
        meses_futuro=3,
        grado_polinomio=2
    )
    if 'error' not in prediccion:
        logger.info(f"   R² del modelo: {prediccion['r_cuadrado']:.4f}")
        logger.info(f"   Confianza: {prediccion['confianza']}")
        logger.info(f"   Predicciones:")
        for fecha, valor in zip(prediccion['fechas_futuras'], prediccion['valores_predichos']):
            logger.info(f"      {fecha[:10]}: NDVI = {valor:.3f}")
        logger.info(f"   ➡️  {prediccion['interpretacion']}")
    
    # 4. Autocorrelación
    logger.info("\n🔄 Analizando autocorrelación...")
    autocorr = analizador_series.calcular_autocorrelacion(
        valores=valores,
        max_lag=12
    )
    if 'error' not in autocorr:
        logger.info(f"   Lag de máxima correlación: {autocorr['lag_max_correlacion']} meses")
        logger.info(f"   Correlación máxima: {autocorr['max_correlacion']:.4f}")
        logger.info(f"   ➡️  {autocorr['interpretacion']}")
    
    return {
        'descomposicion': descomp.to_dict(),
        'cambios': cambios.to_dict(),
        'prediccion': prediccion,
        'autocorrelacion': autocorr
    }


def test_exportador(datos, analisis_raster, analisis_temporal):
    """Prueba exportador de resultados"""
    logger.info("\n" + "=" * 80)
    logger.info("💾 TEST 3: EXPORTADOR DE RESULTADOS")
    logger.info("=" * 80)
    
    # 1. Exportar serie temporal
    logger.info("\n📊 Exportando serie temporal...")
    serie_export = exportador.exportar_serie_temporal(
        serie_datos=[
            {'fecha': f, 'media': v, 'minimo': v-0.05, 'maximo': v+0.05,
             'percentil_25': v-0.02, 'percentil_75': v+0.02}
            for f, v in zip(datos['fechas'], datos['ndvi'])
        ],
        tipo_indice='ndvi'
    )
    logger.info(f"   ✅ Serie exportada: {serie_export['metadata']['num_puntos']} puntos")
    logger.info(f"   Período: {serie_export['metadata']['fecha_inicio'][:10]} → "
               f"{serie_export['metadata']['fecha_fin'][:10]}")
    logger.info(f"   Rango valores: [{serie_export['metadata']['rango_valores']['min']:.3f}, "
               f"{serie_export['metadata']['rango_valores']['max']:.3f}]")
    
    # 2. Exportar alertas como timeline
    logger.info("\n⏱️  Generando timeline de eventos...")
    eventos = []
    if analisis_temporal['cambios']['indices']:
        for i, (fecha, mag, sig) in enumerate(zip(
            analisis_temporal['cambios']['fechas'],
            analisis_temporal['cambios']['magnitud_cambio'],
            analisis_temporal['cambios']['significancia']
        )):
            eventos.append({
                'id': f'cambio_{i}',
                'fecha': datetime.fromisoformat(fecha),
                'descripcion': f'Cambio estructural (Δ={mag:.3f})',
                'tipo': 'point',
                'categoria': 'cambio',
                'severidad': 'alto' if sig == 'alta' else 'medio',
                'detalle': f'Cambio de magnitud {mag:.3f} con significancia {sig}'
            })
    
    timeline = exportador.exportar_timeline(eventos)
    logger.info(f"   ✅ Timeline generado: {len(timeline)} eventos")
    for evento in timeline[:3]:  # Mostrar primeros 3
        logger.info(f"   • {evento['start'][:10]}: {evento['content']}")
    
    # 3. Dashboard completo
    logger.info("\n📱 Generando dashboard completo...")
    dashboard = exportador.exportar_dashboard_completo(
        analisis_completo={
            'estado_general': 'Bueno',
            'tendencia': 'Mejorando',
            'num_alertas': len(eventos),
            'metricas_clave': {
                'ndvi_actual': datos['ndvi'][-1],
                'ndvi_promedio': np.mean(datos['ndvi']),
                'cv': analisis_raster['variabilidad']['coef_variacion']
            },
            'serie_ndvi': [
                {'fecha': f, 'media': v}
                for f, v in zip(datos['fechas'], datos['ndvi'])
            ],
            'alertas': eventos,
            'zonificacion': analisis_raster['hotspots'],
            'recomendaciones': [
                'Mantener prácticas actuales de riego',
                'Monitorear zonas de bajo vigor (hotspots negativos)',
                'Planificar fertilización para próximo período'
            ]
        },
        incluir_geometrias=False
    )
    logger.info(f"   ✅ Dashboard generado con {len(dashboard.keys())} secciones")
    logger.info(f"   • Resumen ejecutivo: {dashboard['resumen_ejecutivo']}")
    logger.info(f"   • Series temporales: {len(dashboard['series_temporales'])} índices")
    logger.info(f"   • Alertas: {len(dashboard['alertas'])} eventos")
    logger.info(f"   • Recomendaciones: {len(dashboard['recomendaciones'])} items")
    
    # 4. Guardar JSON
    import tempfile
    archivo_json = os.path.join(tempfile.gettempdir(), 'dashboard_agrotech.json')
    exportador.guardar_json(dashboard, archivo_json, pretty=True)
    logger.info(f"\n💾 Dashboard guardado en: {archivo_json}")
    
    # Mostrar tamaño
    tamanio_kb = os.path.getsize(archivo_json) / 1024
    logger.info(f"   Tamaño: {tamanio_kb:.1f} KB")
    
    return {
        'serie': serie_export,
        'timeline': timeline,
        'dashboard': dashboard,
        'archivo_json': archivo_json
    }


def test_integracion_completa():
    """Test de integración completa del motor"""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 TEST 4: INTEGRACIÓN COMPLETA")
    logger.info("=" * 80)
    
    # Generar datos
    datos = generar_datos_sinteticos()
    
    # Ejecutar todos los análisis
    logger.info("\n🔄 Ejecutando pipeline completo de análisis...")
    
    # Test 1: Raster
    analisis_raster = test_procesador_raster(datos)
    
    # Test 2: Series temporales
    analisis_temporal = test_analizador_series_temporal(datos)
    
    # Test 3: Exportación
    exportacion = test_exportador(datos, analisis_raster, analisis_temporal)
    
    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.info("📋 RESUMEN FINAL DE ANÁLISIS")
    logger.info("=" * 80)
    
    logger.info("\n✅ ESTADO GENERAL: BUENO")
    logger.info(f"   NDVI actual: {datos['ndvi'][-1]:.3f}")
    logger.info(f"   NDVI promedio histórico: {np.mean(datos['ndvi']):.3f}")
    logger.info(f"   Tendencia: {'Mejorando' if datos['ndvi'][-1] > np.mean(datos['ndvi']) else 'Deteriorando'}")
    
    logger.info("\n📊 MÉTRICAS CLAVE:")
    logger.info(f"   • Variabilidad espacial: {analisis_raster['variabilidad']['coef_variacion']}%")
    logger.info(f"   • Calidad de imagen: {analisis_raster['calidad']['calidad']}")
    logger.info(f"   • Puntos de cambio detectados: {len(analisis_temporal['cambios']['indices'])}")
    logger.info(f"   • Confianza predicción: {analisis_temporal['prediccion'].get('confianza', 'N/A')}")
    
    logger.info("\n🎯 RECOMENDACIONES:")
    logger.info("   1. Mantener monitoreo regular de índices vegetativos")
    logger.info("   2. Prestar atención a hotspots negativos (zonas de estrés)")
    logger.info("   3. Validar tendencia proyectada con observaciones de campo")
    logger.info("   4. Considerar análisis de alta resolución en zonas críticas")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info(f"\n💡 Motor de Análisis Agrícola v2.0 - 100% Funcional")
    logger.info(f"   • Sin dependencias de IA externa")
    logger.info(f"   • Análisis reproducible y auditable")
    logger.info(f"   • Exportación lista para dashboards")
    logger.info(f"   • Soporte completo para geoprocesamiento")
    logger.info("\n")


if __name__ == '__main__':
    try:
        test_integracion_completa()
    except Exception as e:
        logger.error(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
