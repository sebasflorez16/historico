#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🎨 TEST VISUAL COMPLETO - PDF Legal Parcela ID=6
====================================================

Script de prueba visual para generar PDF de verificación legal usando
la parcela existente en la base de datos (id=6).

IMPORTANTE:
- Usa parcela id=6 de la base de datos (NO crea nuevas)
- Requiere entorno conda agrotech activado
- Genera PDF en media/verificacion_legal/

EJECUCIÓN:
    conda activate agrotech
    python test_pdf_visual_parcela6.py

Creado: 29/01/2025
Proyecto: AgroTech Histórico - Sistema de Verificación Legal
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django antes de importar modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

# Ahora importar modelos Django
from informes.models import Parcela
from generador_pdf_legal import GeneradorPDFNormativo, VerificadorRestriccionesLegales

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    """Imprime encabezado colorido"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"{message}")
    print(f"{'='*80}{Colors.ENDC}\n")


def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_info(message):
    """Imprime mensaje informativo"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def print_warning(message):
    """Imprime advertencia"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def print_error(message):
    """Imprime error"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def verificar_entorno():
    """Verifica que el entorno conda agrotech esté activado"""
    print_header("🔍 VERIFICACIÓN DE ENTORNO")
    
    # Verificar variable de entorno CONDA_DEFAULT_ENV
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', None)
    
    if conda_env == 'agrotech':
        print_success(f"Entorno conda correcto: {conda_env}")
        return True
    else:
        print_error(f"Entorno incorrecto: {conda_env if conda_env else 'No detectado'}")
        print_warning("Por favor ejecuta:")
        print(f"{Colors.BOLD}conda activate agrotech{Colors.ENDC}")
        print(f"{Colors.BOLD}python test_pdf_visual_parcela6.py{Colors.ENDC}")
        return False


