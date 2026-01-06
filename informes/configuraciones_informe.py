"""
Configuraciones predefinidas para informes personalizados
Define las plantillas del sistema y configuraciones por defecto
"""

# ============================================================================
# ÍNDICES DISPONIBLES Y SUS DESCRIPCIONES
# ============================================================================

INDICES_DISPONIBLES = {
    'ndvi': {
        'nombre': 'NDVI',
        'nombre_completo': 'Índice de Vegetación de Diferencia Normalizada',
        'descripcion': 'Vigor vegetativo y salud general del cultivo',
        'icono': 'leaf',
        'color': '#28a745',
        'obligatorio': True,  # NDVI siempre se incluye
    },
    'ndre': {
        'nombre': 'NDRE',
        'nombre_completo': 'Índice de Borde Rojo de Diferencia Normalizada',
        'descripcion': 'Nivel de nitrógeno y clorofila en las plantas',
        'icono': 'flask',
        'color': '#17a2b8',
        'obligatorio': False,
    },
    'msavi': {
        'nombre': 'MSAVI',
        'nombre_completo': 'Índice de Vegetación Ajustado al Suelo Modificado',
        'descripcion': 'Estrés hídrico y cobertura vegetal',
        'icono': 'tint',
        'color': '#007bff',
        'obligatorio': False,
    },
    'ndwi': {
        'nombre': 'NDWI',
        'nombre_completo': 'Índice de Agua de Diferencia Normalizada',
        'descripcion': 'Contenido de agua en la vegetación',
        'icono': 'water',
        'color': '#0dcaf0',
        'obligatorio': False,
    },
    'evi': {
        'nombre': 'EVI',
        'nombre_completo': 'Índice de Vegetación Mejorado',
        'descripcion': 'Vegetación densa con reducción de interferencias',
        'icono': 'seedling',
        'color': '#20c997',
        'obligatorio': False,
    },
    'reci': {
        'nombre': 'RECI',
        'nombre_completo': 'Índice de Clorofila de Borde Rojo',
        'descripcion': 'Contenido de clorofila y estado nutricional',
        'icono': 'microscope',
        'color': '#6610f2',
        'obligatorio': False,
    },
}

# ============================================================================
# NIVELES DE DETALLE
# ============================================================================

NIVELES_DETALLE = {
    'ejecutivo': {
        'nombre': 'Ejecutivo',
        'descripcion': 'Resumen conciso con conclusiones principales',
        'icono': 'briefcase',
        'paginas_aprox': '3-5 páginas',
        'incluye': [
            'Resumen ejecutivo',
            'Conclusiones principales',
            'Recomendaciones clave',
            'Gráfico resumen',
        ],
        'excluye': [
            'Datos técnicos detallados',
            'Múltiples gráficos',
            'Imágenes satelitales',
        ],
    },
    'estandar': {
        'nombre': 'Estándar',
        'descripcion': 'Balance entre detalle y concisión',
        'icono': 'file-alt',
        'paginas_aprox': '8-12 páginas',
        'incluye': [
            'Resumen ejecutivo',
            'Análisis de tendencias',
            'Gráficos principales',
            'Recomendaciones detalladas',
            'Imágenes satelitales clave',
        ],
        'excluye': [
            'Datos raw completos',
            'Todas las imágenes disponibles',
        ],
    },
    'completo': {
        'nombre': 'Completo',
        'descripcion': 'Análisis exhaustivo con todos los datos',
        'icono': 'book',
        'paginas_aprox': '15-25 páginas',
        'incluye': [
            'Todo el análisis disponible',
            'Todos los gráficos',
            'Todas las imágenes satelitales',
            'Datos técnicos detallados',
            'Comparativas temporales',
            'Anexos técnicos',
        ],
        'excluye': [],
    },
}

# ============================================================================
# SECCIONES OPCIONALES
# ============================================================================

SECCIONES_OPCIONALES = {
    'tendencias': {
        'nombre': 'Análisis de Tendencias Temporales',
        'descripcion': 'Gráficos y análisis de evolución en el tiempo',
        'icono': 'chart-line',
        'recomendado': True,
    },
    'comparativa_anterior': {
        'nombre': 'Comparativa con Período Anterior',
        'descripcion': 'Comparación con el período inmediatamente anterior',
        'icono': 'exchange-alt',
        'recomendado': False,
    },
    'pronostico': {
        'nombre': 'Pronóstico y Predicciones',
        'descripcion': 'Proyecciones basadas en tendencias actuales',
        'icono': 'crystal-ball',
        'recomendado': False,
    },
    'recomendaciones_riego': {
        'nombre': 'Recomendaciones de Riego',
        'descripcion': 'Sugerencias específicas para optimizar riego',
        'icono': 'shower',
        'recomendado': True,
    },
    'recomendaciones_fertilizacion': {
        'nombre': 'Recomendaciones de Fertilización',
        'descripcion': 'Sugerencias de fertilización según índices',
        'icono': 'magic',
        'recomendado': True,
    },
    'analisis_economico': {
        'nombre': 'Análisis Económico',
        'descripcion': 'Proyección de costos y rentabilidad',
        'icono': 'dollar-sign',
        'recomendado': False,
        'requiere_datos': True,  # Requiere datos económicos en la parcela
    },
    'imagenes_satelitales': {
        'nombre': 'Imágenes Satelitales Detalladas',
        'descripcion': 'Todas las imágenes satelitales disponibles',
        'icono': 'satellite',
        'recomendado': True,
        'peso_adicional': 'Alto',  # Incrementa significativamente el tamaño del PDF
    },
    'datos_meteorologicos': {
        'nombre': 'Datos Meteorológicos',
        'descripcion': 'Precipitación, temperatura y clima del período',
        'icono': 'cloud-sun',
        'recomendado': True,
    },
    'analisis_zonas': {
        'nombre': 'Análisis por Zonas',
        'descripcion': 'Dividir la parcela en zonas de manejo',
        'icono': 'th',
        'recomendado': False,
        'experimental': True,
    },
}

