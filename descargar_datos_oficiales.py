"""
Script de descarga automática de datos geográficos oficiales
=============================================================

Descarga shapefiles oficiales del gobierno colombiano para verificación legal:
1. Red hidrográfica (IGAC)
2. Áreas protegidas (RUNAP - Parques Nacionales)
3. Resguardos indígenas (ANT)
4. Páramos (IDEAM)

IMPORTANTE: Todos los datos son OFICIALES y gratuitos del gobierno.

Uso:
    python descargar_datos_oficiales.py --todo
    python descargar_datos_oficiales.py --red-hidrica
    python descargar_datos_oficiales.py --areas-protegidas

Autor: AgroTech Histórico
Fecha: Enero 2026
"""

import os
import sys
import requests
import zipfile
import argparse
from pathlib import Path
from urllib.parse import urlparse
import time


class DescargadorDatosOficiales:
    """
    Descarga automática de datos geográficos oficiales
    """
    
    # URLs oficiales actualizadas 2026
    URLS_OFICIALES = {
        'red_hidrica': {
            'url': 'https://www.colombiaenmapas.gov.co/SSIGL2.0/Descargas/20230101_Drenajes_sencillos.zip',
            'alternativa': 'https://geoportal.igac.gov.co/contenido/datos-abiertos-cartografia-y-geografia',
            'archivo': 'drenajes_sencillos.zip',
            'descripcion': 'Red hidrográfica nacional (IGAC)',
            'tamano_mb': 150,
            'directorio': 'red_hidrica'
        },
        'areas_protegidas': {
            'url': 'http://mapas.parquesnacionales.gov.co/services/pnn/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=pnn:runap&outputFormat=SHAPE-ZIP',
            'alternativa': 'http://runap.parquesnacionales.gov.co/datos.html',
            'archivo': 'runap.zip',
            'descripcion': 'Áreas protegidas RUNAP (Parques Nacionales)',
            'tamano_mb': 50,
            'directorio': 'runap'
        },
        'resguardos': {
            'url': 'https://www.datos.gov.co/api/geospatial/7n7q-5k8p?method=export&format=Shapefile',
            'alternativa': 'https://geoportal.ant.gov.co/descargas',
            'archivo': 'resguardos_indigenas.zip',
            'descripcion': 'Resguardos indígenas (ANT)',
            'tamano_mb': 30,
            'directorio': 'ant'
        },
        'paramos': {
            'url': 'http://www.ideam.gov.co/documents/24277/95191925/Paramos_Delimitados_2022.zip',
            'alternativa': 'http://geoservicios.ideam.gov.co/geonetwork/srv/spa/catalog.search#/metadata',
            'archivo': 'paramos.zip',
            'descripcion': 'Delimitación de páramos (IDEAM)',
            'tamano_mb': 20,
            'directorio': 'ideam'
        }
    }
    
    def __init__(self, directorio_base='datos_geograficos'):
        self.directorio_base = Path(directorio_base)
        self.crear_directorios()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AgroTech-Historico/1.0 (verificacion-legal)'
        })
    
    def crear_directorios(self):
        """Crea la estructura de directorios necesaria"""
        print("\n📁 Creando estructura de directorios...")
        
        directorios = [
            self.directorio_base,
            self.directorio_base / 'red_hidrica',
            self.directorio_base / 'runap',
            self.directorio_base / 'ant',
            self.directorio_base / 'ideam',
            self.directorio_base / 'descargas_temp'
        ]
        
        for directorio in directorios:
            directorio.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {directorio}")
    
    def descargar_archivo(self, url, destino, descripcion, tamano_mb):
        """
        Descarga un archivo con barra de progreso
        """
        print(f"\n📥 Descargando: {descripcion}")
        print(f"   URL: {url}")
        print(f"   Tamaño estimado: ~{tamano_mb} MB")
        print(f"   Destino: {destino}")
        
        try:
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destino, 'wb') as f:
                if total_size == 0:
                    # Sin información de tamaño
                    print("   Descargando... (tamaño desconocido)")
                    f.write(response.content)
                else:
                    # Con barra de progreso
                    downloaded = 0
                    total_mb = total_size / (1024 * 1024)
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = (downloaded / total_size) * 100
                            downloaded_mb = downloaded / (1024 * 1024)
                            
                            # Barra de progreso simple
                            bar_length = 50
                            filled = int(bar_length * downloaded / total_size)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            
                            print(f'\r   [{bar}] {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)', end='', flush=True)
                    
                    print()  # Nueva línea
            
            print(f"   ✅ Descarga completada: {destino.name}")
            return True
            
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout - el servidor tardó demasiado en responder")
            print(f"   💡 Intenta descargar manualmente desde: {url}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error en descarga: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")
            return False
    
    def extraer_zip(self, archivo_zip, directorio_destino):
        """
        Extrae un archivo ZIP
        """
        print(f"\n📦 Extrayendo {archivo_zip.name}...")
        
        try:
            with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
                # Listar contenido
                archivos = zip_ref.namelist()
                print(f"   Archivos en ZIP: {len(archivos)}")
                
                # Extraer
                zip_ref.extractall(directorio_destino)
                
                # Verificar shapefiles
                shapefiles = [f for f in archivos if f.endswith('.shp')]
                if shapefiles:
                    print(f"   ✅ {len(shapefiles)} shapefile(s) extraído(s)")
                    for shp in shapefiles:
                        print(f"      • {shp}")
                else:
                    print(f"   ⚠️  No se encontraron archivos .shp")
                
                return True
                
        except zipfile.BadZipFile:
            print(f"   ❌ Archivo ZIP corrupto")
            return False
        except Exception as e:
            print(f"   ❌ Error extrayendo: {e}")
            return False
    
    def verificar_shapefile(self, directorio):
        """
        Verifica que existan los archivos necesarios de un shapefile
        """
        extensiones_requeridas = ['.shp', '.shx', '.dbf']
        archivos_shp = list(directorio.glob('**/*.shp'))
        
        if not archivos_shp:
            return False, "No se encontró archivo .shp"
        
        for shp in archivos_shp:
            base = shp.stem
            faltantes = []
            
            for ext in extensiones_requeridas:
                archivo_req = shp.parent / f"{base}{ext}"
                if not archivo_req.exists():
                    faltantes.append(ext)
            
            if faltantes:
                return False, f"Faltan archivos: {', '.join(faltantes)}"
        
        return True, f"Shapefile(s) válido(s): {len(archivos_shp)}"
    
    def descargar_capa(self, nombre_capa):
        """
        Descarga una capa específica
        """
        if nombre_capa not in self.URLS_OFICIALES:
            print(f"❌ Capa desconocida: {nombre_capa}")
            return False
        
        config = self.URLS_OFICIALES[nombre_capa]
        
        print("\n" + "="*80)
        print(f"🌍 DESCARGANDO: {config['descripcion']}")
        print("="*80)
        
        # Directorio de destino
        dir_destino = self.directorio_base / config['directorio']
        dir_temp = self.directorio_base / 'descargas_temp'
        archivo_zip = dir_temp / config['archivo']
        
        # Descargar
        if not self.descargar_archivo(
            config['url'],
            archivo_zip,
            config['descripcion'],
            config['tamano_mb']
        ):
            print(f"\n⚠️  Descarga automática falló.")
            print(f"   Descarga manual desde:")
            print(f"   🔗 {config['url']}")
            print(f"   O desde: {config['alternativa']}")
            return False
        
        # Extraer
        if not self.extraer_zip(archivo_zip, dir_destino):
            return False
        
        # Verificar
        print(f"\n🔍 Verificando shapefile...")
        valido, mensaje = self.verificar_shapefile(dir_destino)
        
        if valido:
            print(f"   ✅ {mensaje}")
            print(f"\n🎉 {config['descripcion']} instalado correctamente")
            
            # Limpiar archivo temporal
            archivo_zip.unlink()
            print(f"   🗑️  Archivo temporal eliminado")
            return True
        else:
            print(f"   ❌ {mensaje}")
            return False
    
    def descargar_todo(self):
        """
        Descarga todas las capas
        """
        print("\n" + "="*80)
        print("🌿 DESCARGA COMPLETA DE DATOS OFICIALES")
        print("="*80)
        print("\nDescargando 4 capas geográficas oficiales del gobierno colombiano:")
        print("1. Red hidrográfica (IGAC)")
        print("2. Áreas protegidas (Parques Nacionales)")
        print("3. Resguardos indígenas (ANT)")
        print("4. Páramos (IDEAM)")
        print("\n⏱️  Tiempo estimado: 10-30 minutos (según conexión)")
        
        input("\n📍 Presiona ENTER para comenzar...")
        
        resultados = {}
        capas = ['red_hidrica', 'areas_protegidas', 'resguardos', 'paramos']
        
        for i, capa in enumerate(capas, 1):
            print(f"\n\n{'='*80}")
            print(f"CAPA {i}/4")
            print('='*80)
            
            resultados[capa] = self.descargar_capa(capa)
            
            if i < len(capas):
                print("\n⏸️  Pausa de 2 segundos antes de siguiente descarga...")
                time.sleep(2)
        
        # Resumen final
        print("\n\n" + "="*80)
        print("📊 RESUMEN DE DESCARGAS")
        print("="*80 + "\n")
        
        exitosas = sum(1 for v in resultados.values() if v)
        total = len(resultados)
        
        for capa, exito in resultados.items():
            config = self.URLS_OFICIALES[capa]
            estado = "✅ EXITOSA" if exito else "❌ FALLIDA"
            print(f"{estado} - {config['descripcion']}")
        
        print(f"\n{'='*80}")
        print(f"Resultado: {exitosas}/{total} capas descargadas exitosamente")
        
        if exitosas == total:
            print("\n🎉 ¡DESCARGA COMPLETA! Sistema listo para usar.")
            print("\nPróximo paso:")
            print("   python test_verificacion_legal_terminal.py --parcela 1")
        elif exitosas > 0:
            print(f"\n⚠️  Sistema parcialmente funcional ({exitosas}/{total} capas)")
            print("   Puedes usar las capas descargadas, pero la verificación será incompleta")
        else:
            print("\n❌ No se pudo descargar ninguna capa")
            print("   Verifica tu conexión a internet e intenta nuevamente")
        
        return exitosas == total
    
    def estado_actual(self):
        """
        Muestra el estado de los datos instalados
        """
        print("\n" + "="*80)
        print("📊 ESTADO ACTUAL DE DATOS GEOGRÁFICOS")
        print("="*80 + "\n")
        
        for nombre, config in self.URLS_OFICIALES.items():
            directorio = self.directorio_base / config['directorio']
            
            if not directorio.exists():
                print(f"❌ {config['descripcion']}")
                print(f"   Directorio no existe: {directorio}")
                print()
                continue
            
            valido, mensaje = self.verificar_shapefile(directorio)
            
            if valido:
                print(f"✅ {config['descripcion']}")
                print(f"   {mensaje}")
                print(f"   Ubicación: {directorio}")
            else:
                print(f"⚠️  {config['descripcion']}")
                print(f"   {mensaje}")
                print(f"   Ubicación: {directorio}")
            
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Descarga datos geográficos oficiales para verificación legal'
    )
    parser.add_argument(
        '--todo',
        action='store_true',
        help='Descargar todas las capas'
    )
    parser.add_argument(
        '--red-hidrica',
        action='store_true',
        help='Descargar solo red hidrográfica (IGAC)'
    )
    parser.add_argument(
        '--areas-protegidas',
        action='store_true',
        help='Descargar solo áreas protegidas (RUNAP)'
    )
    parser.add_argument(
        '--resguardos',
        action='store_true',
        help='Descargar solo resguardos indígenas (ANT)'
    )
    parser.add_argument(
        '--paramos',
        action='store_true',
        help='Descargar solo páramos (IDEAM)'
    )
    parser.add_argument(
        '--estado',
        action='store_true',
        help='Mostrar estado de datos instalados'
    )
    parser.add_argument(
        '--directorio',
        type=str,
        default='datos_geograficos',
        help='Directorio de destino (default: ./datos_geograficos)'
    )
    
    args = parser.parse_args()
    
    # Inicializar descargador
    descargador = DescargadorDatosOficiales(args.directorio)
    
    # Mostrar estado
    if args.estado:
        descargador.estado_actual()
        return
    
    # Determinar qué descargar
    if args.todo:
        descargador.descargar_todo()
    else:
        algo_descargado = False
        
        if args.red_hidrica:
            descargador.descargar_capa('red_hidrica')
            algo_descargado = True
        
        if args.areas_protegidas:
            descargador.descargar_capa('areas_protegidas')
            algo_descargado = True
        
        if args.resguardos:
            descargador.descargar_capa('resguardos')
            algo_descargado = True
        
        if args.paramos:
            descargador.descargar_capa('paramos')
            algo_descargado = True
        
        if not algo_descargado:
            print("\n⚠️  No se especificó qué descargar")
            print("\nUso:")
            print("   python descargar_datos_oficiales.py --todo")
            print("   python descargar_datos_oficiales.py --red-hidrica")
            print("   python descargar_datos_oficiales.py --estado")
            print("\nPara más ayuda:")
            print("   python descargar_datos_oficiales.py --help")


if __name__ == '__main__':
    main()
