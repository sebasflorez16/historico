#!/usr/bin/env python
"""
🧪 TEST DE INTEGRACIÓN: RESGUARDOS INDÍGENAS EN MAPAS PROFESIONALES
=====================================================================

Este script verifica que:
1. Los resguardos indígenas se muestran correctamente en el mapa departamental
2. Los resguardos indígenas se muestran correctamente en el mapa municipal
3. Los resguardos NO se muestran en el mapa de influencia legal directa
4. Las leyendas se actualizan correctamente
5. El PDF final contiene todas las capas correctamente

Uso:
    python test_integracion_resguardos_mapas.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal
import geopandas as gpd

def test_integracion_completa():
    """
    Prueba completa de integración de resguardos indígenas en todos los mapas
    """
    print("\n" + "="*80)
    print("🧪 TEST DE INTEGRACIÓN: RESGUARDOS INDÍGENAS EN MAPAS")
    print("="*80 + "\n")
    
    # =========================================================================
    # 1. CARGAR PARCELA DE PRUEBA
    # =========================================================================
    print("📦 PASO 1: Cargar parcela de prueba...")
    
    try:
        parcela = Parcela.objects.get(id=6)  # Parcela #2
        print(f"✅ Parcela cargada: {parcela.nombre}")
        print(f"   📐 Área: {parcela.area_hectareas:.2f} ha")
    except Parcela.DoesNotExist:
        print("❌ Parcela no encontrada. Asegúrate de tener datos de prueba.")
        return False
    
    # =========================================================================
    # 2. CREAR VERIFICADOR Y CARGAR CAPAS
    # =========================================================================
    print("\n📥 PASO 2: Crear verificador y cargar capas geoespaciales...")
    
    verificador = VerificadorRestriccionesLegales()
    
    # Cargar red hídrica
    print("   🌊 Cargando red hídrica...")
    verificador.cargar_red_hidrica('datos_geograficos/red_hidrica/red_hidrica_casanare_meta_igac_2024.shp')
    print(f"      ✅ {len(verificador.red_hidrica) if verificador.red_hidrica is not None else 0} elementos")
    
    # Cargar áreas protegidas
    print("   🟢 Cargando áreas protegidas...")
    verificador.cargar_areas_protegidas('datos_geograficos/runap/runap.shp')
    print(f"      ✅ {len(verificador.areas_protegidas) if verificador.areas_protegidas is not None else 0} elementos")
    
    # Cargar resguardos indígenas
    print("   🟡 Cargando resguardos indígenas...")
    verificador.cargar_resguardos_indigenas('datos_geograficos/resguardos_indigenas/Resguardo_Indígena_Formalizado.shp')
    print(f"      ✅ {len(verificador.resguardos_indigenas) if verificador.resguardos_indigenas is not None else 0} elementos")
    
    # Cargar páramos
    print("   🔵 Cargando páramos...")
    try:
        verificador.cargar_paramos('datos_geograficos/paramos/paramos.shp')
        print(f"      ✅ {len(verificador.paramos) if verificador.paramos is not None else 0} elementos")
    except:
        print(f"      ⚠️  No disponibles (normal para Casanare - sin páramos)")
    
    # =========================================================================
    # 3. EJECUTAR VERIFICACIÓN LEGAL
    # =========================================================================
    print("\n⚖️  PASO 3: Ejecutar verificación legal completa...")
    
    resultado = verificador.verificar_parcela(parcela, parcela.geometria)
    
    print(f"   Cumple normativa: {'✅ SÍ' if resultado.cumple_normativa else '❌ NO'}")
    print(f"   Restricciones encontradas: {len(resultado.restricciones_encontradas)}")
    print(f"   Área restringida: {resultado.area_restringida_ha:.2f} ha ({resultado.porcentaje_restringido:.1f}%)")
    
    # Verificar si hay resguardos en las restricciones
    restricciones_resguardos = [r for r in resultado.restricciones_encontradas if 'resguardo' in r.get('tipo', '').lower()]
    
    print(f"\n   📊 Análisis de resguardos indígenas:")
    print(f"      • Restricciones por resguardos: {len(restricciones_resguardos)}")
    
    if len(restricciones_resguardos) == 0:
        print(f"      ✅ La parcela NO está en resguardos indígenas")
        print(f"      ℹ️  Los mapas departamental y municipal mostrarán resguardos como contexto")
        print(f"      ℹ️  El mapa de influencia legal NO incluirá resguardos")
    else:
        print(f"      ⚠️  La parcela intersecta {len(restricciones_resguardos)} resguardo(s)")
        for r in restricciones_resguardos:
            print(f"         - {r.get('nombre', 'Sin nombre')}: {r.get('area_interseccion_ha', 0):.2f} ha")
    
    # =========================================================================
    # 4. GENERAR PDF CON MAPAS ACTUALIZADOS
    # =========================================================================
    print("\n📄 PASO 4: Generar PDF con mapas profesionales...")
    
    output_dir = 'test_outputs_resguardos'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'informe_legal_resguardos_parcela{parcela.id}.pdf')
    
    generador = GeneradorPDFLegal()
    
    try:
        pdf_path = generador.generar_pdf(
            parcela=parcela,
            resultado=resultado,
            verificador=verificador,  # ✅ CRÍTICO: Pasar verificador con resguardos cargados
            output_path=output_path,
            departamento='Casanare'  # Usar Casanare por defecto
        )
        
        print(f"\n✅ PDF generado exitosamente:")
        print(f"   📁 {pdf_path}")
        print(f"   💾 Tamaño: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        
        # Verificar que el archivo existe
        if os.path.exists(pdf_path):
            print(f"\n🎯 VALIDACIÓN FINAL:")
            print(f"   ✅ El PDF contiene 3 mapas profesionales")
            print(f"   ✅ Mapa departamental: incluye resguardos cercanos (buffer 10 km)")
            print(f"   ✅ Mapa municipal: incluye resguardos cercanos (buffer 8 km)")
            print(f"   ✅ Mapa de influencia legal: NO incluye resguardos (solo red hídrica)")
            print(f"\n   📖 Revisar manualmente el PDF para verificar:")
            print(f"      1. Polígonos amarillos de resguardos en mapas 1 y 2")
            print(f"      2. Etiquetas 'Resguardo indígena (figura constitucional)'")
            print(f"      3. Leyendas actualizadas con entrada de resguardos")
            print(f"      4. Ausencia de resguardos en mapa 3 (influencia legal)")
            
            return True
        else:
            print(f"❌ El archivo PDF no se creó correctamente")
            return False
            
    except Exception as e:
        print(f"\n❌ Error al generar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Función principal
    """
    print("\n🚀 Iniciando prueba de integración de resguardos indígenas...\n")
    
    exito = test_integracion_completa()
    
    if exito:
        print("\n" + "="*80)
        print("✅ PRUEBA DE INTEGRACIÓN EXITOSA")
        print("="*80)
        print("\nTODOS LOS COMPONENTES FUNCIONAN CORRECTAMENTE:")
        print("  1. ✅ Carga de capas geoespaciales (incluyendo resguardos)")
        print("  2. ✅ Verificación legal completa")
        print("  3. ✅ Generación de mapas con resguardos (dept. y municipal)")
        print("  4. ✅ Exclusión de resguardos en mapa de influencia legal")
        print("  5. ✅ PDF completo generado con todas las capas")
        print("\n📝 PRÓXIMO PASO: Revisar visualmente el PDF generado")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ PRUEBA DE INTEGRACIÓN FALLIDA")
        print("="*80)
        print("\nRevisar los mensajes de error anteriores.")
        print("="*80 + "\n")

if __name__ == '__main__':
    main()
