"""
Script de prueba para verificación legal de parcelas
====================================================

Este script permite probar el verificador de restricciones legales
directamente desde la terminal usando parcelas reales de la base de datos.

Uso:
    python test_verificacion_legal_terminal.py --parcela 1
    python test_verificacion_legal_terminal.py --parcela 1 --parcela 2

Autor: AgroTech Histórico
Fecha: Enero 2026
"""

import os
import sys
import django
import argparse
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from shapely.geometry import mapping


def obtener_geometria_parcela(parcela: Parcela) -> dict:
    """
    Extrae la geometría de una parcela en formato GeoJSON
    """
    # Intentar con campo 'geometria' (PostGIS)
    if hasattr(parcela, 'geometria') and parcela.geometria:
        # Si es un objeto GEOSGeometry de Django
        if hasattr(parcela.geometria, 'geojson'):
            import json
            return json.loads(parcela.geometria.geojson)
        # Si geometry es un string GeoJSON
        elif isinstance(parcela.geometria, str):
            import json
            return json.loads(parcela.geometria)
        # Si geometry es un objeto Shapely
        elif hasattr(parcela.geometria, '__geo_interface__'):
            return parcela.geometria.__geo_interface__
    
    # Intentar con campo 'coordenadas'
    if hasattr(parcela, 'coordenadas') and parcela.coordenadas:
        import json
        if isinstance(parcela.coordenadas, str):
            return json.loads(parcela.coordenadas)
        elif isinstance(parcela.coordenadas, dict):
            return parcela.coordenadas
    
    # Si no hay geometría, intentar construir desde punto central
    if hasattr(parcela, 'centroide') and parcela.centroide:
        from shapely.geometry import Point
        punto = Point(parcela.centroide.x, parcela.centroide.y)
        # Buffer aproximado basado en área
        if parcela.area_hectareas:
            # Calcular radio aproximado en grados (muy aproximado)
            radio_aprox = (parcela.area_hectareas / 100) ** 0.5 * 0.01
        else:
            radio_aprox = 0.005  # ~500m
        buffer = punto.buffer(radio_aprox)
        return mapping(buffer)
    
    raise ValueError(f"Parcela {parcela.id} no tiene geometría válida")


