#!/usr/bin/env python3
"""
Script robusto para extraer ZIP corrupto/problemático
Intenta múltiples métodos de extracción
"""
import os
import zipfile
import subprocess
from pathlib import Path

ZIP_FILE = Path.home() / "Downloads" / "Servicio-205.zip"
DESTINO = Path.home() / "Downloads" / "Servicio-205-extraido"

def metodo_1_unzip_terminal():
    """Método 1: Usar unzip de terminal con opciones de recuperación"""
    print("\n🔧 Método 1: unzip con modo recuperación...")
    try:
        # Crear directorio destino
        DESTINO.mkdir(parents=True, exist_ok=True)
        
        # unzip con opción -F para intentar reparar
        cmd = f'unzip -o "{ZIP_FILE}" -d "{DESTINO}"'
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if resultado.returncode == 0 or "extracting:" in resultado.stdout.lower():
            print("✅ Extracción exitosa con unzip")
            return True
        else:
            print(f"⚠️ unzip retornó código {resultado.returncode}")
            print(resultado.stderr[:500] if resultado.stderr else "")
            return False
    except Exception as e:
        print(f"❌ Error en método 1: {e}")
        return False

def metodo_2_python_zipfile_permisivo():
    """Método 2: Python zipfile en modo permisivo"""
    print("\n🔧 Método 2: Python zipfile modo permisivo...")
    try:
        DESTINO.mkdir(parents=True, exist_ok=True)
        
        # Intentar con allowZip64
        with zipfile.ZipFile(ZIP_FILE, 'r', allowZip64=True) as zip_ref:
            # Listar archivos primero
            archivos = zip_ref.namelist()
            print(f"   Archivos encontrados en ZIP: {len(archivos)}")
            
            # Buscar archivos de drenaje
            drenajes = [f for f in archivos if 'Drenaje_Sencillo' in f or 'drenaje' in f.lower()]
            print(f"   Archivos de drenaje: {len(drenajes)}")
            
            if drenajes:
                print("\n   Extrayendo solo archivos de drenaje...")
                for archivo in drenajes:
                    try:
                        zip_ref.extract(archivo, DESTINO)
                        print(f"   ✓ {archivo}")
                    except Exception as e:
                        print(f"   ✗ {archivo}: {e}")
                return True
            else:
                print("   Extrayendo todos los archivos...")
                zip_ref.extractall(DESTINO)
                return True
                
    except zipfile.BadZipFile as e:
        print(f"❌ BadZipFile: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en método 2: {e}")
        return False

def metodo_3_extraer_parcial():
    """Método 3: Extracción parcial byte a byte"""
    print("\n🔧 Método 3: Extracción manual parcial...")
    try:
        import struct
        
        with open(ZIP_FILE, 'rb') as f:
            # Buscar firmas de archivos locales (0x04034b50)
            contenido = f.read()
            
        # Buscar todos los headers de archivos
        firma_local = b'\x50\x4b\x03\x04'
        posiciones = []
        idx = 0
        while True:
            idx = contenido.find(firma_local, idx)
            if idx == -1:
                break
            posiciones.append(idx)
            idx += 1
        
        print(f"   Encontrados {len(posiciones)} archivos en el ZIP")
        
        if posiciones:
            print("   ℹ️  El archivo tiene contenido válido pero el directorio central está corrupto")
            print("   💡 Intenta con método 1 (unzip) o descarga de nuevo el archivo")
            return False
        
    except Exception as e:
        print(f"❌ Error en método 3: {e}")
        return False

def verificar_archivos_extraidos():
    """Verificar si se extrajeron los archivos de drenaje"""
    print("\n🔍 Verificando archivos extraídos...")
    
    if not DESTINO.exists():
        print("❌ No se creó el directorio de extracción")
        return False
    
    # Buscar archivos de drenaje recursivamente
    drenajes_shp = list(DESTINO.rglob("Drenaje_Sencillo.shp"))
    
    if drenajes_shp:
        print(f"\n✅ ¡Encontrado! Drenaje_Sencillo.shp en:")
        for shp in drenajes_shp:
            print(f"   📁 {shp}")
            
            # Verificar archivos asociados
            base = shp.stem
            dir_shp = shp.parent
            archivos_asociados = [
                f"{base}.shp",
                f"{base}.shx", 
                f"{base}.dbf",
                f"{base}.prj"
            ]
            
            print("\n   Archivos del shapefile:")
            for archivo in archivos_asociados:
                ruta = dir_shp / archivo
                if ruta.exists():
                    tamaño = ruta.stat().st_size / (1024*1024)
                    print(f"   ✓ {archivo} ({tamaño:.1f} MB)")
                else:
                    print(f"   ✗ {archivo} (faltante)")
        
        return True
    else:
        # Listar qué se extrajo
        archivos = list(DESTINO.rglob("*.*"))
        print(f"\n⚠️ No se encontró Drenaje_Sencillo.shp")
        print(f"   Archivos extraídos: {len(archivos)}")
        
        if archivos:
            print("\n   Primeros 20 archivos:")
            for i, archivo in enumerate(archivos[:20]):
                print(f"   - {archivo.name}")
        
        return False

def main():
    print("=" * 70)
    print("🗜️  EXTRACTOR ROBUSTO DE ZIP - Servicio 205 IGAC")
    print("=" * 70)
    
    if not ZIP_FILE.exists():
        print(f"\n❌ No se encuentra el archivo: {ZIP_FILE}")
        print("   Verifica que esté en ~/Downloads/Servicio-205.zip")
        return
    
    tamaño_mb = ZIP_FILE.stat().st_size / (1024 * 1024)
    print(f"\n📦 Archivo: {ZIP_FILE.name}")
    print(f"   Tamaño: {tamaño_mb:.1f} MB")
    print(f"   Destino: {DESTINO}")
    
    # Intentar métodos en orden
    exito = False
    
    # Método 1: unzip (más tolerante con ZIPs problemáticos)
    if not exito:
        exito = metodo_1_unzip_terminal()
    
    # Método 2: Python zipfile
    if not exito:
        exito = metodo_2_python_zipfile_permisivo()
    
    # Método 3: Análisis manual
    if not exito:
        metodo_3_extraer_parcial()
    
    # Verificar resultados
    print("\n" + "=" * 70)
    if verificar_archivos_extraidos():
        print("\n✅ ¡ÉXITO! Archivos de drenaje extraídos correctamente")
        print(f"\n📂 Revisa: {DESTINO}")
        print("\n💡 Siguiente paso: Mover archivos a datos_geograficos/red_hidrica/")
    else:
        print("\n⚠️  No se pudo extraer completamente")
        print("\n💡 Opciones:")
        print("   1. Re-descargar el archivo completo (espera a que llegue a 836.8 MB)")
        print("   2. Usar el descompresor online y descargar solo los archivos Drenaje_Sencillo.*")
        print("   3. Buscar un dataset más pequeño (solo departamento del Cesar)")

if __name__ == "__main__":
    main()
