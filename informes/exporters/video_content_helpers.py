"""
Helpers para generar contenido educativo en videos de timeline
Proporciona explicaciones de índices satelitales y utilidades de formato

@author: AgroTech Team
@version: 1.0.0
"""

from typing import Dict, List, Optional, Tuple

# Configuración de explicaciones de índices satelitales
INDICE_EXPLICACIONES = {
    'ndvi': {
        'nombre_completo': 'Índice de Vegetación',
        'nombre_ingles': 'Normalized Difference Vegetation Index',
        'siglas': 'NDVI',
        'descripcion_corta': 'Mide qué tan sanas están las plantas',
        'descripcion_larga': 'Identifica el estado de salud de los cultivos usando imágenes satelitales',
        'rangos': [
            {'min': -1.0, 'max': -0.2, 'label': 'Agua o suelo desnudo', 'color': '#8B4513'},
            {'min': -0.2, 'max': 0.2, 'label': 'Vegetación escasa', 'color': '#D2691E'},
            {'min': 0.2, 'max': 0.5, 'label': 'Vegetación moderada', 'color': '#FFD700'},
            {'min': 0.5, 'max': 0.7, 'label': 'Vegetación densa', 'color': '#90EE90'},
            {'min': 0.7, 'max': 1.0, 'label': 'Vegetación muy densa', 'color': '#006400'},
        ],
        'aplicacion_general': 'Permite identificar zonas del terreno que necesitan atención',
        'como_funciona': [
            'Las plantas sanas reflejan más luz',
            'que las plantas enfermas o con estrés.',
            'Este índice mide esa diferencia.'
        ],
        'rangos_texto': [
            'Valores muy bajos (-1.0 a -0.2): Agua, nieve o suelo muy expuesto',
            'Valores bajos (-0.2 a 0.2): Suelo desnudo o vegetación muy escasa',
            'Valores medios (0.2 a 0.5): Cultivo en desarrollo o con estrés moderado',
            'Valores altos (0.5 a 0.7): Cultivo saludable con buen vigor vegetativo',
            'Valores muy altos (0.7 a 1.0): Vegetación densa y altamente fotosintética',
        ]
    },
    'ndmi': {
        'nombre_completo': 'Índice de Humedad',
        'nombre_ingles': 'Normalized Difference Moisture Index',
        'siglas': 'NDMI',
        'descripcion_corta': 'Mide cuánta agua tienen las plantas',
        'descripcion_larga': 'Identifica si los cultivos tienen suficiente agua o están en estrés',
        'rangos': [
            {'min': -1.0, 'max': -0.4, 'label': 'Muy seco', 'color': '#8B0000'},
            {'min': -0.4, 'max': -0.1, 'label': 'Seco', 'color': '#D2691E'},
            {'min': -0.1, 'max': 0.2, 'label': 'Humedad moderada', 'color': '#FFD700'},
            {'min': 0.2, 'max': 0.4, 'label': 'Húmedo', 'color': '#90EE90'},
            {'min': 0.4, 'max': 1.0, 'label': 'Muy húmedo', 'color': '#0000FF'},
        ],
        'aplicacion_general': 'Ayuda a programar riegos y detectar zonas secas',
        'como_funciona': [
            'Los cultivos con suficiente agua se ven',
            'diferentes en las imágenes satelitales',
            'que los cultivos secos.'
        ],
        'rangos_texto': [
            'Valores muy bajos (-1.0 a -0.4): Estrés hídrico severo o suelo seco',
            'Valores bajos (-0.4 a -0.1): Cultivo con déficit de agua moderado',
            'Valores medios (-0.1 a 0.2): Humedad adecuada pero mejorable',
            'Valores altos (0.2 a 0.4): Buen contenido de humedad en la planta',
            'Valores muy altos (0.4 a 1.0): Excelente hidratación o exceso de agua',
        ]
    },
    'savi': {
        'nombre_completo': 'Índice de Vegetación Ajustado',
        'nombre_ingles': 'Soil-Adjusted Vegetation Index',
        'siglas': 'SAVI',
        'descripcion_corta': 'Similar al NDVI pero más preciso con suelo visible',
        'descripcion_larga': 'Útil cuando el cultivo no cubre todo el terreno',
        'rangos': [
            {'min': -1.0, 'max': -0.2, 'label': 'Agua o suelo expuesto', 'color': '#8B4513'},
            {'min': -0.2, 'max': 0.2, 'label': 'Cobertura muy baja', 'color': '#D2691E'},
            {'min': 0.2, 'max': 0.4, 'label': 'Cobertura moderada', 'color': '#FFD700'},
            {'min': 0.4, 'max': 0.6, 'label': 'Cobertura alta', 'color': '#90EE90'},
            {'min': 0.6, 'max': 1.0, 'label': 'Cobertura completa', 'color': '#006400'},
        ],
        'aplicacion_general': 'Monitoreo de cultivos jóvenes o con surcos amplios',
        'como_funciona': [
            'Funciona mejor que el NDVI cuando',
            'hay mucho suelo visible entre plantas,',
            'como en cultivos recién sembrados.'
        ],
        'rangos_texto': [
            'Valores muy bajos (-1.0 a -0.2): Agua, suelo desnudo o sin cultivo',
            'Valores bajos (-0.2 a 0.2): Cultivo en etapa muy temprana o germinación',
            'Valores medios (0.2 a 0.4): Cultivo en desarrollo con suelo parcialmente visible',
            'Valores altos (0.4 a 0.6): Buen desarrollo vegetativo con cobertura creciente',
            'Valores muy altos (0.6 a 1.0): Cobertura vegetal completa o casi completa',
        ]
    }
}