def probar_parcela(parcela_id: int, verificador: VerificadorRestriccionesLegales):
    """
    Prueba verificación legal para una parcela específica
    """
    try:
        # Obtener parcela de la base de datos
        parcela = Parcela.objects.get(id=parcela_id)
        
        print(f"\n{'='*80}")
        print(f"🌾 Probando parcela: {parcela.nombre or f'Parcela {parcela.id}'}")
        print(f"{'='*80}")
        print(f"📍 ID: {parcela.id}")
        print(f"📏 Área registrada: {parcela.area_hectareas:.2f} ha" if parcela.area_hectareas else "📏 Área: No especificada")
        print(f"🌱 Cultivo: {parcela.tipo_cultivo or 'No especificado'}")
        print(f"👤 Propietario: {parcela.propietario or 'No especificado'}")
        
        # Extraer geometría
        try:
            geometria = obtener_geometria_parcela(parcela)
            print(f"✅ Geometría cargada correctamente")
        except Exception as e:
            print(f"❌ Error obteniendo geometría: {e}")
            return None
        
        # Realizar verificación
        resultado = verificador.verificar_parcela(
            parcela_id=parcela.id,
            geometria_parcela=geometria,
            nombre_parcela=parcela.nombre or f"Parcela {parcela.id}"
        )
        
        # Mostrar reporte
        print(verificador.generar_reporte_consola(resultado))
        
        # Guardar resultado en archivo JSON
        archivo_salida = f"verificacion_parcela_{parcela_id}.json"
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(resultado.to_json())
        print(f"💾 Resultado guardado en: {archivo_salida}\n")
        
        return resultado
        
    except Parcela.DoesNotExist:
        print(f"❌ Error: Parcela con ID {parcela_id} no existe")
        return None
    except Exception as e:
        print(f"❌ Error procesando parcela {parcela_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def listar_parcelas_disponibles():
    """
    Lista las primeras 20 parcelas disponibles en la base de datos
    """
    print("\n" + "="*80)
    print("📋 PARCELAS DISPONIBLES EN LA BASE DE DATOS")
    print("="*80 + "\n")
    
    parcelas = Parcela.objects.all()[:20]
    
    if not parcelas:
        print("❌ No hay parcelas en la base de datos")
        return
    
    print(f"{'ID':<5} {'Nombre':<30} {'Área (ha)':<12} {'Cultivo':<20}")
    print("-" * 80)
    
    for p in parcelas:
        nombre = (p.nombre or f"Parcela {p.id}")[:28]
        area = f"{p.area_hectareas:.2f}" if p.area_hectareas else "N/A"
        cultivo = (p.tipo_cultivo or "N/A")[:18]
        print(f"{p.id:<5} {nombre:<30} {area:<12} {cultivo:<20}")
    
    total = Parcela.objects.count()
    if total > 20:
        print(f"\n... y {total - 20} parcelas más")
    
    print(f"\nTotal: {total} parcelas")
    print("\nUso: python test_verificacion_legal_terminal.py --parcela <ID>")


def main():
    """
    Función principal
    """
    parser = argparse.ArgumentParser(
        description='Verificación de restricciones legales para parcelas agrícolas'
    )
    parser.add_argument(
        '--parcela',
        type=int,
        action='append',
        help='ID de parcela(s) a verificar (puede repetir: --parcela 1 --parcela 2)'
    )
    parser.add_argument(
        '--listar',
        action='store_true',
        help='Listar parcelas disponibles'
    )
    parser.add_argument(
        '--datos',
        type=str,
        default=None,
        help='Directorio con shapefiles (por defecto: ./datos_geograficos/)'
    )
    
    args = parser.parse_args()
    
    # Si se solicita listar parcelas
    if args.listar:
        listar_parcelas_disponibles()
        return
    
    # Si no se especificaron parcelas, mostrar ayuda
    if not args.parcela:
        print("\n⚠️  Debe especificar al menos una parcela con --parcela <ID>")
        print("   O usar --listar para ver parcelas disponibles\n")
        parser.print_help()
        return
    
    print("\n" + "="*80)
    print("🌿 VERIFICADOR DE RESTRICCIONES LEGALES")
    print("="*80)
    
    # Inicializar verificador
    print("\n📥 Inicializando verificador...")
    verificador = VerificadorRestriccionesLegales(directorio_datos=args.datos)
    
    # Cargar capas geográficas
    print("📥 Cargando capas geográficas...")
    print("-" * 80)
    
    capas_cargadas = 0
    
    if verificador.cargar_red_hidrica():
        capas_cargadas += 1
    
    if verificador.cargar_areas_protegidas():
        capas_cargadas += 1
    
    if verificador.cargar_resguardos_indigenas():
        capas_cargadas += 1
    
    if verificador.cargar_paramos():
        capas_cargadas += 1
    
    print("-" * 80)
    print(f"✅ {capas_cargadas}/4 capas cargadas correctamente")
    
    if capas_cargadas == 0:
        print("\n⚠️  ADVERTENCIA: No se cargó ninguna capa geográfica")
        print("   La verificación será INCOMPLETA")
        print("\n   Para obtener datos geográficos:")
        print("   1. Red hídrica: https://www.datos.gov.co (IGAC)")
        print("   2. Áreas protegidas: http://runap.parquesnacionales.gov.co")
        print("   3. Resguardos: https://www.ant.gov.co")
        print("   4. Páramos: http://www.ideam.gov.co")
        print("\n   Guardar shapefiles en: ./datos_geograficos/")
    
    # Procesar cada parcela
    resultados = []
    for parcela_id in args.parcela:
        resultado = probar_parcela(parcela_id, verificador)
        if resultado:
            resultados.append(resultado)
    
    # Resumen final
    if resultados:
        print("\n" + "="*80)
        print("📊 RESUMEN DE VERIFICACIONES")
        print("="*80 + "\n")
        
        total = len(resultados)
        conformes = sum(1 for r in resultados if r.cumple_normativa)
        no_conformes = total - conformes
        
        print(f"Total verificadas: {total}")
        print(f"✅ Conformes: {conformes} ({conformes/total*100:.1f}%)")
        print(f"❌ No conformes: {no_conformes} ({no_conformes/total*100:.1f}%)")
        
        if no_conformes > 0:
            print(f"\n⚠️  Restricciones más comunes:")
            tipos_restricciones = {}
            for r in resultados:
                for rest in r.restricciones_encontradas:
                    tipo = rest['tipo']
                    tipos_restricciones[tipo] = tipos_restricciones.get(tipo, 0) + 1
            
            for tipo, count in sorted(tipos_restricciones.items(), key=lambda x: -x[1]):
                print(f"   • {tipo.replace('_', ' ').title()}: {count}")
        
        print("\n" + "="*80)


if __name__ == '__main__':
    main()
