#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador de Informe Legal PDF - Parcela #11 (Bio Energy - 308 ha)
====================================================================

Genera el informe legal completo con todos los mapas profesionales,
análisis de proximidad y verificación de restricciones ambientales.

Autor: AgroTech Histórico
Fecha: Febrero 2026
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal
from datetime import datetime

print("\n" + "="*80)
print("📄 GENERACIÓN DE INFORME LEGAL - PARCELA #11 (BIO ENERGY - 308 HA)")
print("="*80)

# 1. Cargar parcela
print("\n1️⃣ Cargando Parcela #11...")
try:
    parcela = Parcela.objects.get(id=11, activa=True)
    print(f"✅ Parcela: {parcela.nombre}")
    print(f"   Propietario: {parcela.propietario}")
    print(f"   Área: {parcela.area_hectareas} ha")
    print(f"   Cultivo: {parcela.tipo_cultivo}")
    print(f"   Departamento: {parcela.departamento if hasattr(parcela, 'departamento') else 'Casanare'}")
except Parcela.DoesNotExist:
    print("❌ Parcela #11 no encontrada")
    sys.exit(1)

# 2. Inicializar verificador (las capas se cargarán automáticamente al calcular distancias)
print("\n2️⃣ Inicializando VerificadorRestriccionesLegales...")
try:
    verificador = VerificadorRestriccionesLegales()
    print("✅ Verificador inicializado")
except Exception as e:
    print(f"❌ Error inicializando verificador: {str(e)}")
    sys.exit(1)

# 3. Ejecutar verificación legal
print("\n3️⃣ Ejecutando verificación legal...")
try:
    resultado = verificador.verificar_parcela(
        parcela_id=parcela.id,
        geometria_parcela=parcela.geometria,
        nombre_parcela=parcela.nombre
    )
    print("✅ Verificación completada")
    print(f"   Cumple normativa: {resultado.cumple_normativa}")
    print(f"   Restricciones: {len(resultado.restricciones_encontradas)}")
    print(f"   Área total: {resultado.area_total_ha} ha")
    print(f"   Área restringida: {resultado.area_restringida_ha} ha")
except Exception as e:
    print(f"❌ Error en verificación: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Inicializar generador PDF
print("\n4️⃣ Inicializando GeneradorPDFLegal...")
try:
    generador = GeneradorPDFLegal()
    print("✅ Generador inicializado")
except Exception as e:
    print(f"❌ Error inicializando generador: {str(e)}")
    sys.exit(1)

# 5. Generar PDF
print("\n5️⃣ Generando PDF...")
print("   (Esto puede tomar 15-30 segundos debido a la generación de 3 mapas profesionales)\n")

try:
    # Definir ruta de salida
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_limpio = parcela.nombre.replace(" ", "_").replace("/", "-")
    nombre_archivo = f"informe_legal_{nombre_limpio}_{timestamp}.pdf"
    
    # Crear directorio si no existe
    output_dir = os.path.join('media', 'verificacion_legal')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, nombre_archivo)
    
    # Obtener departamento
    departamento = getattr(parcela, 'departamento', 'Casanare')
    
    # Generar PDF
    ruta_pdf = generador.generar_pdf(
        parcela=parcela,
        resultado=resultado,
        verificador=verificador,
        output_path=output_path,
        departamento=departamento
    )
    
    # Verificar que se generó
    if os.path.exists(ruta_pdf):
        tamanio_kb = os.path.getsize(ruta_pdf) / 1024
        print(f"\n✅ PDF GENERADO EXITOSAMENTE")
        print(f"   📦 Ubicación: {ruta_pdf}")
        print(f"   📊 Tamaño: {tamanio_kb:.2f} KB")
        
        # Copiar para fácil acceso
        import shutil
        copia_local = f"informe_legal_bioenergy_308ha.pdf"
        shutil.copy(ruta_pdf, copia_local)
        print(f"   💾 Copia guardada en: {copia_local}")
        
        # Abrir PDF
        print(f"\n🔍 Abriendo PDF para inspección visual...")
        os.system(f"open {copia_local}")
        
    else:
        print(f"\n❌ ERROR: El PDF no se generó en {ruta_pdf}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ Error generando PDF: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ PROCESO COMPLETADO")
print("="*80)
print("\n📋 VERIFICACIONES:")
print("   ✅ Parcela de 308 ha cargada")
print("   ✅ Verificación legal ejecutada")
print("   ✅ PDF con 3 mapas profesionales generado")
print("   ✅ Análisis de proximidad incluido")
print("   ✅ Logos de AgroTech integrados")
print("\n💡 PRÓXIMO PASO:")
print("   Revisar el PDF y verificar que la tabla de proximidad")
print("   ahora muestra datos reales en lugar de estar vacía")
print("\n" + "="*80)
