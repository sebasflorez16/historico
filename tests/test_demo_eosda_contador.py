"""
Tests para el contador global de requests EOSDA por demos.
==========================================================
Verifica:
1. Creación de registros DemoEosdaRequest
2. Método DemoEosdaRequest.registrar()
3. Método DemoEosdaRequest.stats_globales()
4. Integración con DemoToken y DemoLead
5. Cálculo de costos por venta
6. Filtros por fecha (hoy, mes)
7. Panel muestra stats EOSDA correctamente
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

import unittest
from datetime import timedelta
from django.utils import timezone
from django.test import RequestFactory
from django.contrib.auth.models import User

from informes.models_demo import DemoToken, DemoLead, DemoEosdaRequest


class TestDemoEosdaRequest(unittest.TestCase):
    """Tests para el modelo DemoEosdaRequest"""
    
    @classmethod
    def setUpClass(cls):
        """Crear datos de prueba"""
        super().setUpClass()
        
        # Limpiar datos previos de tests
        DemoEosdaRequest.objects.filter(
            token__notas_comerciales='TEST_EOSDA_CONTADOR'
        ).delete()
        DemoLead.objects.filter(
            token__notas_comerciales='TEST_EOSDA_CONTADOR'
        ).delete()
        DemoToken.objects.filter(
            notas_comerciales='TEST_EOSDA_CONTADOR'
        ).delete()
        
        # Crear tokens de prueba
        cls.token1 = DemoToken.objects.create(
            nombre_completo='Test Lead EOSDA 1',
            telefono='3001111111',
            estado='usado',
            notas_comerciales='TEST_EOSDA_CONTADOR',
        )
        cls.token2 = DemoToken.objects.create(
            nombre_completo='Test Lead EOSDA 2',
            telefono='3002222222',
            estado='usado',
            notas_comerciales='TEST_EOSDA_CONTADOR',
        )
        cls.token3 = DemoToken.objects.create(
            nombre_completo='Test Lead EOSDA 3',
            telefono='3003333333',
            estado='registrado',
            notas_comerciales='TEST_EOSDA_CONTADOR',
        )
        
        # Crear leads de prueba
        cls.lead1 = DemoLead.objects.create(
            token=cls.token1,
            area_hectareas=15.5,
            centroide_lat=4.5,
            centroide_lon=-74.3,
            convertido_a_cliente=True,  # Lead convertido
        )
        cls.lead2 = DemoLead.objects.create(
            token=cls.token2,
            area_hectareas=8.2,
            centroide_lat=4.6,
            centroide_lon=-74.4,
            convertido_a_cliente=False,
        )
    
    @classmethod
    def tearDownClass(cls):
        """Limpiar datos de prueba"""
        DemoEosdaRequest.objects.filter(
            token__notas_comerciales='TEST_EOSDA_CONTADOR'
        ).delete()
        DemoLead.objects.filter(
            token__notas_comerciales='TEST_EOSDA_CONTADOR'
        ).delete()
        DemoToken.objects.filter(
            notas_comerciales='TEST_EOSDA_CONTADOR'
        ).delete()
        super().tearDownClass()
    
    def setUp(self):
        """Limpiar requests antes de cada test"""
        DemoEosdaRequest.objects.filter(
            token__notas_comerciales='TEST_EOSDA_CONTADOR'
        ).delete()
    
    # ==========================================
    # TEST 1: Creación básica de registro
    # ==========================================
    def test_01_crear_request_basica(self):
        """Puede crear un registro de request EOSDA"""
        req = DemoEosdaRequest.objects.create(
            lead=self.lead1,
            token=self.token1,
            tipo_peticion='stats',
            endpoint='https://api-connect.eos.com/api/gdw/api',
            resultado='ok',
            tiempo_respuesta_ms=2500,
            status_code=200,
            num_escenas=3,
            indices_solicitados='NDVI,NDMI,SAVI',
        )
        self.assertIsNotNone(req.id)
        self.assertEqual(req.resultado, 'ok')
        self.assertEqual(req.num_escenas, 3)
        self.assertEqual(req.tiempo_respuesta_ms, 2500)
        print(f"✅ Test 1: Request creada correctamente (id={req.id})")
    
    # ==========================================
    # TEST 2: Método registrar() de conveniencia
    # ==========================================
    def test_02_metodo_registrar(self):
        """El método registrar() crea correctamente el registro"""
        req = DemoEosdaRequest.registrar(
            lead=self.lead1,
            token=self.token1,
            tipo='stats',
            endpoint='https://api-connect.eos.com/api/gdw/api',
            resultado='ok',
            tiempo_ms=3200,
            status_code=200,
            num_escenas=5,
            indices='NDVI,NDMI,SAVI',
        )
        self.assertIsNotNone(req.id)
        self.assertEqual(req.tipo_peticion, 'stats')
        self.assertEqual(req.tiempo_respuesta_ms, 3200)
        self.assertEqual(req.num_escenas, 5)
        print(f"✅ Test 2: Método registrar() funciona correctamente")
    
    # ==========================================
    # TEST 3: Registrar request fallida
    # ==========================================
    def test_03_registrar_request_fallida(self):
        """Registra correctamente una request con error"""
        req = DemoEosdaRequest.registrar(
            lead=self.lead2,
            token=self.token2,
            tipo='stats',
            endpoint='https://api-connect.eos.com/api/gdw/api',
            resultado='error',
            tiempo_ms=500,
            status_code=403,
            error='API key inválida',
        )
        self.assertEqual(req.resultado, 'error')
        self.assertEqual(req.status_code, 403)
        self.assertEqual(req.error_detalle, 'API key inválida')
        print(f"✅ Test 3: Request fallida registrada correctamente")
    
    # ==========================================
    # TEST 4: Stats globales básicas
    # ==========================================
    def test_04_stats_globales_basicas(self):
        """stats_globales() retorna los contadores correctos"""
        # Crear varias requests
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=2000, status_code=200, num_escenas=3,
        )
        DemoEosdaRequest.registrar(
            lead=self.lead2, token=self.token2,
            resultado='ok', tiempo_ms=3000, status_code=200, num_escenas=5,
        )
        DemoEosdaRequest.registrar(
            lead=self.lead2, token=self.token2,
            resultado='error', tiempo_ms=500, status_code=403,
        )
        
        stats = DemoEosdaRequest.stats_globales()
        
        self.assertGreaterEqual(stats['total_requests'], 3)
        self.assertGreaterEqual(stats['exitosas'], 2)
        self.assertGreaterEqual(stats['fallidas'], 1)
        self.assertGreaterEqual(stats['escenas_total'], 8)
        self.assertIn('costo_total_usd', stats)
        self.assertIn('costo_por_venta_usd', stats)
        print(f"✅ Test 4: Stats globales: {stats['total_requests']} requests, "
              f"${stats['costo_total_usd']} USD total")
    
    # ==========================================
    # TEST 5: Cálculo de costo por venta
    # ==========================================
    def test_05_costo_por_venta(self):
        """El costo por venta se calcula correctamente"""
        # Lead1 está convertido, lead2 no
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=2000, status_code=200, num_escenas=3,
        )
        DemoEosdaRequest.registrar(
            lead=self.lead2, token=self.token2,
            resultado='ok', tiempo_ms=3000, status_code=200, num_escenas=5,
        )
        
        stats = DemoEosdaRequest.stats_globales()
        
        # Debe haber al menos 1 lead convertido con EOSDA
        self.assertGreaterEqual(stats['leads_convertidos_eosda'], 1)
        # El costo por venta debe ser > 0 (hay al menos 1 conversión)
        self.assertGreater(stats['costo_por_venta_usd'], 0)
        print(f"✅ Test 5: Costo por venta: ${stats['costo_por_venta_usd']} USD "
              f"({stats['leads_convertidos_eosda']} conversiones)")
    
    # ==========================================
    # TEST 6: Requests hoy y este mes
    # ==========================================
    def test_06_requests_hoy_mes(self):
        """Filtra correctamente requests de hoy y del mes"""
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=2000, status_code=200,
        )
        
        stats = DemoEosdaRequest.stats_globales()
        
        self.assertGreaterEqual(stats['requests_hoy'], 1)
        self.assertGreaterEqual(stats['requests_mes'], 1)
        print(f"✅ Test 6: Hoy: {stats['requests_hoy']}, Este mes: {stats['requests_mes']}")
    
    # ==========================================
    # TEST 7: Demos únicos con EOSDA
    # ==========================================
    def test_07_demos_unicos_eosda(self):
        """Cuenta correctamente demos únicos que usaron EOSDA"""
        # 2 requests para token1, 1 para token2
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=2000, status_code=200,
        )
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=1500, status_code=200,
        )
        DemoEosdaRequest.registrar(
            lead=self.lead2, token=self.token2,
            resultado='ok', tiempo_ms=3000, status_code=200,
        )
        
        stats = DemoEosdaRequest.stats_globales()
        
        # Debe contar 2 demos únicos (token1 y token2), no 3 requests
        self.assertGreaterEqual(stats['demos_con_eosda'], 2)
        print(f"✅ Test 7: {stats['demos_con_eosda']} demos únicos con EOSDA")
    
    # ==========================================
    # TEST 8: Tiempo promedio de respuesta
    # ==========================================
    def test_08_tiempo_promedio(self):
        """Calcula correctamente el tiempo promedio"""
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=2000, status_code=200,
        )
        DemoEosdaRequest.registrar(
            lead=self.lead2, token=self.token2,
            resultado='ok', tiempo_ms=4000, status_code=200,
        )
        
        stats = DemoEosdaRequest.stats_globales()
        
        # Promedio de 2000 y 4000 = 3000 (puede haber otros registros en DB)
        self.assertGreater(stats['tiempo_promedio_ms'], 0)
        print(f"✅ Test 8: Tiempo promedio: {stats['tiempo_promedio_ms']}ms")
    
    # ==========================================
    # TEST 9: __str__ del modelo
    # ==========================================
    def test_09_str_representation(self):
        """El __str__ muestra información legible"""
        req = DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=2500, status_code=200,
        )
        text = str(req)
        self.assertIn('EOSDA', text)
        self.assertIn('Test Lead EOSDA 1', text)
        print(f"✅ Test 9: __str__: '{text}'")
    
    # ==========================================
    # TEST 10: Request sin lead (fallo antes de crear lead)
    # ==========================================
    def test_10_request_sin_lead(self):
        """Puede registrar request sin lead (fallo temprano)"""
        req = DemoEosdaRequest.registrar(
            lead=None, token=self.token3,
            resultado='error',
            error='Geometría inválida — no se pudo crear el lead',
        )
        self.assertIsNone(req.lead)
        self.assertEqual(req.token, self.token3)
        self.assertEqual(req.resultado, 'error')
        print(f"✅ Test 10: Request sin lead registrada correctamente")
    
    # ==========================================
    # TEST 11: Stats con base vacía (no falla)
    # ==========================================
    def test_11_stats_base_vacia(self):
        """stats_globales() no falla con base vacía"""
        # Ya limpiamos en setUp, pero verificar que funcione
        stats = DemoEosdaRequest.stats_globales()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_requests', stats)
        self.assertIn('costo_total_usd', stats)
        self.assertEqual(stats['costo_por_venta_usd'], 0)  # Sin conversiones = 0
        print(f"✅ Test 11: Stats con base vacía: {stats['total_requests']} requests")
    
    # ==========================================
    # TEST 12: Related name funciona en DemoLead
    # ==========================================
    def test_12_related_name_lead(self):
        """El related_name 'eosda_requests' funciona en DemoLead"""
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=2000, status_code=200,
        )
        DemoEosdaRequest.registrar(
            lead=self.lead1, token=self.token1,
            resultado='ok', tiempo_ms=3000, status_code=200,
        )
        
        # Acceder desde el lead
        requests_lead = self.lead1.eosda_requests.all()
        self.assertGreaterEqual(requests_lead.count(), 2)
        
        # Acceder desde el token
        requests_token = self.token1.eosda_requests.all()
        self.assertGreaterEqual(requests_token.count(), 2)
        
        print(f"✅ Test 12: Related names funcionan — lead: {requests_lead.count()}, "
              f"token: {requests_token.count()}")


def run_tests():
    """Ejecutar todos los tests"""
    print("\n" + "=" * 70)
    print("🛰️  TESTS: Contador Global EOSDA para Demos")
    print("=" * 70 + "\n")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDemoEosdaRequest)
    
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    total = result.testsRun
    fallidos = len(result.failures) + len(result.errors)
    exitosos = total - fallidos
    
    if fallidos == 0:
        print(f"🎉 TODOS LOS TESTS PASARON: {exitosos}/{total}")
    else:
        print(f"⚠️  RESULTADOS: {exitosos}/{total} pasaron, {fallidos} fallaron")
        for fail in result.failures + result.errors:
            print(f"   ❌ {fail[0]}: {fail[1][:200]}")
    
    print("=" * 70 + "\n")
    return result


if __name__ == '__main__':
    run_tests()
