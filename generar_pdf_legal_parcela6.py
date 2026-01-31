#!/usr/bin/env python
"""
Script para generar PDF de verificación legal de la Parcela #2 (id:6) en Casanare
Usa los datos nacionales completos y actualizados.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from datetime import datetime
import json

# Importar el verificador legal que está en la raíz del proyecto
from verificador_legal import VerificadorRestriccionesLegales

def main():
    """Generar PDF de verificación legal para parcela #6"""
    
    print("\n" + "="*80)
    print("🏛️  GENERACIÓN DE PDF DE VERIFICACIÓN LEGAL - PARCELA CASANARE")
    print("="*80)
    
    # 1. Obtener la parcela
    try:
        parcela = Parcela.objects.get(id=6)
        print(f"\n✅ Parcela encontrada:")
        print(f"   ID: {parcela.id}")
        print(f"   Nombre: {parcela.nombre}")
        print(f"   Propietario: {parcela.propietario}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        
        if parcela.geometria:
            centroide = parcela.geometria.centroid
            print(f"   Centroide: {centroide.y:.6f}, {centroide.x:.6f}")
            print(f"   Geometría: {parcela.geometria.geom_type}")
        else:
            print(f"   ❌ ERROR: La parcela no tiene geometría definida")
            return
            
    except Parcela.DoesNotExist:
        print(f"\n❌ ERROR: No se encontró la parcela con id=6")
        return
    
    # 2. Instanciar el verificador legal
    print(f"\n🔍 Iniciando verificación legal...")
    verificador = VerificadorRestriccionesLegales()
    
    # 2.1 Cargar todas las capas geográficas
    print(f"\n📥 Cargando capas geográficas...")
    verificador.cargar_red_hidrica()
    verificador.cargar_areas_protegidas()
    verificador.cargar_resguardos_indigenas()
    verificador.cargar_paramos()
    
    # 3. Ejecutar verificación completa
    print(f"\n📊 Ejecutando verificación de restricciones legales...")
    resultado = verificador.verificar_parcela(
        parcela_id=parcela.id,
        geometria_parcela=parcela.geometria,
        nombre_parcela=parcela.nombre
    )
    
    # 4. Mostrar resumen de resultados
    print(f"\n" + "-"*80)
    print(f"RESUMEN DE VERIFICACIÓN LEGAL")
    print(f"-"*80)
    
    # Convertir a diccionario para facilitar el acceso
    resultado_dict = resultado.to_dict()
    
    print(f"\n📊 INFORMACIÓN GENERAL:")
    print(f"   Área total: {resultado.area_total_ha:.2f} ha")
    print(f"   Área restringida: {resultado.area_restringida_ha:.2f} ha ({resultado.porcentaje_restringido:.1f}%)")
    print(f"   Cumple normativa: {'SÍ ✅' if resultado.cumple_normativa else 'NO ❌'}")
    
    print(f"\n🔍 RESTRICCIONES ENCONTRADAS:")
    if resultado.restricciones_encontradas:
        print(f"   Total: {len(resultado.restricciones_encontradas)}")
        for idx, restriccion in enumerate(resultado.restricciones_encontradas, 1):
            print(f"\n   {idx}. {restriccion.get('tipo', 'N/A')}:")
            print(f"      Nombre: {restriccion.get('nombre', 'N/A')}")
            print(f"      Área afectada: {restriccion.get('area_interseccion_ha', 0):.2f} ha")
            print(f"      Porcentaje: {restriccion.get('porcentaje_area_parcela', 0):.1f}%")
            if 'descripcion' in restriccion:
                print(f"      Descripción: {restriccion['descripcion']}")
    else:
        print(f"   ✅ No se encontraron restricciones legales")
    
    print(f"\n⚠️  ADVERTENCIAS:")
    if resultado.advertencias:
        for adv in resultado.advertencias:
            print(f"   - {adv}")
    else:
        print(f"   ✅ Sin advertencias")
    
    print(f"\n📈 NIVELES DE CONFIANZA:")
    for capa, info in resultado.niveles_confianza.items():
        emoji = "✅" if info['confianza'] == 'Alta' else "⚠️" if info['confianza'] == 'Media' else "❌"
        print(f"   {emoji} {capa}: {info['confianza']}")
        if 'fuente' in info:
            print(f"      Fuente: {info['fuente']}")
        if 'razon' in info:
            print(f"      Razón: {info['razon']}")
    
    print(f"\n� ÁREA CULTIVABLE:")
    if resultado.area_cultivable_ha['determinable']:
        print(f"   ✅ Determinable: {resultado.area_cultivable_ha['valor_ha']:.2f} ha")
    else:
        print(f"   ⚠️  No determinable")
    print(f"   Nota: {resultado.area_cultivable_ha['nota']}")
    
    # 5. Generar reporte en consola
    print(f"\n" + "-"*80)
    print(f"📄 REPORTE COMPLETO:")
    print(f"-"*80)
    print(verificador.generar_reporte_consola(resultado))
    
    # 6. Guardar resultado en JSON
    output_dir = os.path.join(
        os.path.dirname(__file__),
        'media',
        'verificacion_legal'
    )
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = os.path.join(
        output_dir,
        f'verificacion_legal_parcela_{parcela.id}_{timestamp}.json'
    )
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(resultado.to_json())
        
        print(f"\n✅ RESULTADO GUARDADO EXITOSAMENTE")
        print(f"   Ruta JSON: {json_path}")
        
        # Verificar tamaño del archivo
        if os.path.exists(json_path):
            tamaño_kb = os.path.getsize(json_path) / 1024
            print(f"   Tamaño: {tamaño_kb:.2f} KB")
        
        print(f"\n🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print(f"\n💡 El resultado incluye:")
        print(f"   - Verificación de {len(resultado.restricciones_encontradas)} restricciones")
        print(f"   - Área cultivable: {resultado.area_cultivable_ha['determinable'] and 'determinable' or 'no determinable'}")
        print(f"   - Niveles de confianza de {len(resultado.niveles_confianza)} capas geográficas")
        
    except Exception as e:
        print(f"\n❌ ERROR al guardar JSON: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n" + "="*80)


if __name__ == "__main__":
    main()
