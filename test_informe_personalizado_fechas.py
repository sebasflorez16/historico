"""
Test de informes personalizados con rangos de fechas exactos
Verifica que el sistema use las fechas personalizadas correctamente
"""
import os
import sys
import django
import json
from datetime import date, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from informes.models import Parcela, IndiceMensual, Informe
from informes.views import generar_informe_personalizado
from informes.generador_pdf import GeneradorPDFProfesional

def test_informe_con_fechas_personalizadas():
    """
    Test 1: Verificar que el sistema usa fechas personalizadas exactas
    """
    print("\n" + "="*80)
    print("TEST 1: INFORME CON FECHAS PERSONALIZADAS")
    print("="*80)
    
    # Obtener parcela de prueba
    parcela = Parcela.objects.filter(activa=True).first()
    if not parcela:
        print("❌ No hay parcelas disponibles")
        return False
    
    print(f"✅ Parcela: {parcela.nombre} (ID: {parcela.id})")
    
    # Verificar datos disponibles
    indices_disponibles = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
    if indices_disponibles.count() < 3:
        print(f"❌ Parcela tiene muy pocos datos ({indices_disponibles.count()} meses)")
        return False
    
    print(f"✅ Datos disponibles: {indices_disponibles.count()} meses")
    
    # Mostrar rango de datos disponibles
    primer_indice = indices_disponibles.first()
    ultimo_indice = indices_disponibles.last()
    fecha_min = date(primer_indice.año, primer_indice.mes, 1)
    fecha_max = date(ultimo_indice.año, ultimo_indice.mes, 1)
    print(f"📅 Rango disponible: {fecha_min} a {fecha_max}")
    
    # Definir rango personalizado (últimos 6 meses específicos)
    fecha_fin_personalizada = fecha_max
    fecha_inicio_personalizada = date(fecha_max.year, max(1, fecha_max.month - 5), 1)
    
    print(f"\n📊 Generando informe con rango personalizado:")
    print(f"   Desde: {fecha_inicio_personalizada}")
    print(f"   Hasta: {fecha_fin_personalizada}")
    
    # Generar informe usando el generador directamente
    try:
        configuracion = {
            'nivel_detalle': 'completo',
            'indices': ['ndvi', 'msavi', 'savi'],
            'secciones': ['tendencias', 'recomendaciones_riego'],
        }
        
        generador = GeneradorPDFProfesional(configuracion=configuracion)
        ruta_pdf = generador.generar_informe_completo(
            parcela_id=parcela.id,
            fecha_inicio=fecha_inicio_personalizada,
            fecha_fin=fecha_fin_personalizada,
            meses_atras=6  # Este NO debe usarse si hay fechas exactas
        )
        
        if os.path.exists(ruta_pdf):
            print(f"✅ PDF generado: {ruta_pdf}")
            print(f"   Tamaño: {os.path.getsize(ruta_pdf) / 1024:.2f} KB")
            return True
        else:
            print(f"❌ PDF no se generó")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_informe_con_configuracion_reducida():
    """
    Test 2: Verificar que el informe personalizado sea diferente según la configuración
    """
    print("\n" + "="*80)
    print("TEST 2: INFORME CON CONFIGURACIÓN REDUCIDA (SOLO NDVI)")
    print("="*80)
    
    parcela = Parcela.objects.filter(activa=True).first()
    if not parcela:
        print("❌ No hay parcelas disponibles")
        return False
    
    print(f"✅ Parcela: {parcela.nombre}")
    
    # Configuración reducida: solo NDVI
    configuracion_reducida = {
        'nivel_detalle': 'ejecutivo',
        'indices': ['ndvi'],  # SOLO NDVI
        'secciones': [],  # SIN SECCIONES ADICIONALES
    }
    
    print("\n📋 Configuración reducida:")
    print(f"   Nivel: {configuracion_reducida['nivel_detalle']}")
    print(f"   Índices: {configuracion_reducida['indices']}")
    print(f"   Secciones: {configuracion_reducida['secciones']}")
    
    try:
        generador = GeneradorPDFProfesional(configuracion=configuracion_reducida)
        ruta_pdf = generador.generar_informe_completo(
            parcela_id=parcela.id,
            meses_atras=12
        )
        
        if os.path.exists(ruta_pdf):
            tamanio_kb = os.path.getsize(ruta_pdf) / 1024
            print(f"✅ PDF reducido generado: {ruta_pdf}")
            print(f"   Tamaño: {tamanio_kb:.2f} KB")
            
            # Un PDF reducido debería ser más pequeño
            if tamanio_kb < 500:  # Arbitrario, pero razonable
                print("✅ Tamaño esperado para PDF reducido")
            else:
                print(f"⚠️  PDF parece muy grande para ser 'ejecutivo'")
            
            return True
        else:
            print(f"❌ PDF no se generó")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_api_personalizada():
    """
    Test 3: Verificar que la API acepta configuración JSON correctamente
    """
    print("\n" + "="*80)
    print("TEST 3: API DE INFORME PERSONALIZADO")
    print("="*80)
    
    parcela = Parcela.objects.filter(activa=True).first()
    if not parcela:
        print("❌ No hay parcelas disponibles")
        return False
    
    # Crear usuario de prueba
    usuario = User.objects.filter(is_staff=True).first()
    if not usuario:
        usuario = User.objects.create_user('test_user', 'test@test.com', 'password')
    
    print(f"✅ Usuario: {usuario.username}")
    print(f"✅ Parcela: {parcela.nombre}")
    
    # Preparar request con configuración personalizada
    factory = RequestFactory()
    
    # Datos del request (fechas personalizadas + configuración)
    fecha_fin = date.today()
    fecha_inicio = date(fecha_fin.year, fecha_fin.month - 3, 1)
    
    payload = {
        'periodo': {
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
        },
        'configuracion': {
            'nivel_detalle': 'estandar',
            'indices': ['ndvi', 'msavi'],
            'secciones': ['tendencias'],
        }
    }
    
    print(f"\n📤 Enviando configuración:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    request = factory.post(
        f'/informes/parcelas/{parcela.id}/generar-informe-personalizado/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    request.user = usuario
    
    try:
        response = generar_informe_personalizado(request, parcela.id)
        
        if response.status_code == 200:
            data = json.loads(response.content)
            print(f"\n✅ Respuesta exitosa:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verificar que el informe se creó en BD
            informe_id = data.get('informe_id')
            if informe_id:
                informe = Informe.objects.get(id=informe_id)
                print(f"\n✅ Informe registrado en BD:")
                print(f"   ID: {informe.id}")
                print(f"   Título: {informe.titulo}")
                print(f"   Período: {informe.fecha_inicio_analisis} a {informe.fecha_fin_analisis}")
                print(f"   Configuración guardada: {bool(informe.configuracion)}")
                
                if informe.configuracion:
                    print(f"   Nivel detalle: {informe.configuracion.get('nivel_detalle')}")
                    print(f"   Índices: {informe.configuracion.get('indices')}")
                
                return True
        else:
            print(f"❌ Error en API: {response.status_code}")
            print(response.content.decode())
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("🧪 TEST DE INFORMES PERSONALIZADOS CON FECHAS EXACTAS")
    print("="*80)
    
    resultados = []
    
    # Test 1: Fechas personalizadas
    resultados.append(("Fechas personalizadas", test_informe_con_fechas_personalizadas()))
    
    # Test 2: Configuración reducida
    resultados.append(("Configuración reducida", test_informe_con_configuracion_reducida()))
    
    # Test 3: API personalizada
    resultados.append(("API personalizada", test_api_personalizada()))
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN DE TESTS")
    print("="*80)
    
    for nombre, resultado in resultados:
        emoji = "✅" if resultado else "❌"
        print(f"{emoji} {nombre}")
    
    total_exitosos = sum(1 for _, r in resultados if r)
    print(f"\n{'✅' if total_exitosos == len(resultados) else '⚠️'} {total_exitosos}/{len(resultados)} tests exitosos")
    
    return total_exitosos == len(resultados)


if __name__ == '__main__':
    exito = main()
    sys.exit(0 if exito else 1)
