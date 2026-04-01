#!/usr/bin/env python
"""
Script para descargar datos geográficos desde Google Drive en Railway
Se ejecuta automáticamente al hacer deploy
"""

import os
import sys
import requests
from pathlib import Path

# URLs públicas de Google Drive (compartidas con "Cualquiera con el enlace")
DATOS_URLS = {
    'red_hidrica': 'https://drive.google.com/uc?export=download&id=TU_ID_AQUI',
    'runap': 'https://drive.google.com/uc?export=download&id=TU_ID_AQUI',
    'resguardos': 'https://drive.google.com/uc?export=download&id=TU_ID_AQUI',
    'paramos': 'https://drive.google.com/uc?export=download&id=TU_ID_AQUI',
}

def descargar_archivo(url, destino):
    """Descarga archivo con barra de progreso"""
    print(f"📥 Descargando {destino}...")
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(destino, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"  {percent:.1f}% descargado", end='\r')
    
    print(f"✅ Descarga completa: {destino}")

def main():
    """Descarga todos los datos necesarios"""
    base_dir = Path(__file__).parent / 'datos_geograficos'
    base_dir.mkdir(exist_ok=True)
    
    # Solo descargar si NO existen los datos
    if (base_dir / 'red_hidrica').exists():
        print("✅ Datos ya descargados, omitiendo...")
        return
    
    print("🌍 Descargando datos geográficos para producción...")
    
    for nombre, url in DATOS_URLS.items():
        destino = base_dir / f"{nombre}.zip"
        try:
            descargar_archivo(url, destino)
            
            # Descomprimir
            print(f"📦 Descomprimiendo {nombre}...")
            import zipfile
            with zipfile.ZipFile(destino, 'r') as zip_ref:
                zip_ref.extractall(base_dir / nombre)
            
            # Eliminar zip para ahorrar espacio
            destino.unlink()
            print(f"✅ {nombre} listo")
            
        except Exception as e:
            print(f"❌ Error descargando {nombre}: {e}")
            sys.exit(1)
    
    print("🎉 Todos los datos geográficos descargados exitosamente")

if __name__ == '__main__':
    main()