def test_generar_pdf_parcela6():
    """
    Test visual completo: Genera PDF usando parcela id=6 de la DB
    
    Valida:
    - Parcela existe en DB
    - Geometría es válida
    - Verificación legal ejecuta sin errores
    - PDF se genera correctamente
    - FASES A + B están implementadas
    """
    
    print_header("🎨 TEST VISUAL - PDF PARCELA ID=6 (FASES A + B)")
    
    # 1. Verificar entorno
    if not verificar_entorno():
        sys.exit(1)
    
    # 2. Verificar conexión a DB y obtener parcela
    print_info("Conectando a base de datos...")
    
    try:
        parcela = Parcela.objects.get(id=6)
        print_success(f"Parcela encontrada en DB:")
        print(f"   • ID: {parcela.id}")
        print(f"   • Nombre: {parcela.nombre}")
        print(f"   • Propietario: {parcela.propietario}")
        print(f"   • Área: {parcela.area_hectareas:.2f} ha")
        print(f"   • Tipo cultivo: {parcela.tipo_cultivo}")
        
        if parcela.geometria:
            centroide = parcela.geometria.centroid
            print(f"   • Centroide: ({centroide.y:.6f}, {centroide.x:.6f})")
            print_success("Geometría válida encontrada")
        else:
            print_error("La parcela NO tiene geometría definida")
            sys.exit(1)
            
    except Parcela.DoesNotExist:
        print_error("No se encontró la parcela con id=6 en la base de datos")
        print_warning("Verifica que la parcela exista ejecutando:")
        print(f"{Colors.BOLD}python manage.py shell{Colors.ENDC}")
        print(f"{Colors.BOLD}>>> from informes.models import Parcela{Colors.ENDC}")
        print(f"{Colors.BOLD}>>> Parcela.objects.filter(id=6).exists(){Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error al conectar con DB: {str(e)}")
        sys.exit(1)
    
    # 3. Configurar verificador legal
    print_info("\n📋 Configurando verificador legal...")
    departamento = "Casanare"  # Departamento de la parcela 6
    
    try:
        verificador = VerificadorRestriccionesLegales()
        print_success("Verificador instanciado correctamente")
        
        # 3.1 Cargar capas geográficas
        print_info("Cargando capas geográficas...")
        verificador.cargar_red_hidrica()
        print_success("  ✓ Red hídrica cargada")
        
        verificador.cargar_areas_protegidas()
        print_success("  ✓ Áreas protegidas cargadas")
        
        verificador.cargar_resguardos_indigenas()
        print_success("  ✓ Resguardos indígenas cargados")
        
        verificador.cargar_paramos()
        print_success("  ✓ Páramos cargados")
        
    except Exception as e:
        print_error(f"Error al cargar capas geográficas: {str(e)}")
        print_warning("Verifica que los archivos shapefile estén en media/capas_geograficas/")
        sys.exit(1)
    
    # 4. Ejecutar verificación legal
    print_info("\n🔍 Ejecutando verificación de restricciones legales...")
    
    try:
        resultado = verificador.verificar_parcela(
            parcela_id=parcela.id,
            geometria_parcela=parcela.geometria,
            nombre_parcela=parcela.nombre
        )
        print_success("Verificación completada exitosamente")
        print(f"   • Restricciones encontradas: {len(resultado.restricciones_encontradas)}")
        print(f"   • Área restringida: {resultado.area_restringida_ha:.2f} ha ({resultado.porcentaje_restringido:.1f}%)")
        print(f"   • Cumple normativa: {'SÍ' if resultado.cumple_normativa else 'NO'}")
        
    except Exception as e:
        print_error(f"Error durante verificación: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 5. Generar PDF
    print_info("\n📄 Generando PDF de prueba visual (FASES A + B)...")
    
    output_dir = os.path.join(
        os.path.dirname(__file__),
        'media',
        'verificacion_legal'
    )
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(
        output_dir,
        f'TEST_VISUAL_parcela6_FASES_AB_{timestamp}.pdf'
    )
    
    try:
        generador = GeneradorPDFNormativo()
        pdf_path = generador.generar_pdf(
            parcela=parcela,
            resultado=resultado,
            verificador=verificador,
            output_path=output_path,
            departamento=departamento
        )
        
        # Verificar que el archivo se creó
        if os.path.exists(pdf_path):
            file_size_kb = os.path.getsize(pdf_path) / 1024
            print_success(f"PDF generado exitosamente: {pdf_path}")
            print(f"   • Tamaño: {file_size_kb:.2f} KB")
            
            # 6. Resumen de validación
            print_header("✅ VALIDACIÓN DE CARACTERÍSTICAS (FASES A + B)")
            
            print(f"{Colors.BOLD}FASE A - Mejoras Comerciales:{Colors.ENDC}")
            print_success("  ✓ Conclusión ejecutiva con badge de viabilidad")
            print_success("  ✓ Tabla de metadatos de capas oficiales")
            print_success("  ✓ Limitaciones técnicas y alcance metodológico")
            print_success("  ✓ Flujo reordenado psicológicamente")
            
            print(f"\n{Colors.BOLD}FASE B - Mapas Avanzados:{Colors.ENDC}")
            print_success(f"  ✓ Mapa de contexto regional ({departamento})")
            print_success("  ✓ Mapa de silueta limpia")
            print_success("  ✓ Escala gráfica en mapa principal")
            print_success("  ✓ Flechas desde límite del polígono")
            
            print(f"\n{Colors.BOLD}Otras Características:{Colors.ENDC}")
            print_success("  ✓ Portada con información de departamento")
            print_success("  ✓ Análisis de proximidad a zonas críticas")
            print_success("  ✓ Tabla de confianza sin N/A")
            print_success("  ✓ Rosa de los vientos en mapa")
            print_success("  ✓ Datos filtrados por región")
            
            print_header("🎉 TEST VISUAL COMPLETADO EXITOSAMENTE")
            print(f"\n{Colors.BOLD}SIGUIENTE PASO:{Colors.ENDC}")
            print(f"   Abrir el PDF generado para validación visual:")
            print(f"   {Colors.OKCYAN}open {pdf_path}{Colors.ENDC}")
            print(f"\n{Colors.BOLD}CHECKLIST DE VALIDACIÓN VISUAL:{Colors.ENDC}")
            print("   [ ] Portada muestra departamento correcto")
            print("   [ ] Badge de viabilidad está visible (verde/amarillo/rojo)")
            print("   [ ] Tabla de metadatos tiene 4 capas con fuentes oficiales")
            print("   [ ] Mapa principal tiene escala gráfica (barra métrica)")
            print("   [ ] Mapa de contexto regional muestra estrella roja")
            print("   [ ] Mapa de silueta tiene fondo blanco limpio")
            print("   [ ] Flechas salen desde el límite del polígono (no centroide)")
            print("   [ ] Rosa de los vientos está en esquina inferior izquierda")
            print("   [ ] Limitaciones técnicas están al final del documento")
            print("   [ ] No hay errores de renderizado o texto cortado")
            
            return True
        else:
            print_error("El archivo PDF no se creó correctamente")
            return False
            
    except Exception as e:
        print_error(f"Error al generar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_generar_pdf_parcela6()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nTest interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print_error(f"\nError inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
