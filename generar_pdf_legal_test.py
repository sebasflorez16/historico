#!/usr/bin/env python
"""
Script para generar PDF Legal con parcela de la base de datos
Usa el nuevo sistema actualizado con los 3 mapas profesionales
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from generador_pdf_legal import GeneradorPDFLegal
from verificador_legal import VerificadorRestriccionesLegales

def main():
    print("\n" + "="*80)
    print("🏛️  GENERADOR DE INFORME LEGAL - SISTEMA ACTUALIZADO")
    print("="*80 + "\n")
    
    # Buscar parcelas disponibles
    parcelas = Parcela.objects.all()[:10]
    
    if not parcelas:
        print("❌ No hay parcelas en la base de datos")
        return
    
    print("📊 Parcelas disponibles:\n")
    for i, p in enumerate(parcelas, 1):
        cultivo = p.tipo_cultivo or "N/A"
        print(f"{i}. ID: {p.id:3d} | {p.nombre:30s} | {p.area_hectareas:8.2f} ha | {cultivo:15s}")
    
    print(f"\nTotal: {Parcela.objects.count()} parcelas")
    
    # Seleccionar primera parcela o la que tenga geometría
    parcela = None
    for p in parcelas:
        if p.geometria:
            parcela = p
            break
    
    if not parcela:
        parcela = parcelas[0]
    
    print(f"\n✅ Parcela seleccionada: {parcela.nombre} (ID: {parcela.id})")
    print(f"   Área: {parcela.area_hectareas:.2f} ha")
    print(f"   Cultivo: {parcela.tipo_cultivo or 'N/A'}")
    
    if not parcela.geometria:
        print("\n⚠️  ADVERTENCIA: Esta parcela no tiene geometría definida")
        print("   El informe se generará sin mapas georreferenciados")
    
    # Generar PDF
    print("\n" + "-"*80)
    print("🚀 Generando informe legal...")
    print("-"*80 + "\n")
    
    try:
        # Configurar verificador legal
        print("1️⃣  Configurando verificador legal...")
        departamento = "Casanare"  # Por defecto Casanare
        verificador = VerificadorRestriccionesLegales()
        
        # Cargar capas geográficas
        print("   • Cargando red hídrica...")
        verificador.cargar_red_hidrica()
        print("   • Cargando áreas protegidas...")
        verificador.cargar_areas_protegidas()
        print("   • Cargando resguardos indígenas...")
        verificador.cargar_resguardos_indigenas()
        print("   • Cargando páramos...")
        verificador.cargar_paramos()
        
        # Ejecutar verificación
        print("\n2️⃣  Ejecutando verificación legal...")
        resultado = verificador.verificar_parcela(
            parcela_id=parcela.id,
            geometria_parcela=parcela.geometria,
            nombre_parcela=parcela.nombre
        )
        
        print(f"   ✅ Verificación completada")
        print(f"   • Restricciones encontradas: {len(resultado.restricciones_encontradas)}")
        print(f"   • Área cultivable: {resultado.area_cultivable_ha.get('valor_ha', 0):.2f} ha")
        print(f"   • Cumple normativa: {'Sí' if resultado.cumple_normativa else 'No'}")
        
        # Generar PDF
        print("\n3️⃣  Generando PDF con 3 mapas profesionales...")
        output_dir = os.path.join(
            os.path.dirname(__file__),
            'media',
            'verificacion_legal'
        )
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(
            output_dir,
            f'informe_legal_{parcela.nombre.replace(" ", "_")}_{timestamp}.pdf'
        )
        
        generador = GeneradorPDFLegal()
        pdf_path = generador.generar_pdf(
            parcela=parcela,
            resultado=resultado,
            verificador=verificador,
            output_path=output_path,
            departamento=departamento
        )
        
        print(f"\n{'='*80}")
        print(f"✅ PDF GENERADO EXITOSAMENTE")
        print(f"{'='*80}")
        print(f"\n📄 Archivo: {pdf_path}")
        print(f"📏 Parcela: {parcela.nombre} ({parcela.area_hectareas:.2f} ha)")
        print(f"🗓️  Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"\n💡 El PDF incluye:")
        print(f"   • Mapa 1: Ubicación departamental")
        print(f"   • Mapa 2: Mapa municipal profesional V3")
        print(f"   • Mapa 3: Mapa de influencia legal directa")
        print(f"   • Análisis completo de restricciones legales")
        print(f"   • Recomendaciones y advertencias claras")
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR al generar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