def obtener_info_indice(indice: str) -> Dict:
    """
    Obtiene la información completa de un índice
    
    Args:
        indice: Código del índice ('ndvi', 'ndmi', 'savi')
        
    Returns:
        Diccionario con información del índice
    """
    indice_lower = indice.lower()
    if indice_lower not in INDICE_EXPLICACIONES:
        return {
            'nombre_completo': f'Índice {indice.upper()}',
            'descripcion_corta': 'Índice satelital',
            'rangos': [],
            'aplicacion_general': 'Análisis satelital'
        }
    return INDICE_EXPLICACIONES[indice_lower]


def generar_texto_aplicacion_terreno(indice: str, parcela_info: Dict) -> str:
    """
    Genera texto de aplicación del índice específico al terreno
    
    Args:
        indice: Código del índice
        parcela_info: Información de la parcela
        
    Returns:
        Texto formateado de aplicación
    """
    info = obtener_info_indice(indice)
    area = parcela_info.get('area_hectareas', 0)
    cultivo = parcela_info.get('tipo_cultivo', 'cultivo')
    
    aplicacion_base = info.get('aplicacion_general', 'Análisis satelital')
    
    # Formatear texto con información del terreno
    if area > 0:
        texto = f"{aplicacion_base} en {area:.2f} hectáreas"
        if cultivo and cultivo.lower() != 'sin especificar':
            texto += f" de cultivo de {cultivo}"
    else:
        texto = aplicacion_base
    
    return texto


def detectar_proximo_mes_disponible(frames_data: List[Dict], current_index: int) -> Optional[str]:
    """
    Encuentra el próximo mes con imagen satelital disponible
    
    Args:
        frames_data: Lista de frames del timeline
        current_index: Índice actual
        
    Returns:
        Texto del próximo mes disponible o None
    """
    for i in range(current_index + 1, len(frames_data)):
        frame = frames_data[i]
        
        # Verificar si tiene imagen disponible
        imagenes = frame.get('imagenes', {})
        metadata = frame.get('imagen_metadata', {})
        nubosidad = metadata.get('nubosidad')
        
        # Manejar nubosidad None
        if nubosidad is None:
            nubosidad = 0.0  # Asumir buena calidad si no hay datos
        
        # Si tiene alguna imagen y nubosidad aceptable
        tiene_imagen = any(imagenes.values())
        if tiene_imagen and nubosidad <= 0.7:
            return frame.get('periodo_texto', 'Próximo mes')
    
    return None


