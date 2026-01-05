import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Informe, Parcela, ClienteInvitacion
from decimal import Decimal

print("Test simple del sistema de pagos\n")

# Crear objetos necesarios
parcela = Parcela.objects.first()
if not parcela:
    print("❌ No hay parcelas")
    exit(1)

cliente = ClienteInvitacion.objects.first()

# Test 1: Crear informe con precio
print("1️⃣ Crear informe con precio_base=100")
inf = Informe(
    parcela=parcela,
    cliente=cliente,
    periodo_analisis_meses=12,
    precio_base=Decimal('100.00')
)
print(f"Antes de save():")
print(f"  precio_base: {inf.precio_base}")
print(f"  precio_final: {inf.precio_final}")
print(f"  descuento_porcentaje: {inf.descuento_porcentaje}")

inf.save()

print(f"\nDespués de save():")
print(f"  precio_base: {inf.precio_base}")
print(f"  precio_final: {inf.precio_final}")
print(f"  estado_pago: {inf.estado_pago}")
print(f"  saldo_pendiente: {inf.saldo_pendiente}")

# Test 2: Verificar método aplicar_descuento
print(f"\n2️⃣ Aplicar descuento 20%")
print(f"hasattr(aplicar_descuento): {hasattr(inf, 'aplicar_descuento')}")

if hasattr(inf, 'aplicar_descuento'):
    inf.aplicar_descuento(20, "Descuento test")
    print(f"  descuento_porcentaje: {inf.descuento_porcentaje}")
    print(f"  precio_final: {inf.precio_final}")
    print(f"  Expected: 80.00")

# Test 3: Verificar que save() se llama en cada operación
print(f"\n3️⃣ Verificar estructura del modelo")
print(f"Métodos de pago disponibles:")
for attr in dir(inf):
    if not attr.startswith('_') and callable(getattr(inf, attr)):
        if 'pago' in attr or 'descuento' in attr or 'vencido' in attr:
            print(f"  - {attr}()")

# Limpiar
inf.delete()
print("\n✅ Test completado")
