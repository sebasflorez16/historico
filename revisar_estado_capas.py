#!/usr/bin/env python3
"""
Script de monitoreo del estado de las capas geográficas
Muestra qué archivos están disponibles y cuáles faltan
"""

from pathlib import Path
from datetime import datetime

def revisar_estado_capas():
    """Revisa el estado de todas las capas geográficas"""
    
    print("=" * 80)
    print("📊 ESTADO DE CAPAS GEOGRÁFICAS PARA VERIFICACIÓN LEGAL")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_dir = Path("datos_geograficos")
    
    capas = {
        "RUNAP (Áreas Protegidas)": {
            "directorio": base_dir / "runap",
            "archivos_esperados": ["runap.shp", "*.shp"],
            "prioridad": "CRÍTICA",
            "cobertura_esperada": "Nacional (1,837 áreas)",
            "estado_actual": None
        },
        "Resguardos Indígenas": {
            "directorio": base_dir / "resguardos_indigenas",
            "archivos_esperados": ["Resguardo_Indígena_Formalizado.shp", "*.shp"],
            "prioridad": "CRÍTICA",
            "cobertura_esperada": "Nacional (954 resguardos)",
            "estado_actual": None
        },
        "Páramos": {
            "directorio": base_dir / "paramos",
            "archivos_esperados": ["*.shp"],
            "prioridad": "ALTA",
            "cobertura_esperada": "Nacional (~37 complejos)",
            "estado_actual": None
        },
        "Red Hídrica": {
            "directorio": base_dir / "red_hidrica",
            "archivos_esperados": ["*.shp", "drenajes*.geojson"],
            "prioridad": "CRÍTICA",
            "cobertura_esperada": "Nacional (drenajes completos)",
            "estado_actual": None
        }
    }
    
    # Revisar cada capa
    for nombre, config in capas.items():
        directorio = config["directorio"]
        
        print(f"\n{'='*80}")
        print(f"📁 {nombre}")
        print(f"{'='*80}")
        print(f"Prioridad: {config['prioridad']}")
        print(f"Cobertura esperada: {config['cobertura_esperada']}")
        print(f"Directorio: {directorio}")
        
        if not directorio.exists():
            print(f"\n❌ DIRECTORIO NO EXISTE")
            print(f"   Crear con: mkdir -p {directorio}")
            config["estado_actual"] = "NO_EXISTE"
            continue
        
        # Buscar archivos
        archivos_encontrados = []
        for patron in config["archivos_esperados"]:
            archivos = list(directorio.glob(patron))
            # Filtrar archivos departamentales vacíos
            archivos = [f for f in archivos if 'casanare' not in f.name.lower()]
            archivos_encontrados.extend(archivos)
        
        if not archivos_encontrados:
            print(f"\n⚠️  DIRECTORIO VACÍO O SIN SHAPEFILES")
            print(f"   Archivos en directorio: {list(directorio.iterdir())}")
            config["estado_actual"] = "VACIO"
        else:
            print(f"\n✅ ARCHIVOS ENCONTRADOS ({len(archivos_encontrados)}):")
            for archivo in archivos_encontrados:
                # Obtener tamaño
                tamanio = archivo.stat().st_size
                tamanio_mb = tamanio / (1024 * 1024)
                
                # Determinar tipo
                if archivo.suffix == '.shp':
                    tipo = "Shapefile"
                elif archivo.suffix == '.geojson':
                    tipo = "GeoJSON"
                else:
                    tipo = archivo.suffix
                
                print(f"   • {archivo.name}")
                print(f"     Tipo: {tipo}, Tamaño: {tamanio_mb:.2f} MB")
                
                # Validar si es shapefile completo
                if archivo.suffix == '.shp':
                    stem = archivo.stem
                    archivos_auxiliares = [
                        directorio / f"{stem}.dbf",
                        directorio / f"{stem}.prj",
                        directorio / f"{stem}.shx"
                    ]
                    auxiliares_ok = all(f.exists() for f in archivos_auxiliares)
                    
                    if auxiliares_ok:
                        print(f"     ✅ Shapefile completo (con .dbf, .prj, .shx)")
                        config["estado_actual"] = "COMPLETO"
                    else:
                        print(f"     ⚠️  Faltan archivos auxiliares del shapefile")
                        faltantes = [f.name for f in archivos_auxiliares if not f.exists()]
                        print(f"     Faltantes: {', '.join(faltantes)}")
                        config["estado_actual"] = "INCOMPLETO"
                elif archivo.suffix == '.geojson':
                    if tamanio < 1000:  # Menos de 1KB = probablemente vacío
                        print(f"     ⚠️  Archivo muy pequeño (probablemente vacío)")
                        config["estado_actual"] = "VACIO"
                    else:
                        print(f"     ✅ GeoJSON con datos")
                        config["estado_actual"] = "COMPLETO"
    
    # Resumen final
    print(f"\n" + "=" * 80)
    print(f"📋 RESUMEN GENERAL")
    print(f"=" * 80)
    
    print(f"\n{'Capa':<30} {'Estado':<15} {'Prioridad':<10}")
    print(f"{'-'*30} {'-'*15} {'-'*10}")
    
    for nombre, config in capas.items():
        estado = config["estado_actual"] or "DESCONOCIDO"
        prioridad = config["prioridad"]
        
        if estado == "COMPLETO":
            icono = "✅"
        elif estado == "VACIO" or estado == "NO_EXISTE":
            icono = "❌"
        else:
            icono = "⚠️"
        
        print(f"{nombre:<30} {icono} {estado:<15} {prioridad:<10}")
    
    # Análisis de preparación
    print(f"\n" + "=" * 80)
    print(f"🎯 ESTADO DE PREPARACIÓN")
    print(f"=" * 80)
    
    capas_criticas = [c for c in capas.values() if c["prioridad"] == "CRÍTICA"]
    capas_criticas_ok = [c for c in capas_criticas if c["estado_actual"] == "COMPLETO"]
    
    capas_altas = [c for c in capas.values() if c["prioridad"] == "ALTA"]
    capas_altas_ok = [c for c in capas_altas if c["estado_actual"] == "COMPLETO"]
    
    total_capas = len(capas)
    capas_ok = len([c for c in capas.values() if c["estado_actual"] == "COMPLETO"])
    
    print(f"\nCapas totales: {total_capas}")
    print(f"Capas completas: {capas_ok}/{total_capas}")
    print(f"Capas críticas completas: {len(capas_criticas_ok)}/{len(capas_criticas)}")
    print(f"Capas alta prioridad completas: {len(capas_altas_ok)}/{len(capas_altas)}")
    
    if capas_ok == total_capas:
        print(f"\n🎉 SISTEMA COMPLETO - Listo para verificaciones legales")
        return 0
    elif len(capas_criticas_ok) == len(capas_criticas):
        print(f"\n✅ CAPAS CRÍTICAS COMPLETAS - Sistema parcialmente operativo")
        print(f"⚠️  Faltan capas de alta prioridad para verificación completa")
        return 1
    else:
        print(f"\n❌ SISTEMA INCOMPLETO - Faltan capas críticas")
        print(f"\n📥 PRÓXIMOS PASOS:")
        for nombre, config in capas.items():
            if config["prioridad"] == "CRÍTICA" and config["estado_actual"] != "COMPLETO":
                print(f"   • Descargar {nombre}")
        return 2

if __name__ == "__main__":
    import sys
    sys.exit(revisar_estado_capas())
