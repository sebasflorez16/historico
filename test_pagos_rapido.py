#!/usr/bin/env python
"""🧪 TEST RÁPIDO - Sistema de Pagos"""
import os, sys, django
from decimal import Decimal
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from informes.models import Parcela, Informe
from informes.models_clientes import ClienteInvitacion
from django.contrib.gis.geos import Polygon

def test(nombre, resultado, esperado=None):
    ok = resultado == esperado if esperado is not None else True
    print(f"{'✅' if ok else '❌'} {nombre}: {resultado}")

print("\n🧪 TEST RÁPIDO DEL SISTEMA DE PAGOS\n")

user, _ = User.objects.get_or_create(username='test_pay', defaults={'is_staff': True})
cliente, _ = ClienteInvitacion.objects.get_or_create(
    token='PAY_TEST',
    defaults={'nombre_cliente': 'Test', 'creado_por': user, 'fecha_expiracion': timezone.now() + timedelta(days=30)}
)
parcela, _ = Parcela.objects.get_or_create(
    nombre='TestPay',
    defaults={'propietario': 'test', 'geometria': Polygon([(-75.5,6.2),(-75.5,6.3),(-75.4,6.3),(-75.4,6.2),(-75.5,6.2)]), 'fecha_inicio_monitoreo': timezone.now().date()}
)

print("TEST 1: Creación con precio")
inf = Informe.objects.create(parcela=parcela, cliente=cliente, periodo_analisis_meses=12, fecha_inicio_analisis=timezone.now().date()-timedelta(365), fecha_fin_analisis=timezone.now().date(), resumen_ejecutivo="T", precio_base=Decimal('100'), fecha_vencimiento=timezone.now().date()+timedelta(30))
test("Precio final", inf.precio_final, Decimal('100.00'))
test("Estado pendiente", inf.estado_pago, 'pendiente')

print("\nTEST 2: Descuento 20%")
inf.aplicar_descuento(20, "Test")
test("Precio con descuento", inf.precio_final, Decimal('80.00'))

print("\nTEST 3: Pago parcial")
inf.registrar_pago_parcial(30, "TRX")
test("Estado parcial", inf.estado_pago, 'parcial')
test("Saldo", inf.saldo_pendiente, Decimal('50.00'))

print("\nTEST 4: Pagar todo")
inf.registrar_pago_parcial(50)
test("Estado pagado", inf.estado_pago, 'pagado')
test("Saldo cero", inf.saldo_pendiente, Decimal('0.00'))

print("\nTEST 5: Factura")
fac = inf.generar_factura_data()
print(f"  Número: {fac['numero']}")
print(f"  Cliente: {fac['cliente']}")
print(f"  Total: ${fac['precio_final']:,.0f} COP")

print("\n✅ TODOS LOS TESTS COMPLETADOS!\n")

Informe.objects.filter(parcela=parcela).delete()
parcela.delete()
cliente.delete()