# ============================================================================
# CONFIGURACIÓN POR DEFECTO (ACTUAL - SIN CAMBIOS)
# ============================================================================

CONFIGURACION_COMPLETA_DEFAULT = {
    'nivel_detalle': 'completo',
    'indices': list(INDICES_DISPONIBLES.keys()),  # Todos los índices
    'secciones': list(SECCIONES_OPCIONALES.keys()),  # Todas las secciones
    'formato': {
        'orientacion': 'vertical',
        'estilo': 'profesional',
        'idioma': 'es',
    },
    'comparacion': {
        'habilitada': False,
        'tipo': None,
    },
    'personalizacion': {
        'enfoque_especial': None,
        'notas_adicionales': None,
    },
}

# ============================================================================
# PLANTILLAS PREDEFINIDAS DEL SISTEMA
# ============================================================================

PLANTILLAS_SISTEMA = {
    'completo_default': {
        'nombre': '📊 Informe Completo (Por Defecto)',
        'descripcion': 'Análisis exhaustivo con todos los índices y secciones disponibles',
        'tipo_cultivo_sugerido': 'Todos',
        'configuracion': CONFIGURACION_COMPLETA_DEFAULT,
        'es_publica': True,
        'icono': 'star',
    },
    
    'ejecutivo_rapido': {
        'nombre': '⚡ Ejecutivo Rápido',
        'descripcion': 'Resumen conciso ideal para presentaciones ejecutivas',
        'tipo_cultivo_sugerido': 'Todos',
        'configuracion': {
            'nivel_detalle': 'ejecutivo',
            'indices': ['ndvi', 'msavi'],  # Solo índices principales
            'secciones': ['tendencias', 'recomendaciones_riego'],
            'formato': {
                'orientacion': 'vertical',
                'estilo': 'simplificado',
                'idioma': 'es',
            },
            'comparacion': {'habilitada': False, 'tipo': None},
            'personalizacion': {'enfoque_especial': None, 'notas_adicionales': None},
        },
        'es_publica': True,
        'icono': 'bolt',
    },
    
    'optimizacion_riego': {
        'nombre': '💧 Optimización de Riego',
        'descripcion': 'Enfocado en estrés hídrico y recomendaciones de riego',
        'tipo_cultivo_sugerido': 'Todos',
        'configuracion': {
            'nivel_detalle': 'estandar',
            'indices': ['ndvi', 'msavi', 'ndwi'],  # Índices relacionados con agua
            'secciones': [
                'tendencias',
                'recomendaciones_riego',
                'datos_meteorologicos',
                'imagenes_satelitales',
            ],
            'formato': {
                'orientacion': 'vertical',
                'estilo': 'profesional',
                'idioma': 'es',
            },
            'comparacion': {'habilitada': False, 'tipo': None},
            'personalizacion': {
                'enfoque_especial': 'Optimización del uso de agua y prevención de estrés hídrico',
                'notas_adicionales': None,
            },
        },
        'es_publica': True,
        'icono': 'tint',
    },
    
    'nutricion_nitrogeno': {
        'nombre': '🧪 Análisis Nutricional',
        'descripcion': 'Enfocado en nitrógeno, clorofila y fertilización',
        'tipo_cultivo_sugerido': 'Todos',
        'configuracion': {
            'nivel_detalle': 'estandar',
            'indices': ['ndvi', 'ndre', 'reci'],  # Índices relacionados con nutrición
            'secciones': [
                'tendencias',
                'recomendaciones_fertilizacion',
                'imagenes_satelitales',
            ],
            'formato': {
                'orientacion': 'vertical',
                'estilo': 'profesional',
                'idioma': 'es',
            },
            'comparacion': {'habilitada': False, 'tipo': None},
            'personalizacion': {
                'enfoque_especial': 'Optimización de fertilización nitrogenada',
                'notas_adicionales': None,
            },
        },
        'es_publica': True,
        'icono': 'flask',
    },
    
    'monitoreo_estacional': {
        'nombre': '📅 Monitoreo Estacional',
        'descripcion': 'Comparativa con períodos anteriores y pronósticos',
        'tipo_cultivo_sugerido': 'Todos',
        'configuracion': {
            'nivel_detalle': 'completo',
            'indices': ['ndvi', 'msavi', 'ndre', 'evi'],
            'secciones': [
                'tendencias',
                'comparativa_anterior',
                'pronostico',
                'recomendaciones_riego',
                'recomendaciones_fertilizacion',
                'datos_meteorologicos',
                'imagenes_satelitales',
            ],
            'formato': {
                'orientacion': 'vertical',
                'estilo': 'profesional',
                'idioma': 'es',
            },
            'comparacion': {
                'habilitada': True,
                'tipo': 'periodo_anterior',
            },
            'personalizacion': {
                'enfoque_especial': 'Seguimiento estacional y comparativas temporales',
                'notas_adicionales': None,
            },
        },
        'es_publica': True,
        'icono': 'calendar-alt',
    },
    
    'analisis_economico': {
        'nombre': '💰 Análisis Económico',
        'descripcion': 'Enfoque en rentabilidad y proyecciones económicas',
        'tipo_cultivo_sugerido': 'Todos',
        'configuracion': {
            'nivel_detalle': 'completo',
            'indices': ['ndvi', 'msavi', 'evi'],
            'secciones': [
                'tendencias',
                'analisis_economico',
                'recomendaciones_riego',
                'recomendaciones_fertilizacion',
                'pronostico',
            ],
            'formato': {
                'orientacion': 'vertical',
                'estilo': 'profesional',
                'idioma': 'es',
            },
            'comparacion': {
                'habilitada': True,
                'tipo': 'periodo_anterior',
            },
            'personalizacion': {
                'enfoque_especial': 'Optimización de costos y maximización de rentabilidad',
                'notas_adicionales': None,
            },
        },
        'es_publica': True,
        'icono': 'chart-pie',
        'requiere_datos_economicos': True,
    },
}


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def validar_configuracion(config):
    """
    Valida que una configuración tenga todos los campos requeridos
    """
    required_fields = ['nivel_detalle', 'indices', 'secciones', 'formato']
    
    for field in required_fields:
        if field not in config:
            return False, f"Falta el campo requerido: {field}"
    
    # Validar nivel de detalle
    if config['nivel_detalle'] not in NIVELES_DETALLE:
        return False, f"Nivel de detalle inválido: {config['nivel_detalle']}"
    
    # Validar que al menos NDVI esté incluido
    if 'ndvi' not in config['indices']:
        return False, "NDVI es obligatorio en todos los informes"
    
    # Validar índices
    for indice in config['indices']:
        if indice not in INDICES_DISPONIBLES:
            return False, f"Índice desconocido: {indice}"
    
    return True, "Configuración válida"


