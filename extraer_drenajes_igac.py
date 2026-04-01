#!/usr/bin/env python
"""
Script para extraer y validar datos de drenajes desde el ZIP de IGAC (Servicio 205)
"""
import os
import zipfile
import geopandas as gpd
import fiona
from pathlib import Path

def verificar_zip(ruta_zip):
    """Verificar integridad del archivo ZIP"""
    print(f"\n🔍 Verificando archivo: {ruta_zip}")
    
    if not os.path.exists(ruta_zip):
        print(f"❌ Error: No se encuentra el archivo {ruta_zip}")
        return False
    
    tamaño_mb = os.path.getsize(ruta_zip) / (1024 * 1024)
    print(f"   Tamaño: {tamaño_mb:.1f} MB")
    
    try:
        with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
            # Verificar integridad
            bad_file = zip_ref.testzip()
            if bad_file:
                print(f"❌ Archivo corrupto: {bad_file}")
                return False
            
            print(f"✅ ZIP válido: {len(zip_ref.namelist())} archivos dentro")
            
            # Mostrar primeros archivos
            print("\n📁 Contenido (primeros 20 archivos):")
            for i, name in enumerate(zip_ref.namelist()[:20]):
                print(f"   - {name}")
            
            if len(zip_ref.namelist()) > 20:
                print(f"   ... y {len(zip_ref.namelist()) - 20} archivos más")
            
            return True
            
    except zipfile.BadZipFile:
        print("❌ Error: Archivo ZIP corrupto")
        return False
    except Exception as e:
        print(f"❌ Error verificando ZIP: {e}")
        return False

def extraer_zip(ruta_zip, destino='datos_geograficos/temp_igac'):
    """Extraer contenido del ZIP"""
    print(f"\n📦 Extrayendo a: {destino}")
    
    Path(destino).mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
            zip_ref.extractall(destino)
        
        print(f"✅ Extracción completada")
        return destino
        
    except Exception as e:
        print(f"❌ Error extrayendo: {e}")
        return None

def buscar_archivos_geo(directorio):
    """Buscar archivos geográficos (GDB, Shapefile, GeoJSON)"""
    print(f"\n🔍 Buscando archivos geográficos en: {directorio}")
    
    resultados = {
        'gdb': [],
        'shapefile': [],
        'geojson': []
    }
    
    for root, dirs, files in os.walk(directorio):
        # Buscar GDB (directorios con extensión .gdb)
        for d in dirs:
            if d.endswith('.gdb'):
                resultados['gdb'].append(os.path.join(root, d))
        
        # Buscar Shapefiles
        for f in files:
            if f.endswith('.shp'):
                resultados['shapefile'].append(os.path.join(root, f))
            elif f.endswith('.geojson') or f.endswith('.json'):
                resultados['geojson'].append(os.path.join(root, f))
    
    print("\n📊 Archivos encontrados:")
    print(f"   GDB: {len(resultados['gdb'])}")
    print(f"   Shapefiles: {len(resultados['shapefile'])}")
    print(f"   GeoJSON: {len(resultados['geojson'])}")
    
    return resultados

def listar_capas_gdb(ruta_gdb):
    """Listar capas dentro de un GDB"""
    print(f"\n📂 Capas en GDB: {os.path.basename(ruta_gdb)}")
    
    try:
        capas = fiona.listlayers(ruta_gdb)
        print(f"   Total capas: {len(capas)}")
        
        for i, capa in enumerate(capas, 1):
            print(f"   {i}. {capa}")
        
        return capas
        
    except Exception as e:
        print(f"❌ Error listando capas: {e}")
        return []

def identificar_capa_drenajes(capas):
    """Identificar cuál capa contiene los drenajes"""
    print("\n🎯 Buscando capa de drenajes...")
    
    palabras_clave = [
        'drenaje', 'dren', 'hidro', 'rio', 'corriente', 
        'agua', 'stream', 'river', 'water'
    ]
    
    candidatos = []
    
    for capa in capas:
        capa_lower = capa.lower()
        for palabra in palabras_clave:
            if palabra in capa_lower:
                candidatos.append(capa)
                break
    
    if candidatos:
        print(f"✅ Capas candidatas encontradas:")
        for c in candidatos:
            print(f"   - {c}")
        return candidatos[0]  # Retornar primera coincidencia
    else:
        print("⚠️  No se encontró capa obvia de drenajes")
        print("   Se intentará con la primera capa...")
        return capas[0] if capas else None

def validar_geometrias(gdf, nombre_capa):
    """Validar que las geometrías sean LineString"""
    print(f"\n🔍 Validando geometrías de: {nombre_capa}")
    
    tipos = gdf.geometry.geom_type.unique()
    print(f"   Tipos encontrados: {list(tipos)}")
    print(f"   Total elementos: {len(gdf)}")
    
    # Verificar si hay LineStrings
    tiene_lineas = any(t in ['LineString', 'MultiLineString'] for t in tipos)
    tiene_poligonos = any(t in ['Polygon', 'MultiPolygon'] for t in tipos)
    
    if tiene_lineas and not tiene_poligonos:
        print("✅ CORRECTO: Son líneas (drenajes)")
        return True
    elif tiene_poligonos:
        print("❌ INCORRECTO: Son polígonos (zonificación)")
        print("   Necesitas drenajes lineales, no cuencas")
        return False
    else:
        print(f"⚠️  Tipo inesperado: {tipos}")
        return False

