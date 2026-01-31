"""
TEST VISUAL PDF - FASES A+B COMPLETADAS
Genera un PDF de prueba con datos reales para validación visual de:
- FASE A: Conclusión ejecutiva, tabla de metadatos, limitaciones técnicas
- FASE B: Mapa contexto regional, mapa silueta, escala gráfica, flechas desde borde

Autor: Sistema AgroTech
Fecha: 2025-01-29
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.gis.geos import Polygon
from django.contrib.auth import get_user_model
from informes.models import Parcela
from generador_pdf_legal import GeneradorPDFLegal, VerificadorRestriccionesLegales

User = get_user_model()


def crear_parcela_prueba():
    """Crea una parcela de prueba en la base de datos"""
    
    # Obtener o crear usuario de prueba
    usuario, _ = User.objects.get_or_create(
        username='test_pdf_visual',
        defaults={
            'email': 'test@agrotech.com',
            'first_name': 'Usuario',
            'last_name': 'Prueba'
        }
    )
    
    # Polígono de prueba (parcela agrícola en Antioquia, Colombia)
    # Coordenadas reales cerca de Medellín
    coords = [
        (-75.5789, 6.2910),  # SW
        (-75.5770, 6.2910),  # SE
        (-75.5770, 6.2930),  # NE
        (-75.5789, 6.2930),  # NW
        (-75.5789, 6.2910)   # Cerrar polígono
    ]
    geometria = Polygon(coords)
    
    # Crear o actualizar parcela de prueba
    parcela, created = Parcela.objects.update_or_create(
        nombre='Finca El Paraíso - Prueba FASES A+B',
        propietario=usuario,
        defaults={
            'area_hectareas': 5.2,
            'tipo_cultivo': 'Café',
            'geometria': geometria,
            'fecha_inicio_monitoreo': datetime.now().date(),
            'fecha_fin_monitoreo': datetime.now().date(),
        }
    )
    
    print(f"{'✅ Creada' if created else '✅ Actualizada'} parcela: {parcela.nombre}")
    print(f"✅ ID: {parcela.id}")
    print(f"✅ Área: {parcela.area_hectareas} ha")
    print(f"✅ Centroide: {parcela.geometria.centroid.coords}")
    
    return parcela


def main():
    """Ejecuta el test visual del PDF"""
    
    print("\n" + "="*80)
    print("🎨 TEST VISUAL PDF - FASES A+B COMPLETADAS")
    print("="*80 + "\n")
    
    # Crear parcela de prueba en la base de datos
    print("📊 Creando parcela de prueba en la base de datos...")
    parcela = crear_parcela_prueba()
    
    # Crear verificador e inicializar capas
    print(f"\n🗺️  Inicializando verificador de restricciones legales...")
    verificador = VerificadorRestriccionesLegales()
    
    # Ejecutar verificación
    print(f"\n🔍 Ejecutando verificación legal...")
    resultado = verificador.verificar_restricciones(parcela, departamento="Antioquia")
    
    print(f"\n✅ Verificación completada:")
    print(f"   - Traslapes detectados: {resultado.tiene_restricciones}")
    print(f"   - Proximidades calculadas: Sí")
    
    # Crear directorio de salida si no existe
    output_dir = "pdfs_prueba"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generar PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"TEST_FASES_AB_{timestamp}.pdf"
    ruta_pdf = os.path.join(output_dir, nombre_archivo)
    
    print(f"\n🚀 Generando PDF de prueba...")
    print(f"📁 Ruta: {ruta_pdf}\n")
    
    try:
        generador = GeneradorPDFLegal()
        
        # Generar PDF
        ruta_generada = generador.generar_pdf(
            parcela=parcela,
            resultado=resultado,
            verificador=verificador,
            output_path=ruta_pdf,
            departamento="Antioquia"
        )
        
        print("\n" + "="*80)
        print("✅ PDF GENERADO EXITOSAMENTE")
        print("="*80)
        print(f"\n📄 Archivo: {ruta_generada}")
        
        # Obtener tamaño del archivo
        size_mb = os.path.getsize(ruta_generada) / (1024 * 1024)
        print(f"📊 Tamaño: {size_mb:.2f} MB")
        
        # Checklist de elementos a validar visualmente
        print("\n" + "="*80)
        print("🔍 CHECKLIST DE VALIDACIÓN VISUAL")
        print("="*80)
        
        checklist = [
            ("FASE A - Conclusión Ejecutiva", [
                "✓ Badge de viabilidad verde con ícono ✓",
                "✓ Síntesis comercial clara y concisa",
                "✓ Nota de responsabilidad profesional",
                "✓ Formato visual destacado"
            ]),
            ("FASE A - Tabla de Metadatos", [
                "✓ 5 capas listadas (ZRC, Resguardos, Negritudes, Parques, Reservas)",
                "✓ Columnas: Fuente, Autoridad, Año, Tipo, Escala, Limitaciones, URL",
                "✓ Formato tabular profesional",
                "✓ Enlaces clickeables"
            ]),
            ("FASE A - Limitaciones Técnicas", [
                "✓ Alcance del análisis definido",
                "✓ Limitaciones metodológicas claras",
                "✓ Advertencias legales",
                "✓ Texto estructurado y legible"
            ]),
            ("FASE B - Mapa Contexto Regional", [
                "✓ Vista amplia del departamento",
                "✓ Estrella roja en ubicación de parcela",
                "✓ Círculo de contexto",
                "✓ Título y leyenda"
            ]),
            ("FASE B - Mapa Silueta Limpia", [
                "✓ Solo polígono negro",
                "✓ Fondo blanco",
                "✓ Sin capas adicionales",
                "✓ Título claro"
            ]),
            ("FASE B - Escala Gráfica", [
                "✓ Barra métrica en mapa principal",
                "✓ Tamaño adaptativo",
                "✓ Etiquetas de distancia",
                "✓ Posición inferior derecha"
            ]),
            ("FASE B - Flechas desde Borde", [
                "✓ Flechas salen desde el borde del polígono",
                "✓ No desde el centroide",
                "✓ Etiquetas de distancia visibles",
                "✓ Colores diferenciados por capa"
            ]),
            ("Orden Psicológico de Venta", [
                "✓ 1. Portada profesional",
                "✓ 2. Conclusión ejecutiva (PRIMERO)",
                "✓ 3. Información básica",
                "✓ 4. Resultados detallados",
                "✓ 5. Mapas adicionales",
                "✓ 6. Metadatos y limitaciones (ÚLTIMO)"
            ])
        ]
        
        for seccion, items in checklist:
            print(f"\n📋 {seccion}:")
            for item in items:
                print(f"   {item}")
        
        print("\n" + "="*80)
        print("🎯 PRÓXIMOS PASOS")
        print("="*80)
        print(f"""
1. Abrir el PDF: {ruta_generada}
2. Validar visualmente todos los elementos del checklist anterior
3. Verificar:
   - Calidad de mapas (resolución, colores, leyendas)
   - Claridad del copy comercial
   - Orden lógico de secciones
   - Profesionalismo general del documento
4. Si todo está OK:
   - ✅ Marcar testing visual como PASADO
   - ✅ Proceder con validación de stakeholders
   - ✅ Preparar deploy a producción
5. Si hay ajustes menores:
   - 🔧 Documentar observaciones
   - 🔧 Aplicar refinamientos
   - 🔧 Regenerar y re-validar
        """)
        
        print("\n" + "="*80)
        print("✨ TEST COMPLETADO")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR durante la generación del PDF:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
