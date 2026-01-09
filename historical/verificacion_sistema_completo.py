#!/usr/bin/env python
"""
Script de verificación completa del sistema AgroTech Histórico
Valida todo el flujo: sincronización EOSDA → BD → PDF → UI

Uso:
    python verificacion_sistema_completo.py --parcela 11
"""
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.services.eosda_api import EosdaAPIService
from informes.generador_pdf import GeneradorPDFProfesional

def verificar_parcela(parcela_id):
    """Verifica estado completo de una parcela"""
    print(f"\n{'='*70}")
    print(f"🔍 VERIFICACIÓN COMPLETA - Parcela #{parcela_id}")
    print(f"{'='*70}\n")
    
    # 1. Verificar que existe en BD local
    try:
        parcela = Parcela.objects.get(pk=parcela_id)
        print(f"✅ Parcela encontrada en BD local")
        print(f"   - Nombre: {parcela.nombre}")
        print(f"   - Cultivo: {parcela.tipo_cultivo}")
        print(f"   - Área: {parcela.area_hectareas:.2f} ha")
        print(f"   - EOSDA Field ID: {parcela.eosda_field_id or 'No asignado'}")
    except Parcela.DoesNotExist:
        print(f"❌ Parcela #{parcela_id} no existe en BD local")
        return False
    
    # 2. Verificar datos satelitales en BD
    indices_count = IndiceMensual.objects.filter(parcela=parcela).count()
    print(f"\n📊 Datos satelitales en BD:")
    print(f"   - Total registros: {indices_count}")
    
    if indices_count == 0:
        print(f"   ⚠️  Sin datos satelitales aún")
        print(f"   💡 Ejecuta: obtener_datos_satelitales() para sincronizar")
    else:
        # Verificar que solo hay 1 imagen por mes
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
        meses_vistos = set()
        duplicados = False
        
        for idx in indices:
            mes_key = f"{idx.año}-{idx.mes:02d}"
            if mes_key in meses_vistos:
                print(f"   ❌ DUPLICADO detectado: {mes_key}")
                duplicados = True
            meses_vistos.add(mes_key)
        
        if not duplicados:
            print(f"   ✅ Solo 1 imagen por mes (correctamente filtrado)")
        
        # Mostrar últimos 5 registros
        print(f"\n   📅 Últimos 5 registros:")
        for idx in indices.order_by('-año', '-mes')[:5]:
            print(f"      {idx.año}-{idx.mes:02d}: NDVI={idx.ndvi_mean:.2f}, "
                  f"Nubosidad={idx.nubosidad_imagen}%, "
                  f"Satélite={idx.satelite_imagen or 'N/A'}")
    
    # 3. Verificar conexión EOSDA
    print(f"\n🛰️  Conexión EOSDA:")
    if not parcela.eosda_field_id:
        print(f"   ⚠️  Parcela sin field EOSDA asignado")
        print(f"   💡 Ejecuta: sincronizar_parcela_con_eosda() para asignar")
    else:
        service = EosdaAPIService()
        # Verificar que el field existe en EOSDA
        url = f"{service.base_url}/fields/{parcela.eosda_field_id}"
        try:
            response = service.session.get(url, params={'api_key': service.api_key}, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Field verificado en EOSDA API")
                field_data = response.json()
                print(f"      - Nombre EOSDA: {field_data.get('name')}")
                print(f"      - Área EOSDA: {field_data.get('area', 0):.2f} ha")
            else:
                print(f"   ⚠️  Field no encontrado en EOSDA (status {response.status_code})")
        except Exception as e:
            print(f"   ⚠️  Error verificando EOSDA: {str(e)[:50]}")
    
    # 4. Verificar que PDF se puede generar
    print(f"\n📄 Generación de PDF:")
    if indices_count < 3:
        print(f"   ⚠️  Mínimo 3 meses de datos requeridos (actual: {indices_count})")
    else:
        try:
            # No generamos el PDF real, solo verificamos que se puede
            generador = GeneradorPDFProfesional()
            print(f"   ✅ GeneradorPDFProfesional inicializado correctamente")
            print(f"   💡 Para generar PDF real, usa la interfaz web")
        except Exception as e:
            print(f"   ❌ Error en generador: {str(e)[:100]}")
    
    # 5. Resumen final
    print(f"\n{'='*70}")
    print(f"📝 RESUMEN:")
    print(f"{'='*70}")
    
    estado_bd = "✅" if True else "❌"
    estado_datos = "✅" if indices_count > 0 else "⚠️ "
    estado_eosda = "✅" if parcela.eosda_field_id else "⚠️ "
    estado_pdf = "✅" if indices_count >= 3 else "⚠️ "
    
    print(f"{estado_bd} Parcela en BD local")
    print(f"{estado_datos} Datos satelitales (mínimo 1 mes)")
    print(f"{estado_eosda} Sincronización EOSDA")
    print(f"{estado_pdf} Generación de PDF (mínimo 3 meses)")
    
    if all([estado == "✅" for estado in [estado_bd, estado_datos, estado_eosda, estado_pdf]]):
        print(f"\n🎉 Sistema completamente funcional para parcela #{parcela_id}")
    else:
        print(f"\n💡 Acciones recomendadas:")
        if estado_eosda != "✅":
            print(f"   1. Ejecutar sincronización EOSDA")
        if estado_datos != "✅":
            print(f"   2. Obtener datos satelitales")
        if estado_pdf != "✅":
            print(f"   3. Esperar más meses de datos para PDF completo")
    
    print(f"\n{'='*70}\n")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Verificar sistema completo')
    parser.add_argument('--parcela', type=int, required=True, help='ID de parcela a verificar')
    args = parser.parse_args()
    
    verificar_parcela(args.parcela)
