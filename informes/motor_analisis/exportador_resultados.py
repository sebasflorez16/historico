"""
Exportador de Resultados para Dashboards y Visualizaciones
===========================================================

Exporta los resultados del motor de análisis en formatos optimizados
para visualizaciones interactivas, dashboards y sistemas externos:

- GeoJSON para mapas interactivos (Leaflet, Mapbox, Folium)
- JSON estructurado para gráficos (Chart.js, D3.js, Plotly)
- CSV para análisis en Excel/R/Python
- Formato Timeline para visualizaciones temporales

Características:
- ✅ Serialización completa de geometrías PostGIS
- ✅ Optimización de tamaño (compresión, decimales)
- ✅ Compatibilidad con estándares GIS (RFC 7946)
- ✅ Metadatos completos para trazabilidad
"""

import json
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)


class ExportadorResultados:
    """
    Exportador de resultados de análisis para múltiples formatos.
    
    Soporta:
    1. GeoJSON para mapas
    2. JSON para gráficos
    3. CSV para análisis
    4. Timeline para visualizaciones temporales
    """
    
    def __init__(self):
        """Inicializa el exportador"""
        self.logger = logging.getLogger(__name__)
    
    def exportar_geojson(
        self,
        parcelas: List[Dict[str, Any]],
        incluir_analisis: bool = True
    ) -> Dict[str, Any]:
        """
        Exporta parcelas y análisis a GeoJSON (RFC 7946).
        
        Args:
            parcelas: Lista de diccionarios con datos de parcelas
            incluir_analisis: Si incluir resultados de análisis
            
        Returns:
            Dict compatible con GeoJSON
        """
        features = []
        
        for parcela in parcelas:
            feature = {
                'type': 'Feature',
                'id': parcela.get('id'),
                'geometry': self._procesar_geometria(parcela.get('geometria')),
                'properties': self._procesar_propiedades(
                    parcela,
                    incluir_analisis
                )
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'generado': datetime.now().isoformat(),
                'num_parcelas': len(features),
                'sistema': 'AgroTech Análisis Profesional'
            }
        }
        
        self.logger.info(f"✅ GeoJSON generado: {len(features)} features")
        
        return geojson
    
    def _procesar_geometria(self, geometria: Any) -> Optional[Dict[str, Any]]:
        """
        Procesa geometría a formato GeoJSON.
        
        Soporta:
        - Django GEOSGeometry (PostGIS)
        - Shapely Geometry
        - Dict GeoJSON directo
        """
        if geometria is None:
            return None
        
        # Si ya es dict, validar y retornar
        if isinstance(geometria, dict):
            if 'type' in geometria and 'coordinates' in geometria:
                return geometria
        
        # Si tiene método geojson (Django GEOSGeometry)
        if hasattr(geometria, 'geojson'):
            return json.loads(geometria.geojson)
        
        # Si tiene método __geo_interface__ (Shapely)
        if hasattr(geometria, '__geo_interface__'):
            return geometria.__geo_interface__
        
        # Si es string JSON
        if isinstance(geometria, str):
            try:
                return json.loads(geometria)
            except json.JSONDecodeError:
                self.logger.warning(f"⚠️ No se pudo parsear geometría: {geometria[:100]}")
                return None
        
        self.logger.warning(f"⚠️ Tipo de geometría no soportado: {type(geometria)}")
        return None
    
    def _procesar_propiedades(
        self,
        parcela: Dict[str, Any],
        incluir_analisis: bool
    ) -> Dict[str, Any]:
        """Extrae propiedades para GeoJSON"""
        props = {
            'nombre': parcela.get('nombre'),
            'tipo_cultivo': parcela.get('tipo_cultivo'),
            'area_hectareas': parcela.get('area_hectareas'),
            'propietario': parcela.get('propietario'),
        }
        
        if incluir_analisis:
            # Agregar análisis más reciente
            if 'analisis_actual' in parcela:
                analisis = parcela['analisis_actual']
                props.update({
                    'ndvi_actual': analisis.get('ndvi'),
                    'ndmi_actual': analisis.get('ndmi'),
                    'estado_salud': analisis.get('estado_salud'),
                    'alerta_nivel': analisis.get('alerta_nivel'),
                    'zona_productiva': analisis.get('zona_productiva'),
                })
        
        # Limpiar valores None
        return {k: v for k, v in props.items() if v is not None}
    
    def exportar_serie_temporal(
        self,
        serie_datos: List[Dict[str, Any]],
        tipo_indice: str
    ) -> Dict[str, Any]:
        """
        Exporta serie temporal para gráficos.
        
        Formato optimizado para Chart.js, D3.js, Plotly
        
        Args:
            serie_datos: Lista de puntos temporales
            tipo_indice: Tipo de índice (ndvi, ndmi, savi)
            
        Returns:
            Dict con series estructuradas
        """
        # Ordenar por fecha
        serie_ordenada = sorted(
            serie_datos,
            key=lambda x: x.get('fecha', datetime.min)
        )
        
        # Extraer valores
        fechas = []
        valores = []
        valores_min = []
        valores_max = []
        valores_p25 = []
        valores_p75 = []
        
        for punto in serie_ordenada:
            fecha = punto.get('fecha')
            if isinstance(fecha, datetime):
                fechas.append(fecha.isoformat())
            else:
                fechas.append(str(fecha))
            
            valores.append(punto.get('media'))
            valores_min.append(punto.get('minimo'))
            valores_max.append(punto.get('maximo'))
            valores_p25.append(punto.get('percentil_25'))
            valores_p75.append(punto.get('percentil_75'))
        
        return {
            'tipo_indice': tipo_indice,
            'fechas': fechas,
            'series': {
                'media': valores,
                'minimo': valores_min,
                'maximo': valores_max,
                'percentil_25': valores_p25,
                'percentil_75': valores_p75
            },
            'metadata': {
                'num_puntos': len(fechas),
                'fecha_inicio': fechas[0] if fechas else None,
                'fecha_fin': fechas[-1] if fechas else None,
                'rango_valores': {
                    'min': min([v for v in valores if v is not None], default=None),
                    'max': max([v for v in valores if v is not None], default=None)
                }
            }
        }
    
    def exportar_timeline(
        self,
        eventos: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Exporta eventos para visualización tipo timeline.
        
        Compatible con bibliotecas como vis.js, timeline.js
        
        Args:
            eventos: Lista de eventos (alertas, cambios, hitos)
            
        Returns:
            Lista de eventos formateados
        """
        timeline = []
        
        for evento in eventos:
            item = {
                'id': evento.get('id'),
                'content': evento.get('descripcion'),
                'start': self._formatear_fecha(evento.get('fecha')),
                'type': evento.get('tipo', 'point'),
                'group': evento.get('categoria'),
                'className': self._clasificar_evento(evento.get('severidad')),
                'title': evento.get('detalle'),  # Tooltip
            }
            
            # Si es evento con duración
            if 'fecha_fin' in evento:
                item['end'] = self._formatear_fecha(evento.get('fecha_fin'))
                item['type'] = 'range'
            
            timeline.append(item)
        
        return sorted(timeline, key=lambda x: x.get('start', ''))
    
    def _formatear_fecha(self, fecha: Any) -> str:
        """Formatea fecha a ISO 8601"""
        if isinstance(fecha, datetime):
            return fecha.isoformat()
        elif isinstance(fecha, str):
            return fecha
        else:
            return datetime.now().isoformat()
    
    def _clasificar_evento(self, severidad: Optional[str]) -> str:
        """Clasifica evento por severidad para CSS"""
        if severidad == 'critico':
            return 'evento-critico'
        elif severidad == 'alto':
            return 'evento-alerta'
        elif severidad == 'medio':
            return 'evento-aviso'
        else:
            return 'evento-info'
    
    def exportar_csv(
        self,
        datos: List[Dict[str, Any]],
        archivo_salida: str,
        campos: Optional[List[str]] = None
    ) -> bool:
        """
        Exporta datos a CSV.
        
        Args:
            datos: Lista de diccionarios con datos
            archivo_salida: Ruta del archivo CSV
            campos: Lista de campos a exportar (None = todos)
            
        Returns:
            True si se exportó correctamente
        """
        if not datos:
            self.logger.warning("⚠️ No hay datos para exportar")
            return False
        
        try:
            # Determinar campos
            if campos is None:
                campos = list(datos[0].keys())
            
            with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()
                
                for fila in datos:
                    # Filtrar solo campos especificados
                    fila_filtrada = {k: fila.get(k) for k in campos}
                    writer.writerow(fila_filtrada)
            
            self.logger.info(f"✅ CSV exportado: {archivo_salida} ({len(datos)} filas)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error exportando CSV: {str(e)}")
            return False
    
    def exportar_dashboard_completo(
        self,
        analisis_completo: Dict[str, Any],
        incluir_geometrias: bool = False
    ) -> Dict[str, Any]:
        """
        Exporta análisis completo para dashboard interactivo.
        
        Incluye:
        - Resumen ejecutivo
        - Series temporales
        - Alertas activas
        - Zonificación
        - Recomendaciones
        
        Args:
            analisis_completo: Dict con todo el análisis
            incluir_geometrias: Si incluir geometrías GeoJSON
            
        Returns:
            Dict optimizado para dashboard
        """
        dashboard = {
            'metadata': {
                'generado': datetime.now().isoformat(),
                'version': '1.0.0',
                'sistema': 'AgroTech Motor Análisis Profesional'
            },
            'resumen_ejecutivo': {
                'estado_general': analisis_completo.get('estado_general'),
                'tendencia': analisis_completo.get('tendencia'),
                'alertas_activas': analisis_completo.get('num_alertas', 0),
                'metricas_clave': analisis_completo.get('metricas_clave', {}),
            },
            'series_temporales': {},
            'alertas': analisis_completo.get('alertas', []),
            'zonificacion': analisis_completo.get('zonificacion', {}),
            'recomendaciones': analisis_completo.get('recomendaciones', []),
        }
        
        # Agregar series temporales
        for indice in ['ndvi', 'ndmi', 'savi']:
            if f'serie_{indice}' in analisis_completo:
                dashboard['series_temporales'][indice] = \
                    self.exportar_serie_temporal(
                        analisis_completo[f'serie_{indice}'],
                        indice
                    )
        
        # Agregar geometrías si se solicita
        if incluir_geometrias and 'parcelas' in analisis_completo:
            dashboard['mapa'] = self.exportar_geojson(
                analisis_completo['parcelas'],
                incluir_analisis=True
            )
        
        return dashboard
    
    def guardar_json(
        self,
        datos: Dict[str, Any],
        archivo_salida: str,
        pretty: bool = True
    ) -> bool:
        """
        Guarda datos en archivo JSON.
        
        Args:
            datos: Datos a guardar
            archivo_salida: Ruta del archivo
            pretty: Si formatear con indentación
            
        Returns:
            True si se guardó correctamente
        """
        try:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(datos, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(datos, f, ensure_ascii=False)
            
            self.logger.info(f"✅ JSON guardado: {archivo_salida}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error guardando JSON: {str(e)}")
            return False


# Instancia global
exportador = ExportadorResultados()
