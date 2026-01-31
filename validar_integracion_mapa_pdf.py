#!/usr/bin/env python
"""
Validación: Confirmar que el generador PDF está configurado para usar el nuevo mapa
"""
import os
import sys

def validar_integracion_mapa():
    """Valida que el código del generador PDF use el nuevo mapa georeferenciado"""
    
    print("=" * 80)
    print("🔍 VALIDANDO INTEGRACIÓN DEL MAPA GEOREFERENCIADO EN PDF TÉCNICO")
    print("=" * 80)
    
    generador_path = '/Users/sebasflorez16/Documents/AgroTech Historico/informes/generador_pdf.py'
    
    if not os.path.exists(generador_path):
        print(f"❌ No se encontró el archivo: {generador_path}")
        return False
    
    with open(generador_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Validaciones
    validaciones = {
        '1. Priorización del nuevo mapa': 'mapa_intervencion_limpio_path',
        '2. Fallback al mapa antiguo': 'mapa_diagnostico_path',
        '3. Título dinámico del mapa': 'Mapa Georeferenciado de Intervención',
        '4. Descripción del nuevo mapa': 'coordenadas GPS',
        '5. Variable mapa_final_path': 'mapa_final_path',
        '6. Detección del tipo de mapa': 'es_mapa_georeferenciado'
    }
    
    print("\n📋 VERIFICANDO COMPONENTES CLAVE:\n")
    
    todas_ok = True
    for nombre, patron in validaciones.items():
        if patron in contenido:
            print(f"   ✅ {nombre}")
        else:
            print(f"   ❌ {nombre} - NO ENCONTRADO: '{patron}'")
            todas_ok = False
    
    # Buscar la sección específica del mapa
    print("\n🗺️  VERIFICANDO SECCIÓN DEL MAPA:\n")
    
    if 'mapa_final_path = diagnostico.get' in contenido:
        print("   ✅ Lógica de selección de mapa implementada")
        
        # Extraer la sección relevante
        inicio = contenido.find('# Mapa georeferenciado')
        if inicio != -1:
            fin = contenido.find('except Exception as e:', inicio) + 200
            seccion = contenido[inicio:fin]
            
            print("\n📄 FRAGMENTO DE CÓDIGO RELEVANTE:")
            print("-" * 80)
            lineas = seccion.split('\n')[:20]  # Primeras 20 líneas
            for linea in lineas:
                print(f"   {linea}")
            print("-" * 80)
        else:
            print("   ⚠️  No se encontró el comentario '# Mapa georeferenciado'")
    else:
        print("   ❌ NO se encontró la lógica de selección de mapa")
        todas_ok = False
    
    # Verificar que se use en Image()
    print("\n🖼️  VERIFICANDO USO EN RENDERIZADO:\n")
    if 'Image(mapa_final_path' in contenido:
        print("   ✅ El mapa se renderiza usando mapa_final_path")
    else:
        print("   ❌ NO se usa mapa_final_path en Image()")
        todas_ok = False
    
    # Resumen final
    print("\n" + "=" * 80)
    if todas_ok:
        print("✅ VALIDACIÓN EXITOSA")
        print("\nEl generador PDF está correctamente configurado para:")
        print("   1. Priorizar el nuevo mapa georeferenciado")
        print("   2. Usar el mapa antiguo como fallback")
        print("   3. Mostrar título y descripción apropiados")
        print("   4. Renderizar el mapa en la sección de diagnóstico")
        print("\n🎯 PRÓXIMO PASO:")
        print("   Genera un PDF completo para cualquier parcela y verifica visualmente")
        print("   que la sección del mapa muestre el nuevo formato georeferenciado.")
    else:
        print("❌ VALIDACIÓN FALLIDA")
        print("\nRevisar el archivo generador_pdf.py")
    print("=" * 80)
    
    return todas_ok

if __name__ == '__main__':
    exito = validar_integracion_mapa()
    sys.exit(0 if exito else 1)
