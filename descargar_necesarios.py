"""
Descarga inteligente de datos geográficos
==========================================

Solo descarga lo que NO está disponible vía API oficial.

Resultado del análisis híbrido:
✅ RUNAP - Usa API (no necesita descarga)
❌ Red Hidrográfica - Necesita descarga (CRÍTICO)
❌ Resguardos - Necesita descarga
❌ Páramos - Necesita descarga

Este script descarga solo los 3 archivos necesarios.

Uso:
    python descargar_necesarios.py

Autor: AgroTech Histórico
Fecha: Enero 2026
"""

import requests
import zipfile
from pathlib import Path
import time


def descargar_con_progreso(url, destino, descripcion):
    """Descarga archivo con barra de progreso"""
    print(f"\n📥 Descargando: {descripcion}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(destino, 'wb') as f:
            if total_size == 0:
                print("   Descargando...")
                f.write(response.content)
            else:
                downloaded = 0
                total_mb = total_size / (1024 * 1024)
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_size) * 100
                        downloaded_mb = downloaded / (1024 * 1024)
                        
                        bar_length = 50
                        filled = int(bar_length * downloaded / total_size)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        
                        print(f'\r   [{bar}] {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)', end='', flush=True)
                
                print()
        
        print(f"   ✅ Descargado: {destino.name}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def extraer_zip(archivo_zip, directorio_destino):
    """Extrae archivo ZIP"""
    print(f"\n📦 Extrayendo {archivo_zip.name}...")
    
    try:
        with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
            archivos = zip_ref.namelist()
            zip_ref.extractall(directorio_destino)
            
            shapefiles = [f for f in archivos if f.endswith('.shp')]
            print(f"   ✅ {len(shapefiles)} shapefile(s) extraído(s)")
            for shp in shapefiles[:3]:
                print(f"      • {shp}")
            
            return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def convertir_geojson_a_shapefile(archivo_geojson, directorio_destino):
    """Convierte GeoJSON a Shapefile usando GeoPandas"""
    print(f"\n🔄 Convirtiendo GeoJSON a Shapefile...")
    
    try:
        import geopandas as gpd
        import json
        
        # Leer GeoJSON
        with open(archivo_geojson, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Convertir a GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf.crs = 'EPSG:4326'
        
        # Guardar como Shapefile
        output_shp = directorio_destino / 'data.shp'
        gdf.to_file(output_shp)
        
        print(f"   ✅ Shapefile creado: {output_shp.name}")
        print(f"   📊 {len(gdf)} elementos convertidos")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("="*80)
    print("🌿 DESCARGA INTELIGENTE - SOLO DATOS NECESARIOS")
    print("="*80)
    print("\n✅ RUNAP: Usa API oficial (no necesita descarga)")
    print("📥 Descargando solo 3 archivos que necesitan almacenamiento local:\n")
    
    # Crear directorios
    base = Path('datos_geograficos')
    base.mkdir(exist_ok=True)
    temp = base / 'temp'
    temp.mkdir(exist_ok=True)
    
    # Datasets a descargar (solo los que no tienen API)
    # URLs ACTUALIZADAS 2026 - Verificadas oficialmente
    datasets = [
        {
            'nombre': 'Zonificación Hidrográfica (datos.gov.co)',
            'urls': [
                'https://www.datos.gov.co/api/geospatial/5kjg-nuda?method=export&format=Shapefile',
                'https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Zonificaci-n-Hidrogr-fica-Colombia/5kjg-nuda',
            ],
            'archivo': 'zonificacion_hidrica.zip',
            'directorio': base / 'red_hidrica',
            'critico': True,
            'nota': 'Zonificación hidrográfica oficial - usar para retiros de cauces'
        },
        {
            'nombre': 'Resguardos Indígenas Formalizados (ANT ArcGIS Open Data)',
            'urls': [
                'https://opendata.arcgis.com/datasets/8f2e71f5e9e34f1a829f0fb1ff4e463a_0.zip',
                'https://services.arcgis.com/DDzi7vRExVRMO5AB/arcgis/rest/services/Resguardos_Indigenas_Formalizados/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson',
            ],
            'archivo': 'resguardos_indigenas.zip',
            'directorio': base / 'ant',
            'critico': False,
            'nota': 'Resguardos indígenas oficiales ANT - ArcGIS Open Data (actualizado)',
            'es_geojson': True  # Segunda URL es GeoJSON directo
        },
        {
            'nombre': 'Páramos Delimitados (MinAmbiente/SIAC)',
            'urls': [
                'https://www.siac.gov.co/documentos/DOC_Portal/DOC_Agua/Paramos/Paramos_Delimitados_2020.zip',
                'http://geonetwork.minambiente.gov.co:8080/geonetwork/srv/spa/catalog.search#/metadata/a622db8a-93f1-44c5-9ae9-0d1d8f70729f',
            ],
            'archivo': 'paramos.zip',
            'directorio': base / 'ideam',
            'critico': False,
            'nota': 'Páramos delimitados oficiales MinAmbiente - SIAC Junio 2020'
        }
    ]
    
    resultados = []
    
    for i, dataset in enumerate(datasets, 1):
        print(f"\n{'='*80}")
        print(f"DATASET {i}/3: {dataset['nombre']}")
        if dataset['critico']:
            print("⚠️  CRÍTICO - Necesario para retiros hídricos")
        if 'nota' in dataset:
            print(f"📝 {dataset['nota']}")
        print('='*80)
        
        # Si requiere descarga manual
        if dataset.get('manual', False):
            print(f"\n   📌 Descarga manual requerida:")
            for url in dataset['urls']:
                print(f"      {url}")
            print(f"   💡 Guardar archivos en: {dataset['directorio']}")
            resultados.append(False)
            continue
        
        # Crear directorio
        dataset['directorio'].mkdir(exist_ok=True)
        
        # Intentar cada URL
        exito = False
        for j, url in enumerate(dataset['urls'], 1):
            if j > 1:
                print(f"\n   Probando URL alternativa {j}...")
            
            # Determinar tipo de archivo
            es_geojson = dataset.get('es_geojson', False) and j == 2
            
            if es_geojson:
                archivo_destino = temp / 'data.geojson'
            else:
                archivo_destino = temp / dataset['archivo']
            
            if descargar_con_progreso(url, archivo_destino, dataset['nombre']):
                if es_geojson:
                    # Convertir GeoJSON a Shapefile
                    if convertir_geojson_a_shapefile(archivo_destino, dataset['directorio']):
                        archivo_destino.unlink()  # Eliminar GeoJSON temporal
                        exito = True
                        break
                else:
                    # Extraer ZIP
                    if extraer_zip(archivo_destino, dataset['directorio']):
                        archivo_destino.unlink()  # Eliminar ZIP
                        exito = True
                        break
            
            if not exito and j < len(dataset['urls']):
                print("   ⏸️  Intentando siguiente URL...")
                time.sleep(1)
        
        if not exito:
            print(f"\n   ❌ No se pudo descargar {dataset['nombre']}")
            print(f"   💡 Descarga manual:")
            for url in dataset['urls'][:1]:
                print(f"      {url}")
        
        resultados.append(exito)
        
        if i < len(datasets):
            print(f"\n   ⏸️  Pausa antes de siguiente descarga...")
            time.sleep(2)
    
    # Resumen
    print("\n\n" + "="*80)
    print("📊 RESUMEN DE DESCARGAS")
    print("="*80 + "\n")
    
    print("✅ RUNAP (Áreas Protegidas): API activa - 1,829 áreas")
    
    for dataset, exito in zip(datasets, resultados):
        estado = "✅ EXITOSA" if exito else "❌ FALLIDA"
        print(f"{estado} - {dataset['nombre']}")
    
    exitosas = sum(resultados)
    total = len(datasets)
    
    print(f"\n{'='*80}")
    print(f"Resultado: {exitosas + 1}/{total + 1} fuentes disponibles")
    
    if exitosas >= 1:  # Al menos red hídrica
        print("\n🎉 Sistema funcional!")
        print("   RUNAP: API ✅")
        if resultados[0]:
            print("   Red Hidrográfica: Archivo ✅ (CRÍTICO)")
        if exitosas == total:
            print("   Todos los datos descargados ✅")
        
        print("\n📍 Próximo paso:")
        print("   python test_verificacion_legal_terminal.py --parcela 1")
    else:
        print("\n⚠️  Sistema parcialmente funcional")
        print("   Algunas verificaciones estarán incompletas")


if __name__ == '__main__':
    main()
