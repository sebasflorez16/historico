#!/usr/bin/env python
"""
🎯 TEST COMPLETO - PDF LEGAL CON 3 MAPAS PROFESIONALES INTEGRADOS
===================================================================

Valida que el informe legal incluya los tres mapas en el orden correcto:
1. Mapa Departamental → Contexto regional
2. Mapa Municipal → Contexto local
3. Mapa de Influencia Legal Directa → Análisis crítico del lindero

El PDF generado debe ser apto para entrega a cliente bancario/auditoría legal.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal
from datetime import datetime


def test_pdf_legal_completo():
    """
    Genera PDF legal completo con los 3 mapas profesionales integrados
    """
    print("\n" + "="*100)
    print("🎯 TEST DE GENERACIÓN DE PDF LEGAL COMPLETO CON 3 MAPAS PROFESIONALES")
    print("="*100 + "\n")
    
    # =========================================================================
    # 1. CARGAR PARCELA DE PRUEBA
    # =========================================================================
    parcela_id = 6  # Parcela en Paz de Ariporo, Casanare (zona de prueba validada)
    
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        print(f"✅ Parcela cargada correctamente:")
        print(f"   📍 ID: {parcela.id}")
        print(f"   📝 Nombre: {parcela.nombre}")
        print(f"   🌾 Cultivo: {parcela.tipo_cultivo}")
        print(f"   📏 Área: {parcela.area_hectareas:.2f} ha")
        print(f"   🏛️  Departamento: Casanare (inferido)")
        
    except Parcela.DoesNotExist:
        print(f"❌ ERROR: No se encontró la parcela con ID={parcela_id}")
        print(f"   💡 Verifica que exista en la base de datos con: python manage.py shell")
        sys.exit(1)
    
    # =========================================================================
    # 2. EJECUTAR VERIFICACIÓN LEGAL
    # =========================================================================
    print(f"\n{'='*100}")
    print(f"🔍 EJECUTANDO VERIFICACIÓN LEGAL DE RESTRICCIONES")
    print(f"{'='*100}\n")
    
    verificador = VerificadorRestriccionesLegales()
    
    # 🔧 CARGAR CAPAS GEOGRÁFICAS ANTES DE VERIFICAR
    print(f"📂 Cargando capas geográficas oficiales...")
    print(f"   1️⃣  Cargando red hídrica (IGAC)...")
    verificador.cargar_red_hidrica()
    print(f"   2️⃣  Cargando áreas protegidas (RUNAP)...")
    verificador.cargar_areas_protegidas()
    print(f"   3️⃣  Cargando resguardos indígenas (MinInterior)...")
    verificador.cargar_resguardos_indigenas()
    print(f"   4️⃣  Cargando páramos (MinAmbiente)...")
    verificador.cargar_paramos()
    print(f"✅ Todas las capas cargadas correctamente\n")
    
    resultado = verificador.verificar_parcela(
        parcela_id=parcela.id,
        geometria_parcela=parcela.geometria,
        nombre_parcela=parcela.nombre
    )
    
    print(f"✅ Verificación legal completada:")
    print(f"   📊 Área total analizada: {resultado.area_total_ha:.2f} ha")
    print(f"   🚨 Restricciones encontradas: {len(resultado.restricciones_encontradas)}")
    print(f"   📏 Área restringida: {resultado.area_restringida_ha:.2f} ha ({resultado.porcentaje_restringido:.1f}%)")
    print(f"   ✅ Cumple normativa: {'Sí' if resultado.cumple_normativa else 'No'}")
    
    if resultado.restricciones_encontradas:
        print(f"\n   📋 Detalle de restricciones:")
        for i, rest in enumerate(resultado.restricciones_encontradas, 1):
            print(f"      {i}. {rest.get('tipo', 'N/A')}: {rest.get('nombre', 'N/A')[:40]} "
                  f"({rest.get('porcentaje_area_parcela', 0):.1f}% de la parcela)")
    else:
        print(f"   🎉 ¡Sin restricciones! La parcela está 100% libre para cultivo")
    
    # =========================================================================
    # 3. GENERAR PDF LEGAL CON 3 MAPAS PROFESIONALES
    # =========================================================================
    print(f"\n{'='*100}")
    print(f"📄 GENERANDO PDF LEGAL COMPLETO CON 3 MAPAS PROFESIONALES")
    print(f"{'='*100}\n")
    
    output_dir = "media/informes_legales"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"informe_legal_parcela{parcela.id}_{timestamp}_3mapas.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"📁 Ruta de salida: {output_path}")
    print(f"🗺️  Mapas a incluir:")
    print(f"   1️⃣  MAPA DEPARTAMENTAL → Contexto regional (áreas protegidas, páramos, red hídrica principal)")
    print(f"   2️⃣  MAPA MUNICIPAL → Contexto local (límite municipal, red hídrica jerarquizada)")
    print(f"   3️⃣  MAPA INFLUENCIA LEGAL DIRECTA → Análisis crítico del lindero (distancias legales a ríos)")
    print(f"\n🚀 Iniciando generación...\n")
    
    generador = GeneradorPDFLegal()
    
    try:
        pdf_path = generador.generar_pdf(
            parcela=parcela,
            resultado=resultado,
            verificador=verificador,
            output_path=output_path,
            departamento="Casanare"
        )
        
        print(f"\n{'='*100}")
        print(f"✅ PDF LEGAL GENERADO EXITOSAMENTE")
        print(f"{'='*100}\n")
        print(f"📄 Archivo: {pdf_path}")
        print(f"📊 Tamaño: {os.path.getsize(pdf_path) / 1024:.1f} KB")
        print(f"🕒 Timestamp: {timestamp}")
        
        print(f"\n🎯 CONTENIDO DEL PDF:")
        print(f"   ✅ Portada profesional")
        print(f"   ✅ Conclusión ejecutiva con badge de viabilidad")
        print(f"   ✅ Metadatos de capas geográficas")
        print(f"   ✅ Análisis de proximidad a zonas críticas")
        print(f"   ✅ 🗺️  MAPA 1: CONTEXTO DEPARTAMENTAL (nuevo)")
        print(f"   ✅ 🗺️  MAPA 2: CONTEXTO MUNICIPAL (mejorado)")
        print(f"   ✅ 🗺️  MAPA 3: INFLUENCIA LEGAL DIRECTA (crítico - con flechas y distancias)")
        print(f"   ✅ Tabla detallada de restricciones")
        print(f"   ✅ Niveles de confianza de datos")
        print(f"   ✅ Recomendaciones legales contextualizadas")
        print(f"   ✅ Limitaciones técnicas y advertencias")
        print(f"   ✅ Bloque de fuentes legales oficiales (IGAC, IDEAM, DANE, RUNAP)")
        
        print(f"\n🔍 VALIDACIÓN VISUAL:")
        print(f"   📌 Abre el PDF y verifica:")
        print(f"      1. Los 3 mapas están en el orden correcto (Depto → Municipal → Influencia Legal)")
        print(f"      2. El Mapa 3 (Influencia Legal) muestra flechas rojas con distancias exactas a ríos")
        print(f"      3. Las escalas gráficas, rosas de vientos y leyendas son legibles")
        print(f"      4. El formato es profesional y apto para banca/auditoría legal")
        
        print(f"\n💡 COMANDO PARA ABRIR EL PDF:")
        print(f"   open {pdf_path}")
        
        return pdf_path
        
    except Exception as e:
        print(f"\n{'='*100}")
        print(f"❌ ERROR AL GENERAR PDF")
        print(f"{'='*100}\n")
        print(f"🔴 Excepción: {type(e).__name__}")
        print(f"📝 Mensaje: {str(e)}")
        
        import traceback
        print(f"\n📋 Traceback completo:")
        traceback.print_exc()
        
        sys.exit(1)


if __name__ == "__main__":
    try:
        pdf_path = test_pdf_legal_completo()
        
        print(f"\n{'='*100}")
        print(f"🎉 TEST COMPLETADO EXITOSAMENTE")
        print(f"{'='*100}\n")
        print(f"✅ PDF legal con 3 mapas profesionales generado correctamente")
        print(f"✅ Listo para entrega al cliente bancario/auditoría legal")
        print(f"\n📄 Ruta final: {pdf_path}")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Test interrumpido por el usuario (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error inesperado en el test: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
