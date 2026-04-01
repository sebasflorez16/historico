"""
Sistema híbrido de acceso a datos geográficos oficiales
========================================================

Estrategia inteligente:
1. Intenta API oficial (rápido, actualizado)
2. Si API falla → usa archivos locales (backup)
3. Si no hay archivos → ofrece descargarlos

Autor: AgroTech Histórico
Fecha: Enero 2026
"""

import requests
import geopandas as gpd
from pathlib import Path
from typing import Optional, Tuple
import json
from io import BytesIO
import warnings


class AccesoDatosHibrido:
    """
    Gestiona acceso híbrido a datos geográficos oficiales
    """
    
    # Configuración de APIs oficiales
    APIS_OFICIALES = {
        'runap': {
            'tipo': 'WFS',
            'url': 'http://mapas.parquesnacionales.gov.co/services/pnn/ows',
            'params': {
                'service': 'WFS',
                'version': '1.0.0',
                'request': 'GetFeature',
                'typeName': 'pnn:runap',
                'outputFormat': 'json'
            },
            'nombre': 'RUNAP - Áreas Protegidas'
        },
        'resguardos': {
            'tipo': 'REST',
            'url': 'https://www.datos.gov.co/resource/7n7q-5k8p.geojson',
            'params': {},
            'nombre': 'Resguardos Indígenas (ANT)'
        }
    }
    
    # URLs de descarga para archivos completos
    URLS_DESCARGA = {
        'red_hidrica': {
            'urls': [
                'https://www.colombiaenmapas.gov.co/SSIGL2.0/Descargas/Drenajes_sencillos.zip',
                'http://geoservicios.igac.gov.co/geonetwork/srv/api/records/2cac81da-3f68-4aa4-90ad-e815c3f87c32/attachments/Drenajes_Sencillos.zip',
            ],
            'archivo_local': 'red_hidrica',
            'descripcion': 'Red hidrográfica (IGAC)'
        },
        'runap': {
            'urls': [
                'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=SHAPE-ZIP',
            ],
            'archivo_local': 'runap',
            'descripcion': 'Áreas protegidas (RUNAP)'
        },
        'resguardos': {
            'urls': [
                'https://www.datos.gov.co/api/geospatial/7n7q-5k8p?method=export&format=Shapefile',
                'https://geoportal.ant.gov.co/descargas/resguardos_indigenas.zip',
            ],
            'archivo_local': 'ant',
            'descripcion': 'Resguardos indígenas (ANT)'
        },
        'paramos': {
            'urls': [
                'http://www.ideam.gov.co/documents/24277/95191925/Paramos_Delimitados_2023.zip',
                'http://geoservicios.ideam.gov.co/descargas/paramos_delimitados.zip',
            ],
            'archivo_local': 'ideam',
            'descripcion': 'Páramos delimitados (IDEAM)'
        }
    }
    
    def __init__(self, directorio_base='datos_geograficos'):
        self.directorio_base = Path(directorio_base)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AgroTech-Historico/1.0'
        })
        self.cache = {}
    
    def cargar_desde_api(self, nombre_capa: str, bbox: Optional[Tuple] = None) -> Optional[gpd.GeoDataFrame]:
        """
        Intenta cargar datos desde API oficial
        
        Args:
            nombre_capa: Nombre de la capa (runap, resguardos, etc)
            bbox: Bounding box (minx, miny, maxx, maxy) para filtrar área
        
        Returns:
            GeoDataFrame o None si falla
        """
        if nombre_capa not in self.APIS_OFICIALES:
            return None
        
        config = self.APIS_OFICIALES[nombre_capa]
        
        try:
            print(f"   🌐 Intentando API: {config['nombre']}...")
            
            params = config['params'].copy()
            
            # Agregar bbox si se proporciona
            if bbox and config['tipo'] == 'WFS':
                params['bbox'] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            
            response = self.session.get(
                config['url'],
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # Parsear GeoJSON
            geojson_data = response.json()
            
            if 'features' in geojson_data and len(geojson_data['features']) > 0:
                gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
                gdf.crs = 'EPSG:4326'
                print(f"      ✅ API: {len(gdf)} elementos descargados")
                return gdf
            else:
                print(f"      ⚠️  API sin datos para el área")
                return None
                
        except requests.Timeout:
            print(f"      ⏱️  Timeout en API")
            return None
        except requests.RequestException as e:
            print(f"      ❌ Error en API: {str(e)[:50]}")
            return None
        except Exception as e:
            print(f"      ❌ Error procesando API: {str(e)[:50]}")
            return None
    
    def cargar_desde_archivo(self, nombre_capa: str) -> Optional[gpd.GeoDataFrame]:
        """
        Carga datos desde archivo local
        
        Args:
            nombre_capa: Nombre de la capa
        
        Returns:
            GeoDataFrame o None si no existe
        """
        if nombre_capa not in self.URLS_DESCARGA:
            return None
        
        config = self.URLS_DESCARGA[nombre_capa]
        directorio = self.directorio_base / config['archivo_local']
        
        if not directorio.exists():
            return None
        
        # Buscar archivos .shp
        shapefiles = list(directorio.glob('**/*.shp'))
        
        if not shapefiles:
            return None
        
        try:
            print(f"   💾 Cargando desde archivo local...")
            gdf = gpd.read_file(shapefiles[0])
            
            if gdf.crs != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')
            
            print(f"      ✅ Archivo: {len(gdf)} elementos cargados")
            return gdf
            
        except Exception as e:
            print(f"      ❌ Error leyendo archivo: {e}")
            return None
    
    def obtener_datos(self, nombre_capa: str, bbox: Optional[Tuple] = None, forzar_archivo: bool = False) -> Optional[gpd.GeoDataFrame]:
        """
        Obtiene datos usando estrategia híbrida
        
        Estrategia:
        1. Si forzar_archivo=False: Intenta API primero
        2. Si API falla o forzar_archivo=True: usa archivo local
        3. Si no hay archivo: informa cómo descargar
        
        Args:
            nombre_capa: Nombre de la capa
            bbox: Bounding box opcional para filtrar
            forzar_archivo: Si True, omite API y usa archivo directo
        
        Returns:
            GeoDataFrame o None
        """
        # Verificar caché
        cache_key = f"{nombre_capa}_{bbox}"
        if cache_key in self.cache:
            print(f"   ♻️  Usando caché para {nombre_capa}")
            return self.cache[cache_key]
        
        gdf = None
        
        # Estrategia 1: API (si no está forzado a archivo)
        if not forzar_archivo:
            gdf = self.cargar_desde_api(nombre_capa, bbox)
        
        # Estrategia 2: Archivo local
        if gdf is None:
            gdf = self.cargar_desde_archivo(nombre_capa)
        
        # Estrategia 3: Informar cómo descargar
        if gdf is None:
            print(f"      ⚠️  Datos no disponibles")
            if nombre_capa in self.URLS_DESCARGA:
                config = self.URLS_DESCARGA[nombre_capa]
                print(f"      💡 Para descargar: python descargar_datos_oficiales.py --{nombre_capa}")
                print(f"         O manualmente desde:")
                for url in config['urls'][:1]:
                    print(f"         🔗 {url}")
        else:
            # Guardar en caché
            self.cache[cache_key] = gdf
        
        return gdf
    
    def verificar_disponibilidad(self) -> dict:
        """
        Verifica qué datos están disponibles (API + archivos)
        
        Returns:
            Dict con estado de cada capa
        """
        resultado = {}
        
        for nombre_capa in ['red_hidrica', 'runap', 'resguardos', 'paramos']:
            estado = {
                'api_disponible': False,
                'archivo_disponible': False,
                'puede_descargar': True
            }
            
            # Verificar API
            if nombre_capa in self.APIS_OFICIALES:
                try:
                    response = self.session.head(
                        self.APIS_OFICIALES[nombre_capa]['url'],
                        timeout=5
                    )
                    estado['api_disponible'] = response.status_code == 200
                except:
                    pass
            
            # Verificar archivo
            if nombre_capa in self.URLS_DESCARGA:
                config = self.URLS_DESCARGA[nombre_capa]
                directorio = self.directorio_base / config['archivo_local']
                shapefiles = list(directorio.glob('**/*.shp')) if directorio.exists() else []
                estado['archivo_disponible'] = len(shapefiles) > 0
            
            resultado[nombre_capa] = estado
        
        return resultado
    
    def generar_reporte_disponibilidad(self) -> str:
        """
        Genera reporte legible de disponibilidad de datos
        """
        disponibilidad = self.verificar_disponibilidad()
        
        reporte = "\n" + "="*80 + "\n"
        reporte += "📊 DISPONIBILIDAD DE DATOS GEOGRÁFICOS\n"
        reporte += "="*80 + "\n\n"
        
        nombres = {
            'red_hidrica': 'Red Hidrográfica (IGAC)',
            'runap': 'Áreas Protegidas (RUNAP)',
            'resguardos': 'Resguardos Indígenas (ANT)',
            'paramos': 'Páramos (IDEAM)'
        }
        
        for capa, estado in disponibilidad.items():
            nombre = nombres.get(capa, capa)
            reporte += f"📍 {nombre}\n"
            
            if estado['api_disponible']:
                reporte += "   ✅ API disponible (actualizado en tiempo real)\n"
            else:
                reporte += "   ❌ API no disponible\n"
            
            if estado['archivo_disponible']:
                reporte += "   ✅ Archivo local disponible (backup offline)\n"
            else:
                reporte += "   ⚠️  Sin archivo local\n"
            
            if not estado['api_disponible'] and not estado['archivo_disponible']:
                reporte += "   💡 Ejecutar: python descargar_datos_oficiales.py --todo\n"
            
            reporte += "\n"
        
        reporte += "="*80 + "\n"
        
        return reporte


def ejemplo_uso():
    """
    Ejemplo de uso del sistema híbrido
    """
    print("🌿 Sistema Híbrido de Datos Geográficos\n")
    
    acceso = AccesoDatosHibrido()
    
    # Mostrar disponibilidad
    print(acceso.generar_reporte_disponibilidad())
    
    # Ejemplo: obtener áreas protegidas
    print("\n📥 Probando carga de RUNAP (áreas protegidas)...")
    
    # Bbox ejemplo (Colombia aproximado)
    bbox_colombia = (-79, -4, -66, 13)
    
    runap = acceso.obtener_datos('runap', bbox=bbox_colombia)
    
    if runap is not None:
        print(f"\n✅ RUNAP cargado: {len(runap)} áreas protegidas")
    else:
        print(f"\n❌ No se pudo cargar RUNAP")


if __name__ == '__main__':
    ejemplo_uso()
