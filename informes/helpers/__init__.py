"""
Módulo de helpers para informes PDF
===================================

Funciones de utilidad para generación de PDFs profesionales.
"""

from .diagnostico_pdf_helper import (
    generar_tabla_desglose_severidad,
    agregar_seccion_diagnostico_unificado,
    obtener_resumen_metricas_diagnostico
)

__all__ = [
    'generar_tabla_desglose_severidad',
    'agregar_seccion_diagnostico_unificado',
    'obtener_resumen_metricas_diagnostico'
]
