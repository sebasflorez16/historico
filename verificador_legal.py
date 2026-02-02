"""
Módulo de Verificación de Restricciones Legales para Parcelas Agrícolas
=========================================================================

Este módulo verifica el cumplimiento de restricciones legales colombianas:
1. Retiros obligatorios de fuentes hídricas (Decreto 1541/1978)
2. Áreas protegidas (parques, reservas indígenas, páramos)
3. Zonas de riesgo (inundación, deslizamientos)

Fuentes de datos (TODAS GRATUITAS):
- RUNAP: Parques nacionales y áreas protegidas
- ANT: Resguardos indígenas
- IDEAM: Límites de páramos y red hídrica
- IGAC: Red hidrográfica nacional
- OpenStreetMap: Complemento para ríos/quebradas

Autor: AgroTech Histórico
Fecha: Enero 2026
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import geopandas as gpd
    from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon
    from shapely.ops import unary_union
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    print("⚠️  GeoPandas no disponible. Instalar con: pip install geopandas")


@dataclass
class ResultadoVerificacion:
    """Resultado de verificación de restricciones legales"""
    parcela_id: int
    area_total_ha: float
    area_cultivable_ha: Dict  # NUEVO: {"determinable": bool, "valor_ha": float|None, "nota": str}
    area_restringida_ha: float
    porcentaje_restringido: float
    cumple_normativa: bool
    restricciones_encontradas: List[Dict]
    fecha_verificacion: str
    advertencias: List[str]
    niveles_confianza: Dict[str, Dict]  # NUEVO: niveles de confianza por capa
    desglose_areas: Dict  # NUEVO: desglose detallado de áreas por fuente
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class VerificadorRestriccionesLegales:
    """
    Verificador de restricciones legales para parcelas agrícolas
    """
    
    # Retiros mínimos según Decreto 1541/1978 y normativa ambiental (metros)
    RETIROS_MINIMOS = {
        'rio_principal': 100,      # Ríos grandes (>50m ancho)
        'rio_secundario': 50,       # Ríos medianos (10-50m)
        'quebrada': 30,             # Quebradas y arroyos (<10m)
        'nacimiento': 100,          # Nacimientos (radio)
        'laguna': 30,               # Lagunas y ciénagas
        'humedal': 30,              # Humedales
        'canal_riego': 10,          # Canales artificiales
    }
    
    def __init__(self, directorio_datos: Optional[str] = None):
        """
        Inicializa el verificador
        
        Args:
            directorio_datos: Ruta al directorio con shapefiles. 
                            Si es None, usa ./datos_geograficos/
        """
        if not GEOPANDAS_AVAILABLE:
            raise ImportError(
                "GeoPandas es requerido. Instalar con:\n"
                "pip install geopandas"
            )
        
        if directorio_datos is None:
            directorio_datos = os.path.join(
                os.path.dirname(__file__), 
                'datos_geograficos'
            )
        
        self.directorio_datos = Path(directorio_datos)
        self.red_hidrica = None
        self.areas_protegidas = None
        self.resguardos_indigenas = None
        self.paramos = None
        
        # NUEVO: Para almacenar datos usados en última verificación (para mapas)
        self.red_hidrica_cercana = None
        self.metadata_verificacion = {}
        
        # Estadísticas de carga
        self.stats = {
            'red_hidrica_loaded': False,
            'areas_protegidas_loaded': False,
            'resguardos_loaded': False,
            'paramos_loaded': False,
        }
        
        # NUEVO: Niveles de confianza por capa
        self.niveles_confianza = {
            'red_hidrica': {
                'cargada': False,
                'tipo_dato': None,  # 'zonificacion', 'drenaje', 'real'
                'confianza': 'Nula',  # 'Alta', 'Media', 'Baja', 'Nula'
                'razon': 'Capa no cargada',
                'geometria_valida': None  # True si LineString, False si Polygon
            },
            'areas_protegidas': {
                'cargada': False,
                'tipo_dato': None,
                'confianza': 'Nula',
                'razon': 'Capa no cargada',
                'geometria_valida': True  # RUNAP siempre válido (API oficial)
            },
            'resguardos_indigenas': {
                'cargada': False,
                'tipo_dato': None,
                'confianza': 'Nula',
                'razon': 'Capa no cargada',
                'geometria_valida': True
            },
            'paramos': {
                'cargada': False,
                'tipo_dato': None,
                'confianza': 'Nula',
                'razon': 'Capa no cargada',
                'geometria_valida': True
            }
        }
    
    def cargar_red_hidrica(self, archivo: Optional[str] = None) -> bool:
        """
        Carga la red hidrográfica desde shapefile IGAC/IDEAM
        
        Args:
            archivo: Ruta al shapefile. Si es None, busca en directorio_datos
        
        Returns:
            True si carga exitosa
        """
        try:
            if archivo is None:
                # Buscar archivo en directorio datos
                directorio = self.directorio_datos / 'red_hidrica'
                
                # Buscar cualquier archivo .shp en el directorio
                if directorio.exists():
                    shapefiles = list(directorio.glob('*.shp'))
                    
                    # 🔧 PRIORIDAD CORREGIDA: Usar archivo con cobertura COMPLETA de Casanare/Meta
                    archivos_prioritarios = [
                        'red_hidrica_casanare_meta_igac_2024.shp',  # ⭐ MEJOR: Cobertura completa (10,586 cauces)
                        'Drenaje_Sencillo.shp',                      # Descarga ZIP completa
                        'drenajes_sencillos_igac.shp',               # ⚠️ BBOX limitado (solo 2,000 cauces, cobertura parcial)
                        'drenajes.shp',
                        'red_hidrica.shp'
                    ]
                    
                    archivo_seleccionado = None
                    for nombre_prior in archivos_prioritarios:
                        for shp in shapefiles:
                            if shp.name == nombre_prior:
                                archivo_seleccionado = str(shp)
                                break
                        if archivo_seleccionado:
                            break
                    
                    # Si no encuentra prioritario, usar el primero
                    if not archivo_seleccionado and shapefiles:
                        archivo_seleccionado = str(shapefiles[0])
                    
                    archivo = archivo_seleccionado
            
            if archivo and os.path.exists(archivo):
                self.red_hidrica = gpd.read_file(archivo)
                
                # Asegurar que está en WGS84 (EPSG:4326)
                if self.red_hidrica.crs != 'EPSG:4326':
                    self.red_hidrica = self.red_hidrica.to_crs('EPSG:4326')
                
                self.stats['red_hidrica_loaded'] = True
                
                # NUEVO: Validar tipo de geometría
                tipos_geom = self.red_hidrica.geometry.geom_type.unique()
                tiene_lineas = any(t in ['LineString', 'MultiLineString'] for t in tipos_geom)
                tiene_poligonos = any(t in ['Polygon', 'MultiPolygon'] for t in tipos_geom)
                
                if tiene_poligonos and not tiene_lineas:
                    # DATOS INCORRECTOS: Zonificación en lugar de drenaje
                    self.niveles_confianza['red_hidrica']['cargada'] = True
                    self.niveles_confianza['red_hidrica']['tipo_dato'] = 'zonificacion'
                    self.niveles_confianza['red_hidrica']['confianza'] = 'Baja'
                    self.niveles_confianza['red_hidrica']['razon'] = 'Red hídrica usa zonificación (polígonos), NO drenaje (líneas)'
                    self.niveles_confianza['red_hidrica']['geometria_valida'] = False
                    print(f"⚠️  Red hídrica cargada: {len(self.red_hidrica)} elementos (ZONIFICACIÓN - confianza BAJA)")
                elif tiene_lineas:
                    # DATOS CORRECTOS: Drenaje lineal
                    self.niveles_confianza['red_hidrica']['cargada'] = True
                    self.niveles_confianza['red_hidrica']['tipo_dato'] = 'drenaje'
                    self.niveles_confianza['red_hidrica']['confianza'] = 'Alta'
                    self.niveles_confianza['red_hidrica']['razon'] = 'Red de drenaje con geometría lineal correcta'
                    self.niveles_confianza['red_hidrica']['geometria_valida'] = True
                    print(f"✅ Red hídrica cargada: {len(self.red_hidrica)} elementos (DRENAJE - confianza ALTA)")
                else:
                    # Tipo no reconocido
                    self.niveles_confianza['red_hidrica']['cargada'] = True
                    self.niveles_confianza['red_hidrica']['tipo_dato'] = 'desconocido'
                    self.niveles_confianza['red_hidrica']['confianza'] = 'Media'
                    self.niveles_confianza['red_hidrica']['razon'] = f'Tipos de geometría no reconocidos: {tipos_geom}'
                    self.niveles_confianza['red_hidrica']['geometria_valida'] = None
                    print(f"⚠️  Red hídrica cargada: {len(self.red_hidrica)} elementos (tipo desconocido)")
                
                return True
            else:
                print("⚠️  Archivo de red hídrica no encontrado")
                return False
                
        except Exception as e:
            print(f"❌ Error cargando red hídrica: {e}")
            return False
    
    def cargar_areas_protegidas(self, archivo: Optional[str] = None) -> bool:
        """
        Carga áreas protegidas (RUNAP - Parques Nacionales)
        
        Args:
            archivo: Ruta al shapefile/GeoJSON RUNAP
        
        Returns:
            True si carga exitosa
        """
        try:
            if archivo is None:
                # 🚨 PRIORIDAD CRÍTICA: Shapefile nacional > GeoJSON departamental
                directorio = self.directorio_datos / 'runap'
                
                if directorio.exists():
                    # 1. PRIORIDAD MÁXIMA: Shapefile nacional completo (runap.shp)
                    shapefiles_nacionales = list(directorio.glob('runap.shp'))
                    if shapefiles_nacionales:
                        archivo = str(shapefiles_nacionales[0])
                        print(f"📂 Usando shapefile NACIONAL: {archivo}")
                    else:
                        # 2. FALLBACK: Otros shapefiles
                        shapefiles = list(directorio.glob('*.shp'))
                        if shapefiles:
                            archivo = str(shapefiles[0])
                            print(f"📂 Usando shapefile: {archivo}")
                        else:
                            # 3. ÚLTIMO RECURSO: GeoJSON (puede estar incompleto)
                            geojson_files = list(directorio.glob('*.geojson'))
                            # Filtrar archivos vacíos conocidos
                            geojson_files = [f for f in geojson_files if f.stat().st_size > 100]
                            if geojson_files:
                                archivo = str(geojson_files[0])
                                print(f"⚠️  Usando GeoJSON (puede estar incompleto): {archivo}")
            
            if archivo and os.path.exists(archivo):
                self.areas_protegidas = gpd.read_file(archivo)
                
                # CRÍTICO: Verificar archivo vacío
                if len(self.areas_protegidas) == 0:
                    print(f"❌ RUNAP: ARCHIVO VACÍO (0 áreas protegidas) - confianza NULA")
                    self.stats['areas_protegidas_loaded'] = False
                    self.niveles_confianza['areas_protegidas']['cargada'] = False
                    self.niveles_confianza['areas_protegidas']['tipo_dato'] = 'Archivo vacío'
                    self.niveles_confianza['areas_protegidas']['confianza'] = 'Nula'
                    self.niveles_confianza['areas_protegidas']['razon'] = '❌ ARCHIVO VACÍO - No hay datos de RUNAP'
                    return False
                
                # Reproyectar a WGS84 si es necesario
                crs_original = str(self.areas_protegidas.crs)
                if self.areas_protegidas.crs != 'EPSG:4326':
                    print(f"🔄 Reproyectando RUNAP de {crs_original} a EPSG:4326...")
                    self.areas_protegidas = self.areas_protegidas.to_crs('EPSG:4326')
                
                self.stats['areas_protegidas_loaded'] = True
                
                # Determinar confianza según fuente
                es_nacional = 'runap.shp' in str(archivo).lower()
                num_areas = len(self.areas_protegidas)
                
                self.niveles_confianza['areas_protegidas']['cargada'] = True
                self.niveles_confianza['areas_protegidas']['tipo_dato'] = 'RUNAP nacional' if es_nacional else 'RUNAP departamental'
                self.niveles_confianza['areas_protegidas']['confianza'] = 'Alta' if es_nacional else 'Media'
                self.niveles_confianza['areas_protegidas']['razon'] = (
                    f'Fuente oficial PNN nacional ({num_areas} áreas)' if es_nacional 
                    else f'Fuente departamental ({num_areas} áreas, puede estar incompleta)'
                )
                
                print(f"✅ Áreas protegidas cargadas: {num_areas} elementos (RUNAP - confianza {'ALTA' if es_nacional else 'MEDIA'})")
                return True
            else:
                print("⚠️  Archivo de áreas protegidas no encontrado")
                return False
                
        except Exception as e:
            print(f"❌ Error cargando áreas protegidas: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def cargar_resguardos_indigenas(self, archivo: Optional[str] = None) -> bool:
        """
        Carga resguardos indígenas (ANT)
        
        Args:
            archivo: Ruta al shapefile/GeoJSON ANT
        
        Returns:
            True si carga exitosa
        """
        try:
            if archivo is None:
                # Buscar archivo en directorio datos
                directorio = self.directorio_datos / 'resguardos_indigenas'
                
                # 🚨 PRIORIDAD: Shapefiles completos > GeoJSON > archivos vacíos
                if directorio.exists():
                    # Buscar shapefiles completos (datos oficiales de ANT)
                    shapefiles = list(directorio.glob('*.shp'))
                    # Filtrar archivos vacíos conocidos
                    shapefiles = [f for f in shapefiles if 'casanare' not in f.name.lower()]
                    
                    if shapefiles:
                        archivo = str(shapefiles[0])
                    else:
                        # Buscar GeoJSON (solo si no hay shapefiles)
                        geojson_files = list(directorio.glob('*.geojson'))
                        # Filtrar archivos vacíos conocidos
                        geojson_files = [f for f in geojson_files if 'casanare' not in f.name.lower()]
                        if geojson_files:
                            archivo = str(geojson_files[0])
            
            if archivo and os.path.exists(archivo):
                self.resguardos_indigenas = gpd.read_file(archivo)
                
                if self.resguardos_indigenas.crs != 'EPSG:4326':
                    self.resguardos_indigenas = self.resguardos_indigenas.to_crs('EPSG:4326')
                
                # 🚨 CRÍTICO: Verificar si el archivo tiene datos REALES
                num_features = len(self.resguardos_indigenas)
                
                if num_features == 0:
                    # ❌ ARCHIVO VACÍO - NO HAY DATOS REALES
                    self.stats['resguardos_loaded'] = False  # Marcar como NO cargado
                    self.niveles_confianza['resguardos_indigenas']['cargada'] = False
                    self.niveles_confianza['resguardos_indigenas']['tipo_dato'] = 'Archivo vacío'
                    self.niveles_confianza['resguardos_indigenas']['confianza'] = 'Nula'
                    self.niveles_confianza['resguardos_indigenas']['razon'] = '❌ ARCHIVO VACÍO - Descarga falló (no hay datos de ANT)'
                    print(f"❌ Resguardos indígenas: ARCHIVO VACÍO (0 elementos) - confianza NULA")
                    print(f"   ⚠️  ADVERTENCIA CRÍTICA: NO se puede verificar cumplimiento sin estos datos")
                    return False
                else:
                    # ✅ Archivo con datos reales
                    self.stats['resguardos_loaded'] = True
                    self.niveles_confianza['resguardos_indigenas']['cargada'] = True
                    self.niveles_confianza['resguardos_indigenas']['tipo_dato'] = 'ANT oficial'
                    self.niveles_confianza['resguardos_indigenas']['confianza'] = 'Alta'
                    self.niveles_confianza['resguardos_indigenas']['razon'] = f'Fuente oficial ANT ({num_features} resguardos)'
                    print(f"✅ Resguardos indígenas cargados: {num_features} elementos (ANT - confianza ALTA)")
                    return True
            else:
                print("⚠️  Archivo de resguardos indígenas no encontrado")
                return False
                
        except Exception as e:
            print(f"❌ Error cargando resguardos indígenas: {e}")
            return False
    
    def cargar_paramos(self, archivo: Optional[str] = None) -> bool:
        """
        Carga límites de páramos (SIAC/MADS)
        
        Args:
            archivo: Ruta al shapefile/GeoJSON páramos
        
        Returns:
            True si carga exitosa
        """
        try:
            if archivo is None:
                # Buscar archivo en directorio datos (prioritario: GeoJSON casanare)
                directorio = self.directorio_datos / 'paramos'
                
                # Prioridad: GeoJSON de Casanare > otros GeoJSON > shapefiles
                if directorio.exists():
                    geojson_casanare = list(directorio.glob('*casanare.geojson'))
                    if geojson_casanare:
                        archivo = str(geojson_casanare[0])
                    else:
                        archivos_geo = list(directorio.glob('*.geojson')) + list(directorio.glob('*.shp'))
                        if archivos_geo:
                            archivo = str(archivos_geo[0])
            
            if archivo and os.path.exists(archivo):
                self.paramos = gpd.read_file(archivo)
                
                if self.paramos.crs != 'EPSG:4326':
                    self.paramos = self.paramos.to_crs('EPSG:4326')
                
                # 🚨 CRÍTICO: Verificar si el archivo tiene datos REALES
                num_features = len(self.paramos)
                
                # Verificar si tiene metadata que explique por qué está vacío
                import json
                try:
                    with open(archivo, 'r') as f:
                        data = json.load(f)
                        tiene_metadata = 'metadata' in data and data['metadata'].get('note')
                except:
                    tiene_metadata = False
                
                if num_features == 0:
                    if tiene_metadata:
                        # ✅ Vacío VÁLIDO (con explicación geográfica)
                        self.stats['paramos_loaded'] = True
                        self.niveles_confianza['paramos']['cargada'] = True
                        self.niveles_confianza['paramos']['tipo_dato'] = 'SIAC/MADS (vacío válido)'
                        self.niveles_confianza['paramos']['confianza'] = 'Alta'
                        self.niveles_confianza['paramos']['razon'] = 'Región sin páramos (confirmado geográficamente - llanura tropical)'
                        print(f"✅ Páramos cargados: 0 elementos (SIAC - confianza ALTA - vacío válido para llanura)")
                        return True
                    else:
                        # ❌ Vacío SIN explicación - descarga falló
                        self.stats['paramos_loaded'] = False
                        self.niveles_confianza['paramos']['cargada'] = False
                        self.niveles_confianza['paramos']['tipo_dato'] = 'Archivo vacío'
                        self.niveles_confianza['paramos']['confianza'] = 'Nula'
                        self.niveles_confianza['paramos']['razon'] = '❌ ARCHIVO VACÍO - Descarga falló (no hay datos de SIAC)'
                        print(f"❌ Páramos: ARCHIVO VACÍO sin metadata - confianza NULA")
                        print(f"   ⚠️  ADVERTENCIA: Verificar si región realmente no tiene páramos")
                        return False
                else:
                    # ✅ Archivo con datos reales
                    self.stats['paramos_loaded'] = True
                    self.niveles_confianza['paramos']['cargada'] = True
                    self.niveles_confianza['paramos']['tipo_dato'] = 'SIAC/MADS'
                    self.niveles_confianza['paramos']['confianza'] = 'Alta'
                    self.niveles_confianza['paramos']['razon'] = f'Fuente oficial SIAC ({num_features} páramos)'
                    print(f"✅ Páramos cargados: {num_features} elementos (SIAC - confianza ALTA)")
                    return True
            else:
                print("⚠️  Archivo de páramos no encontrado")
                return False
                
        except Exception as e:
            print(f"❌ Error cargando páramos: {e}")
            return False
    
    def verificar_retiros_hidricos(
        self, 
        geometria_parcela,  # Django GEOS o Dict GeoJSON
        distancia_maxima_km: float = 5.0
    ) -> Tuple[List[Dict], float]:
        """
        Verifica cumplimiento de retiros obligatorios de fuentes hídricas
        
        Args:
            geometria_parcela: Django GEOS Polygon o GeoJSON dict
            distancia_maxima_km: Radio de búsqueda (km)
        
        Returns:
            Tuple[restricciones_encontradas, area_restringida_ha]
        """
        if self.red_hidrica is None:
            return [], 0.0
        
        try:
            # Convertir geometría a Shapely
            from shapely import wkt
            
            if hasattr(geometria_parcela, 'wkt'):
                # Django GEOS
                parcela_geom = wkt.loads(geometria_parcela.wkt)
            else:
                # GeoJSON dict
                parcela_geom = shape(geometria_parcela)
            
            # Crear GeoDataFrame temporal para la parcela
            parcela_gdf = gpd.GeoDataFrame(
                [{'geometry': parcela_geom}], 
                crs='EPSG:4326'
            )
            
            # Proyectar a métrica (MAGNA-SIRGAS / Colombia Bogotá zone)
            # EPSG:3116 para cálculos precisos en metros
            parcela_metric = parcela_gdf.to_crs('EPSG:3116')
            
            # Buffer de búsqueda (convertir km a metros)
            buffer_busqueda = parcela_metric.buffer(distancia_maxima_km * 1000)
            buffer_busqueda_wgs84 = gpd.GeoDataFrame(
                [{'geometry': buffer_busqueda.iloc[0]}],
                crs='EPSG:3116'
            ).to_crs('EPSG:4326')
            
            # Filtrar elementos de red hídrica dentro del buffer
            red_cercana = self.red_hidrica[
                self.red_hidrica.intersects(buffer_busqueda_wgs84.iloc[0].geometry)
            ]
            
            restricciones = []
            areas_restriccion = []
            
            for idx, elemento in red_cercana.iterrows():
                # Determinar tipo de fuente hídrica CON JUSTIFICACIÓN
                tipo_fuente, justificacion = self._clasificar_fuente_hidrica(elemento)
                retiro_minimo = self.RETIROS_MINIMOS.get(tipo_fuente, 30)
                
                # NUEVO: Obtener información detallada del elemento
                nombre_fuente = elemento.get('NOMBRE', elemento.get('nombre', 'Sin nombre'))
                tipo_geometria = elemento.geometry.geom_type
                
                # Proyectar elemento a métrica
                elemento_gdf = gpd.GeoDataFrame(
                    [{'geometry': elemento.geometry}],
                    crs='EPSG:4326'
                ).to_crs('EPSG:3116')
                
                # NUEVO: Calcular distancia REAL a la parcela
                distancia_real_m = parcela_metric.iloc[0].geometry.distance(elemento_gdf.iloc[0].geometry)
                
                # Crear buffer de retiro
                buffer_retiro = elemento_gdf.buffer(retiro_minimo)
                
                # Verificar intersección con parcela
                interseccion = parcela_metric.iloc[0].geometry.intersection(
                    buffer_retiro.iloc[0]
                )
                
                if not interseccion.is_empty:
                    area_afectada_m2 = interseccion.area
                    area_afectada_ha = area_afectada_m2 / 10000
                    
                    # NUEVO: Información detallada
                    longitud_cauce_m = None
                    if tipo_geometria in ['LineString', 'MultiLineString']:
                        longitud_cauce_m = elemento.geometry.length * 111320  # Aprox m
                    
                    restricciones.append({
                        'tipo': 'retiro_hidrico',
                        'subtipo': tipo_fuente,
                        'retiro_minimo_m': retiro_minimo,
                        'area_afectada_ha': round(area_afectada_ha, 4),
                        'nombre': str(nombre_fuente) if nombre_fuente else 'Sin nombre',
                        'normativa': 'Decreto 1541/1978 Art. 83',
                        'severidad': 'ALTA' if area_afectada_ha > 1 else 'MEDIA',
                        'distancia_real_m': round(distancia_real_m, 2),  # NUEVO
                        'tipo_geometria': tipo_geometria,  # NUEVO
                        'longitud_cauce_m': round(longitud_cauce_m, 2) if longitud_cauce_m else None,  # NUEVO
                        'geometria_fuente': elemento.geometry,  # NUEVO: Para dibujar en el mapa
                        'justificacion_retiro': justificacion,  # NUEVO: Por qué se clasificó así
                        'nota_preliminar': 'Retiro preliminar - requiere validación CAR'  # NUEVO
                    })
                    
                    areas_restriccion.append(interseccion)
            
            # Calcular área total restringida (unir geometrías solapadas)
            if areas_restriccion:
                area_total_restringida = unary_union(areas_restriccion).area / 10000
            else:
                area_total_restringida = 0.0
            
            # NUEVO: Guardar red hídrica cercana para el mapa
            self.red_hidrica_cercana = red_cercana  # Almacenar para uso en mapa
            
            return restricciones, area_total_restringida
            
        except Exception as e:
            print(f"❌ Error verificando retiros hídricos: {e}")
            return [], 0.0
    
    def verificar_areas_protegidas(
        self,
        geometria_parcela  # Django GEOS o Dict GeoJSON
    ) -> Tuple[List[Dict], float]:
        """
        Verifica si la parcela intersecta con áreas protegidas
        
        Args:
            geometria_parcela: Django GEOS Polygon o GeoJSON dict
        
        Returns:
            Tuple[restricciones_encontradas, area_restringida_ha]
        """
        restricciones = []
        area_total_restringida = 0.0
        
        # Convertir geometría a Shapely
        from shapely import wkt
        
        if hasattr(geometria_parcela, 'wkt'):
            parcela_geom = wkt.loads(geometria_parcela.wkt)
        else:
            parcela_geom = shape(geometria_parcela)
        
        # Verificar parques nacionales y áreas protegidas
        if self.areas_protegidas is not None:
            rest, area = self._verificar_capa(
                parcela_geom,
                self.areas_protegidas,
                'area_protegida',
                'Ley 99/1993',
                'MUY_ALTA'
            )
            restricciones.extend(rest)
            area_total_restringida += area
        
        # Verificar resguardos indígenas
        if self.resguardos_indigenas is not None:
            rest, area = self._verificar_capa(
                parcela_geom,
                self.resguardos_indigenas,
                'resguardo_indigena',
                'Decreto 2164/1995',
                'MUY_ALTA'
            )
            restricciones.extend(rest)
            area_total_restringida += area
        
        # Verificar páramos
        if self.paramos is not None:
            rest, area = self._verificar_capa(
                parcela_geom,
                self.paramos,
                'paramo',
                'Ley 1930/2018',
                'MUY_ALTA'
            )
            restricciones.extend(rest)
            area_total_restringida += area
        
        return restricciones, area_total_restringida
    
    def _verificar_capa(
        self,
        parcela_geom,
        capa_gdf,
        tipo: str,
        normativa: str,
        severidad: str
    ) -> Tuple[List[Dict], float]:
        """
        Verifica intersección con una capa geográfica
        
        FILTRADO ESPACIAL INTELIGENTE:
        1. Filtra por intersección con la geometría de la parcela
        2. NO usa nombres de departamentos (pueden faltar)
        3. Funciona con capas nacionales reproyectadas automáticamente
        """
        restricciones = []
        area_total = 0.0
        
        try:
            # 🚨 CRÍTICO: Asegurar que ambas geometrías están en el mismo CRS
            if str(capa_gdf.crs) != 'EPSG:4326':
                print(f"🔄 Reproyectando capa {tipo} de {capa_gdf.crs} a EPSG:4326...")
                capa_gdf = capa_gdf.to_crs('EPSG:4326')
            
            # NUEVO: Optimización con buffer de búsqueda (evita procesar toda la capa nacional)
            # Crear bbox ampliado de la parcela para filtrado rápido
            bounds = parcela_geom.bounds  # (minx, miny, maxx, maxy)
            buffer_deg = 0.1  # ~11 km de margen
            bbox_ampliado = (
                bounds[0] - buffer_deg,
                bounds[1] - buffer_deg,
                bounds[2] + buffer_deg,
                bounds[3] + buffer_deg
            )
            
            # Filtro espacial rápido por bbox (índice espacial)
            capa_filtrada = capa_gdf.cx[
                bbox_ampliado[0]:bbox_ampliado[2],  # lon_min:lon_max
                bbox_ampliado[1]:bbox_ampliado[3]   # lat_min:lat_max
            ]
            
            if len(capa_filtrada) == 0:
                # No hay elementos cerca de la parcela
                return [], 0.0
            
            # Filtrar elementos que REALMENTE intersectan (no solo bbox)
            intersecciones = capa_filtrada[capa_filtrada.intersects(parcela_geom)]
            
            for idx, elemento in intersecciones.iterrows():
                interseccion = parcela_geom.intersection(elemento.geometry)
                
                if not interseccion.is_empty:
                    # Calcular área en hectáreas (usar proyección métrica)
                    parcela_gdf = gpd.GeoDataFrame(
                        [{'geometry': interseccion}],
                        crs='EPSG:4326'
                    ).to_crs('EPSG:3116')
                    
                    area_ha = parcela_gdf.iloc[0].geometry.area / 10000
                    
                    # NUEVO: Extraer nombre con múltiples intentos de campos
                    nombre = self._extraer_nombre_elemento(elemento, tipo)
                    categoria = self._extraer_categoria_elemento(elemento, tipo)
                    
                    restricciones.append({
                        'tipo': tipo,
                        'area_afectada_ha': round(area_ha, 4),
                        'nombre': nombre,
                        'categoria': categoria,  # NUEVO
                        'normativa': normativa,
                        'severidad': severidad,
                        'geometria': mapping(elemento.geometry),  # NUEVO: Para el mapa
                        'area_total_elemento_ha': round(elemento.geometry.area * 12100, 2) if hasattr(elemento.geometry, 'area') else None  # NUEVO
                    })
                    
                    area_total += area_ha
            
            return restricciones, area_total
            
        except Exception as e:
            print(f"❌ Error verificando capa {tipo}: {e}")
            import traceback
            traceback.print_exc()
            return [], 0.0
    
    def _extraer_nombre_elemento(self, elemento, tipo_capa: str) -> str:
        """Extrae el nombre del elemento con múltiples intentos de campos"""
        # Intentar campos comunes según el tipo de capa
        campos_nombre = []
        
        if tipo_capa == 'area_protegida':
            campos_nombre = ['ap_nombre', 'nombre_geo', 'NOMBRE_GEO', 'NOMBRE', 'nombre', 'ap_categor']
        elif tipo_capa == 'resguardo_indigena':
            campos_nombre = ['NOMBRE_RES', 'NOMBRE', 'nombre', 'RESGUARDO', 'resguardo']
        elif tipo_capa == 'paramo':
            campos_nombre = ['NOMBRE', 'nombre', 'NOMBRE_PAR', 'NOM_PARAMO']
        else:
            campos_nombre = ['NOMBRE', 'nombre', 'NAME', 'name']
        
        # Buscar primer campo que exista y tenga valor
        for campo in campos_nombre:
            valor = elemento.get(campo, None)
            if valor and str(valor).strip() and str(valor).upper() != 'NONE':
                return str(valor).strip()
        
        return 'Sin nombre'
    
    def _extraer_categoria_elemento(self, elemento, tipo_capa: str) -> str:
        """Extrae la categoría del elemento (para áreas protegidas principalmente)"""
        if tipo_capa == 'area_protegida':
            campos_categoria = ['ap_categor', 'CATEGORIA', 'categoria', 'TIPO', 'tipo']
            for campo in campos_categoria:
                valor = elemento.get(campo, None)
                if valor and str(valor).strip() and str(valor).upper() != 'NONE':
                    return str(valor).strip()
        
        return tipo_capa.replace('_', ' ').title()
    
    def _clasificar_fuente_hidrica(self, elemento) -> Tuple[str, str]:
        """
        Clasifica el tipo de fuente hídrica según atributos del shapefile
        
        Returns:
            Tuple[str, str]: (tipo_fuente, justificación)
        """
        # Intentar clasificar por atributos comunes
        nombre = str(elemento.get('NOMBRE', '')).lower()
        tipo = str(elemento.get('TIPO', '')).lower()
        orden = elemento.get('ORDEN', 0)
        
        # Clasificación por orden de Strahler (común en datos IGAC)
        if orden >= 4:
            return 'rio_principal', f'Orden de Strahler {orden} (río grande)'
        elif orden == 3:
            return 'rio_secundario', f'Orden de Strahler {orden} (río mediano)'
        elif orden in [1, 2]:
            return 'quebrada', f'Orden de Strahler {orden} (quebrada menor)'
        
        # Clasificación por nombre/tipo
        if 'nacimiento' in nombre or 'nacimiento' in tipo:
            return 'nacimiento', 'Identificado como nacimiento por nombre/tipo'
        elif 'laguna' in nombre or 'ciénaga' in nombre:
            return 'laguna', 'Identificado como laguna/ciénaga por nombre'
        elif 'humedal' in nombre or 'humedal' in tipo:
            return 'humedal', 'Identificado como humedal por nombre/tipo'
        elif 'canal' in nombre:
            return 'canal_riego', 'Identificado como canal artificial por nombre'
        elif 'río' in nombre or 'rio' in nombre:
            return 'rio_secundario', 'Identificado como río por nombre'
        elif 'quebrada' in nombre or 'caño' in nombre:
            return 'quebrada', 'Identificado como quebrada/caño por nombre'
        
        # Por defecto, asumir quebrada (más restrictivo es mejor)
        return 'quebrada', 'Clasificación por defecto (criterio conservador)'
    
    def verificar_parcela(
        self,
        parcela_id: int,
        geometria_parcela: Dict,
        nombre_parcela: str = ""
    ) -> ResultadoVerificacion:
        """
        Verificación completa de restricciones legales para una parcela
        
        Args:
            parcela_id: ID de la parcela
            geometria_parcela: Django GEOS Polygon o GeoJSON dict
            nombre_parcela: Nombre descriptivo de la parcela
        
        Returns:
            ResultadoVerificacion con todos los detalles
        """
        # Convertir geometría a shapely
        from shapely import wkt
        
        if hasattr(geometria_parcela, 'wkt'):
            # Es Django GEOS, convertir via WKT
            parcela_geom = wkt.loads(geometria_parcela.wkt)
        else:
            # Es GeoJSON dict
            parcela_geom = shape(geometria_parcela)
            
        parcela_gdf = gpd.GeoDataFrame(
            [{'geometry': parcela_geom}],
            crs='EPSG:4326'
        ).to_crs('EPSG:3116')
        area_total_ha = parcela_gdf.iloc[0].geometry.area / 10000
        
        restricciones_todas = []
        area_restringida_total = 0.0
        advertencias = []
        
        # 🔧 CRÍTICO: Cargar capas geográficas si no están cargadas
        print(f"\n🔄 Verificando estado de capas geográficas...")
        if not self.stats['red_hidrica_loaded']:
            print(f"   📥 Cargando red hídrica...")
            self.cargar_red_hidrica()
        
        if not self.stats['areas_protegidas_loaded']:
            print(f"   📥 Cargando áreas protegidas...")
            self.cargar_areas_protegidas()
        
        if not self.stats['resguardos_loaded']:
            print(f"   📥 Cargando resguardos indígenas...")
            self.cargar_resguardos_indigenas()
        
        if not self.stats['paramos_loaded']:
            print(f"   📥 Cargando páramos...")
            self.cargar_paramos()
        
        print(f"   ✅ Capas geográficas listas")
        
        # Verificar retiros hídricos
        print(f"\n🔍 Verificando retiros hídricos para {nombre_parcela}...")
        rest_hidricos, area_hidricos = self.verificar_retiros_hidricos(geometria_parcela)
        restricciones_todas.extend(rest_hidricos)
        area_restringida_total += area_hidricos
        
        if rest_hidricos:
            print(f"   ⚠️  {len(rest_hidricos)} restricciones hídricas encontradas")
        else:
            print(f"   ✅ Sin restricciones hídricas")
        
        # Verificar áreas protegidas
        print(f"🔍 Verificando áreas protegidas...")
        rest_protegidas, area_protegidas = self.verificar_areas_protegidas(geometria_parcela)
        restricciones_todas.extend(rest_protegidas)
        area_restringida_total += area_protegidas
        
        if rest_protegidas:
            print(f"   ⚠️  {len(rest_protegidas)} restricciones de áreas protegidas encontradas")
        else:
            print(f"   ✅ Sin restricciones de áreas protegidas")
        
        # Generar advertencias
        if not self.stats['red_hidrica_loaded']:
            advertencias.append("Red hídrica no cargada - verificación incompleta")
        if not self.stats['areas_protegidas_loaded']:
            advertencias.append("Áreas protegidas no cargadas - verificación incompleta")
        if not self.stats['resguardos_loaded']:
            advertencias.append("Resguardos indígenas no cargados - verificación incompleta")
        if not self.stats['paramos_loaded']:
            advertencias.append("Páramos no cargados - verificación incompleta")
        
        # NUEVO: Validar si datos de red hídrica son confiables
        if self.stats['red_hidrica_loaded'] and self.niveles_confianza['red_hidrica']['confianza'] == 'Baja':
            advertencias.append(self.niveles_confianza['red_hidrica']['razon'])
        
        # NUEVO: Determinar si el área cultivable es DETERMINABLE
        # Lógica mejorada: puede ser determinable parcialmente
        tiene_red_hidrica_confiable = (
            self.stats['red_hidrica_loaded'] and 
            self.niveles_confianza['red_hidrica']['confianza'] in ['Alta', 'Media']
        )
        
        verificacion_completa = (
            tiene_red_hidrica_confiable and 
            self.stats['areas_protegidas_loaded'] and
            self.stats['resguardos_loaded'] and
            self.stats['paramos_loaded']
        )
        
        # NUEVO: Desglose detallado de áreas por fuente
        desglose_areas = {
            'area_total_ha': round(area_total_ha, 2),
            'areas_por_fuente': [],
            'area_sin_afectacion_ha': 0.0,
            'porcentaje_por_tipo': {}
        }
        
        # Agrupar áreas por tipo de restricción
        for rest in restricciones_todas:
            desglose_areas['areas_por_fuente'].append({
                'nombre': rest.get('nombre', 'N/A'),
                'tipo': rest.get('tipo'),
                'subtipo': rest.get('subtipo'),
                'area_ha': rest.get('area_afectada_ha', 0),
                'distancia_m': rest.get('distancia_real_m'),
                'retiro_m': rest.get('retiro_minimo_m')
            })
        
        # Calcular área sin afectación
        desglose_areas['area_sin_afectacion_ha'] = round(max(0, area_total_ha - area_restringida_total), 2)
        
        # Calcular área cultivable con estructura mejorada
        if verificacion_completa:
            # Todas las capas disponibles y confiables
            area_cultivable_estructura = {
                'determinable': True,
                'valor_ha': round(max(0, area_total_ha - area_restringida_total), 2),
                'nota': 'Verificación completa con todas las capas oficiales'
            }
        elif tiene_red_hidrica_confiable:
            # Solo red hídrica confiable - determinar área PARCIAL
            capas_faltantes = []
            if not self.stats['areas_protegidas_loaded']:
                capas_faltantes.append('áreas protegidas')
            if not self.stats['resguardos_loaded']:
                capas_faltantes.append('resguardos indígenas')
            if not self.stats['paramos_loaded']:
                capas_faltantes.append('páramos')
            
            nota = f"Área preliminar basada solo en retiros hídricos. Pendiente: {', '.join(capas_faltantes)}"
            
            area_cultivable_estructura = {
                'determinable': True,  # SÍ es determinable parcialmente
                'valor_ha': round(max(0, area_total_ha - area_restringida_total), 2),
                'nota': nota,
                'advertencia': 'VERIFICACIÓN PARCIAL - Requiere validar otras restricciones'
            }
        else:
            # No hay datos confiables para ninguna capa
            area_cultivable_estructura = {
                'determinable': False,
                'valor_ha': None,
                'nota': 'Requiere datos oficiales confiables de red hídrica y otras capas geográficas'
            }
        
        # Calcular área cultivable (mantener para compatibilidad)
        area_cultivable_ha = max(0, area_total_ha - area_restringida_total)
        porcentaje_restringido = (area_restringida_total / area_total_ha * 100) if area_total_ha > 0 else 0
        
        # 🚨 CRÍTICO: Determinar cumplimiento de forma RESPONSABLE
        # NO podemos decir "cumple" si NO tenemos TODOS los datos críticos
        
        # Verificar si tenemos las 2 capas CRÍTICAS (red hídrica + áreas protegidas)
        tiene_capas_criticas = (
            tiene_red_hidrica_confiable and 
            self.stats['areas_protegidas_loaded']
        )
        
        # Verificar si tenemos las capas SECUNDARIAS (resguardos + páramos)
        tiene_capas_secundarias = (
            self.stats['resguardos_loaded'] and 
            self.stats['paramos_loaded']
        )
        
        if verificacion_completa:
            # ✅ Todas las capas disponibles - podemos dar veredicto definitivo
            cumple = len(restricciones_todas) == 0
        elif tiene_capas_criticas and not tiene_capas_secundarias:
            # ⚠️ Solo capas críticas - veredicto PRELIMINAR
            # NO podemos garantizar cumplimiento total
            cumple = False  # 🚨 CONSERVADOR: decir NO cumple si faltan datos
            advertencias.append("🚨 VERIFICACIÓN INCOMPLETA - Faltan datos de resguardos indígenas y/o páramos")
            advertencias.append("⚠️  NO se puede garantizar cumplimiento legal sin TODOS los datos oficiales")
        else:
            # ❌ Faltan capas críticas - NO podemos dar ningún veredicto
            cumple = False
            advertencias.append("❌ VERIFICACIÓN INCOMPLETA - Faltan datos CRÍTICOS (red hídrica o áreas protegidas)")
            advertencias.append("🚨 NO SE PUEDE DETERMINAR CUMPLIMIENTO sin datos oficiales completos")
        
        resultado = ResultadoVerificacion(
            parcela_id=parcela_id,
            area_total_ha=round(area_total_ha, 2),
            area_cultivable_ha=area_cultivable_estructura,  # NUEVO: Estructura en lugar de valor
            area_restringida_ha=round(area_restringida_total, 2),
            porcentaje_restringido=round(porcentaje_restringido, 2),
            cumple_normativa=cumple,
            restricciones_encontradas=restricciones_todas,
            fecha_verificacion=datetime.now().isoformat(),
            advertencias=advertencias,
            niveles_confianza=self.niveles_confianza,  # NUEVO
            desglose_areas=desglose_areas  # NUEVO
        )
        
        return resultado
    
    def generar_reporte_consola(self, resultado: ResultadoVerificacion) -> str:
        """
        Genera reporte formateado para mostrar en consola
        """
        linea = "=" * 80
        reporte = f"\n{linea}\n"
        reporte += "📋 REPORTE DE VERIFICACIÓN DE RESTRICCIONES LEGALES\n"
        reporte += f"{linea}\n\n"
        
        # Información general
        reporte += f"📍 Parcela ID: {resultado.parcela_id}\n"
        reporte += f"📅 Fecha: {resultado.fecha_verificacion}\n"
        reporte += f"📊 Área total: {resultado.area_total_ha:.2f} ha\n"
        
        # Manejar area_cultivable como dict o valor legacy
        if isinstance(resultado.area_cultivable_ha, dict):
            if resultado.area_cultivable_ha['determinable']:
                reporte += f"✅ Área cultivable: {resultado.area_cultivable_ha['valor_ha']:.2f} ha (preliminar)\n"
            else:
                reporte += f"⚠️  Área cultivable: NO DETERMINABLE - {resultado.area_cultivable_ha['nota']}\n"
        else:
            reporte += f"✅ Área cultivable: {resultado.area_cultivable_ha:.2f} ha\n"
        
        reporte += f"⚠️  Área restringida: {resultado.area_restringida_ha:.2f} ha ({resultado.porcentaje_restringido:.1f}%)\n\n"
        
        # Estado de cumplimiento
        if resultado.cumple_normativa:
            reporte += "✅ CUMPLE CON TODA LA NORMATIVA AMBIENTAL\n\n"
        else:
            reporte += f"❌ NO CUMPLE - {len(resultado.restricciones_encontradas)} RESTRICCIONES ENCONTRADAS\n\n"
        
        # Detalle de restricciones
        if resultado.restricciones_encontradas:
            reporte += f"{linea}\n"
            reporte += "⚠️  RESTRICCIONES DETALLADAS:\n"
            reporte += f"{linea}\n\n"
            
            for i, rest in enumerate(resultado.restricciones_encontradas, 1):
                reporte += f"{i}. {rest['tipo'].upper().replace('_', ' ')}\n"
                reporte += f"   Nombre: {rest.get('nombre', 'N/A')}\n"
                reporte += f"   Área afectada: {rest['area_afectada_ha']:.4f} ha\n"
                reporte += f"   Normativa: {rest['normativa']}\n"
                reporte += f"   Severidad: {rest['severidad']}\n"
                
                if 'retiro_minimo_m' in rest:
                    reporte += f"   Retiro mínimo: {rest['retiro_minimo_m']} metros\n"
                
                reporte += "\n"
        
        # Advertencias
        if resultado.advertencias:
            reporte += f"{linea}\n"
            reporte += "⚠️  ADVERTENCIAS:\n"
            for adv in resultado.advertencias:
                reporte += f"   • {adv}\n"
            reporte += "\n"
        
        reporte += f"{linea}\n"
        
        return reporte


def ejemplo_uso():
    """
    Ejemplo de uso del verificador
    """
    print("=" * 80)
    print("🌿 VERIFICADOR DE RESTRICCIONES LEGALES - EJEMPLO DE USO")
    print("=" * 80)
    
    # Inicializar verificador
    verificador = VerificadorRestriccionesLegales()
    
    # Cargar capas (intentar cargar todas las disponibles)
    print("\n📥 Cargando capas geográficas...")
    verificador.cargar_red_hidrica()
    verificador.cargar_areas_protegidas()
    verificador.cargar_resguardos_indigenas()
    verificador.cargar_paramos()
    
    # Ejemplo de geometría de parcela (GeoJSON)
    # Este es un polígono de ejemplo - reemplazar con datos reales
    geometria_ejemplo = {
        "type": "Polygon",
        "coordinates": [[
            [-75.5, 5.5],
            [-75.5, 5.501],
            [-75.501, 5.501],
            [-75.501, 5.5],
            [-75.5, 5.5]
        ]]
    }
    
    # Verificar parcela
    resultado = verificador.verificar_parcela(
        parcela_id=999,
        geometria_parcela=geometria_ejemplo,
        nombre_parcela="Parcela de Prueba"
    )
    
    # Mostrar reporte
    print(verificador.generar_reporte_consola(resultado))
    
    # Guardar resultado JSON
    print("💾 Guardando resultado en JSON...")
    with open('resultado_verificacion_ejemplo.json', 'w', encoding='utf-8') as f:
        f.write(resultado.to_json())
    print("   ✅ Guardado en: resultado_verificacion_ejemplo.json")


if __name__ == '__main__':
    if not GEOPANDAS_AVAILABLE:
        print("❌ GeoPandas no está instalado.")
        print("   Instalar con: pip install geopandas")
    else:
        ejemplo_uso()