def formatear_coordenadas(lat: float, lon: float) -> Tuple[str, str]:
    """
    Formatea coordenadas en formato legible
    
    Args:
        lat: Latitud
        lon: Longitud
        
    Returns:
        Tupla (lat_texto, lon_texto)
    """
    # Formatear latitud
    lat_abs = abs(lat)
    lat_dir = 'N' if lat >= 0 else 'S'
    lat_texto = f"{lat_abs:.6f}° {lat_dir}"
    
    # Formatear longitud
    lon_abs = abs(lon)
    lon_dir = 'E' if lon >= 0 else 'W'
    lon_texto = f"{lon_abs:.6f}° {lon_dir}"
    
    return lat_texto, lon_texto


def truncar_texto(texto: str, max_chars: int = 500) -> str:
    """
    Trunca texto a un máximo de caracteres sin cortar palabras
    
    Args:
        texto: Texto original
        max_chars: Máximo de caracteres
        
    Returns:
        Texto truncado
    """
    if not texto or len(texto) <= max_chars:
        return texto
    
    # Truncar en el último espacio antes del límite
    texto_truncado = texto[:max_chars]
    ultimo_espacio = texto_truncado.rfind(' ')
    
    if ultimo_espacio > 0:
        texto_truncado = texto_truncado[:ultimo_espacio]
    
    return texto_truncado + '...'


def limpiar_texto_analisis(texto: str, max_lineas: int = 12) -> str:
    """
    Limpia y formatea texto de análisis para video
    Limita número de líneas y elimina formato markdown
    
    Args:
        texto: Texto original
        max_lineas: Máximo número de líneas
        
    Returns:
        Texto limpio y formateado
    """
    if not texto:
        return ""
    
    # Eliminar markdown básico
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('###', '').replace('##', '').replace('#', '')
    
    # Dividir en líneas y limpiar
    lineas = [l.strip() for l in texto.split('\n') if l.strip()]
    
    # Limitar número de líneas
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
    
    return '\n'.join(lineas)


def parsear_recomendaciones_desde_texto(texto: str, max_recos: int = 4) -> List[str]:
    """
    Parsea recomendaciones desde texto plano
    
    Args:
        texto: Texto con recomendaciones
        max_recos: Máximo número de recomendaciones
        
    Returns:
        Lista de recomendaciones
    """
    if not texto:
        return []
    
    recos = []
    
    # Intentar parsear por líneas con bullets o números
    for line in texto.split('\n'):
        line = line.strip()
        
        # Detectar bullets comunes
        if line.startswith(('-', '•', '*', '→', '►')):
            reco = line.lstrip('-•*→► ').strip()
            if reco and len(reco) > 10:
                recos.append(reco)
        
        # Si empieza con número
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            reco = line[2:].strip()
            if reco and len(reco) > 10:
                recos.append(reco)
        
        # Línea simple (si aún no tenemos suficientes)
        elif line and len(recos) < max_recos and len(line) > 15:
            if not line.isupper() and not line.endswith(':'):
                recos.append(line)
    
    # Si no se encontraron bullets, dividir por puntos
    if not recos:
        frases = [f.strip() for f in texto.split('.') if f.strip() and len(f.strip()) > 15]
        recos = frases[:max_recos]
    
    return recos[:max_recos]


def calcular_estadisticas_periodo(frames_data: List[Dict], indice: str) -> Dict:
    """
    Calcula estadísticas del período completo
    
    Args:
        frames_data: Lista de frames
        indice: Índice a analizar
        
    Returns:
        Diccionario con estadísticas
    """
    valores = []
    meses_con_datos = 0
    
    for frame in frames_data:
        valor = frame.get(indice, {}).get('promedio')
        if valor is not None:
            valores.append(valor)
            meses_con_datos += 1
    
    if not valores:
        return {
            'promedio': 0,
            'minimo': 0,
            'maximo': 0,
            'meses_con_datos': 0,
            'total_meses': len(frames_data)
        }
    
    return {
        'promedio': sum(valores) / len(valores),
        'minimo': min(valores),
        'maximo': max(valores),
        'meses_con_datos': meses_con_datos,
        'total_meses': len(frames_data)
    }
