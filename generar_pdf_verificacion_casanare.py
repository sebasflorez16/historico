#!/usr/bin/env python3
"""
Script para generar PDF de verificación legal de prueba
Usa una parcela en Casanare con todos los datos geográficos instalados
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.gis.geos import Point, Polygon
from verificador_legal import VerificadorRestriccionesLegales
from shapely.geometry import mapping
import json

def generar_pdf_prueba_casanare():
    """Genera un PDF de verificación legal para la parcela REAL de la base de datos (ID=6)"""
    
    print("=" * 80)
    print("📄 GENERACIÓN DE PDF DE VERIFICACIÓN LEGAL - CASANARE")
    print("=" * 80)
    
    # USAR PARCELA REAL DE LA BASE DE DATOS
    from informes.models import Parcela
    
    try:
        parcela_real = Parcela.objects.get(id=6)
        print(f"\n✅ Parcela encontrada en la base de datos:")
        print(f"   ID: {parcela_real.id}")
        print(f"   Nombre: {parcela_real.nombre}")
        print(f"   Propietario: {parcela_real.propietario}")
        print(f"   Área: {parcela_real.area_hectareas:.2f} ha")
        print(f"   Tipo de cultivo: {parcela_real.tipo_cultivo or 'No especificado'}")
        
        # Obtener centroide para mostrar ubicación
        centroide = parcela_real.geometria.centroid
        print(f"   Ubicación (centroide): {centroide.y:.6f}°N, {centroide.x:.6f}°W")
        
    except Parcela.DoesNotExist:
        print(f"❌ ERROR: No se encontró la parcela con ID=6 en la base de datos")
        return None
    
    # Convertir geometría Django a Shapely para el verificador
    from shapely.geometry import shape
    import json
    parcela_geom_shapely = shape(json.loads(parcela_real.geometria.geojson))
    
    print(f"\n📐 Geometría de la parcela:")
    print(f"   Tipo: {parcela_geom_shapely.geom_type}")
    print(f"   Área calculada: {parcela_real.area_hectareas:.2f} ha")
    print(f"   Coordenadas bounds: {parcela_geom_shapely.bounds}")
    
    # Inicializar verificador
    print(f"\n🔄 Inicializando verificador legal...")
    verificador = VerificadorRestriccionesLegales()
    
    # Cargar todas las capas
    print(f"\n📥 Cargando capas geográficas:")
    
    print(f"   1. Red hídrica...")
    verificador.cargar_red_hidrica()
    
    print(f"   2. Áreas protegidas (RUNAP)...")
    verificador.cargar_areas_protegidas()
    
    print(f"   3. Resguardos indígenas...")
    verificador.cargar_resguardos_indigenas()
    
    print(f"   4. Páramos...")
    verificador.cargar_paramos()
    
    # Ejecutar verificación
    print(f"\n🔍 Ejecutando verificación legal...")
    resultado = verificador.verificar_parcela(
        parcela_id=parcela_real.id,
        geometria_parcela=mapping(parcela_geom_shapely),
        nombre_parcela=parcela_real.nombre
    )
    
    # Mostrar resultados
    print(f"\n" + "=" * 80)
    print(f"📊 RESULTADOS DE VERIFICACIÓN")
    print(f"=" * 80)
    
    print(f"\n✅ Cumple normativa: {'SÍ' if resultado.cumple_normativa else 'NO'}")
    print(f"📊 Área total: {resultado.area_total_ha:.2f} ha")
    
    if resultado.area_cultivable_ha['determinable']:
        print(f"🌾 Área cultivable: {resultado.area_cultivable_ha['valor_ha']:.2f} ha")
    else:
        print(f"⚠️  Área cultivable: {resultado.area_cultivable_ha['nota']}")
    
    print(f"🚫 Área restringida: {resultado.area_restringida_ha:.2f} ha")
    print(f"📈 Porcentaje restringido: {resultado.porcentaje_restringido:.2f}%")
    
    print(f"\n🔍 Restricciones encontradas: {len(resultado.restricciones_encontradas)}")
    if resultado.restricciones_encontradas:
        for i, rest in enumerate(resultado.restricciones_encontradas, 1):
            print(f"\n   {i}. {rest['tipo'].upper()}")
            print(f"      Nombre: {rest.get('nombre', 'N/A')}")
            if 'categoria' in rest:
                print(f"      Categoría: {rest['categoria']}")
            print(f"      Área afectada: {rest['area_afectada_ha']:.4f} ha")
            print(f"      Normativa: {rest['normativa']}")
    else:
        print(f"   ✅ No se encontraron restricciones")
    
    if resultado.advertencias:
        print(f"\n⚠️  ADVERTENCIAS ({len(resultado.advertencias)}):")
        for adv in resultado.advertencias:
            print(f"   • {adv}")
    
    print(f"\n📋 Niveles de confianza:")
    for capa, datos in resultado.niveles_confianza.items():
        if datos['cargada']:
            print(f"   • {capa.replace('_', ' ').title()}: {datos['confianza']} ({datos['razon']})")
        else:
            print(f"   • {capa.replace('_', ' ').title()}: No cargada")
    
    # Generar JSON de resultado
    print(f"\n📄 Guardando resultado en JSON...")
    resultado_json = resultado.to_json()
    
    output_json = "resultado_verificacion_casanare.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        f.write(resultado_json)
    
    print(f"✅ JSON guardado: {output_json}")
    
    # Ahora generar el PDF usando el generador MEJORADO
    print(f"\n📄 Generando PDF MEJORADO de verificación legal...")
    
    try:
        from generador_pdf_legal import GeneradorPDFLegal
        from datetime import datetime
        
        # USAR LA PARCELA REAL DIRECTAMENTE (no crear mock)
        # Generar nombre único con timestamp para comparación
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_pdf = f"./media/verificacion_legal/verificacion_legal_casanare_parcela_{parcela_real.id}_{timestamp}.pdf"
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
        
        # Usar el generador mejorado con la parcela REAL
        generador = GeneradorPDFLegal()
        generador.generar_pdf(
            parcela=parcela_real,  # Parcela real de la DB
            resultado=resultado,
            verificador=verificador,
            output_path=output_pdf,
            departamento="Casanare"  # Hardcoded porque el modelo no tiene campo departamento
        )
        
        print(f"✅ PDF MEJORADO generado: {output_pdf}")
        print(f"\n   📊 DATOS REALES USADOS:")
        print(f"      - Parcela ID: {parcela_real.id}")
        print(f"      - Nombre: {parcela_real.nombre}")
        print(f"      - Propietario: {parcela_real.propietario}")
        print(f"      - Área: {parcela_real.area_hectareas:.2f} ha")
        print(f"      - Geometría: REAL de la base de datos")
        print(f"      - Timestamp: {timestamp}")
        print(f"\n   💡 Ahora puedes comparar este PDF con versiones anteriores")
        print(f"      en la carpeta: ./media/verificacion_legal/")
        
        # Abrir el PDF automáticamente
        import subprocess
        subprocess.run(['open', output_pdf])
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n💡 ALTERNATIVA: Usar el JSON generado para crear el PDF manualmente")
        print(f"   Archivo: {output_json}")
    
    print(f"\n" + "=" * 80)
    print(f"✅ VERIFICACIÓN COMPLETADA")
    print(f"=" * 80)
    
    return resultado

if __name__ == "__main__":
    resultado = generar_pdf_prueba_casanare()
    
    if resultado.cumple_normativa:
        print(f"\n🎉 LA PARCELA CUMPLE CON TODA LA NORMATIVA AMBIENTAL")
        sys.exit(0)
    else:
        print(f"\n⚠️  LA PARCELA TIENE RESTRICCIONES O FALTAN DATOS")
        sys.exit(1)
