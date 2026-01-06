"""
Servicio para generar informes PDF automáticos con análisis satelital
Incluye gráficos, mapas y análisis IA local
"""

import io
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Agg')  # Usar backend sin interfaz gráfica
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import folium
from folium import plugins
import base64
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas

from ..models import Parcela, IndiceMensual, Informe

logger = logging.getLogger(__name__)


class GeneradorInformePDF:
    """
    Servicio para generar informes PDF con análisis satelital completo
    """
    
    def __init__(self):
        # Configurar estilo de matplotlib para gráficos profesionales
        plt.style.use('default')
        plt.rcParams.update({
            'font.size': 10,
            'axes.titlesize': 12,
            'axes.labelsize': 10,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.titlesize': 14,
            'figure.dpi': 300,
            'savefig.dpi': 300,
            'savefig.bbox': 'tight'
        })
    
    def generar_informe_optimizado(self, parcela: Parcela, usuario,
                                  periodo_meses: int = 12, 
                                  configuracion=None) -> Dict:
        """
        Genera informe usando el método optimizado de EOSDA con caché y tracking.
        
        Este método reemplaza la obtención manual de datos con una llamada
        optimizada que:
        - Consulta caché primero (0 requests si existe)
        - Hace 1 sola petición para todos los índices
        - Registra estadísticas de uso
        
        Args:
            parcela: Parcela para generar informe
            usuario: Usuario que solicita el informe
            periodo_meses: Meses de análisis
            configuracion: ConfiguracionReporte opcional
            
        Returns:
            Dict con success, informe_id, archivo_pdf, analisis_ia
        """
        from .eosda_api import eosda_service
        from ..models import ConfiguracionReporte
        
        try:
            logger.info(f"🚀 Generando informe OPTIMIZADO para {parcela.nombre}")
            
            # Verificar sincronización
            if not parcela.puede_obtener_datos_eosda:
                raise ValueError(f"Parcela no sincronizada con EOSDA. field_id: {parcela.eosda_field_id}")
            
            # Obtener configuración si existe
            if not configuracion:
                try:
                    configuracion = ConfiguracionReporte.objects.get(
                        usuario=usuario,
                        parcela=parcela
                    )
                except ConfiguracionReporte.DoesNotExist:
                    # Usar configuración por defecto
                    logger.info("Usando configuración por defecto")
            
            # Calcular fechas
            fecha_fin = date.today()
            fecha_inicio = fecha_fin - timedelta(days=periodo_meses * 30)
            
            # Determinar índices a solicitar
            indices = ['ndvi']  # NDVI siempre incluido
            if configuracion:
                if configuracion.incluir_ndmi:
                    indices.append('ndmi')
                if configuracion.incluir_savi:
                    indices.append('savi')
            else:
                # Por defecto, todos los índices
                indices = ['ndvi', 'ndmi', 'savi']
            
            logger.info(f"📊 Solicitando índices: {', '.join(indices)}")
            
            # ✨ MÉTODO OPTIMIZADO: 1 sola petición, caché inteligente
            datos_eosda = eosda_service.obtener_datos_optimizado(
                field_id=parcela.eosda_field_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                indices=indices,
                usuario=usuario,
                parcela=parcela,
                max_nubosidad=50
            )
            
            if 'error' in datos_eosda or not datos_eosda.get('resultados'):
                raise ValueError(f"Error obteniendo datos de EOSDA: {datos_eosda.get('error', 'Sin datos')}")
            
            # Procesar resultados
            resultados = datos_eosda['resultados']
            logger.info(f"✅ Obtenidos {len(resultados)} escenas satelitales")
            
            # Convertir datos de EOSDA a formato para análisis
            datos_procesados = self._procesar_datos_eosda(resultados, indices)
            
            # Crear análisis IA con los datos obtenidos
            analisis_ia = self._generar_analisis_ia_local(datos_procesados)
            
            # Generar componentes visuales
            grafico_tendencias = self._generar_grafico_tendencias_eosda(datos_procesados)
            mapa_ndvi = self._generar_mapa_parcela(parcela, datos_procesados.get('ultimo_dato'))
            
            # Generar PDF
            archivo_pdf = self._crear_pdf_informe(
                parcela=parcela,
                periodo_meses=periodo_meses,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                datos_analisis=datos_procesados,
                grafico_tendencias=grafico_tendencias,
                mapa_ndvi=mapa_ndvi,
                analisis_ia=analisis_ia
            )
            
            # Crear registro de informe
            informe = Informe.objects.create(
                parcela=parcela,
                periodo_analisis_meses=periodo_meses,
                fecha_inicio_analisis=fecha_inicio,
                fecha_fin_analisis=fecha_fin,
                titulo=f"Análisis Satelital Optimizado - {parcela.nombre}",
                resumen_ejecutivo=analisis_ia['resumen_ejecutivo'],
                analisis_tendencias=analisis_ia['analisis_tendencias'],
                conclusiones_ia=analisis_ia['conclusiones'],
                recomendaciones=analisis_ia['recomendaciones'],
                archivo_pdf=archivo_pdf,
                grafico_tendencias=grafico_tendencias,
                mapa_ndvi_imagen=mapa_ndvi,
                ndvi_promedio_periodo=datos_procesados['estadisticas'].get('ndvi_promedio'),
                ndmi_promedio_periodo=datos_procesados['estadisticas'].get('ndmi_promedio'),
                savi_promedio_periodo=datos_procesados['estadisticas'].get('savi_promedio'),
            )
            
            logger.info(f"✅ Informe optimizado generado: ID {informe.id}")
            logger.info(f"📊 Total escenas procesadas: {datos_procesados['estadisticas']['total_escenas']}")
            
            return {
                'success': True,
                'informe_id': informe.id,
                'archivo_pdf': archivo_pdf.url if archivo_pdf else None,
                'analisis_ia': analisis_ia,
                'num_escenas': datos_procesados['estadisticas']['total_escenas'],
                'indices_incluidos': indices
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando informe optimizado: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _procesar_datos_eosda(self, resultados: List[Dict], indices: List[str]) -> Dict:
        """
        Procesa los datos crudos de EOSDA en formato para análisis
        
        Args:
            resultados: Lista de escenas con statistics
            indices: Índices solicitados
            
        Returns:
            Dict con datos_disponibles, series temporales, estadísticas
        """
        try:
            if not resultados:
                return {'datos_disponibles': False}
            
            # Inicializar series temporales
            series = {indice: [] for indice in indices}
            fechas = []
            
            # Procesar cada escena
            for escena in resultados:
                fecha_str = escena.get('date')
                if not fecha_str:
                    continue
                
                # Parsear fecha
                fecha = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                fechas.append(fecha)
                
                # Extraer estadísticas de cada índice
                stats = escena.get('statistics', {})
                for indice in indices:
                    indice_data = stats.get(indice, {})
                    mean_value = indice_data.get('mean')
                    
                    series[indice].append({
                        'fecha': fecha,
                        'valor': mean_value,
                        'std': indice_data.get('std'),
                        'min': indice_data.get('min'),
                        'max': indice_data.get('max'),
                        'pixels_analizados': indice_data.get('pixels_analyzed', 0)
                    })
            
            # Calcular estadísticas globales
            estadisticas = {}
            for indice in indices:
                valores = [d['valor'] for d in series[indice] if d['valor'] is not None]
                if valores:
                    estadisticas[f'{indice}_promedio'] = sum(valores) / len(valores)
                    estadisticas[f'{indice}_maximo'] = max(valores)
                    estadisticas[f'{indice}_minimo'] = min(valores)
                else:
                    estadisticas[f'{indice}_promedio'] = None
                    estadisticas[f'{indice}_maximo'] = None
                    estadisticas[f'{indice}_minimo'] = None
            
            estadisticas['total_escenas'] = len(resultados)
            estadisticas['total_registros'] = len(fechas)
            
            return {
                'datos_disponibles': True,
                'series': series,
                'fechas': fechas,
                'ultimo_dato': series.get('ndvi', [{}])[-1] if series.get('ndvi') else None,
                'estadisticas': estadisticas,
                'periodo': {
                    'inicio': min(fechas) if fechas else None,
                    'fin': max(fechas) if fechas else None,
                    'total_dias': (max(fechas) - min(fechas)).days if fechas else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando datos EOSDA: {str(e)}")
            return {'datos_disponibles': False}
    
    def _generar_grafico_tendencias_eosda(self, datos: Dict) -> Optional[ContentFile]:
        """
        Genera gráfico de tendencias a partir de datos procesados de EOSDA
        """
        try:
            if not datos.get('datos_disponibles'):
                return None
            
            series = datos['series']
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Colores para cada índice
            colores = {
                'ndvi': '#4CAF50',
                'ndmi': '#2196F3',
                'savi': '#FF9800'
            }
            
            # Graficar cada índice
            for indice, datos_serie in series.items():
                if not datos_serie:
                    continue
                
                fechas = [d['fecha'] for d in datos_serie if d['valor'] is not None]
                valores = [d['valor'] for d in datos_serie if d['valor'] is not None]
                
                if fechas and valores:
                    ax.plot(fechas, valores, 
                           marker='o', 
                           markersize=4,
                           linewidth=2,
                           label=indice.upper(),
                           color=colores.get(indice, '#333'))
            
            # Configurar ejes
            ax.set_xlabel('Fecha', fontsize=12, fontweight='bold')
            ax.set_ylabel('Valor del Índice', fontsize=12, fontweight='bold')
            ax.set_title('Evolución de Índices Vegetativos', fontsize=14, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
            # Formato de fechas
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            
            # Ajustar layout
            plt.tight_layout()
            
            # Guardar en memoria
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            # Guardar como ContentFile
            filename = f"grafico_tendencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            return ContentFile(buffer.read(), name=filename)
            
        except Exception as e:
            logger.error(f"Error generando gráfico: {str(e)}")
            return None
    
    def generar_informe_completo(self, parcela: Parcela, 
                                periodo_meses: int = 12) -> Dict:
        """
        Genera un informe PDF completo para una parcela específica
        """
        try:
            logger.info(f"Iniciando generación de informe para {parcela.nombre}")
            
            # Calcular fechas del período
            fecha_fin = date.today()
            fecha_inicio = fecha_fin - timedelta(days=periodo_meses * 30)
            
            # Obtener datos para el informe
            datos_analisis = self._recopilar_datos_analisis(
                parcela, fecha_inicio, fecha_fin
            )
            
            if not datos_analisis['datos_disponibles']:
                raise ValueError("No hay datos suficientes para generar el informe")
            
            # Generar componentes del informe
            grafico_tendencias = self._generar_grafico_tendencias(datos_analisis['indices'])
            mapa_ndvi = self._generar_mapa_parcela(parcela, datos_analisis['ultimo_indice'])
            
            # Crear análisis IA
            analisis_ia = self._generar_analisis_ia_local(datos_analisis)
            
            # Generar PDF
            archivo_pdf = self._crear_pdf_informe(
                parcela=parcela,
                periodo_meses=periodo_meses,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                datos_analisis=datos_analisis,
                grafico_tendencias=grafico_tendencias,
                mapa_ndvi=mapa_ndvi,
                analisis_ia=analisis_ia
            )
            
            # Crear registro en base de datos
            informe = Informe.objects.create(
                parcela=parcela,
                periodo_analisis_meses=periodo_meses,
                fecha_inicio_analisis=fecha_inicio,
                fecha_fin_analisis=fecha_fin,
                titulo=f"Análisis Satelital - {parcela.nombre} ({periodo_meses} meses)",
                resumen_ejecutivo=analisis_ia['resumen_ejecutivo'],
                analisis_tendencias=analisis_ia['analisis_tendencias'],
                conclusiones_ia=analisis_ia['conclusiones'],
                recomendaciones=analisis_ia['recomendaciones'],
                archivo_pdf=archivo_pdf,
                grafico_tendencias=grafico_tendencias,
                mapa_ndvi_imagen=mapa_ndvi,
                ndvi_promedio_periodo=datos_analisis['estadisticas']['ndvi_promedio'],
                ndmi_promedio_periodo=datos_analisis['estadisticas']['ndmi_promedio'],
                savi_promedio_periodo=datos_analisis['estadisticas']['savi_promedio'],
            )
            
            logger.info(f"Informe generado exitosamente: ID {informe.id}")
            
            return {
                'success': True,
                'informe_id': informe.id,
                'archivo_pdf': archivo_pdf.url if archivo_pdf else None,
                'analisis_ia': analisis_ia
            }
            
        except Exception as e:
            logger.error(f"Error generando informe: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _recopilar_datos_analisis(self, parcela: Parcela, 
                                 fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Recopila todos los datos necesarios para el análisis
        """
        try:
            # Obtener índices mensuales del período
            indices = IndiceMensual.objects.filter(
                parcela=parcela,
                año__gte=fecha_inicio.year,
                año__lte=fecha_fin.year
            ).order_by('año', 'mes')
            
            if not indices.exists():
                return {'datos_disponibles': False}
            
            # Convertir a lista para facilitar el procesamiento
            indices_list = list(indices)
            
            # Calcular estadísticas generales
            ndvi_valores = [i.ndvi_promedio for i in indices_list if i.ndvi_promedio is not None]
            ndmi_valores = [i.ndmi_promedio for i in indices_list if i.ndmi_promedio is not None]
            savi_valores = [i.savi_promedio for i in indices_list if i.savi_promedio is not None]
            temp_valores = [i.temperatura_promedio for i in indices_list if i.temperatura_promedio is not None]
            
            estadisticas = {
                'ndvi_promedio': sum(ndvi_valores) / len(ndvi_valores) if ndvi_valores else None,
                'ndvi_maximo': max(ndvi_valores) if ndvi_valores else None,
                'ndvi_minimo': min(ndvi_valores) if ndvi_valores else None,
                'ndmi_promedio': sum(ndmi_valores) / len(ndmi_valores) if ndmi_valores else None,
                'ndmi_maximo': max(ndmi_valores) if ndmi_valores else None,
                'ndmi_minimo': min(ndmi_valores) if ndmi_valores else None,
                'savi_promedio': sum(savi_valores) / len(savi_valores) if savi_valores else None,
                'temperatura_promedio': sum(temp_valores) / len(temp_valores) if temp_valores else None,
                'total_registros': len(indices_list)
            }
            
            return {
                'datos_disponibles': True,
                'indices': indices_list,
                'ultimo_indice': indices_list[-1] if indices_list else None,
                'estadisticas': estadisticas,
                'periodo': {
                    'inicio': fecha_inicio,
                    'fin': fecha_fin,
                    'meses': len(indices_list)
                }
            }
            
        except Exception as e:
            logger.error(f"Error recopilando datos: {str(e)}")
            return {'datos_disponibles': False, 'error': str(e)}
    
    def _generar_grafico_tendencias(self, indices: List[IndiceMensual]) -> Optional[ContentFile]:
        """
        Genera gráfico de tendencias NDVI, NDMI, SAVI
        """
        try:
            # Preparar datos
            fechas = []
            ndvi_vals = []
            ndmi_vals = []
            savi_vals = []
            
            for indice in indices:
                fecha = datetime(indice.año, indice.mes, 1)
                fechas.append(fecha)
                ndvi_vals.append(indice.ndvi_promedio)
                ndmi_vals.append(indice.ndmi_promedio)
                savi_vals.append(indice.savi_promedio)
            
            # Crear figura
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle('Análisis de Tendencias Satelitales - AgroTech Histórico', 
                        fontsize=16, fontweight='bold', color='#2d5a27')
            
            # Gráfico NDVI
            ax1.plot(fechas, ndvi_vals, 'o-', color='#4a7c59', linewidth=2, markersize=4)
            ax1.set_title('NDVI - Índice de Vegetación', fontweight='bold')
            ax1.set_ylabel('NDVI')
            ax1.grid(True, alpha=0.3)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            
            # Gráfico NDMI
            ax2.plot(fechas, ndmi_vals, 'o-', color='#2c3e50', linewidth=2, markersize=4)
            ax2.set_title('NDMI - Índice de Humedad', fontweight='bold')
            ax2.set_ylabel('NDMI')
            ax2.grid(True, alpha=0.3)
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
            ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            
            # Gráfico SAVI
            ax3.plot(fechas, savi_vals, 'o-', color='#f39c12', linewidth=2, markersize=4)
            ax3.set_title('SAVI - Vegetación Ajustada al Suelo', fontweight='bold')
            ax3.set_ylabel('SAVI')
            ax3.grid(True, alpha=0.3)
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
            ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            
            # Gráfico combinado
            ax4.plot(fechas, ndvi_vals, 'o-', label='NDVI', color='#4a7c59', linewidth=2)
            ax4.plot(fechas, ndmi_vals, 's-', label='NDMI', color='#2c3e50', linewidth=2)
            ax4.plot(fechas, savi_vals, '^-', label='SAVI', color='#f39c12', linewidth=2)
            ax4.set_title('Comparación de Índices', fontweight='bold')
            ax4.set_ylabel('Valor del Índice')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
            ax4.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            
            # Rotar etiquetas de fecha
            for ax in [ax1, ax2, ax3, ax4]:
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # Guardar como archivo
            buffer = BytesIO()
            plt.savefig(buffer, format='PNG', bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            
            # Crear ContentFile
            nombre_archivo = f'grafico_tendencias_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            archivo = ContentFile(buffer.getvalue(), name=nombre_archivo)
            
            plt.close(fig)
            return archivo
            
        except Exception as e:
            logger.error(f"Error generando gráfico: {str(e)}")
            return None
    
    def _generar_mapa_parcela(self, parcela: Parcela, 
                             ultimo_indice: IndiceMensual = None) -> Optional[ContentFile]:
        """
        Genera mapa de la parcela con visualización NDVI
        """
        try:
            centro = parcela.centro_parcela
            if not centro:
                return None
            
            # Crear mapa base
            mapa = folium.Map(
                location=[centro['lat'], centro['lng']],
                zoom_start=15,
                tiles='Esri.WorldImagery'
            )
            
            # Agregar polígono de la parcela
            coordenadas = parcela.coordenadas_dict
            if coordenadas and 'coordinates' in coordenadas:
                coords_folium = []
                for coord in coordenadas['coordinates'][0]:
                    coords_folium.append([coord[1], coord[0]])  # lat, lng para folium
                
                # Color basado en NDVI si está disponible
                if ultimo_indice and ultimo_indice.ndvi_promedio:
                    ndvi = ultimo_indice.ndvi_promedio
                    if ndvi >= 0.7:
                        color = '#2d5a27'  # Verde oscuro - excelente
                    elif ndvi >= 0.5:
                        color = '#4a7c59'  # Verde medio - bueno
                    elif ndvi >= 0.3:
                        color = '#f39c12'  # Amarillo - regular
                    else:
                        color = '#e74c3c'  # Rojo - pobre
                else:
                    color = '#2c3e50'  # Gris por defecto
                
                folium.Polygon(
                    coords_folium,
                    popup=f"<b>{parcela.nombre}</b><br>"
                          f"Propietario: {parcela.propietario}<br>"
                          f"NDVI: {ultimo_indice.ndvi_promedio if ultimo_indice else 'N/A'}",
                    color=color,
                    fillColor=color,
                    fillOpacity=0.4,
                    weight=3
                ).add_to(mapa)
            
            # Agregar marcador central
            folium.Marker(
                [centro['lat'], centro['lng']],
                popup=f"<b>{parcela.nombre}</b>",
                icon=folium.Icon(color='green', icon='leaf')
            ).add_to(mapa)
            
            # Agregar escala y mini mapa
            plugins.MiniMap(toggle_display=True).add_to(mapa)
            
            # Guardar como imagen
            nombre_archivo = f'mapa_parcela_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
            mapa_html = mapa._repr_html_()
            
            # Para efectos del ejemplo, simularemos una imagen del mapa
            # En producción se podría usar selenium para capturar el mapa como imagen
            archivo = ContentFile(
                mapa_html.encode('utf-8'), 
                name=nombre_archivo.replace('.html', '.png')
            )
            
            return archivo
            
        except Exception as e:
            logger.error(f"Error generando mapa: {str(e)}")
            return None
    
    def _generar_analisis_ia_local(self, datos_analisis: Dict) -> Dict:
        """
        Genera análisis IA local basado en los datos satelitales
        """
        try:
            estadisticas = datos_analisis['estadisticas']
            indices = datos_analisis['indices']
            
            # Análisis de tendencias NDVI
            ndvi_valores = [i.ndvi_promedio for i in indices if i.ndvi_promedio]
            tendencia_ndvi = self._analizar_tendencia(ndvi_valores)
            
            # Análisis de salud general
            ndvi_promedio = estadisticas.get('ndvi_promedio', 0)
            if ndvi_promedio >= 0.7:
                salud_general = "excelente"
                interpretacion = "La parcela muestra un estado de salud vegetal excelente con alta densidad de biomasa."
            elif ndvi_promedio >= 0.5:
                salud_general = "buena"
                interpretacion = "La parcela presenta un buen estado de salud vegetal con desarrollo adecuado."
            elif ndvi_promedio >= 0.3:
                salud_general = "regular"
                interpretacion = "La parcela muestra un estado vegetal regular que requiere atención."
            else:
                salud_general = "pobre"
                interpretacion = "La parcela presenta problemas significativos en el desarrollo vegetal."
            
            # Generar resumen ejecutivo
            resumen_ejecutivo = f"""
            Durante el período analizado de {datos_analisis['periodo']['meses']} meses, la parcela ha mostrado 
            un rendimiento {salud_general} con un NDVI promedio de {ndvi_promedio:.3f}. 
            {interpretacion} La tendencia observada es {tendencia_ndvi}, lo que indica 
            {'una mejora sostenida' if tendencia_ndvi == 'creciente' else 'estabilidad' if tendencia_ndvi == 'estable' else 'necesidad de intervención'} 
            en las condiciones del cultivo.
            """
            
            # Análisis de tendencias detallado
            analisis_tendencias = f"""
            Análisis de Índices Vegetales:
            
            NDVI (Índice de Vegetación):
            - Promedio del período: {ndvi_promedio:.3f}
            - Rango: {estadisticas.get('ndvi_minimo', 0):.3f} - {estadisticas.get('ndvi_maximo', 0):.3f}
            - Tendencia: {tendencia_ndvi}
            
            NDMI (Índice de Humedad):
            - Promedio: {estadisticas.get('ndmi_promedio', 0):.3f}
            - Indicador de estrés hídrico y contenido de humedad en la vegetación
            
            SAVI (Vegetación Ajustada al Suelo):
            - Promedio: {estadisticas.get('savi_promedio', 0):.3f}
            - Medida corregida de densidad vegetal considerando la influencia del suelo
            """
            
            # Conclusiones IA
            conclusiones = self._generar_conclusiones_especificas(
                estadisticas, tendencia_ndvi, salud_general
            )
            
            # Recomendaciones
            recomendaciones = self._generar_recomendaciones(
                estadisticas, tendencia_ndvi, salud_general
            )
            
            return {
                'resumen_ejecutivo': resumen_ejecutivo.strip(),
                'analisis_tendencias': analisis_tendencias.strip(),
                'conclusiones': conclusiones,
                'recomendaciones': recomendaciones,
                'salud_general': salud_general
            }
            
        except Exception as e:
            logger.error(f"Error en análisis IA: {str(e)}")
            return {
                'resumen_ejecutivo': 'Error generando análisis automático.',
                'analisis_tendencias': 'Datos insuficientes para análisis.',
                'conclusiones': 'Requiere análisis manual.',
                'recomendaciones': 'Consulte con un especialista agrícola.',
                'salud_general': 'indeterminada'
            }
    
    def _analizar_tendencia(self, valores: List[float]) -> str:
        """
        Analiza la tendencia de una serie de valores
        """
        if len(valores) < 3:
            return 'indeterminada'
        
        # Calcular pendiente promedio
        diferencias = []
        for i in range(1, len(valores)):
            diferencias.append(valores[i] - valores[i-1])
        
        pendiente_promedio = sum(diferencias) / len(diferencias)
        
        if pendiente_promedio > 0.01:
            return 'creciente'
        elif pendiente_promedio < -0.01:
            return 'decreciente'
        else:
            return 'estable'
    
    def _generar_conclusiones_especificas(self, estadisticas: Dict, 
                                        tendencia: str, salud: str) -> str:
        """
        Genera conclusiones específicas basadas en el análisis
        """
        conclusiones = []
        
        # Análisis NDVI
        ndvi = estadisticas.get('ndvi_promedio', 0)
        if ndvi > 0.7:
            conclusiones.append("- El cultivo presenta una excelente densidad de biomasa vegetal.")
        elif ndvi > 0.5:
            conclusiones.append("- El desarrollo vegetal es adecuado para la época del año.")
        else:
            conclusiones.append("- Se detectan posibles problemas en el desarrollo vegetal que requieren atención.")
        
        # Análisis de tendencia
        if tendencia == 'creciente':
            conclusiones.append("- Se observa una mejora progresiva en la salud del cultivo.")
        elif tendencia == 'decreciente':
            conclusiones.append("- La tendencia descendente sugiere la necesidad de intervención técnica.")
        else:
            conclusiones.append("- Los índices muestran estabilidad en el período analizado.")
        
        # Análisis NDMI
        ndmi = estadisticas.get('ndmi_promedio', 0)
        if ndmi > 0.3:
            conclusiones.append("- Los niveles de humedad en la vegetación son adecuados.")
        elif ndmi > 0:
            conclusiones.append("- Los niveles de humedad son moderados, monitorear riego.")
        else:
            conclusiones.append("- Se detecta posible estrés hídrico en el cultivo.")
        
        return '\n'.join(conclusiones)
    
    def _generar_recomendaciones(self, estadisticas: Dict, 
                               tendencia: str, salud: str) -> str:
        """
        Genera recomendaciones técnicas basadas en el análisis
        """
        recomendaciones = []
        
        if salud == 'excelente':
            recomendaciones.append("- Mantener las prácticas actuales de manejo.")
            recomendaciones.append("- Continuar con el programa de monitoreo satelital.")
        elif salud == 'buena':
            recomendaciones.append("- Optimizar el programa de fertilización.")
            recomendaciones.append("- Revisar sistema de riego para maximizar rendimiento.")
        elif salud == 'regular':
            recomendaciones.append("- Evaluar necesidades nutricionales del cultivo.")
            recomendaciones.append("- Verificar sistema de drenaje y manejo del agua.")
            recomendaciones.append("- Considerar análisis de suelo detallado.")
        else:
            recomendaciones.append("- Realizar intervención técnica inmediata.")
            recomendaciones.append("- Análisis detallado de plagas y enfermedades.")
            recomendaciones.append("- Evaluación completa del sistema de riego y nutrición.")
        
        if tendencia == 'decreciente':
            recomendaciones.append("- Monitoreo más frecuente durante las próximas semanas.")
            recomendaciones.append("- Consulta con especialista en agronomía.")
        
        # Recomendación estacional
        mes_actual = datetime.now().month
        if mes_actual in [12, 1, 2]:  # Época seca
            recomendaciones.append("- Reforzar programa de riego durante época seca.")
        elif mes_actual in [3, 4, 5, 10, 11]:  # Transición
            recomendaciones.append("- Preparar para cambios estacionales.")
        else:  # Época húmeda
            recomendaciones.append("- Verificar sistemas de drenaje por temporada húmeda.")
        
        return '\n'.join(recomendaciones)
    
    def _crear_pdf_informe(self, **kwargs) -> ContentFile:
        """
        Crea el archivo PDF final del informe
        """
        try:
            # Crear buffer para el PDF
            buffer = BytesIO()
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Obtener estilos
            styles = getSampleStyleSheet()
            
            # Crear estilos personalizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                textColor=colors.HexColor('#2d5a27'),
                alignment=TA_CENTER
            )
            
            # Contenido del documento
            story = []
            
            # Título principal
            story.append(Paragraph("INFORME DE ANÁLISIS SATELITAL AGRÍCOLA", title_style))
            story.append(Paragraph("AgroTech Histórico", styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Información de la parcela
            parcela_info = f"""
            <b>Parcela:</b> {kwargs['parcela'].nombre}<br/>
            <b>Propietario:</b> {kwargs['parcela'].propietario}<br/>
            <b>Período de análisis:</b> {kwargs['fecha_inicio']} - {kwargs['fecha_fin']}<br/>
            <b>Fecha del informe:</b> {datetime.now().strftime('%d de %B de %Y')}<br/>
            """
            story.append(Paragraph(parcela_info, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Resumen ejecutivo
            story.append(Paragraph("RESUMEN EJECUTIVO", styles['Heading2']))
            story.append(Paragraph(kwargs['analisis_ia']['resumen_ejecutivo'], styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Nota sobre simulación
            if not kwargs.get('datos_reales', True):
                story.append(Paragraph(
                    "<b>Nota:</b> Este informe utiliza datos simulados para demostración. "
                    "En producción, se conectaría con la API de EOSDA para datos reales.",
                    styles['Normal']
                ))
                story.append(Spacer(1, 20))
            
            # Construir PDF
            doc.build(story)
            
            # Crear archivo
            buffer.seek(0)
            nombre_archivo = f'informe_{kwargs["parcela"].nombre.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            
            return ContentFile(buffer.getvalue(), name=nombre_archivo)
            
        except Exception as e:
            logger.error(f"Error creando PDF: {str(e)}")
            return None


# Instancia global del servicio
generador_pdf = GeneradorInformePDF()