def obtener_configuracion_default():
    """
    Retorna la configuración completa por defecto (actual)
    """
    return CONFIGURACION_COMPLETA_DEFAULT.copy()


def obtener_plantillas_disponibles(usuario=None):
    """
    Obtiene todas las plantillas disponibles para un usuario
    Incluye plantillas del sistema + plantillas del usuario + plantillas públicas
    """
    from .models import PlantillaInforme
    
    # Plantillas del sistema (siempre disponibles)
    plantillas = []
    for key, plantilla in PLANTILLAS_SISTEMA.items():
        plantillas.append({
            'id': f'sistema_{key}',
            'tipo': 'sistema',
            **plantilla
        })
    
    # Plantillas del usuario (si está autenticado)
    if usuario and usuario.is_authenticated:
        plantillas_usuario = PlantillaInforme.objects.filter(usuario=usuario)
        for plantilla in plantillas_usuario:
            plantillas.append({
                'id': f'usuario_{plantilla.id}',
                'tipo': 'usuario',
                'nombre': plantilla.nombre,
                'descripcion': plantilla.descripcion,
                'configuracion': plantilla.configuracion,
                'tipo_cultivo_sugerido': plantilla.tipo_cultivo_sugerido,
                'veces_usada': plantilla.veces_usada,
            })
        
        # Plantillas públicas de otros usuarios
        plantillas_publicas = PlantillaInforme.objects.filter(
            es_publica=True
        ).exclude(usuario=usuario)
        
        for plantilla in plantillas_publicas:
            plantillas.append({
                'id': f'publica_{plantilla.id}',
                'tipo': 'publica',
                'nombre': f"{plantilla.nombre} (Pública)",
                'descripcion': plantilla.descripcion,
                'configuracion': plantilla.configuracion,
                'tipo_cultivo_sugerido': plantilla.tipo_cultivo_sugerido,
                'veces_usada': plantilla.veces_usada,
                'autor': plantilla.usuario.username if plantilla.usuario else 'Sistema',
            })
    
    return plantillas
