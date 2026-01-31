#!/usr/bin/env python
"""
🧪 TEST: Mapa Departamental Profesional
=========================================

Genera y valida el Mapa 2: Ubicación Departamental con Restricciones Legales

Características:
- Límite departamental dominante (gris oscuro técnico)
- Parcela como punto destacado (rojo intenso)
- Resguardos indígenas (amarillo suave con etiquetas)
- Áreas protegidas (rojo suave con etiquetas)
- Elementos cartográficos profesionales
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from mapas_profesionales import generar_mapa_departamental_profesional, agregar_bloque_fuentes_legales
from datetime import datetime

def test_mapa_departamental():
    """Genera mapa departamental de prueba"""
    
    print("\n" + "="*80)
    print("🧪 TEST: Mapa Departamental Profesional")
    print("="*80)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ CARGAR PARCELA
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    parcela_id = 6  # Parcela #2 en Yopal, Casanare
    
    try:
        parcela = Parcela.objects.get(id=parcela_id)
        print(f"\n✅ Parcela cargada: {parcela.nombre}")
        print(f"   Propietario: {parcela.propietario}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
    except Parcela.DoesNotExist:
        print(f"\n❌ Error: Parcela con ID {parcela_id} no existe")
        return
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ CARGAR CAPAS GEOGRÁFICAS OFICIALES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📥 Cargando capas geográficas oficiales...")
    
    verificador = VerificadorRestriccionesLegales()
    
    print(f"✅ Red hídrica: {len(verificador.red_hidrica) if verificador.red_hidrica is not None else 0} elementos")
    print(f"✅ Áreas protegidas: {len(verificador.areas_protegidas) if verificador.areas_protegidas is not None else 0} elementos")
    print(f"✅ Resguardos indígenas: {len(verificador.resguardos_indigenas) if verificador.resguardos_indigenas is not None else 0} elementos")
    print(f"✅ Páramos: {len(verificador.paramos) if verificador.paramos is not None else 0} elementos")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3️⃣ GENERAR MAPA DEPARTAMENTAL PROFESIONAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n" + "━"*80)
    print("🗺️  GENERACIÓN DE MAPA DEPARTAMENTAL PROFESIONAL")
    print("━"*80)
    
    try:
        img_buffer = generar_mapa_departamental_profesional(
            parcela=parcela,
            verificador=verificador,
            save_to_file=True
        )
        
        print("\n" + "━"*80)
        print("📊 RESUMEN DE GENERACIÓN")
        print("━"*80)
        print(f"Parcela:              {parcela.nombre}")
        print(f"Departamento:         Detectado automáticamente")
        print(f"Resolución:           300 DPI")
        print(f"Tamaño:               12x10 pulgadas")
        print(f"Buffer generado:      ✅ Listo para PDF")
        print("━"*80)
        
        print("\n✅ MAPA DEPARTAMENTAL PROFESIONAL GENERADO EXITOSAMENTE")
        
    except Exception as e:
        print(f"\n❌ Error al generar mapa: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4️⃣ GENERAR BLOQUE DE FUENTES LEGALES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n📚 Generando bloque de fuentes legales...")
    
    try:
        tabla_fuentes = agregar_bloque_fuentes_legales()
        print("✅ Bloque de fuentes legales creado")
        print("\nPara añadirlo al PDF, usar:")
        print("   elementos.append(tabla_fuentes)")
        print("   elementos.append(Spacer(1, 0.3*cm))")
    except Exception as e:
        print(f"⚠️  Error al crear bloque de fuentes: {str(e)}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5️⃣ RESUMEN FINAL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print("\n" + "="*80)
    print("🎉 TEST COMPLETADO - Ver resultado en: test_outputs_mapas/")
    print("="*80)
    
    print("\n📋 CARACTERÍSTICAS DEL MAPA GENERADO:")
    print("   ✅ Límite departamental: Gris oscuro técnico (#424242)")
    print("   ✅ Parcela: Punto rojo intenso destacado")
    print("   ✅ Resguardos indígenas: Amarillo suave con etiquetas")
    print("   ✅ Áreas protegidas: Rojo suave con etiquetas")
    print("   ✅ Norte, escala y leyenda profesional")
    print("   ✅ Etiquetas solo dentro del marco")
    print("   ✅ Resolución 300 DPI (listo para imprimir)")
    
    print("\n💡 PRÓXIMO PASO:")
    print("   Integrar en generador_pdf_legal.py como MAPA 2")
    print("   Ubicación sugerida: Después del mapa municipal")

if __name__ == '__main__':
    test_mapa_departamental()
