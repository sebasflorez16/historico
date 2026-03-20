"""
Analizador NDMI - Normalized Difference Moisture Index
Interpreta contenido de humedad en vegetación
"""
import statistics
from typing import Dict, List, Any


class AnalizadorNDMI:
    """
    Analiza datos de NDMI para evaluar estado hídrico de la vegetación
    
    Umbrales NDMI (alineados con la infografía de interpretación):
    - < -0.2: Estrés hídrico fuerte (ROJO)
    - -0.2 a 0.0: Baja humedad (NARANJA)
    - 0.0 a 0.2: Estrés leve / humedad limitada (AMARILLO)
    - 0.2 a 0.4: Humedad adecuada (VERDE CLARO)
    - 0.4 a 0.8: Buena humedad (VERDE)
    """
    
    # Umbrales alineados con la infografía que ve el agricultor
    UMBRAL_ESTRES_SEVERO = -0.2    # < -0.2 = Estrés hídrico fuerte
    UMBRAL_BAJA_HUMEDAD = 0.0      # -0.2 a 0.0 = Baja humedad
    UMBRAL_ESTRES_LEVE = 0.2       # 0.0 a 0.2 = Estrés leve
    UMBRAL_HUMEDAD_ADECUADA = 0.4  # 0.2 a 0.4 = Humedad adecuada
    UMBRAL_BUENA_HUMEDAD = 0.8     # 0.4 a 0.8 = Buena humedad
    
    def __init__(self, tipo_cultivo: str = "General"):
        self.tipo_cultivo = tipo_cultivo
    
    def analizar(self, datos_ndmi: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza serie temporal de NDMI"""
        if not datos_ndmi:
            return self._resultado_sin_datos()
        
        valores = [d.get('ndmi', 0) for d in datos_ndmi if d.get('ndmi') is not None]
        
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
        alertas = self._generar_alertas(promedio, minimo, tendencia, valores)
        
        # Interpretaciones
        interpretacion_tecnica = self._generar_interpretacion_tecnica(
            promedio, desv_std, tendencia, estado, minimo, maximo
        )
        
        interpretacion_simple = self._generar_interpretacion_simple(
            promedio, tendencia, estado
        )
        
        return {
            'indice': 'NDMI',
            'nombre': 'Índice de Humedad Normalizado',
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
            'riesgo_hidrico': self._evaluar_riesgo_hidrico(promedio, minimo)
        }
    
    def _calcular_tendencia(self, valores: List[float]) -> Dict[str, Any]:
        """Calcula tendencia temporal"""
        if len(valores) < 3:
            return {'direccion': 'estable', 'magnitud': 0, 'descripcion': 'Datos insuficientes'}
        
        n = len(valores)
        cambio_promedio = sum(valores[i] - valores[i-1] for i in range(1, n)) / (n - 1)
        cambio_porcentual = (valores[-1] - valores[0]) / abs(valores[0]) * 100 if valores[0] != 0 else 0
        
        if abs(cambio_promedio) < 0.02:
            direccion = 'estable'
            descripcion = 'Humedad estable'
        elif cambio_promedio > 0.05:
            direccion = 'ascendente_fuerte'
            descripcion = 'Aumento significativo de humedad'
        elif cambio_promedio > 0:
            direccion = 'ascendente'
            descripcion = 'Humedad en aumento'
        elif cambio_promedio < -0.05:
            direccion = 'descendente_fuerte'
            descripcion = 'Pérdida significativa de humedad'
        else:
            direccion = 'descendente'
            descripcion = 'Humedad en descenso'
        
        return {
            'direccion': direccion,
            'magnitud': round(cambio_promedio, 3),
            'cambio_porcentual': round(cambio_porcentual, 1),
            'descripcion': descripcion
        }
    
    def _clasificar_estado(self, promedio: float) -> Dict[str, str]:
        """Clasifica estado hídrico - alineado con la infografía de índices"""
        if promedio < self.UMBRAL_ESTRES_SEVERO:
            return {
                'nivel': 'critico',
                'etiqueta': 'Estrés Hídrico Fuerte',
                'color': '#dc3545',
                'icono': ''
            }
        elif promedio < self.UMBRAL_BAJA_HUMEDAD:
            return {
                'nivel': 'bajo',
                'etiqueta': 'Baja Humedad',
                'color': '#fd7e14',
                'icono': ''
            }
        elif promedio < self.UMBRAL_ESTRES_LEVE:
            return {
                'nivel': 'moderado',
                'etiqueta': 'Estrés Leve (Humedad Limitada)',
                'color': '#ffc107',
                'icono': ''
            }
        elif promedio < self.UMBRAL_HUMEDAD_ADECUADA:
            return {
                'nivel': 'bueno',
                'etiqueta': 'Humedad Adecuada',
                'color': '#28a745',
                'icono': ''
            }
        elif promedio < self.UMBRAL_BUENA_HUMEDAD:
            return {
                'nivel': 'muy_bueno',
                'etiqueta': 'Buena Humedad',
                'color': '#17a2b8',
                'icono': ''
            }
        else:
            return {
                'nivel': 'saturacion',
                'etiqueta': 'Humedad Muy Alta',
                'color': '#6c757d',
                'icono': ''
            }
    
    def _generar_interpretacion_tecnica(self, promedio: float, desv_std: float,
                                       tendencia: Dict, estado: Dict,
                                       minimo: float, maximo: float) -> str:
        """Interpretación técnica"""
        # Describir variabilidad en lenguaje claro
        if desv_std < 0.05:
            variabilidad_desc = "La humedad es muy pareja en toda la parcela."
        elif desv_std < 0.10:
            variabilidad_desc = "La humedad es bastante uniforme, con diferencias menores entre zonas."
        elif desv_std < 0.15:
            variabilidad_desc = "Hay algunas zonas con más humedad que otras dentro de la parcela."
        else:
            variabilidad_desc = "La humedad varía bastante entre diferentes zonas de la parcela."
        
        # Describir rango en lenguaje claro
        rango = maximo - minimo
        if rango < 0.1:
            rango_desc = "Los niveles de humedad fueron muy estables durante todo el período."
        elif rango < 0.25:
            rango_desc = "Hubo variaciones moderadas de humedad entre los meses analizados."
        else:
            rango_desc = "Hubo cambios importantes en la humedad entre los mejores y peores meses."
        
        interpretacion = f"""
<strong>Análisis NDMI - Contenido de Humedad</strong><br><br>

El NDMI promedio de <strong>{promedio:.3f}</strong> indica un estado <strong>{estado['etiqueta'].lower()}</strong> 
del contenido de agua en la vegetación. Este valor es el promedio de todo el período analizado.<br><br>

<strong>Estado del Agua:</strong><br>
• <strong>Estado hídrico: {self._interpretar_estado_hidrico(promedio)}</strong> - Nivel general de agua disponible para las plantas.<br>
• <strong>Rango en el período: {minimo:.3f} a {maximo:.3f}</strong> - {rango_desc}<br>
• <strong>Uniformidad:</strong> {variabilidad_desc}<br><br>

<strong>Tendencia Temporal:</strong><br>
{tendencia['descripcion']}. 
{self._interpretar_tendencia_tecnica(tendencia, promedio)}<br><br>

<strong>Recomendación Hídrica:</strong><br>
{self._generar_recomendacion_tecnica(promedio, tendencia)}
"""
        return interpretacion.strip()
    
    def _generar_interpretacion_simple(self, promedio: float, tendencia: Dict, estado: Dict) -> str:
        """Interpretación simple - coherente con el estado real"""
        # CLAVE: La explicación simple debe ser COHERENTE con el estado hídrico real
        nivel = estado.get('nivel', '')
        
        interpretacion = f"""
<strong>¿Tienen agua suficiente mis plantas?</strong><br><br>

El contenido de agua en sus plantas es <strong>{estado['etiqueta'].lower()}</strong>. 
{self._explicar_simple(promedio)}<br><br>

<strong>Tendencia:</strong><br>
{self._explicar_tendencia_simple(tendencia, promedio)}
"""
        return interpretacion.strip()
    
    def _generar_alertas(self, promedio: float, minimo: float, 
                        tendencia: Dict, valores: List[float]) -> List[Dict]:
        """Genera alertas hídricas"""
        alertas = []
        
        # Alerta solo si hay estrés real (baja humedad o peor, según infografía)
        if promedio < self.UMBRAL_BAJA_HUMEDAD:
            alertas.append({
                'tipo': 'critico' if promedio < self.UMBRAL_ESTRES_SEVERO else 'advertencia',
                'prioridad': 'alta',
                'icono': '',
                'titulo': 'Baja Humedad Detectada',
                'mensaje': f'NDMI promedio ({promedio:.3f}) indica humedad insuficiente para las plantas.',
                'accion': 'Aumentar frecuencia/volumen de riego'
            })
        
        # Tendencia descendente
        if tendencia['direccion'] in ['descendente', 'descendente_fuerte']:
            alertas.append({
                'tipo': 'advertencia',
                'prioridad': 'alta',
                'icono': '',
                'titulo': 'Pérdida de Humedad',
                'mensaje': f"El contenido de humedad ha bajado {abs(tendencia['cambio_porcentual']):.1f}%.",
                'accion': 'Monitorear y ajustar plan de riego'
            })
        
        # Saturación
        if promedio > self.UMBRAL_BUENA_HUMEDAD:
            alertas.append({
                'tipo': 'info',
                'prioridad': 'media',
                'icono': '',
                'titulo': 'Humedad Muy Alta',
                'mensaje': f'NDMI muy alto ({promedio:.3f}). Posible exceso hídrico o período lluvioso.',
                'accion': 'Verificar drenaje, evitar riego excesivo'
            })
        
        return alertas
    
    # Métodos auxiliares
    
    def _resultado_sin_datos(self) -> Dict:
        """Resultado cuando no hay datos"""
        return {
            'indice': 'NDMI',
            'nombre': 'Índice de Humedad Normalizado',
            'error': 'No hay datos disponibles',
            'estadisticas': {},
            'estado': {'nivel': 'sin_datos', 'etiqueta': 'Sin Datos', 'icono': ''},
            'interpretacion_tecnica': 'No hay datos NDMI disponibles.',
            'interpretacion_simple': 'Aún no tenemos información sobre humedad.',
            'alertas': []
        }
    
    def _interpretar_estado_hidrico(self, ndmi: float) -> str:
        """Interpretación del estado hídrico - alineada con infografía"""
        if ndmi < self.UMBRAL_ESTRES_SEVERO:
            return "Estrés hídrico fuerte"
        elif ndmi < self.UMBRAL_BAJA_HUMEDAD:
            return "Baja humedad"
        elif ndmi < self.UMBRAL_ESTRES_LEVE:
            return "Estrés leve (humedad limitada)"
        elif ndmi < self.UMBRAL_HUMEDAD_ADECUADA:
            return "Humedad adecuada"
        else:
            return "Buena humedad"
    
    def _interpretar_tendencia_tecnica(self, tendencia: Dict, promedio: float) -> str:
        """Interpretación técnica de tendencia"""
        if 'descendente' in tendencia['direccion']:
            return "Indica consumo hídrico activo o déficit progresivo. Evaluar evapotranspiración y ajustar riego."
        elif 'ascendente' in tendencia['direccion']:
            return "Asociado a precipitación o incremento en frecuencia de riego. Verificar balance hídrico."
        else:
            return "Estabilidad en contenido hídrico, acorde con manejo actual."
    
    def _generar_recomendacion_tecnica(self, promedio: float, tendencia: Dict) -> str:
        """Recomendación técnica de manejo - alineada con infografía"""
        if promedio < self.UMBRAL_ESTRES_SEVERO:
            return "Estrés hídrico fuerte detectado. Aumentar riego de forma urgente y verificar el sistema de suministro de agua."
        elif promedio < self.UMBRAL_BAJA_HUMEDAD:
            return "Humedad baja. Aumentar lámina de riego en 20-30%. Considerar riego más frecuente."
        elif promedio < self.UMBRAL_ESTRES_LEVE:
            if 'descendente' in tendencia['direccion']:
                return "Humedad limitada con tendencia a la baja. Monitorear de cerca y preparar plan de riego adicional."
            else:
                return "Humedad limitada pero estable. Monitorear evolución y considerar incrementar riego si el cultivo lo requiere."
        elif promedio < self.UMBRAL_HUMEDAD_ADECUADA:
            return "Humedad adecuada. Mantener régimen hídrico actual."
        else:
            return "Buena humedad. Si es muy alta, verificar drenaje para evitar exceso."
    
    def _explicar_simple(self, promedio: float) -> str:
        """Explicación simple - alineada con infografía"""
        if promedio < self.UMBRAL_ESTRES_SEVERO:
            return "Sus plantas están sufriendo por falta de agua. Necesitan riego urgente."
        elif promedio < self.UMBRAL_BAJA_HUMEDAD:
            return "La humedad está baja. Sus plantas necesitan más agua de la que están recibiendo."
        elif promedio < self.UMBRAL_ESTRES_LEVE:
            return "La humedad es limitada pero no crítica. Las plantas tienen algo de agua, aunque podrían necesitar más. Mantenga vigilancia."
        elif promedio < self.UMBRAL_HUMEDAD_ADECUADA:
            return "La humedad es adecuada. Sus plantas tienen el agua que necesitan para desarrollarse bien."
        else:
            return "Hay buena humedad disponible. Las condiciones de agua son muy favorables para sus plantas."
    
    def _explicar_tendencia_simple(self, tendencia: Dict, promedio: float) -> str:
        """Explicación simple de tendencia - coherente con el estado hídrico real"""
        if 'descendente' in tendencia['direccion']:
            return f"El agua está bajando ({abs(tendencia['cambio_porcentual']):.0f}% menos). Sus plantas están usando el agua o no están recibiendo suficiente. Momento de regar más."
        elif 'ascendente' in tendencia['direccion']:
            return f"El agua está subiendo ({tendencia['cambio_porcentual']:.0f}% más). Buena señal, las plantas están recibiendo agua de lluvia o riego."
        else:
            # Coherente con el estado real
            if promedio < self.UMBRAL_BAJA_HUMEDAD:
                return "El nivel de agua se ha mantenido bajo de forma constante durante el período. Es necesario revisar el riego."
            elif promedio < self.UMBRAL_ESTRES_LEVE:
                return "El nivel de agua se mantiene estable pero limitado. Monitoree el riego para evitar que baje más."
            else:
                return "El nivel de agua se mantiene estable durante el período analizado. Las condiciones son adecuadas."
    
    def _evaluar_riesgo_hidrico(self, promedio: float, minimo: float) -> str:
        """Evalúa riesgo hídrico - alineado con infografía"""
        if minimo < self.UMBRAL_ESTRES_SEVERO:
            return "Alto"
        elif promedio < self.UMBRAL_BAJA_HUMEDAD:
            return "Medio-Alto"
        elif promedio < self.UMBRAL_ESTRES_LEVE:
            return "Medio"
        elif promedio < self.UMBRAL_HUMEDAD_ADECUADA:
            return "Bajo"
        else:
            return "Muy Bajo"
    
    def _calcular_puntuacion(self, promedio: float, tendencia: Dict) -> float:
        """Calcula puntuación 0-10"""
        # Normalizar NDMI (-1 a 1) a escala 0-10
        # Óptimo es 0.3, penalizar extremos
        if promedio < 0:
            puntuacion_base = max(0, (promedio + 1) * 5)  # -1=0, 0=5
        else:
            if promedio <= 0.4:
                puntuacion_base = 5 + (promedio / 0.4) * 5  # 0=5, 0.4=10
            else:
                puntuacion_base = 10 - (promedio - 0.4) * 5  # >0.4 baja de 10
        
        # Ajuste por tendencia
        if 'descendente' in tendencia['direccion'] and promedio < 0.2:
            puntuacion_base -= 1
        
        return round(max(0, min(10, puntuacion_base)), 1)
