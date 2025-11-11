"""
Servicio para integración con la API de EOSDA
Obtiene datos satelitales como NDVI, NDMI, SAVI y datos climatológicos
"""

import requests
import json
import logging
from datetime import datetime, date, timedelta
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
import time

logger = logging.getLogger(__name__)


class EosdaAPIService:
    """
    Servicio para interactuar con la API de EOSDA y obtener datos satelitales
    Incluye Field Management API para sincronizar parcelas
    """
    
    def __init__(self):
        self.api_key = settings.EOSDA_API_KEY
        self.base_url = settings.EOSDA_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,  # EOSDA usa x-api-key en lugar de Bearer
            'Content-Type': 'application/json'
        })
    
    def validar_configuracion(self) -> bool:
        """
        Valida que la configuración de la API esté correctamente establecida
        """
        if not self.api_key or self.api_key == 'demo_token_reemplazar_con_real':
            logger.warning("Token de EOSDA no configurado correctamente")
            return False
        return True
    
    # ========= FIELD MANAGEMENT API =========
    
    def crear_campo_eosda(self, parcela) -> Dict:
        """
        Crea un campo en EOSDA usando Field Management API
        Documentación: https://doc.eos.com/docs/field-management-api/field-management/
        """
        try:
            from django.utils import timezone
            
            # Endpoint correcto según documentación oficial
            url = f"{self.base_url}/field-management"
            
            # Preparar geometría en formato GeoJSON
            if hasattr(parcela, 'geometria') and parcela.geometria:
                # Usar geometría PostGIS nativa
                geojson_dict = json.loads(parcela.geometria.geojson)
            else:
                # Fallback a coordenadas JSON
                geojson_dict = parcela.coordenadas_dict
            
            if not geojson_dict:
                error_msg = "No hay geometría disponible para la parcela"
                parcela.marcar_error_eosda(error_msg)
                return {'exito': False, 'error': error_msg}
            
            # Payload según documentación oficial de EOSDA Field Management API
            # IMPORTANTE: La respuesta retorna "id" no "field_id"
            payload = {
                'type': 'Feature',
                'properties': {
                    'name': parcela.nombre,
                    'group': 'AgroTech Histórico',
                    'years_data': [{
                        'crop_type': parcela.tipo_cultivo or 'Other',
                        'year': parcela.fecha_inicio_monitoreo.year if parcela.fecha_inicio_monitoreo else datetime.now().year,
                        'sowing_date': parcela.fecha_inicio_monitoreo.isoformat() if parcela.fecha_inicio_monitoreo else None
                    }]
                },
                'geometry': geojson_dict
            }
            
            logger.info(f"Creando campo en EOSDA para parcela: {parcela.nombre}")
            logger.debug(f"Payload enviado a EOSDA: {json.dumps(payload, indent=2)}")
            
            # Crear campo en EOSDA con timeout adecuado
            response = self.session.post(url, json=payload, timeout=30)
            
            logger.info(f"Respuesta EOSDA - Status: {response.status_code}")
            logger.debug(f"Respuesta EOSDA - Body: {response.text}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                # IMPORTANTE: Según documentación, la respuesta es {"id": number, "area": number}
                field_id = data.get('id') or data.get('field_id')
                
                if field_id:
                    # Actualizar parcela con información de EOSDA
                    parcela.marcar_sincronizada_eosda(
                        field_id=str(field_id),
                        nombre_campo=payload['properties']['name']
                    )
                    
                    logger.info(f"✅ Campo creado exitosamente en EOSDA con ID: {field_id}")
                    return {
                        'exito': True,
                        'field_id': str(field_id),
                        'area': data.get('area'),
                        'mensaje': f'Campo registrado en EOSDA con ID {field_id}',
                        'datos': data
                    }
                else:
                    error_msg = f"EOSDA no retornó field_id en la respuesta: {data}"
                    parcela.marcar_error_eosda(error_msg)
                    logger.error(error_msg)
                    return {'exito': False, 'error': error_msg}
            else:
                error_msg = f"Error HTTP {response.status_code}: {response.text[:500]}"
                parcela.marcar_error_eosda(error_msg)
                logger.error(f"❌ Error creando campo en EOSDA: {error_msg}")
                return {'exito': False, 'error': error_msg, 'status_code': response.status_code}
                
        except requests.exceptions.Timeout:
            error_msg = "Timeout al conectar con EOSDA (>30s)"
            parcela.marcar_error_eosda(error_msg)
            logger.error(error_msg)
            return {'exito': False, 'error': error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = "Error de conexión con EOSDA API"
            parcela.marcar_error_eosda(error_msg)
            logger.error(error_msg)
            return {'exito': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Excepción creando campo: {str(e)}"
            parcela.marcar_error_eosda(error_msg)
            logger.error(f"Error en crear_campo_eosda: {error_msg}", exc_info=True)
            return {'exito': False, 'error': error_msg}
    
    def obtener_campos_eosda(self) -> List[Dict]:
        """
        Obtiene la lista de campos desde EOSDA Field Management API
        Documentación: https://doc.eos.com/docs/field-management-api/field-management/
        """
        try:
            # Endpoint correcto según documentación oficial
            url = f"{self.base_url}/field-management/fields"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                fields = response.json()
                logger.info(f"Se obtuvieron {len(fields)} campos desde EOSDA")
                return fields if isinstance(fields, list) else []
            else:
                logger.warning(f"Error obteniendo campos de EOSDA: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo campos de EOSDA: {str(e)}")
            return []
    
    def sincronizar_parcela_con_eosda(self, parcela) -> Dict:
        """
        Sincroniza una parcela con EOSDA, creándola si no existe
        """
        try:
            # Verificar si ya está sincronizada
            if parcela.eosda_sincronizada and parcela.eosda_field_id:
                logger.info(f"Parcela {parcela.nombre} ya está sincronizada con EOSDA: {parcela.eosda_field_id}")
                return {
                    'exito': True,
                    'field_id': parcela.eosda_field_id,
                    'mensaje': 'Ya sincronizada',
                    'ya_existia': True
                }
            
            # Crear campo en EOSDA
            resultado = self.crear_campo_eosda(parcela)
            
            if resultado['exito']:
                logger.info(f"Parcela {parcela.nombre} sincronizada exitosamente con EOSDA")
            else:
                logger.error(f"Error sincronizando {parcela.nombre}: {resultado['error']}")
                
            return resultado
            
        except Exception as e:
            logger.error(f"Error en sincronizar_parcela_con_eosda: {str(e)}")
            return {'exito': False, 'error': str(e)}
    
    def obtener_datos_parcela(self, parcela, fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Obtiene todos los datos satelitales para una parcela en un período específico
        NUEVA VERSIÓN: Usa field_id de EOSDA en lugar de geometría
        """
        try:
            # Validar configuración
            if not self.validar_configuracion():
                return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
            
            # 1. SINCRONIZAR CON EOSDA PRIMERO (Field Management API)
            if not parcela.eosda_sincronizada:
                logger.info(f"Sincronizando parcela {parcela.nombre} con EOSDA...")
                resultado_sync = self.sincronizar_parcela_con_eosda(parcela)
                if not resultado_sync['exito']:
                    logger.warning(f"No se pudo sincronizar {parcela.nombre}, usando datos simulados")
                    return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
            
            # 2. USAR FIELD_ID PARA OBTENER DATOS (Statistics API)
            field_id = parcela.eosda_field_id
            if not field_id:
                logger.warning(f"Parcela {parcela.nombre} no tiene field_id, usando datos simulados")
                return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
            
            logger.info(f"Obteniendo datos satelitales para field_id: {field_id}")
            
            # Obtener índices usando field_id
            datos_satelitales = {
                'ndvi': self._obtener_indice_temporal_por_field_id(field_id, 'NDVI', fecha_inicio, fecha_fin),
                'ndmi': self._obtener_indice_temporal_por_field_id(field_id, 'NDMI', fecha_inicio, fecha_fin),
                'savi': self._obtener_indice_temporal_por_field_id(field_id, 'SAVI', fecha_inicio, fecha_fin),
                'datos_clima': self._obtener_datos_climaticos_por_field_id(field_id, fecha_inicio, fecha_fin)
            }
            
            logger.info(f"Datos obtenidos exitosamente para field_id {field_id}")
            return datos_satelitales
            
        except Exception as e:
            logger.error(f"Error al obtener datos de EOSDA para {parcela.nombre}: {str(e)}")
            # Retornar datos simulados en caso de error
            return self._generar_datos_simulados(parcela, fecha_inicio, fecha_fin)
    
    def _obtener_indice_temporal_por_field_id(self, field_id: str, indice: str, 
                                            fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos temporales de un índice específico usando field_id de EOSDA
        VERSIÓN OPTIMIZADA: Usa field_id en lugar de geometría
        """
        try:
            # Endpoint de estadísticas según documentación oficial
            url = f"{self.base_url}/gdw/api"
            
            # Convertir fechas a formato ISO
            start_date = fecha_inicio.isoformat()
            end_date = fecha_fin.isoformat()
            
            # Mapear índices a nombres de EOSDA
            index_mapping = {
                'NDVI': 'ndvi',
                'NDMI': 'ndmi', 
                'SAVI': 'savi'
            }
            
            if indice not in index_mapping:
                logger.warning(f"Índice {indice} no soportado")
                return []
            
            # Parámetros según documentación de EOSDA Statistics API con field_id
            payload = {
                'type': 'mt_stats',
                'params': {
                    'bm_type': [index_mapping[indice]],
                    'date_start': start_date,
                    'date_end': end_date,
                    'field_id': field_id,  # USAR FIELD_ID EN LUGAR DE GEOMETRY
                    'sensors': ['S2_MSI_L2A'],  # Sentinel-2
                    'reference': f'{indice}_{field_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'limit': 50,  # Número de escenas
                    'max_cloud_cover_in_aoi': 80,
                    'exclude_cover_pixels': True,  # Enmascarar nubes
                    'cloud_masking_level': 3  # Máximo enmascarado
                }
            }
            
            logger.info(f"Solicitando datos {indice} para field_id {field_id} desde {start_date} hasta {end_date}")
            
            # Crear tarea
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code not in [200, 201, 202]:
                logger.warning(f"Error en API EOSDA para {indice}: {response.status_code} - {response.text[:200]}")
                return []
            
            # Obtener task_id de la respuesta
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                logger.error(f"No se obtuvo task_id para {indice}")
                return []
            
            # Esperar y obtener resultados
            return self._obtener_resultados_tarea(task_id, indice)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con EOSDA para {indice}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error procesando {indice}: {str(e)}")
            return []
    
    def _obtener_datos_climaticos_por_field_id(self, field_id: str, 
                                             fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos climáticos usando field_id (placeholder por ahora)
        """
        try:
            # Implementar Weather API cuando esté disponible
            logger.info(f"Datos climáticos no implementados aún para field_id: {field_id}")
            return []
        except Exception as e:
            logger.error(f"Error en datos climáticos para field_id {field_id}: {str(e)}")
            return []
    
    def _obtener_indice_temporal(self, geojson: Dict, indice: str, 
                                fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos temporales de un índice específico usando API Statistics de EOSDA
        """
        try:
            # Endpoint de estadísticas según documentación oficial
            url = f"{self.base_url}/gdw/api"
            
            # Convertir fechas a formato ISO
            start_date = fecha_inicio.isoformat()
            end_date = fecha_fin.isoformat()
            
            # Mapear índices a nombres de EOSDA
            index_mapping = {
                'NDVI': 'ndvi',
                'NDMI': 'ndmi', 
                'SAVI': 'savi'
            }
            
            if indice not in index_mapping:
                logger.warning(f"Índice {indice} no soportado")
                return []
            
            # Parámetros según documentación de EOSDA Statistics API
            payload = {
                'type': 'mt_stats',
                'params': {
                    'bm_type': [index_mapping[indice]],
                    'date_start': start_date,
                    'date_end': end_date,
                    'geometry': geojson,
                    'sensors': ['S2_MSI_L2A'],  # Sentinel-2
                    'reference': f'{indice}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'limit': 50,  # Número de escenas
                    'max_cloud_cover_in_aoi': 80,
                    'exclude_cover_pixels': True,  # Enmascarar nubes
                    'cloud_masking_level': 3  # Máximo enmascarado
                }
            }
            
            logger.info(f"Solicitando datos {indice} desde {start_date} hasta {end_date}")
            
            # Crear tarea
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code not in [200, 201, 202]:
                logger.warning(f"Error en API EOSDA para {indice}: {response.status_code} - {response.text[:200]}")
                return []
            
            # Obtener task_id de la respuesta
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                logger.error(f"No se obtuvo task_id para {indice}")
                return []
            
            # Esperar y obtener resultados
            return self._obtener_resultados_tarea(task_id, indice)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con EOSDA para {indice}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error procesando {indice}: {str(e)}")
            return []

    def _obtener_resultados_tarea(self, task_id: str, indice: str, max_intentos: int = 10) -> List[Dict]:
        """
        Obtiene los resultados de una tarea asíncrona de EOSDA Statistics
        """
        try:
            url = f"{self.base_url}/gdw/api/{task_id}"
            
            for intento in range(max_intentos):
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Error consultando tarea {task_id}: {response.status_code}")
                    return []
                
                data = response.json()
                
                # Verificar si hay resultados
                if 'result' in data and data['result']:
                    logger.info(f"Datos obtenidos para {indice}: {len(data['result'])} escenas")
                    return self._procesar_datos_estadisticas(data['result'], indice)
                
                # Verificar si hay errores
                if 'errors' in data and data['errors']:
                    logger.warning(f"Errores en tarea {task_id}: {len(data['errors'])} errores")
                
                # Esperar antes del siguiente intento (menos tiempo para desarrollo)
                if intento < max_intentos - 1:
                    time.sleep(5)  # Esperar 5 segundos entre intentos
            
            logger.warning(f"Timeout esperando resultados para {indice}, tarea {task_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo resultados de tarea {task_id}: {str(e)}")
            return []

    def _procesar_datos_estadisticas(self, resultados: List[Dict], indice: str) -> List[Dict]:
        """
        Procesa los datos de estadísticas de EOSDA en formato estándar
        """
        try:
            datos_procesados = []
            
            for resultado in resultados:
                # Extraer información relevante
                fecha_str = resultado.get('date', '')
                if not fecha_str:
                    continue
                
                # Convertir fecha
                try:
                    fecha = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
                except:
                    continue
                
                # Usar el promedio como valor principal
                valor = resultado.get('average')
                if valor is None:
                    continue
                
                # Crear punto de datos
                punto_datos = {
                    'fecha': fecha,
                    'valor': round(float(valor), 4),
                    'indice': indice,
                    'metadatos': {
                        'scene_id': resultado.get('scene_id', ''),
                        'cloud_coverage': resultado.get('cloud', 0),
                        'min': resultado.get('min'),
                        'max': resultado.get('max'),
                        'std': resultado.get('std'),
                        'median': resultado.get('median')
                    }
                }
                
                datos_procesados.append(punto_datos)
            
            # Ordenar por fecha
            datos_procesados.sort(key=lambda x: x['fecha'])
            
            logger.info(f"Procesados {len(datos_procesados)} puntos de datos para {indice}")
            return datos_procesados
            
        except Exception as e:
            logger.error(f"Error procesando estadísticas para {indice}: {str(e)}")
            return []
    
    def _obtener_datos_climaticos(self, geojson: Dict, 
                                 fecha_inicio: date, fecha_fin: date) -> List[Dict]:
        """
        Obtiene datos climatológicos (temperatura, precipitación)
        """
        try:
            url = f"{self.base_url}/weather/history"
            
            payload = {
                'geometry': geojson,
                'start_date': fecha_inicio.isoformat(),
                'end_date': fecha_fin.isoformat(),
                'parameters': ['temperature', 'precipitation', 'humidity']
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._procesar_datos_climaticos(data)
            else:
                logger.warning(f"Error en datos climáticos EOSDA: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener datos climáticos: {str(e)}")
            return []
    
    def _procesar_datos_temporales(self, data: Dict, indice: str) -> List[Dict]:
        """
        Procesa los datos temporales recibidos de la API
        """
        try:
            resultados = []
            
            # Extraer series temporales de la respuesta
            time_series = data.get('time_series', [])
            
            for entry in time_series:
                fecha = datetime.fromisoformat(entry.get('date', '')).date()
                valor_promedio = entry.get('mean', None)
                valor_max = entry.get('max', None)
                valor_min = entry.get('min', None)
                nubosidad = entry.get('cloud_coverage', 0)
                
                if valor_promedio is not None:
                    resultados.append({
                        'fecha': fecha,
                        'promedio': float(valor_promedio),
                        'maximo': float(valor_max) if valor_max else None,
                        'minimo': float(valor_min) if valor_min else None,
                        'nubosidad': float(nubosidad),
                        'indice': indice
                    })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error procesando datos temporales de {indice}: {str(e)}")
            return []
    
    def _procesar_datos_climaticos(self, data: Dict) -> List[Dict]:
        """
        Procesa los datos climatológicos recibidos de la API
        """
        try:
            resultados = []
            
            weather_data = data.get('weather_data', [])
            
            for entry in weather_data:
                fecha = datetime.fromisoformat(entry.get('date', '')).date()
                
                resultados.append({
                    'fecha': fecha,
                    'temperatura_promedio': entry.get('temperature_avg'),
                    'temperatura_maxima': entry.get('temperature_max'),
                    'temperatura_minima': entry.get('temperature_min'),
                    'precipitacion_total': entry.get('precipitation_total'),
                    'humedad_promedio': entry.get('humidity_avg')
                })
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error procesando datos climáticos: {str(e)}")
            return []
    
    def _generar_datos_simulados(self, parcela, fecha_inicio: date, fecha_fin: date) -> Dict:
        """
        Genera datos simulados para desarrollo y pruebas
        """
        import random
        import numpy as np
        
        logger.info(f"Generando datos simulados para {parcela.nombre}")
        
        # Generar fechas mensuales en el rango
        fechas = []
        fecha_actual = fecha_inicio.replace(day=1)  # Primer día del mes
        
        while fecha_actual <= fecha_fin:
            fechas.append(fecha_actual)
            # Siguiente mes
            if fecha_actual.month == 12:
                fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
            else:
                fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)
        
        # Generar datos NDVI simulados (0.2 a 0.9)
        ndvi_base = 0.5 + 0.3 * np.sin(np.linspace(0, 4*np.pi, len(fechas)))
        ndvi_data = []
        for i, fecha in enumerate(fechas):
            valor = max(0.2, min(0.9, ndvi_base[i] + random.uniform(-0.1, 0.1)))
            ndvi_data.append({
                'fecha': fecha,
                'promedio': round(valor, 3),
                'maximo': round(min(0.9, valor + random.uniform(0.05, 0.15)), 3),
                'minimo': round(max(0.2, valor - random.uniform(0.05, 0.15)), 3),
                'nubosidad': random.uniform(10, 60),
                'indice': 'NDVI'
            })
        
        # Generar datos NDMI simulados (-0.5 a 0.5)
        ndmi_base = 0.1 + 0.3 * np.cos(np.linspace(0, 4*np.pi, len(fechas)))
        ndmi_data = []
        for i, fecha in enumerate(fechas):
            valor = max(-0.5, min(0.5, ndmi_base[i] + random.uniform(-0.1, 0.1)))
            ndmi_data.append({
                'fecha': fecha,
                'promedio': round(valor, 3),
                'maximo': round(min(0.5, valor + random.uniform(0.05, 0.15)), 3),
                'minimo': round(max(-0.5, valor - random.uniform(0.05, 0.15)), 3),
                'nubosidad': random.uniform(10, 60),
                'indice': 'NDMI'
            })
        
        # Generar datos SAVI simulados (similar a NDVI pero ligeramente menor)
        savi_data = []
        for i, fecha in enumerate(fechas):
            valor_ndvi = ndvi_data[i]['promedio']
            valor_savi = valor_ndvi * 0.85  # SAVI típicamente menor que NDVI
            savi_data.append({
                'fecha': fecha,
                'promedio': round(valor_savi, 3),
                'maximo': round(min(0.8, valor_savi + random.uniform(0.05, 0.15)), 3),
                'minimo': round(max(0.1, valor_savi - random.uniform(0.05, 0.15)), 3),
                'nubosidad': random.uniform(10, 60),
                'indice': 'SAVI'
            })
        
        # Generar datos climáticos simulados
        datos_clima = []
        for fecha in fechas:
            # Simular temperaturas según época del año (Colombia)
            mes = fecha.month
            temp_base = 22 if mes in [12, 1, 2] else 25  # Más frío en diciembre-febrero
            
            datos_clima.append({
                'fecha': fecha,
                'temperatura_promedio': round(temp_base + random.uniform(-3, 3), 1),
                'temperatura_maxima': round(temp_base + random.uniform(5, 8), 1),
                'temperatura_minima': round(temp_base - random.uniform(5, 8), 1),
                'precipitacion_total': round(random.uniform(50, 200), 1),
                'humedad_promedio': round(random.uniform(65, 85), 1)
            })
        
        return {
            'ndvi': ndvi_data,
            'ndmi': ndmi_data,
            'savi': savi_data,
            'datos_clima': datos_clima,
            'simulado': True
        }
    
    def obtener_imagen_satelital(self, parcela, fecha: date, indice: str = 'NDVI') -> Optional[str]:
        """
        Obtiene una imagen satelital de la parcela para una fecha específica
        Retorna la URL de la imagen o None si no está disponible
        """
        try:
            if not self.validar_configuracion():
                return None
            
            url = f"{self.base_url}/satellite/image"
            
            payload = {
                'geometry': parcela.coordenadas_dict,
                'date': fecha.isoformat(),
                'index': indice,
                'format': 'PNG',
                'resolution': 10
            }
            
            response = self.session.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('image_url')
            else:
                logger.warning(f"No se pudo obtener imagen satelital: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error al obtener imagen satelital: {str(e)}")
            return None
    
    def verificar_conectividad(self) -> Dict[str, bool]:
        """
        Verifica la conectividad con la API Statistics de EOSDA
        """
        resultado = {
            'configuracion_valida': self.validar_configuracion(),
            'conexion_exitosa': False,
            'tiempo_respuesta': None,
            'task_id': None,
            'status': None,
            'mensaje': None
        }
        
        try:
            inicio = time.time()
            # Endpoint de statistics para verificar conectividad
            url = f"{self.base_url}/gdw/api"
            
            # Parámetros mínimos para crear una tarea de prueba
            payload = {
                'type': 'mt_stats',
                'params': {
                    'bm_type': ['ndvi'],
                    'date_start': '2025-01-01',
                    'date_end': '2025-01-02',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[
                            [-74.1, 4.5],
                            [-74.0, 4.5], 
                            [-74.0, 4.6],
                            [-74.1, 4.6],
                            [-74.1, 4.5]
                        ]]
                    },
                    'sensors': ['S2_MSI_L2A'],
                    'reference': 'connectivity_test',
                    'limit': 1,
                    'max_cloud_cover_in_aoi': 100
                }
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            resultado['tiempo_respuesta'] = round((time.time() - inicio) * 1000, 2)
            
            if response.status_code in [200, 201, 202]:
                resultado['conexion_exitosa'] = True
                data = response.json()
                resultado['task_id'] = data.get('task_id', 'N/A')
                resultado['status'] = data.get('status', 'N/A')
                resultado['mensaje'] = 'Conectado exitosamente'
                logger.info(f"Verificación EOSDA: Status {response.status_code}, Tiempo: {resultado['tiempo_respuesta']}ms")
            else:
                resultado['conexion_exitosa'] = False
                resultado['mensaje'] = f'Error: {response.status_code} - {response.text[:100]}'
                logger.warning(f"Verificación EOSDA fallida: Status {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error verificando conectividad EOSDA: {str(e)}")
            resultado['conexion_exitosa'] = False
            resultado['mensaje'] = f'Error de conexión: {str(e)}'
        
        return resultado


# Instancia global del servicio
eosda_service = EosdaAPIService()