#!/usr/bin/env python
"""
🧪 TEST COMPLETO: Interfaz Web → Informe Legal PDF (Parcela #6)
Simula exactamente el flujo de un usuario haciendo clic en el botón
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from verificador_legal import VerificadorRestriccionesLegales
from generador_pdf_legal import GeneradorPDFLegal

print("=" * 80)
print("🧪 TEST: Generación Informe Legal PDF - Parcela #6")
print("=" * 80)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1️⃣ VERIFICAR PARCELA #6
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n1️⃣ Cargando Parcela #6...")
try:
    parcela = Parcela.objects.get(id=6)
    print(f"✅ Parcela: {parcela.nombre}")
    print(f"   Propietario: {parcela.propietario}")
    print(f"   Área: {parcela.area_hectareas:.2f} ha")
    print(f"   Cultivo: {parcela.tipo_cultivo}")
    print(f"   Activa: {parcela.activa}")
    
    if parcela.geometria and not parcela.geometria.empty:
        print(f"   ✅ Geometría válida")
        # Obtener extent de la geometría
        extent = parcela.geometria.extent
        print(f"   Coordenadas: {extent[1]:.6f}, {extent[0]:.6f}")
    else:
        print(f"   ❌ Sin geometría")
        sys.exit(1)
        
except Parcela.DoesNotExist:
    print("❌ Parcela #6 no encontrada en la base de datos")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2️⃣ CREAR VERIFICADOR (COMO LO HACE LA VISTA WEB)
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
    # Usar el método verificar_parcela que retorna ResultadoVerificacion
    resultado = verificador.verificar_parcela(
        parcela_id=parcela.id,
        geometria_parcela=parcela.geometria,  # Django GEOS Polygon
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4️⃣ CREAR GENERADOR PDF (COMO LO HACE LA VISTA WEB)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n4️⃣ Inicializando GeneradorPDFLegal...")
try:
    generador = GeneradorPDFLegal()
    print("✅ Generador inicializado")
except Exception as e:
    print(f"❌ Error inicializando generador: {str(e)}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5️⃣ GENERAR PDF (SIMULAR EL CLIC DEL USUARIO)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n5️⃣ Generando PDF...")
print("   (Esto simula lo que ocurre cuando el usuario hace clic en '⚖️ Informe Legal')")
print()

try:
    # Definir ruta de salida
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_limpio = parcela.nombre.replace(" ", "_").replace("/", "-")
    nombre_archivo = f"informe_legal_{nombre_limpio}_{timestamp}.pdf"
    
    # Crear directorio si no existe
    output_dir = os.path.join('media', 'verificacion_legal')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, nombre_archivo)
    
    ruta_pdf = generador.generar_pdf(
        parcela=parcela,
        resultado=resultado,
        verificador=verificador,
        output_path=output_path,
        departamento='Casanare'
    )
    
    print("\n" + "=" * 80)
    print("✅ PDF GENERADO EXITOSAMENTE")
    print("=" * 80)
    
    # Verificar archivo
    if os.path.exists(ruta_pdf):
        size_mb = os.path.getsize(ruta_pdf) / (1024 * 1024)
        print(f"\n📦 Detalles del archivo:")
        print(f"   Ubicación: {ruta_pdf}")
        print(f"   Tamaño: {size_mb:.2f} MB")
        
        # Verificar que es un PDF válido
        with open(ruta_pdf, 'rb') as f:
            header = f.read(4)
            if header == b'%PDF':
                print(f"   ✅ Archivo PDF válido")
            else:
                print(f"   ⚠️ Archivo no parece ser PDF válido")
        
        # Copiar a directorio de test para fácil acceso
        import shutil
        test_output = 'test_pdf_parcela6_web.pdf'
        shutil.copy(ruta_pdf, test_output)
        print(f"\n💾 Copia guardada en: {test_output}")
        print(f"   Puedes abrirlo con: open {test_output}")
        
        # Abrir automáticamente
        print(f"\n🔍 Abriendo PDF para inspección visual...")
        os.system(f'open "{ruta_pdf}"')
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print("\n📋 VERIFICACIONES PENDIENTES:")
        print("   1. ✅ Verificar que el PDF se abrió correctamente")
        print("   2. ✅ Verificar que contiene los 3 mapas:")
        print("      • Mapa 1: Ubicación Departamental")
        print("      • Mapa 2: Ubicación Municipal")
        print("      • Mapa 3: Influencia Legal Directa (NUEVO)")
        print("   3. ✅ Verificar tabla de proximidad")
        print("   4. ✅ Verificar resumen ejecutivo")
        
    else:
        print(f"\n❌ ERROR: El archivo PDF no se generó en la ruta esperada")
        print(f"   Ruta: {ruta_pdf}")
        
except Exception as e:
    print(f"\n❌ ERROR GENERANDO PDF:")
    print(f"   {str(e)}")
    print(f"\n📋 Stack trace completo:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
