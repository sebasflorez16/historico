#!/usr/bin/env python
"""
Test completo del sistema de informes personalizados
Verifica la generación de PDFs con configuraciones personalizadas
"""

import os
import sys
import django
import json
from datetime import datetime, date, timedelta

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from informes.models import Parcela, IndiceMensual, Informe
from informes.generador_pdf import GeneradorPDFProfesional
from informes.configuraciones_informe import (
    obtener_configuracion_default,
    PLANTILLAS_SISTEMA,
    INDICES_DISPONIBLES,
    SECCIONES_OPCIONALES
)

# Renombrar para compatibilidad
PLANTILLAS_PREDEFINIDAS = PLANTILLAS_SISTEMA
SECCIONES_DISPONIBLES = SECCIONES_OPCIONALES


class TestInformesPersonalizados:
    """Test del sistema de informes personalizados"""
    
    def __init__(self):
        self.client = Client()
        self.errores = []
        self.warnings = []
        self.exitos = []
        
    def log_error(self, mensaje):
        """Registra un error"""
        print(f"❌ ERROR: {mensaje}")
        self.errores.append(mensaje)
    
    def log_warning(self, mensaje):
        """Registra un warning"""
        print(f"⚠️  WARNING: {mensaje}")
        self.warnings.append(mensaje)
    
    def log_exito(self, mensaje):
        """Registra un éxito"""
        print(f"✅ {mensaje}")
        self.exitos.append(mensaje)
    
    def test_configuraciones_predefinidas(self):
        """Test 1: Verificar que las plantillas predefinidas están correctas"""
        print("\n" + "="*80)
        print("TEST 1: Verificar Plantillas Predefinidas")
        print("="*80)
        
        try:
            # Verificar que hay plantillas
            if not PLANTILLAS_PREDEFINIDAS:
                self.log_error("No hay plantillas predefinidas")
                return False
            
            self.log_exito(f"Encontradas {len(PLANTILLAS_PREDEFINIDAS)} plantillas predefinidas")
            
            # Verificar cada plantilla
            for nombre, config in PLANTILLAS_PREDEFINIDAS.items():
                print(f"\n📋 Plantilla: {nombre}")
                print(f"   Nivel: {config.get('nivel_detalle')}")
                print(f"   Índices: {len(config.get('indices', []))}")
                print(f"   Secciones: {len(config.get('secciones', []))}")
                
                # Validar estructura
                if 'nivel_detalle' not in config:
                    self.log_warning(f"Plantilla {nombre} sin nivel_detalle")
                
                if 'indices' not in config:
                    self.log_warning(f"Plantilla {nombre} sin índices")
                
                # Verificar que NDVI está siempre incluido
                indices = config.get('indices', [])
                if 'ndvi' not in [i.lower() for i in indices]:
                    self.log_warning(f"Plantilla {nombre} no incluye NDVI (obligatorio)")
            
            self.log_exito("Todas las plantillas tienen estructura válida")
            return True
            
        except Exception as e:
            self.log_error(f"Error verificando plantillas: {str(e)}")
            return False
    
    def test_generador_pdf_configuracion_default(self):
        """Test 2: Generar PDF con configuración por defecto"""
        print("\n" + "="*80)
        print("TEST 2: Generador PDF con Configuración Default")
        print("="*80)
        
        try:
            # Obtener parcela de prueba
            parcela = Parcela.objects.filter(activa=True).first()
            if not parcela:
                self.log_warning("No hay parcelas activas para probar")
                return False
            
            # Verificar que hay datos
            indices_count = IndiceMensual.objects.filter(parcela=parcela).count()
            if indices_count == 0:
                self.log_warning(f"Parcela {parcela.nombre} no tiene datos satelitales")
                return False
            
            self.log_exito(f"Parcela: {parcela.nombre} ({indices_count} registros)")
            
            # Generar PDF con configuración default
            generador = GeneradorPDFProfesional()
            
            print(f"📊 Generando informe completo...")
            ruta_pdf = generador.generar_informe_completo(
                parcela_id=parcela.id,
                meses_atras=12
            )
            
            # Verificar que se generó el archivo
            if not os.path.exists(ruta_pdf):
                self.log_error(f"El PDF no se generó en {ruta_pdf}")
                return False
            
            # Verificar tamaño del archivo
            tamaño = os.path.getsize(ruta_pdf)
            if tamaño < 1000:  # Menos de 1KB es sospechoso
                self.log_error(f"PDF muy pequeño ({tamaño} bytes)")
                return False
            
            self.log_exito(f"PDF generado: {os.path.basename(ruta_pdf)} ({tamaño/1024:.1f} KB)")
            return True
            
        except Exception as e:
            self.log_error(f"Error generando PDF default: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_generador_pdf_ejecutivo(self):
        """Test 3: Generar PDF con nivel ejecutivo"""
        print("\n" + "="*80)
        print("TEST 3: Generador PDF Ejecutivo (Mínimo)")
        print("="*80)
        
        try:
            parcela = Parcela.objects.filter(activa=True).first()
            if not parcela:
                return False
            
            # Configuración ejecutiva (mínima) - usar clave correcta
            config_ejecutivo = PLANTILLAS_PREDEFINIDAS.get('ejecutivo_rapido', {}).get('configuracion')
            
            if not config_ejecutivo:
                self.log_warning("Plantilla ejecutivo_rapido no encontrada")
                return False
            
            print(f"📊 Configuración:")
            print(f"   Nivel: {config_ejecutivo['nivel_detalle']}")
            print(f"   Índices: {config_ejecutivo['indices']}")
            print(f"   Secciones: {len(config_ejecutivo['secciones'])}")
            
            # Generar PDF
            generador = GeneradorPDFProfesional(configuracion=config_ejecutivo)
            ruta_pdf = generador.generar_informe_completo(
                parcela_id=parcela.id,
                meses_atras=6
            )
            
            if not os.path.exists(ruta_pdf):
                self.log_error("PDF ejecutivo no generado")
                return False
            
            tamaño = os.path.getsize(ruta_pdf)
            self.log_exito(f"PDF ejecutivo generado ({tamaño/1024:.1f} KB)")
            
            # El PDF ejecutivo debe ser más pequeño que el completo
            if tamaño > 5 * 1024 * 1024:  # Más de 5MB es mucho para ejecutivo
                self.log_warning(f"PDF ejecutivo muy grande ({tamaño/1024/1024:.1f} MB)")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error generando PDF ejecutivo: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_generador_pdf_personalizado(self):
        """Test 4: Generar PDF con configuración personalizada"""
        print("\n" + "="*80)
        print("TEST 4: Generador PDF Personalizado")
        print("="*80)
        
        try:
            parcela = Parcela.objects.filter(activa=True).first()
            if not parcela:
                return False
            
            # Configuración personalizada: solo NDVI y NDRE, sin recomendaciones
            config_custom = {
                'nivel_detalle': 'estandar',
                'indices': ['ndvi', 'ndre'],
                'secciones': ['tendencias', 'estadisticas'],
                'personalizacion': {
                    'incluir_imagenes': True,
                    'incluir_graficos': True,
                    'enfoque_especial': 'Análisis enfocado en vigor vegetativo'
                }
            }
            
            print(f"📊 Configuración personalizada:")
            print(json.dumps(config_custom, indent=2))
            
            # Generar PDF
            generador = GeneradorPDFProfesional(configuracion=config_custom)
            ruta_pdf = generador.generar_informe_completo(
                parcela_id=parcela.id,
                meses_atras=12
            )
            
            if not os.path.exists(ruta_pdf):
                self.log_error("PDF personalizado no generado")
                return False
            
            tamaño = os.path.getsize(ruta_pdf)
            self.log_exito(f"PDF personalizado generado ({tamaño/1024:.1f} KB)")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error generando PDF personalizado: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_api_generacion_personalizada(self):
        """Test 5: API de generación personalizada"""
        print("\n" + "="*80)
        print("TEST 5: API de Generación Personalizada")
        print("="*80)
        
        try:
            # Crear usuario de prueba si no existe
            user, created = User.objects.get_or_create(
                username='test_user',
                defaults={'is_superuser': True}
            )
            if created:
                user.set_password('testpass123')
                user.save()
            
            # Login
            login_success = self.client.login(username='test_user', password='testpass123')
            if not login_success:
                self.log_error("No se pudo hacer login")
                return False
            
            self.log_exito("Login exitoso")
            
            # Obtener parcela
            parcela = Parcela.objects.filter(activa=True).first()
            if not parcela:
                self.log_warning("No hay parcelas para probar")
                return False
            
            # Configuración de prueba - usar plantilla completa
            config_test = PLANTILLAS_PREDEFINIDAS.get('completo_default', {}).get('configuracion')
            
            if not config_test:
                self.log_error("Plantilla completo_default no encontrada")
                return False
            
            # Hacer request POST
            response = self.client.post(
                f'/parcelas/{parcela.id}/generar-informe-personalizado/',
                data=json.dumps({
                    'configuracion': config_test,
                    'meses': 12
                }),
                content_type='application/json'
            )
            
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📄 Respuesta: {json.dumps(data, indent=2)}")
                
                if data.get('success'):
                    self.log_exito(f"Informe generado: ID {data.get('informe_id')}")
                    
                    # Verificar que se creó el registro en BD
                    informe = Informe.objects.filter(id=data['informe_id']).first()
                    if informe:
                        self.log_exito("Registro de informe creado en BD")
                        
                        # Verificar que tiene configuración guardada
                        if informe.configuracion:
                            self.log_exito("Configuración guardada en BD")
                        else:
                            self.log_warning("Informe sin configuración guardada")
                        
                        # Verificar archivo PDF
                        if informe.archivo_pdf:
                            ruta_completa = os.path.join(
                                '/Users/sebasflorez16/Documents/AgroTech Historico/historical/media',
                                str(informe.archivo_pdf)
                            )
                            if os.path.exists(ruta_completa):
                                tamaño = os.path.getsize(ruta_completa)
                                self.log_exito(f"Archivo PDF verificado ({tamaño/1024:.1f} KB)")
                            else:
                                self.log_error(f"Archivo PDF no encontrado: {ruta_completa}")
                    else:
                        self.log_error("No se encontró el registro del informe en BD")
                else:
                    self.log_error(f"API retornó error: {data.get('error')}")
                    return False
            else:
                self.log_error(f"Status code inesperado: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data}")
                except:
                    print(f"Response: {response.content.decode()}")
                return False
            
            return True
            
        except Exception as e:
            self.log_error(f"Error probando API: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_compatibilidad_hacia_atras(self):
        """Test 6: Compatibilidad hacia atrás (informes sin configuración)"""
        print("\n" + "="*80)
        print("TEST 6: Compatibilidad Hacia Atrás")
        print("="*80)
        
        try:
            # Generar PDF SIN configuración (debe usar default)
            parcela = Parcela.objects.filter(activa=True).first()
            if not parcela:
                return False
            
            print("📊 Generando PDF sin configuración (None)...")
            generador = GeneradorPDFProfesional(configuracion=None)
            ruta_pdf = generador.generar_informe_completo(
                parcela_id=parcela.id,
                meses_atras=12
            )
            
            if os.path.exists(ruta_pdf):
                self.log_exito("PDF generado sin configuración (compatibilidad OK)")
                return True
            else:
                self.log_error("No se pudo generar PDF sin configuración")
                return False
                
        except Exception as e:
            self.log_error(f"Error en compatibilidad: {str(e)}")
            return False
    
    def ejecutar_todos(self):
        """Ejecuta todos los tests"""
        print("\n" + "🚀 " + "="*78)
        print("🚀 INICIANDO TESTS DEL SISTEMA DE INFORMES PERSONALIZADOS")
        print("🚀 " + "="*78)
        
        tests = [
            self.test_configuraciones_predefinidas,
            self.test_generador_pdf_configuracion_default,
            self.test_generador_pdf_ejecutivo,
            self.test_generador_pdf_personalizado,
            self.test_api_generacion_personalizada,
            self.test_compatibilidad_hacia_atras,
        ]
        
        resultados = []
        for test in tests:
            try:
                resultado = test()
                resultados.append(resultado)
            except Exception as e:
                print(f"\n❌ EXCEPCIÓN EN TEST: {str(e)}")
                import traceback
                traceback.print_exc()
                resultados.append(False)
        
        # Resumen final
        print("\n" + "="*80)
        print("📊 RESUMEN DE RESULTADOS")
        print("="*80)
        
        total_tests = len(resultados)
        tests_exitosos = sum(1 for r in resultados if r)
        tests_fallidos = total_tests - tests_exitosos
        
        print(f"\n✅ Tests exitosos: {tests_exitosos}/{total_tests}")
        print(f"❌ Tests fallidos: {tests_fallidos}/{total_tests}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        if self.errores:
            print("\n❌ ERRORES:")
            for error in self.errores:
                print(f"   - {error}")
        
        print("\n" + "="*80)
        
        if tests_fallidos == 0:
            print("🎉 ¡TODOS LOS TESTS PASARON! Sistema 100% funcional")
            return True
        else:
            print(f"⚠️  {tests_fallidos} test(s) fallaron. Revisar errores arriba.")
            return False


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║       🌾 AGROTECH - TEST DE INFORMES PERSONALIZADOS 🌾                   ║
║                                                                           ║
║   Sistema completo de generación de PDFs con configuración personalizada ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    tester = TestInformesPersonalizados()
    exito = tester.ejecutar_todos()
    
    sys.exit(0 if exito else 1)
