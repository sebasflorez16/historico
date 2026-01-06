"""
Servicio para procesamiento y análisis de datos satelitales
Calcula promedios mensuales, tendencias y análisis IA local
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
import pandas as pd
import numpy as np
from ..models import Parcela, IndiceMensual, Informe
from .eosda_api import eosda_service

logger = logging.getLogger(__name__)


class AnalisisSatelitalService:
    """
    Servicio para procesar y analizar datos satelitales obtenidos de EOSDA
    """
    
    def __init__(self):
        pass
    
    def procesar_datos_mensuales(self, parcela: Parcela, 
                                fecha_inicio: date = None, 
                                fecha_fin: date = None) -> Dict:
        """
        Procesa y guarda los datos mensuales de una parcela
        """
        try:
            # Establecer fechas por defecto si no se proporcionan
            if not fecha_fin:
                fecha_fin = date.today()
            if not fecha_inicio:
                fecha_inicio = fecha_fin - timedelta(days=365)  # Último año
            
            logger.info(f"Procesando datos mensuales para {parcela.nombre} "
                       f"desde {fecha_inicio} hasta {fecha_fin}")
            
            # Obtener datos de EOSDA
            datos_satelitales = eosda_service.obtener_datos_parcela(
                parcela, fecha_inicio, fecha_fin
            )
            
            if not datos_satelitales:
                raise ValueError("No se pudieron obtener datos satelitales")
            
            # Procesar datos por mes
            resultados = self._procesar_por_meses(parcela, datos_satelitales)
            
            logger.info(f"Procesamiento completado para {parcela.nombre}. "
                       f"Meses procesados: {len(resultados['meses_procesados'])}")
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error procesando datos mensuales: {str(e)}")
            return {'error': str(e), 'meses_procesados': []}
    
    def _procesar_por_meses(self, parcela: Parcela, datos_satelitales: Dict) -> Dict:
        """
        Procesa los datos satelitales agrupándolos por mes y guardándolos en BD
        """
        meses_procesados = []
        
        try:
            # Convertir datos a DataFrames para facilitar el procesamiento
            df_ndvi = self._datos_a_dataframe(datos_satelitales.get('ndvi', []))
            df_ndmi = self._datos_a_dataframe(datos_satelitales.get('ndmi', []))
            df_savi = self._datos_a_dataframe(datos_satelitales.get('savi', []))
            df_clima = self._datos_a_dataframe(datos_satelitales.get('datos_clima', []))
            
            # Obtener todos los meses únicos
            fechas_unicas = set()
            for df in [df_ndvi, df_ndmi, df_savi, df_clima]:
                if not df.empty:
                    fechas_unicas.update(df['fecha'].dt.to_period('M').unique())
            
            # Procesar cada mes
            for periodo_mensual in sorted(fechas_unicas):
                año = periodo_mensual.year
                mes = periodo_mensual.month
                
                try:
                    with transaction.atomic():
                        # Obtener o crear registro mensual
                        indice_mensual, created = IndiceMensual.objects.get_or_create(
                            parcela=parcela,
                            año=año,
                            mes=mes,
                            defaults={}
                        )
                        
                        # Procesar NDVI para este mes
                        ndvi_mes = self._calcular_estadisticas_mensuales(
                            df_ndvi, año, mes
                        )
                        if ndvi_mes:
                            indice_mensual.ndvi_promedio = ndvi_mes['promedio']
                            indice_mensual.ndvi_maximo = ndvi_mes['maximo']
                            indice_mensual.ndvi_minimo = ndvi_mes['minimo']
                            indice_mensual.nubosidad_promedio = ndvi_mes.get('nubosidad_promedio')
                        
                        # Procesar NDMI para este mes
                        ndmi_mes = self._calcular_estadisticas_mensuales(
                            df_ndmi, año, mes
                        )
                        if ndmi_mes:
                            indice_mensual.ndmi_promedio = ndmi_mes['promedio']
                            indice_mensual.ndmi_maximo = ndmi_mes['maximo']
                            indice_mensual.ndmi_minimo = ndmi_mes['minimo']
                        
                        # Procesar SAVI para este mes
                        savi_mes = self._calcular_estadisticas_mensuales(
                            df_savi, año, mes
                        )
                        if savi_mes:
                            indice_mensual.savi_promedio = savi_mes['promedio']
                            indice_mensual.savi_maximo = savi_mes['maximo']
                            indice_mensual.savi_minimo = savi_mes['minimo']
                        
                        # Procesar datos climáticos para este mes
                        clima_mes = self._calcular_climaticos_mensuales(
                            df_clima, año, mes
                        )
                        if clima_mes:
                            indice_mensual.temperatura_promedio = clima_mes.get('temperatura_promedio')
                            indice_mensual.temperatura_maxima = clima_mes.get('temperatura_maxima')
                            indice_mensual.temperatura_minima = clima_mes.get('temperatura_minima')
                            indice_mensual.precipitacion_total = clima_mes.get('precipitacion_total')
                        
                        # Determinar calidad de datos
                        indice_mensual.calidad_datos = self._evaluar_calidad_datos(
                            indice_mensual
                        )
                        
                        # Guardar
                        indice_mensual.save()
                        
                        meses_procesados.append({
                            'año': año,
                            'mes': mes,
                            'created': created,
                            'ndvi': indice_mensual.ndvi_promedio,
                            'ndmi': indice_mensual.ndmi_promedio,
                            'savi': indice_mensual.savi_promedio
                        })
                
                except Exception as e:
                    logger.error(f"Error procesando mes {mes}/{año}: {str(e)}")
                    continue
            
            return {
                'meses_procesados': meses_procesados,
                'total_meses': len(meses_procesados),
                'simulado': datos_satelitales.get('simulado', False)
            }
            
        except Exception as e:
            logger.error(f"Error en procesamiento por meses: {str(e)}")
            return {'meses_procesados': [], 'error': str(e)}
    
    def _datos_a_dataframe(self, datos: List[Dict]) -> pd.DataFrame:
        """
        Convierte lista de datos a DataFrame de pandas
        """
        if not datos:
            return pd.DataFrame()
        
        try:
            df = pd.DataFrame(datos)
            if 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])
            return df
        except Exception as e:
            logger.error(f"Error convirtiendo datos a DataFrame: {str(e)}")
            return pd.DataFrame()
    
    def _calcular_estadisticas_mensuales(self, df: pd.DataFrame, año: int, mes: int) -> Optional[Dict]:
        """
        Calcula estadísticas mensuales para un índice específico
        """
        if df.empty:
            return None
        
        try:
            # Filtrar por año y mes
            filtro_mes = (df['fecha'].dt.year == año) & (df['fecha'].dt.month == mes)
            df_mes = df[filtro_mes]
            
            if df_mes.empty:
                return None
            
            estadisticas = {
                'promedio': df_mes['promedio'].mean() if 'promedio' in df_mes.columns else None,
                'maximo': df_mes['maximo'].max() if 'maximo' in df_mes.columns else None,
                'minimo': df_mes['minimo'].min() if 'minimo' in df_mes.columns else None,
            }
            
            # Nubosidad si está disponible
            if 'nubosidad' in df_mes.columns:
                estadisticas['nubosidad_promedio'] = df_mes['nubosidad'].mean()
            
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas mensuales: {str(e)}")
            return None
    
    def _calcular_climaticos_mensuales(self, df: pd.DataFrame, año: int, mes: int) -> Optional[Dict]:
        """
        Calcula estadísticas climáticas mensuales
        """
        if df.empty:
            return None
        
        try:
            # Filtrar por año y mes
            filtro_mes = (df['fecha'].dt.year == año) & (df['fecha'].dt.month == mes)
            df_mes = df[filtro_mes]
            
            if df_mes.empty:
                return None
            
            estadisticas = {}
            
            # Temperaturas
            if 'temperatura_promedio' in df_mes.columns:
                estadisticas['temperatura_promedio'] = df_mes['temperatura_promedio'].mean()
            if 'temperatura_maxima' in df_mes.columns:
                estadisticas['temperatura_maxima'] = df_mes['temperatura_maxima'].max()
            if 'temperatura_minima' in df_mes.columns:
                estadisticas['temperatura_minima'] = df_mes['temperatura_minima'].min()
            
            # Precipitación total
            if 'precipitacion_total' in df_mes.columns:
                estadisticas['precipitacion_total'] = df_mes['precipitacion_total'].sum()
            
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error calculando datos climáticos mensuales: {str(e)}")
            return None
    
    def _evaluar_calidad_datos(self, indice_mensual) -> str:
        """
        Evalúa la calidad de los datos basándose en la completitud
        """
        campos_principales = [
            indice_mensual.ndvi_promedio,
            indice_mensual.ndmi_promedio,
            indice_mensual.savi_promedio
        ]
        
        campos_completos = sum(1 for campo in campos_principales if campo is not None)
        
        if campos_completos == 3:
            return 'excelente'
        elif campos_completos >= 2:
            return 'buena'
        elif campos_completos >= 1:
            return 'regular'
        else:
            return 'pobre'
    
    def calcular_tendencias_parcela(self, parcela: Parcela, 
                                   meses_analisis: int = 12) -> Dict:
        """
        Calcula las tendencias de los índices de una parcela
        """
        try:
            # Obtener datos de los últimos N meses
            fecha_limite = timezone.now().date() - timedelta(days=meses_analisis * 30)
            
            indices = IndiceMensual.objects.filter(
                parcela=parcela,
                fecha_consulta_api__date__gte=fecha_limite
            ).order_by('año', 'mes')
            
            if not indices.exists():
                return {'error': 'No hay datos suficientes para calcular tendencias'}
            
            # Convertir a DataFrame
            data = []
            for indice in indices:
                data.append({
                    'fecha': date(indice.año, indice.mes, 1),
                    'ndvi': indice.ndvi_promedio,
                    'ndmi': indice.ndmi_promedio,
                    'savi': indice.savi_promedio,
                    'temperatura': indice.temperatura_promedio
                })
            
            df = pd.DataFrame(data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Calcular tendencias usando regresión lineal
            tendencias = {}
            
            for columna in ['ndvi', 'ndmi', 'savi', 'temperatura']:
                if df[columna].notna().any():
                    tendencia = self._calcular_tendencia_lineal(
                        df['fecha'], df[columna]
                    )
                    tendencias[columna] = tendencia
            
            # Calcular estadísticas generales
            estadisticas = {
                'periodo_analizado': f"{meses_analisis} meses",
                'total_registros': len(df),
                'fecha_inicio': df['fecha'].min().strftime('%Y-%m-%d'),
                'fecha_fin': df['fecha'].max().strftime('%Y-%m-%d'),
                'promedios': {
                    'ndvi': df['ndvi'].mean() if df['ndvi'].notna().any() else None,
                    'ndmi': df['ndmi'].mean() if df['ndmi'].notna().any() else None,
                    'savi': df['savi'].mean() if df['savi'].notna().any() else None,
                    'temperatura': df['temperatura'].mean() if df['temperatura'].notna().any() else None,
                }
            }
            
            return {
                'tendencias': tendencias,
                'estadisticas': estadisticas,
                'datos_disponibles': True
            }
            
        except Exception as e:
            logger.error(f"Error calculando tendencias: {str(e)}")
            return {'error': str(e), 'datos_disponibles': False}
    
    def _calcular_tendencia_lineal(self, fechas: pd.Series, valores: pd.Series) -> Dict:
        """
        Calcula la tendencia lineal de una serie temporal
        """
        try:
            # Filtrar valores no nulos
            mask = valores.notna()
            x = fechas[mask]
            y = valores[mask]
            
            if len(x) < 2:
                return {'tendencia': 'sin_datos', 'pendiente': 0, 'significancia': 'baja'}
            
            # Convertir fechas a números para regresión
            x_num = (x - x.min()).dt.days.values
            y_values = y.values
            
            # Regresión lineal
            coeficientes = np.polyfit(x_num, y_values, 1)
            pendiente = coeficientes[0]
            
            # Determinar tipo de tendencia
            if abs(pendiente) < 0.001:
                tendencia = 'estable'
            elif pendiente > 0:
                tendencia = 'creciente'
            else:
                tendencia = 'decreciente'
            
            # Calcular R² para significancia
            y_pred = np.polyval(coeficientes, x_num)
            r_squared = 1 - (np.sum((y_values - y_pred) ** 2) / 
                           np.sum((y_values - np.mean(y_values)) ** 2))
            
            if r_squared > 0.7:
                significancia = 'alta'
            elif r_squared > 0.3:
                significancia = 'media'
            else:
                significancia = 'baja'
            
            return {
                'tendencia': tendencia,
                'pendiente': float(pendiente),
                'r_squared': float(r_squared),
                'significancia': significancia
            }
            
        except Exception as e:
            logger.error(f"Error calculando tendencia lineal: {str(e)}")
            return {'tendencia': 'error', 'pendiente': 0, 'significancia': 'baja'}


# Instancia global del servicio
analisis_service = AnalisisSatelitalService()