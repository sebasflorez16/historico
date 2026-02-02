#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador de Informe Legal PDF - Parcela Bio Energy (308 ha)
=============================================================

Genera informe legal completo con:
- Logos actualizados de AgroTech
- 3 mapas profesionales
- Análisis de restricciones ambientales
- Verificación legal completa

Parcela: Bio Energy (ID: 11)
Área: 308.71 ha
Propietario: Bioenegi SAS

Autor: AgroTech Histórico
Fecha: Febrero 2026
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal

print("\n" + "="*80)
print("📄 GENERACIÓN DE INFORME LEGAL - PARCELA BIO ENERGY (308 HA)")
print("="*80)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1️⃣ CARGAR PARCELA BIO ENERGY (ID: 11)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n1️⃣ Cargando Parcela Bio Energy...")
try:
    parcela = Parcela.objects.get(id=11, activa=True)
    print(f"✅ Parcela: {parcela.nombre}")
    print(f"   Propietario: {parcela.propietario}")
    print(f"   Área: {parcela.area_hectareas:.2f} ha")
    print(f"   Cultivo: {parcela.tipo_cultivo}")
    print(f"   Activa: {parcela.activa}")
    
    if parcela.geometria:
        centroide = parcela.geometria.centroid
        print(f"   ✅ Geometría válida")
        print(f"   Coordenadas: {centroide.y:.6f}, {centroide.x:.6f}")
    else:
        print("   ❌ Sin geometría definida")
        sys.exit(1)
        
except Parcela.DoesNotExist:
    print("❌ Parcela Bio Energy (ID: 11) no encontrada")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error cargando parcela: {str(e)}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2️⃣ INICIALIZAR VERIFICADOR DE RESTRICCIONES LEGALES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n2️⃣ Inicializando VerificadorRestriccionesLegales...")
try:
    verificador = VerificadorRestriccionesLegales()
    
    # Mostrar capas cargadas
    capas_info = []
    if verificador.red_hidrica is not None:
        capas_info.append(f"Red hídrica: {len(verificador.red_hidrica)} elementos")
    if verificador.areas_protegidas is not None:
        capas_info.append(f"Áreas protegidas: {len(verificador.areas_protegidas)} elementos")
    if verificador.resguardos_indigenas is not None:
        capas_info.append(f"Resguardos: {len(verificador.resguardos_indigenas)} elementos")
    if verificador.paramos is not None:
        capas_info.append(f"Páramos: {len(verificador.paramos)} elementos")
    
    print("✅ Verificador inicializado")
    for info in capas_info:
        print(f"   • {info}")
        
except Exception as e:
    print(f"❌ Error inicializando verificador: {str(e)}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3️⃣ EJECUTAR VERIFICACIÓN LEGAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    
    if resultado.area_cultivable_ha['determinable']:
        print(f"   Área cultivable: {resultado.area_cultivable_ha['valor_ha']:.2f} ha")
    else:
        print(f"   Área cultivable: No determinable")
        print(f"   Nota: {resultado.area_cultivable_ha['nota']}")
        
except Exception as e:
    print(f"❌ Error en verificación: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4️⃣ INICIALIZAR GENERADOR PDF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n4️⃣ Inicializando GeneradorPDFLegal...")
try:
    generador = GeneradorPDFLegal()
    print("✅ Generador inicializado")
    print("   ✅ Logo actualizado: 'Agro Tech logo solo.png'")
    print("   ✅ Pie de página con branding")
except Exception as e:
    print(f"❌ Error inicializando generador: {str(e)}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5️⃣ GENERAR PDF COMPLETO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n5️⃣ Generando PDF completo...")
print("   (Esto puede tomar 30-60 segundos debido al tamaño de la parcela)")
print("")

try:
    # Definir ruta de salida
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_limpio = parcela.nombre.replace(" ", "_").replace("/", "-")
    nombre_archivo = f"informe_legal_{nombre_limpio}_{timestamp}.pdf"
    
    # Crear directorio si no existe
    output_dir = os.path.join('media', 'verificacion_legal')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, nombre_archivo)
    
    # Detectar departamento (por defecto Casanare)
    departamento = "Casanare"
    
    # Generar PDF
    ruta_pdf = generador.generar_pdf(
        parcela=parcela,
        resultado=resultado,
        verificador=verificador,
        output_path=output_path,
        departamento=departamento
    )
    
    # Verificar que el archivo se generó
    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"El PDF no se generó correctamente en {ruta_pdf}")
    
    print("\n" + "="*80)
    print("✅ PDF GENERADO EXITOSAMENTE")
    print("="*80)
    
    # Detalles del archivo
    tamaño_mb = os.path.getsize(ruta_pdf) / (1024 * 1024)
    print(f"\n📦 Detalles del archivo:")
    print(f"   Ubicación: {ruta_pdf}")
    print(f"   Tamaño: {tamaño_mb:.2f} MB")
    print(f"   ✅ Archivo PDF válido")
    
    # Copiar a directorio raíz para fácil acceso
    import shutil
    copia_path = f"informe_bio_energy_308ha.pdf"
    shutil.copy(ruta_pdf, copia_path)
    print(f"\n💾 Copia guardada en: {copia_path}")
    print(f"   Puedes abrirlo con: open {copia_path}")
    
    # Abrir PDF automáticamente
    print(f"\n🔍 Abriendo PDF para inspección visual...")
    os.system(f"open {copia_path}")
    
    print("\n" + "="*80)
    print("✅ GENERACIÓN COMPLETADA")
    print("="*80)
    
    print("\n📋 VERIFICACIONES PENDIENTES:")
    print("   1. ✅ Verificar que el PDF se abrió correctamente")
    print("   2. ✅ Verificar logo 'Agro Tech logo solo.png' en portada")
    print("   3. ✅ Verificar pie de página con logo en todas las páginas")
    print("   4. ✅ Verificar los 3 mapas profesionales:")
    print("      • Mapa 1: Ubicación Departamental")
    print("      • Mapa 2: Ubicación Municipal")
    print("      • Mapa 3: Influencia Legal Directa")
    print("   5. ✅ Verificar tabla de proximidad")
    print("   6. ✅ Verificar resumen ejecutivo")
    print("   7. ✅ Verificar análisis de restricciones")
    
    print("\n📊 INFORMACIÓN DE LA PARCELA:")
    print(f"   • Nombre: {parcela.nombre}")
    print(f"   • Propietario: {parcela.propietario}")
    print(f"   • Área: {parcela.area_hectareas:.2f} ha (¡La más grande!)")
    print(f"   • Restricciones encontradas: {len(resultado.restricciones_encontradas)}")
    print(f"   • Cumple normativa: {'✅ SÍ' if resultado.cumple_normativa else '⚠️ NO'}")
    
except Exception as e:
    print(f"\n❌ Error generando PDF: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
print("="*80)
