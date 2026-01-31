#!/usr/bin/env python
"""Detector Geográfico Automático"""
import os
from pathlib import Path
from typing import Dict, Optional
import geopandas as gpd
from shapely import wkt

class DetectorGeografico:
    def __init__(self, directorio_datos: Optional[str] = None):
        if directorio_datos is None:
            directorio_datos = os.path.join(os.path.dirname(__file__), 'datos_geograficos')
        self.directorio_datos = Path(directorio_datos)
        self.departamentos_gdf = None
        self.municipios_gdf = None
        self._cargar_capas_administrativas()
    
    def _cargar_capas_administrativas(self):
        try:
            dept_path = self.directorio_datos / 'limites_departamentales' / 'gadm_extract' / 'gadm41_COL_1.shp'
            if dept_path.exists():
                self.departamentos_gdf = gpd.read_file(dept_path)
                print(f"✅ Departamentos: {len(self.departamentos_gdf)}")
            mun_path = self.directorio_datos / 'limites_departamentales' / 'gadm_extract' / 'gadm41_COL_2.shp'
            if mun_path.exists():
                self.municipios_gdf = gpd.read_file(mun_path)
                print(f"✅ Municipios: {len(self.municipios_gdf)}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def detectar_ubicacion(self, geometria_parcela) -> Dict:
        if hasattr(geometria_parcela, 'wkt'):
            parcela_geom = wkt.loads(geometria_parcela.wkt)
        else:
            parcela_geom = geometria_parcela
        parcela_gdf = gpd.GeoDataFrame([{'geometry': parcela_geom}], crs='EPSG:4326')
        centroide = parcela_gdf.geometry.centroid.iloc[0]
        resultado = {'departamento': None, 'municipio': None, 'departamento_gdf': None, 'municipio_gdf': None, 'centroide': centroide}
        if self.departamentos_gdf is not None:
            dept_match = self.departamentos_gdf[self.departamentos_gdf.contains(centroide)]
            if not dept_match.empty:
                resultado['departamento'] = dept_match.iloc[0].get('NAME_1', 'Desconocido')
                resultado['departamento_gdf'] = dept_match.copy()
                print(f"🎯 Departamento: {resultado['departamento']}")
        if self.municipios_gdf is not None:
            mun_match = self.municipios_gdf[self.municipios_gdf.contains(centroide)]
            if not mun_match.empty:
                resultado['municipio'] = mun_match.iloc[0].get('NAME_2', 'Desconocido')
                resultado['municipio_gdf'] = mun_match.copy()
                print(f"🎯 Municipio: {resultado['municipio']}")
        return resultado
    
    def cargar_red_hidrica_municipal(self, municipio_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        try:
            directorio = self.directorio_datos / 'red_hidrica'
            archivos = ['red_hidrica_casanare_meta_igac_2024.shp', 'Drenaje_Sencillo.shp']
            archivo_sel = None
            if directorio.exists():
                for nombre in archivos:
                    path = directorio / nombre
                    if path.exists():
                        archivo_sel = str(path)
                        break
            if archivo_sel:
                red_completa = gpd.read_file(archivo_sel)
                if red_completa.crs != 'EPSG:4326':
                    red_completa = red_completa.to_crs('EPSG:4326')
                bounds = municipio_gdf.total_bounds
                red_municipal = red_completa.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
                print(f"✅ Red hídrica: {len(red_municipal)} elementos")
                for campo in ['NOMBRE', 'nombre', 'name', 'NOMBRE_GEO']:
                    if campo in red_municipal.columns:
                        con_nombre = red_municipal[campo].notna().sum()
                        print(f"   📛 Con nombre ({campo}): {con_nombre}")
                        break
                return red_municipal
        except Exception as e:
            print(f"❌ Error red hídrica: {e}")
        return None
    
    def proceso_completo(self, geometria_parcela) -> Dict:
        print("\n" + "="*70)
        print("🌍 DETECCIÓN AUTOMÁTICA")
        print("="*70)
        ubicacion = self.detectar_ubicacion(geometria_parcela)
        if ubicacion['municipio_gdf'] is not None:
            red = self.cargar_red_hidrica_municipal(ubicacion['municipio_gdf'])
            ubicacion['red_hidrica'] = red
        print("="*70 + "\n")
        return ubicacion
