"""
Motor de Análisis Agrícola Profesional v3.0
==========================================

Sistema determinístico multi-índice de análisis agrícola con trazabilidad completa.

ARQUITECTURA v3.0 - MULTI-ÍNDICE AUDITABLE
==========================================

Características principales:
- ✅ Multi-índice: Procesa NDVI, NDMI, SAVI y futuros índices bajo arquitectura común
- ✅ Auditable: Registro completo de proveniencia de datos (Data Provenance)
- ✅ Defendible: Reporte Técnico con metodologías, limitaciones y confianza
- ✅ Diagnóstico cruzado: Análisis combinado de índices (ej: vigor vs humedad)
- ✅ Ponderación automática: Recomendaciones ajustadas por calidad de datos
- ✅ Reproducible: Mismos datos → Mismos resultados
- ✅ Económico: Sin costos de API externa

MÓDULOS CORE
============

1. proveniencia_datos:
   - RegistradorProveniencia: Tracking completo de fuentes de datos
   - MetadatosImagen: Metadatos satelitales (calidad, nubosidad, satélite)
   - RegistroIndice: Trazabilidad de cada índice calculado
   - Exportación de auditoría completa

2. reporte_tecnico:
   - ReporteTecnico: Objeto formal de análisis técnico
   - Documentación de bibliotecas utilizadas (NumPy, SciPy, scikit-learn)
   - Registro de reglas agronómicas aplicadas
   - Limitaciones explícitas del análisis
   - Nivel de confianza calculado (muy_alta, alta, media, baja, muy_baja)
   - Ponderación automática de recomendaciones por confianza

3. procesador_multiindice:
   - ProcesadorMultiIndice: Procesador unificado para cualquier índice
   - RegistroIndices: Registro dinámico de índices disponibles
   - DefinicionIndice: Metadatos y validación por índice
   - Soporte para NDVI, NDMI, SAVI y futuros índices
   - Estadísticas estandarizadas para comparación

4. diagnostico_cruzado:
   - MotorDiagnosticoCruzado: Análisis combinado de múltiples índices
   - PatronCruzado: Patrones agronómicos (ej: estrés hídrico severo)
   - Diagnóstico diferencial basado en combinaciones
   - Recomendaciones priorizadas por severidad y confianza
   - 7 patrones predefinidos + extensible

MÓDULOS HEREDADOS (compatibilidad con v2.0)
===========================================

5. procesador_indices: Estadísticas y tendencias de índices vegetativos
6. zonificador: Zonificación productiva por percentiles
7. detector_anomalias: Detección de eventos críticos y anomalías
8. generador_diagnosticos: Integración y generación de informes
9. procesador_raster: Análisis avanzado de imágenes satelitales
10. analizador_series_temporal: Análisis temporal (tendencias, predicción)
11. exportador_resultados: Exportación para dashboards y visualización

FLUJO DE TRABAJO v3.0
=====================

1. REGISTRO DE DATOS:
   registrador = RegistradorProveniencia()
   registrador.registrar_imagen(metadatos_imagen)
   registrador.registrar_indice(registro_indice)

2. ANÁLISIS MULTI-ÍNDICE:
   motor = MotorDiagnosticoCruzado(tipo_cultivo='maíz')
   resultado = motor.analizar_multiindice({
       'ndvi': datos_ndvi,
       'ndmi': datos_ndmi,
       'savi': datos_savi
   })

3. REPORTE TÉCNICO:
   reporte = ReporteTecnico(
       id_reporte="RT-20241215",
       periodo_analisis_inicio=date(2024, 1, 1),
       periodo_analisis_fin=date(2024, 12, 1)
   )
   reporte.calcular_confianza(confianza_datos=0.85, ...)
   reporte.agregar_limitacion('datos', 'Nubosidad >20% en 3 imágenes', 'medio')
   
4. PONDERACIÓN DE RECOMENDACIONES:
   rec_ponderada = reporte.ponderar_recomendacion(
       "Implementar riego inmediato",
       prioridad_base='alta'
   )
   # Si confianza es baja, automáticamente degrada prioridad

5. AUDITORÍA:
   auditoria = registrador.exportar_auditoria()
   resumen = registrador.generar_resumen_proveniencia()

REFERENCIAS CIENTÍFICAS
=======================
- Rouse et al. (1974): NDVI original
- Huete (1988): SAVI
- Gao (1996): NDWI/NDMI
- Tucker (1979): Aplicaciones NDVI
- ISO 19115: Metadatos geográficos
- FAIR Data Principles: Findable, Accessible, Interoperable, Reusable
"""

# Módulos v3.0 - Multi-índice auditable
from .proveniencia_datos import (
    RegistradorProveniencia,
    MetadatosImagen,
    RegistroIndice,
    FuenteDatos,
    CalidadImagen
)
from .reporte_tecnico import (
    ReporteTecnico,
    NivelConfianza,
    BibliotecaTecnica,
    ReglaAgronomica,
    Limitacion
)
from .procesador_multiindice import (
    ProcesadorMultiIndice,
    RegistroIndices,
    DefinicionIndice,
    TipoIndice,
    registro_indices
)
from .diagnostico_cruzado import (
    MotorDiagnosticoCruzado,
    PatronCruzado,
    analizar_parcela
)

# Módulos v2.0 - Compatibilidad
from .procesador_indices import ProcesadorIndices
from .zonificador import ZonificadorProductivo
from .detector_anomalias import DetectorAnomalias
from .generador_diagnosticos import GeneradorDiagnosticos
from .procesador_raster import ProcesadorRaster, procesador_raster
from .analizador_series_temporal import AnalizadorSeriesTemporal, analizador_series
from .exportador_resultados import ExportadorResultados, exportador

__all__ = [
    # v3.0 - Multi-índice auditable
    'RegistradorProveniencia',
    'MetadatosImagen',
    'RegistroIndice',
    'FuenteDatos',
    'CalidadImagen',
    'ReporteTecnico',
    'NivelConfianza',
    'BibliotecaTecnica',
    'ReglaAgronomica',
    'Limitacion',
    'ProcesadorMultiIndice',
    'RegistroIndices',
    'DefinicionIndice',
    'TipoIndice',
    'registro_indices',
    'MotorDiagnosticoCruzado',
    'PatronCruzado',
    'analizar_parcela',
    
    # v2.0 - Compatibilidad
    'ProcesadorIndices',
    'ZonificadorProductivo',
    'DetectorAnomalias',
    'GeneradorDiagnosticos',
    'ProcesadorRaster',
    'procesador_raster',
    'AnalizadorSeriesTemporal',
    'analizador_series',
    'ExportadorResultados',
    'exportador',
]

__version__ = '3.0.0'
__author__ = 'AgroTech Team'
__description__ = 'Motor de Análisis Agrícola Multi-Índice Auditable'
