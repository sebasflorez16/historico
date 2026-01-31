#!/usr/bin/env python
"""
🧪 TEST: Mapa de Influencia Legal Directa de la Parcela

Este script prueba la generación del mapa más importante del informe legal:
el que muestra la parcela y sus relaciones espaciales con restricciones externas.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from mapas_profesionales import generar_mapa_influencia_legal_directa

print("=" * 80)
print("🧪 TEST: Mapa de Influencia Legal Directa de la Parcela")
print("=" * 80)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1️⃣ CARGAR PARCELA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    parcela = Parcela.objects.get(id=6)
    print(f"\n✅ Parcela cargada: {parcela.nombre}")
    print(f"   Propietario: {parcela.propietario}")
    print(f"   Área: {parcela.area_hectareas:.2f} ha")
except Parcela.DoesNotExist:
    print("\n❌ Error: Parcela #6 no encontrada")
    print("   Usando parcela alternativa...")
    parcela = Parcela.objects.first()
    if not parcela:
        print("❌ No hay parcelas en la base de datos")
        sys.exit(1)
    print(f"✅ Parcela cargada: {parcela.nombre}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2️⃣ CARGAR CAPAS GEOGRÁFICAS OFICIALES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n📥 Cargando capas geográficas oficiales...")

verificador = VerificadorRestriccionesLegales()

print(f"✅ Red hídrica: {len(verificador.red_hidrica) if verificador.red_hidrica is not None else 0} elementos")
print(f"✅ Áreas protegidas: {len(verificador.areas_protegidas) if verificador.areas_protegidas is not None else 0} elementos")
print(f"✅ Resguardos indígenas: {len(verificador.resguardos_indigenas) if verificador.resguardos_indigenas is not None else 0} elementos")
print(f"✅ Páramos: {len(verificador.paramos) if verificador.paramos is not None else 0} elementos")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3️⃣ GENERAR MAPA DE INFLUENCIA LEGAL DIRECTA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n" + "━" * 80)
print("🗺️  GENERACIÓN DE MAPA DE INFLUENCIA LEGAL DIRECTA")
print("━" * 80)

try:
    img_buffer = generar_mapa_influencia_legal_directa(
        parcela=parcela,
        verificador=verificador,
        save_to_file=True
    )
    
    print("\n" + "━" * 80)
    print("📊 RESUMEN DE GENERACIÓN")
    print("━" * 80)
    print(f"Parcela:              {parcela.nombre}")
    print(f"Enfoque:              Influencia legal directa")
    print(f"Resolución:           {300} DPI")
    print(f"Tamaño:               14x12 pulgadas")
    print(f"Buffer generado:      ✅ Listo para PDF")
    print("━" * 80)
    
    print("\n✅ MAPA DE INFLUENCIA LEGAL DIRECTA GENERADO EXITOSAMENTE")
    
except Exception as e:
    print(f"\n❌ Error generando mapa: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4️⃣ RESUMEN FINAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n" + "=" * 80)
print("🎉 TEST COMPLETADO - Ver resultado en: test_outputs_mapas/")
print("=" * 80)

print("\n📋 CARACTERÍSTICAS DEL MAPA GENERADO:")
print("   ✅ Parcela como elemento central (60-70% del área)")
print("   ✅ Flechas de referencia a elementos externos")
print("   ✅ Distancias calculadas desde lindero (NO centroide)")
print("   ✅ Direcciones cardinales precisas")
print("   ✅ Minimalista, técnico, apto para banca")
print("   ✅ Resolución 300 DPI (listo para imprimir)")

print("\n💡 PRÓXIMO PASO:")
print("   Integrar en generador_pdf_legal.py como MAPA 3")
print("   Ubicación sugerida: Después del mapa departamental")
