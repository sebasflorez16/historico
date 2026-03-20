"""
Analizador SAVI - Soil-Adjusted Vegetation Index
Interpreta vegetación corrigiendo influencia del suelo
"""
import statistics
from typing import Dict, List, Any


class AnalizadorSAVI:
    """
    Analiza datos de SAVI - útil para cultivos con baja cobertura o suelo expuesto
    
    SAVI es similar a NDVI pero corregido para minimizar influencia del suelo
    Especialmente útil en: cultivos jóvenes, baja densidad, suelos claros
    """
    
    UMBRAL_BAJO = 0.3
    UMBRAL_MODERADO = 0.5
    UMBRAL_BUENO = 0.65
    UMBRAL_EXCELENTE = 0.75
    
    def __init__(self, tipo_cultivo: str = "General"):
        self.tipo_cultivo = tipo_cultivo
    
    def analizar(self, datos_savi: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza serie temporal de SAVI"""
        if not datos_savi:
            return self._resultado_sin_datos()
        
        valores = [d.get('savi', 0) for d in datos_savi if d.get('savi') is not None]
        
        if not valores:
            return self._resultado_sin_datos()
        
        # Estadísticas
        promedio = statistics.mean(valores)
        mediana = statistics.median(valores)
        minimo = min(valores)
        maximo = max(valores)
        desv_std = statistics.stdev(valores) if len(valores) > 1 else 0
        
        # Análisis
        tendencia = self._calcular_tendencia(valores)
        estado = self._clasificar_estado(promedio)
        
        # Interpretaciones
        interpretacion_tecnica = self._generar_interpretacion_tecnica(
            promedio, desv_std, tendencia, estado
        )
        
        interpretacion_simple = self._generar_interpretacion_simple(
            promedio, tendencia, estado
        )
        
        alertas = self._generar_alertas(promedio, tendencia)
        
        return {
            'indice': 'SAVI',
            'nombre': 'Índice de Vegetación Ajustado al Suelo',
            'estadisticas': {
                'promedio': round(promedio, 3),
                'mediana': round(mediana, 3),
                'minimo': round(minimo, 3),
                'maximo': round(maximo, 3),
                'desviacion_estandar': round(desv_std, 3)
            },
            'estado': estado,
            'tendencia': tendencia,
            'interpretacion_tecnica': interpretacion_tecnica,
            'interpretacion_simple': interpretacion_simple,
            'alertas': alertas,
            'puntuacion': self._calcular_puntuacion(promedio, tendencia),
            'exposicion_suelo': self._estimar_exposicion_suelo(promedio)
        }
    
    def _calcular_tendencia(self, valores: List[float]) -> Dict[str, Any]:
        """Calcula tendencia temporal"""
        if len(valores) < 3:
            return {'direccion': 'estable', 'magnitud': 0, 'descripcion': 'Datos insuficientes'}
        
        n = len(valores)
        cambio_promedio = sum(valores[i] - valores[i-1] for i in range(1, n)) / (n - 1)
        cambio_porcentual = (valores[-1] - valores[0]) / valores[0] * 100 if valores[0] != 0 else 0
        
        if abs(cambio_promedio) < 0.02:
            direccion = 'estable'
            descripcion = 'Cobertura estable'
        elif cambio_promedio > 0.04:
            direccion = 'ascendente_fuerte'
            descripcion = 'Aumento significativo de cobertura'
        elif cambio_promedio > 0:
            direccion = 'ascendente'
            descripcion = 'Cobertura en aumento'
        elif cambio_promedio < -0.04:
            direccion = 'descendente_fuerte'
            descripcion = 'Pérdida significativa de cobertura'
        else:
            direccion = 'descendente'
            descripcion = 'Cobertura en descenso'
        
        return {
            'direccion': direccion,
            'magnitud': round(cambio_promedio, 3),
            'cambio_porcentual': round(cambio_porcentual, 1),
            'descripcion': descripcion
        }
    
    def _clasificar_estado(self, promedio: float) -> Dict[str, str]:
        """Clasifica estado de cobertura"""
        if promedio < self.UMBRAL_BAJO:
            return {
                'nivel': 'bajo',
                'etiqueta': 'Cobertura Baja',
                'color': '#fd7e14',
                'icono': ''
            }
        elif promedio < self.UMBRAL_MODERADO:
            return {
                'nivel': 'moderado',
                'etiqueta': 'Cobertura Moderada',
                'color': '#ffc107',
                'icono': ''
            }
        elif promedio < self.UMBRAL_BUENO:
            return {
                'nivel': 'bueno',
                'etiqueta': 'Buena Cobertura',
                'color': '#28a745',
                'icono': ''
            }
        else:
            return {
                'nivel': 'excelente',
                'etiqueta': 'Cobertura Excelente',
                'color': '#20c997',
                'icono': ''
            }
    
    def _generar_interpretacion_tecnica(self, promedio: float, desv_std: float,
                                       tendencia: Dict, estado: Dict) -> str:
        """Interpretación técnica"""
        exposicion = self._estimar_exposicion_suelo(promedio)
        cobertura = 100 - exposicion
        
        # Describir cobertura en lenguaje claro
        if cobertura >= 80:
            cobertura_desc = "Las plantas cubren casi todo el terreno, con muy poco suelo visible."
        elif cobertura >= 60:
            cobertura_desc = "La mayor parte del terreno está cubierto por plantas, con algunas zonas de suelo visible."
        elif cobertura >= 40:
            cobertura_desc = "Hay un balance entre plantas y suelo. Se ven ambos de forma clara."
        else:
            cobertura_desc = "Se ve más suelo que plantas. La cobertura vegetal es limitada."
        
        # Describir variabilidad en lenguaje claro
        if desv_std < 0.05:
            variabilidad_desc = "La cobertura es muy pareja en toda la parcela."
        elif desv_std < 0.10:
            variabilidad_desc = "La cobertura es bastante uniforme, con diferencias menores entre zonas."
        elif desv_std < 0.15:
            variabilidad_desc = "Hay algunas zonas con más cobertura que otras."
        else:
            variabilidad_desc = "La cobertura varía bastante entre diferentes zonas de la parcela."
        
        # Describir tendencia en lenguaje claro
        if 'ascendente' in tendencia['direccion']:
            tendencia_desc = "La cobertura vegetal está aumentando. Las plantas están cubriendo más terreno con el tiempo."
        elif 'descendente' in tendencia['direccion']:
            tendencia_desc = "La cobertura vegetal está disminuyendo. Se está viendo más suelo con el tiempo, lo cual requiere atención."
        else:
            tendencia_desc = "La cobertura se ha mantenido estable durante el período analizado. No hay cambios significativos."
        
        interpretacion = f"""
<strong>Análisis SAVI - Cobertura del Suelo</strong><br><br>

El SAVI promedio de <strong>{promedio:.3f}</strong> indica 
<strong>{estado['etiqueta'].lower()}</strong>. Este valor es el promedio de todo el período analizado.<br><br>

<strong>Estado de la Cobertura:</strong><br>
• <strong>Suelo visible estimado: {exposicion}%</strong> - Porcentaje del terreno donde se ve el suelo directamente.<br>
• <strong>Cobertura vegetal: {cobertura}%</strong> - Porcentaje del terreno cubierto por plantas.<br>
• {cobertura_desc}<br>
• <strong>Uniformidad:</strong> {variabilidad_desc}<br><br>

<strong>Interpretación Agronómica:</strong><br>
SAVI mide qué tanto del terreno está cubierto por vegetación, corrigiendo el efecto del suelo. 
Es especialmente útil en cultivos jóvenes o con baja densidad. {self._interpretar_savi_tecnica(promedio)}<br><br>

<strong>Tendencia en el Período:</strong><br>
{tendencia_desc}
"""
        return interpretacion.strip()
    
    def _generar_interpretacion_simple(self, promedio: float, tendencia: Dict, estado: Dict) -> str:
        """Interpretación simple"""
        interpretacion = f"""
<strong>¿Qué tan cubierto está el suelo?</strong><br><br>

La cobertura de su parcela es <strong>{estado['etiqueta'].lower()}</strong>. 
{self._explicar_simple(promedio)}<br><br>

<strong>Tendencia:</strong><br>
{self._explicar_tendencia_simple(tendencia)}
"""
        return interpretacion.strip()
    
    def _generar_alertas(self, promedio: float, tendencia: Dict) -> List[Dict]:
        """Genera alertas"""
        alertas = []
        
        # Cobertura baja
        if promedio < self.UMBRAL_BAJO:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'media',
                'icono': '',
                'titulo': 'Baja Cobertura Vegetal',
                'mensaje': f'SAVI de {promedio:.2f} indica mucho suelo expuesto.',
                'accion': 'Evaluar densidad de siembra o desarrollo del cultivo'
            })
        
        # Tendencia descendente
        if tendencia['direccion'] in ['descendente', 'descendente_fuerte']:
            alertas.append({
                'tipo': 'info',
                'prioridad': 'media',
                'icono': '',
                'titulo': 'Reducción de Cobertura',
                'mensaje': f"La cobertura ha disminuido {abs(tendencia['cambio_porcentual']):.1f}%.",
                'accion': 'Monitorear desarrollo del cultivo'
            })
        
        return alertas
    
    # Métodos auxiliares
    
    def _resultado_sin_datos(self) -> Dict:
        """Resultado cuando no hay datos"""
        return {
            'indice': 'SAVI',
            'nombre': 'Índice de Vegetación Ajustado al Suelo',
            'error': 'No hay datos disponibles',
            'estadisticas': {},
            'estado': {'nivel': 'sin_datos', 'etiqueta': 'Sin Datos', 'icono': ''},
            'interpretacion_tecnica': 'No hay datos SAVI disponibles.',
            'interpretacion_simple': 'Aún no tenemos información sobre cobertura.',
            'alertas': []
        }
    
    def _estimar_exposicion_suelo(self, savi: float) -> int:
        """Estima porcentaje de suelo expuesto"""
        if savi < 0.2:
            return 80
        elif savi < 0.4:
            return 50
        elif savi < 0.6:
            return 30
        else:
            return 15
    
    def _interpretar_savi_tecnica(self, savi: float) -> str:
        """Interpretación técnica de SAVI"""
        if savi < 0.3:
            return "Indicador de cultivo joven, baja densidad o estrés. Verificar etapa fenológica esperada."
        elif savi < 0.5:
            return "Desarrollo vegetativo moderado. Normal en fases tempranas o cultivos espaciados."
        elif savi < 0.7:
            return "Buen desarrollo vegetativo con cobertura adecuada para la etapa del cultivo."
        else:
            return "Excelente cobertura vegetal. Cultivo en pleno desarrollo vegetativo."
    
    def _explicar_simple(self, savi: float) -> str:
        """Explicación simple"""
        if savi < 0.3:
            return "Se ve mucho suelo entre las plantas. Es normal si el cultivo es joven, pero hay que vigilar."
        elif savi < 0.5:
            return "Hay un balance entre plantas y suelo visible. Las plantas están creciendo."
        elif savi < 0.7:
            return "Las plantas cubren bien el suelo. Se ve más verde que tierra."
        else:
            return "¡Excelente! Las plantas cubren casi todo el suelo, muy poco espacio vacío."
    
    def _explicar_tendencia_simple(self, tendencia: Dict) -> str:
        """Explicación simple de tendencia"""
        if 'ascendente' in tendencia['direccion']:
            return f"Las plantas están cubriendo más terreno ({tendencia['cambio_porcentual']:.0f}% más). Están creciendo bien."
        elif 'descendente' in tendencia['direccion']:
            return f"Se está viendo más suelo ({abs(tendencia['cambio_porcentual']):.0f}% menos plantas). Revisar qué está pasando."
        else:
            return "La cobertura se mantiene igual. Sin cambios importantes."
    
    def _calcular_puntuacion(self, promedio: float, tendencia: Dict) -> float:
        """Calcula puntuación 0-10"""
        puntuacion_base = (promedio / 1.0) * 10
        
        if tendencia['direccion'] == 'ascendente_fuerte':
            ajuste = 0.5
        elif tendencia['direccion'] == 'descendente_fuerte':
            ajuste = -0.5
        else:
            ajuste = 0
        
        return round(max(0, min(10, puntuacion_base + ajuste)), 1)
