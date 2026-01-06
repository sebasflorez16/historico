#!/usr/bin/env python
"""
Script de demostración para AgroTech Histórico
Automatiza la creación de datos de prueba y generación de informes
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual, Informe
from informes.services.eosda_api import eosda_service
from informes.services.analisis_datos import analisis_service
from informes.services.generador_pdf import generador_pdf

def crear_parcela_demo():
    """
    Crea una parcela de demostración con coordenadas de ejemplo
    """
    print("🌱 Creando parcela de demostración...")
    
    # Coordenadas de ejemplo (área rural cerca de Bogotá)
    geojson_ejemplo = {
        "type": "Polygon",
        "coordinates": [[
            [-74.2973, 4.5709],
            [-74.2950, 4.5709],
            [-74.2950, 4.5690],
            [-74.2973, 4.5690],
            [-74.2973, 4.5709]
        ]]
    }
    
    # Verificar si ya existe una parcela demo
    parcela_existente = Parcela.objects.filter(nombre="Finca Demo AgroTech").first()
    if parcela_existente:
        print(f"   ✅ Utilizando parcela existente: {parcela_existente.nombre}")
        return parcela_existente
    
    # Importar herramientas geoespaciales PostGIS
    from django.contrib.gis.geos import GEOSGeometry
    
    # Convertir GeoJSON a geometría PostGIS nativa
    geojson_str = json.dumps(geojson_ejemplo)
    geometria_postgis = GEOSGeometry(geojson_str)
    
    # Crear nueva parcela con PostGIS
    parcela = Parcela.objects.create(
        nombre="Finca Demo AgroTech",
        propietario="Agricultor Demostrativo",
        tipo_cultivo="Café",
        geometria=geometria_postgis,  # Campo PostGIS nativo (auto-calcula área/perímetro)
        fecha_inicio_monitoreo=date.today() - timedelta(days=365),
        notas="Parcela de demostración para pruebas del sistema AgroTech Histórico"
    )
    
    print(f"   ✅ Parcela creada: {parcela.nombre} ({parcela.area_hectareas} ha)")
    return parcela

def procesar_datos_satelitales(parcela):
    """
    Procesa datos satelitales para la parcela (simulados si no hay API real)
    """
    print("🛰️  Procesando datos satelitales...")
    
    # Verificar conectividad EOSDA
    conectividad = eosda_service.verificar_conectividad()
    if conectividad['conexion_exitosa']:
        print("   ✅ API EOSDA disponible - obteniendo datos reales")
    else:
        print("   ⚠️  API EOSDA no disponible - generando datos simulados")
    
    # Procesar datos de los últimos 12 meses
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=365)
    
    resultado = analisis_service.procesar_datos_mensuales(
        parcela, fecha_inicio, fecha_fin
    )
    
    if 'error' in resultado:
        print(f"   ❌ Error procesando datos: {resultado['error']}")
        return False
    
    meses_procesados = resultado.get('total_meses', 0)
    simulado = resultado.get('simulado', False)
    
    print(f"   ✅ Procesados {meses_procesados} meses de datos")
    if simulado:
        print("   📊 Datos simulados generados para demostración")
    
    return True

def generar_informe_demo(parcela):
    """
    Genera un informe PDF de demostración
    """
    print("📄 Generando informe PDF...")
    
    resultado = generador_pdf.generar_informe_completo(
        parcela=parcela,
        periodo_meses=12
    )
    
    if not resultado['success']:
        print(f"   ❌ Error generando informe: {resultado.get('error', 'Error desconocido')}")
        return None
    
    print(f"   ✅ Informe generado - ID: {resultado['informe_id']}")
    if resultado['archivo_pdf']:
        print(f"   📎 Archivo PDF: {resultado['archivo_pdf']}")
    
    return resultado['informe_id']

def mostrar_estadisticas():
    """
    Muestra estadísticas actuales del sistema
    """
    print("\n📊 ESTADÍSTICAS DEL SISTEMA")
    print("=" * 50)
    
    total_parcelas = Parcela.objects.filter(activa=True).count()
    total_indices = IndiceMensual.objects.count()
    total_informes = Informe.objects.count()
    
    print(f"Parcelas activas:     {total_parcelas}")
    print(f"Datos satelitales:    {total_indices} registros mensuales")
    print(f"Informes generados:   {total_informes}")
    
    # Última actividad
    ultimo_indice = IndiceMensual.objects.order_by('-fecha_consulta_api').first()
    if ultimo_indice:
        print(f"Último dato:          {ultimo_indice.fecha_consulta_api.strftime('%d/%m/%Y %H:%M')}")
    
    ultimo_informe = Informe.objects.order_by('-fecha_generacion').first()
    if ultimo_informe:
        print(f"Último informe:       {ultimo_informe.fecha_generacion.strftime('%d/%m/%Y %H:%M')}")

def verificar_sistema():
    """
    Verifica el estado general del sistema
    """
    print("\n🔍 VERIFICACIÓN DEL SISTEMA")
    print("=" * 50)
    
    # Verificar base de datos
    try:
        total_parcelas = Parcela.objects.count()
        print(f"✅ Base de datos operativa ({total_parcelas} parcelas)")
    except Exception as e:
        print(f"❌ Error en base de datos: {str(e)}")
        return False
    
    # Verificar servicios
    try:
        conectividad = eosda_service.verificar_conectividad()
        if conectividad['conexion_exitosa']:
            print(f"✅ API EOSDA operativa (respuesta: {conectividad['tiempo_respuesta']}ms)")
        else:
            print("⚠️  API EOSDA no disponible - funcionará en modo simulación")
    except Exception as e:
        print(f"❌ Error verificando API EOSDA: {str(e)}")
    
    # Verificar directorios
    import os
    from django.conf import settings
    
    media_dir = settings.MEDIA_ROOT
    if os.path.exists(media_dir):
        print("✅ Directorio de medios configurado")
    else:
        print("⚠️  Directorio de medios no existe")
    
    print("✅ Verificación completada")
    return True

def menu_principal():
    """
    Menú interactivo para la demostración
    """
    while True:
        print("\n" + "="*60)
        print("🌱 AGROTECH HISTÓRICO - DEMOSTRACIÓN")
        print("="*60)
        print("1. Crear parcela de demostración")
        print("2. Procesar datos satelitales")
        print("3. Generar informe PDF")
        print("4. Ejecutar demostración completa")
        print("5. Ver estadísticas del sistema")
        print("6. Verificar estado del sistema")
        print("7. Limpiar datos de demo")
        print("0. Salir")
        print("-" * 60)
        
        try:
            opcion = input("Seleccione una opción: ").strip()
            
            if opcion == '0':
                print("👋 ¡Gracias por probar AgroTech Histórico!")
                break
            elif opcion == '1':
                parcela = crear_parcela_demo()
                print(f"\n✅ Parcela '{parcela.nombre}' lista para análisis")
            elif opcion == '2':
                parcela = Parcela.objects.filter(nombre="Finca Demo AgroTech").first()
                if not parcela:
                    print("❌ Primero debe crear la parcela de demostración (opción 1)")
                    continue
                procesar_datos_satelitales(parcela)
            elif opcion == '3':
                parcela = Parcela.objects.filter(nombre="Finca Demo AgroTech").first()
                if not parcela:
                    print("❌ Primero debe crear la parcela de demostración (opción 1)")
                    continue
                generar_informe_demo(parcela)
            elif opcion == '4':
                ejecutar_demo_completa()
            elif opcion == '5':
                mostrar_estadisticas()
            elif opcion == '6':
                verificar_sistema()
            elif opcion == '7':
                limpiar_datos_demo()
            else:
                print("❌ Opción no válida")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def ejecutar_demo_completa():
    """
    Ejecuta la demostración completa automáticamente
    """
    print("\n🚀 EJECUTANDO DEMOSTRACIÓN COMPLETA")
    print("=" * 50)
    
    try:
        # Paso 1: Verificar sistema
        if not verificar_sistema():
            print("❌ Falló la verificación del sistema")
            return
        
        # Paso 2: Crear parcela
        parcela = crear_parcela_demo()
        
        # Paso 3: Procesar datos
        if procesar_datos_satelitales(parcela):
            print("   🎯 Datos satelitales procesados correctamente")
        else:
            print("   ❌ Error procesando datos satelitales")
            return
        
        # Paso 4: Generar informe
        informe_id = generar_informe_demo(parcela)
        if informe_id:
            print(f"   📋 Informe generado con ID: {informe_id}")
        
        # Paso 5: Mostrar resultados
        mostrar_estadisticas()
        
        print("\n🎉 ¡DEMOSTRACIÓN COMPLETADA EXITOSAMENTE!")
        print(f"   👀 Puede revisar la parcela en: /informes/parcelas/{parcela.id}/")
        if informe_id:
            print(f"   📄 Ver informe en: /informes/informes/{informe_id}/")
        
    except Exception as e:
        print(f"❌ Error durante la demostración: {str(e)}")

def limpiar_datos_demo():
    """
    Limpia los datos de demostración
    """
    confirmacion = input("⚠️  ¿Está seguro de eliminar todos los datos de demo? (s/N): ")
    if confirmacion.lower() != 's':
        print("   Operación cancelada")
        return
    
    print("🧹 Limpiando datos de demostración...")
    
    # Eliminar parcelas demo
    parcelas_demo = Parcela.objects.filter(nombre__contains="Demo")
    count_parcelas = parcelas_demo.count()
    parcelas_demo.delete()
    
    # Los índices e informes se eliminan automáticamente por CASCADE
    print(f"   ✅ Eliminadas {count_parcelas} parcelas de demo")
    print("   ✅ Datos asociados eliminados automáticamente")

def main():
    """
    Función principal del script
    """
    print("🌱 Bienvenido a AgroTech Histórico - Sistema de Demostración")
    print("📡 Sistema de análisis satelital agrícola con integración EOSDA")
    print()
    
    # Verificar que Django esté configurado correctamente
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Conexión a base de datos establecida")
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {str(e)}")
        print("   Ejecute: python manage.py migrate")
        sys.exit(1)
    
    # Verificar si es ejecución no interactiva
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("🤖 Modo automático activado")
        ejecutar_demo_completa()
    else:
        menu_principal()

if __name__ == '__main__':
    main()