def procesar_gdb(ruta_gdb):
    """Procesar archivo GDB completo"""
    print(f"\n{'='*80}")
    print(f"PROCESANDO GDB: {os.path.basename(ruta_gdb)}")
    print(f"{'='*80}")
    
    # Listar capas
    capas = listar_capas_gdb(ruta_gdb)
    if not capas:
        return None
    
    # Identificar capa de drenajes
    capa_drenajes = identificar_capa_drenajes(capas)
    if not capa_drenajes:
        print("❌ No se pudo identificar capa de drenajes")
        return None
    
    print(f"\n📖 Cargando capa: {capa_drenajes}")
    
    try:
        # Cargar la capa
        gdf = gpd.read_file(ruta_gdb, layer=capa_drenajes)
        
        # Validar geometrías
        if validar_geometrias(gdf, capa_drenajes):
            print(f"\n✅ Datos válidos encontrados")
            
            # Mostrar columnas
            print(f"\n📋 Columnas disponibles:")
            for col in gdf.columns:
                print(f"   - {col}")
            
            # Guardar como Shapefile
            output_dir = Path('datos_geograficos/red_hidrica')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_shp = output_dir / 'drenajes_igac.shp'
            
            print(f"\n💾 Guardando como Shapefile: {output_shp}")
            gdf.to_file(str(output_shp))
            
            print(f"✅ COMPLETADO: {len(gdf)} drenajes guardados")
            print(f"   Ubicación: {output_shp}")
            
            return str(output_shp)
        else:
            print("\n⚠️  Geometrías incorrectas, buscando otra capa...")
            
            # Intentar con otras capas
            for capa in capas:
                if capa != capa_drenajes:
                    print(f"\n   Probando: {capa}")
                    try:
                        gdf_test = gpd.read_file(ruta_gdb, layer=capa)
                        if validar_geometrias(gdf_test, capa):
                            gdf = gdf_test
                            capa_drenajes = capa
                            break
                    except:
                        continue
            
            if validar_geometrias(gdf, capa_drenajes):
                output_dir = Path('datos_geograficos/red_hidrica')
                output_dir.mkdir(parents=True, exist_ok=True)
                output_shp = output_dir / 'drenajes_igac.shp'
                gdf.to_file(str(output_shp))
                return str(output_shp)
            else:
                return None
            
    except Exception as e:
        print(f"❌ Error cargando capa {capa_drenajes}: {e}")
        return None

def procesar_shapefile(ruta_shp):
    """Procesar Shapefile directamente"""
    print(f"\n{'='*80}")
    print(f"PROCESANDO SHAPEFILE: {os.path.basename(ruta_shp)}")
    print(f"{'='*80}")
    
    try:
        gdf = gpd.read_file(ruta_shp)
        
        if validar_geometrias(gdf, os.path.basename(ruta_shp)):
            # Copiar a ubicación final
            output_dir = Path('datos_geograficos/red_hidrica')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_shp = output_dir / 'drenajes_igac.shp'
            
            gdf.to_file(str(output_shp))
            print(f"✅ Copiado a: {output_shp}")
            return str(output_shp)
        else:
            return None
            
    except Exception as e:
        print(f"❌ Error procesando shapefile: {e}")
        return None

def main():
    print("="*80)
    print("EXTRACTOR DE DRENAJES IGAC - Servicio 205")
    print("="*80)
    
    # Ruta al ZIP descargado
    ruta_zip = os.path.expanduser('~/Downloads/Servicio-205.zip')
    
    # Verificar si existe en Downloads
    if not os.path.exists(ruta_zip):
        # Buscar en Descargas (español)
        ruta_zip = os.path.expanduser('~/Descargas/Servicio-205.zip')
    
    if not os.path.exists(ruta_zip):
        print(f"\n❌ No se encuentra el archivo ZIP")
        print(f"   Buscado en:")
        print(f"   - ~/Downloads/Servicio-205.zip")
        print(f"   - ~/Descargas/Servicio-205.zip")
        print(f"\n💡 Por favor especifica la ruta completa del archivo")
        return
    
    # 1. Verificar ZIP
    if not verificar_zip(ruta_zip):
        return
    
    # 2. Extraer
    destino = extraer_zip(ruta_zip)
    if not destino:
        return
    
    # 3. Buscar archivos geográficos
    archivos = buscar_archivos_geo(destino)
    
    # 4. Procesar según formato encontrado
    resultado = None
    
    if archivos['gdb']:
        print(f"\n🎯 Procesando GDB encontrado...")
        for gdb in archivos['gdb']:
            resultado = procesar_gdb(gdb)
            if resultado:
                break
    
    if not resultado and archivos['shapefile']:
        print(f"\n🎯 Procesando Shapefiles encontrados...")
        for shp in archivos['shapefile']:
            if 'dren' in shp.lower() or 'hidro' in shp.lower():
                resultado = procesar_shapefile(shp)
                if resultado:
                    break
    
    # Resultado final
    print("\n" + "="*80)
    if resultado:
        print("✅ ÉXITO: Drenajes IGAC procesados correctamente")
        print(f"   Archivo: {resultado}")
        print("\n📝 Siguiente paso:")
        print("   conda run -n agro-rest python test_pdf_verificacion_con_mapa.py")
    else:
        print("❌ No se pudieron extraer drenajes válidos")
        print("\n💡 Revisa manualmente el contenido extraído en:")
        print(f"   {destino}")
    print("="*80)

if __name__ == '__main__':
    main()
