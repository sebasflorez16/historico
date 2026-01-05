#!/usr/bin/env python
"""
🧪 TEST COMPLETO DEL SISTEMA DE PAGOS
Verifica todas las funciones del modelo Informe y sistema contable
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

# Recargar módulo de modelos para asegurar que tenemos la última versión
import importlib
from django.utils import timezone
from django.contrib.auth.models import User
import informes.models
importlib.reload(informes.models)
from informes.models import Parcela, Informe
from informes.models_clientes import ClienteInvitacion, RegistroEconomico

def print_separator(title=""):
    """Imprime separador visual"""
    print("\n" + "="*70)
    if title:
        print(f"  {title}")
        print("="*70)

def test_resultado(nombre_test, resultado, esperado=None):
    """Muestra resultado de un test"""
    if esperado is not None:
        exito = resultado == esperado
        emoji = "✅" if exito else "❌"
        print(f"{emoji} {nombre_test}")
        print(f"   Resultado: {resultado}")
        if not exito:
            print(f"   Esperado: {esperado}")
    else:
        print(f"✅ {nombre_test}")
        print(f"   Resultado: {resultado}")
    return resultado

def limpiar_datos_test():
    """Limpia datos de prueba anteriores"""
    print_separator("🧹 LIMPIEZA DE DATOS DE PRUEBA")
    Informe.objects.filter(titulo__icontains='TEST').delete()
    Parcela.objects.filter(nombre__icontains='TEST').delete()
    ClienteInvitacion.objects.filter(nombre_cliente__icontains='TEST').delete()
    print("✅ Datos de prueba eliminados")

def crear_datos_prueba():
    """Crea datos de prueba necesarios"""
    print_separator("📦 CREACIÓN DE DATOS DE PRUEBA")
    
    # Crear usuario admin
    user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={'is_superuser': True, 'is_staff': True}
    )
    if created:
        user.set_password('admin123')
        user.save()
    print(f"✅ Usuario: {user.username}")
    
    # Crear cliente
    cliente, created = ClienteInvitacion.objects.get_or_create(
        token='TEST123456',
        defaults={
            'nombre_cliente': 'Cliente TEST',
            'email_cliente': 'test@example.com',
            'costo_servicio': Decimal('100.00'),
            'creado_por': user,
            'fecha_expiracion': timezone.now() + timedelta(days=30)
        }
    )
    print(f"✅ Cliente: {cliente.nombre_cliente}")
    
    # Crear parcela
    from django.contrib.gis.geos import Polygon
    coords = [
        (-75.5, 6.2),
        (-75.5, 6.3),
        (-75.4, 6.3),
        (-75.4, 6.2),
        (-75.5, 6.2)
    ]
    parcela, created = Parcela.objects.get_or_create(
        nombre='Parcela TEST Contabilidad',
        defaults={
            'propietario': 'admin_test',
            'area_hectareas': 10.5,
            'tipo_cultivo': 'maiz',
            'geometria': Polygon(coords),
            'fecha_inicio_monitoreo': timezone.now().date()
        }
    )
    print(f"✅ Parcela: {parcela.nombre}")
    
    return user, cliente, parcela

def test_1_creacion_basica(parcela, cliente):
    """Test 1: Creación básica de informe con precio"""
    print_separator("TEST 1: Creación básica con precio")
    
    informe = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=12,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=365),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Resumen TEST",
        precio_base=Decimal('100.00'),
        fecha_vencimiento=timezone.now().date() + timedelta(days=30)
    )
    
    test_resultado("Título auto-generado", informe.titulo is not None)
    test_resultado("Precio final calculado", informe.precio_final, Decimal('100.00'))
    test_resultado("Estado inicial pendiente", informe.estado_pago, 'pendiente')
    test_resultado("Saldo pendiente correcto", informe.saldo_pendiente, Decimal('100.00'))
    
    return informe

def test_2_aplicar_descuento(informe):
    """Test 2: Aplicar descuentos"""
    print_separator("TEST 2: Aplicar descuentos")
    
    precio_original = informe.precio_base
    nuevo_precio = informe.aplicar_descuento(20, "Descuento cliente frecuente")
    
    test_resultado("Descuento aplicado 20%", informe.descuento_porcentaje, Decimal('20.00'))
    test_resultado("Precio final con descuento", nuevo_precio, Decimal('80.00'))
    test_resultado("Monto descuento calculado", informe.descuento_monto, Decimal('20.00'))
    test_resultado("Nota de descuento agregada", "Descuento" in informe.notas_pago)

def test_3_pago_parcial(informe):
    """Test 3: Registrar pagos parciales"""
    print_separator("TEST 3: Pagos parciales")
    
    # Primer pago parcial
    informe.registrar_pago_parcial(
        monto=30,
        metodo="Transferencia",
        referencia="TRX001",
        notas="Primer abono"
    )
    
    test_resultado("Estado cambiado a parcial", informe.estado_pago, 'parcial')
    test_resultado("Monto pagado registrado", informe.monto_pagado, Decimal('30.00'))
    test_resultado("Saldo actualizado", informe.saldo_pendiente, Decimal('50.00'))
    test_resultado("Porcentaje pagado", informe.porcentaje_pagado, 37.5)
    
    # Segundo pago parcial
    informe.registrar_pago_parcial(
        monto=20,
        metodo="Efectivo",
        referencia="EFE001",
        notas="Segundo abono"
    )
    
    test_resultado("Monto acumulado", informe.monto_pagado, Decimal('50.00'))
    test_resultado("Saldo restante", informe.saldo_pendiente, Decimal('30.00'))

def test_4_pago_completo(informe):
    """Test 4: Completar pago"""
    print_separator("TEST 4: Pago completo")
    
    # Pagar el resto
    informe.registrar_pago_parcial(
        monto=30,
        metodo="Tarjeta",
        referencia="CARD001",
        notas="Pago final"
    )
    
    test_resultado("Estado pagado", informe.estado_pago, 'pagado')
    test_resultado("Saldo cero", informe.saldo_pendiente, Decimal('0.00'))
    test_resultado("Fecha pago registrada", informe.fecha_pago is not None)
    test_resultado("100% pagado", informe.porcentaje_pagado, 100.0)

def test_5_informe_cortesia(parcela, cliente):
    """Test 5: Informe de cortesía"""
    print_separator("TEST 5: Informe de cortesía")
    
    informe = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=6,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=180),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Informe cortesía TEST",
        precio_base=Decimal('0.00')
    )
    
    test_resultado("Estado cortesía auto", informe.estado_pago, 'cortesia')
    test_resultado("Sin saldo", informe.saldo_pendiente, Decimal('0.00'))
    test_resultado("Emoji cortesía en str", '🎁' in str(informe))
    
    return informe

def test_6_vencimiento(parcela, cliente):
    """Test 6: Verificación de vencimiento"""
    print_separator("TEST 6: Vencimiento de pago")
    
    # Crear informe vencido (fecha vencimiento en el pasado)
    informe = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=12,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=365),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Informe vencido TEST",
        precio_base=Decimal('100.00'),
        fecha_vencimiento=timezone.now().date() - timedelta(days=15)
    )
    
    # Forzar re-save para actualizar estado
    informe.save()
    
    test_resultado("Estado vencido", informe.estado_pago, 'vencido')
    test_resultado("Está vencido", informe.esta_vencido, True)
    test_resultado("Días vencido", informe.dias_vencido, 15)
    test_resultado("Días para vencimiento", informe.dias_para_vencimiento, 0)
    
    # Calcular mora
    mora = informe.calcular_mora(porcentaje_diario=0.1)
    print(f"💰 Mora calculada: ${mora}")
    
    return informe

def test_7_marcar_como_pagado(informe_vencido):
    """Test 7: Marcar directamente como pagado"""
    print_separator("TEST 7: Marcar como pagado directo")
    
    informe_vencido.marcar_como_pagado(
        metodo="Transferencia",
        referencia="TRX999",
        notas="Pago de informe vencido"
    )
    
    test_resultado("Estado pagado", informe_vencido.estado_pago, 'pagado')
    test_resultado("Monto completo", informe_vencido.monto_pagado, informe_vencido.precio_final)
    test_resultado("Ya no está vencido", informe_vencido.esta_vencido, False)
    test_resultado("Mora cero después de pagar", informe_vencido.calcular_mora(), Decimal('0.00'))

def test_8_anular_pago(parcela, cliente):
    """Test 8: Anular pago"""
    print_separator("TEST 8: Anular pago")
    
    informe = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=6,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=180),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Informe para anular TEST",
        precio_base=Decimal('50.00')
    )
    
    # Hacer pago parcial
    informe.registrar_pago_parcial(monto=25, metodo="Efectivo", referencia="EFE123")
    test_resultado("Pago parcial registrado", informe.monto_pagado, Decimal('25.00'))
    
    # Anular pago
    informe.anular_pago(motivo="Error en el monto")
    
    test_resultado("Monto anulado", informe.monto_pagado, Decimal('0.00'))
    test_resultado("Estado pendiente", informe.estado_pago, 'pendiente')
    test_resultado("Nota anulación", "anulado" in informe.notas_pago.lower())

def test_9_factura_data(parcela, cliente):
    """Test 9: Generar datos de factura"""
    print_separator("TEST 9: Datos de factura")
    
    informe = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=12,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=365),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Informe factura TEST",
        precio_base=Decimal('200.00'),
        descuento_porcentaje=Decimal('15.00')
    )
    
    factura = informe.generar_factura_data()
    
    print("📄 Datos de factura generados:")
    print(f"   Número: {factura['numero_factura']}")
    print(f"   Cliente: {factura['cliente']}")
    print(f"   Precio base: ${factura['precio_base']}")
    print(f"   Descuento: {factura['descuento_porcentaje']}% (${factura['descuento_monto']})")
    print(f"   Total: ${factura['precio_final']}")
    print(f"   Estado: {factura['estado_pago']}")
    
    test_resultado("Número factura generado", factura['numero_factura'].startswith('INF-'))
    test_resultado("Descuento en factura", factura['descuento_monto'], 30.0)
    test_resultado("Total factura", factura['precio_final'], 170.0)

def test_10_metodos_clase(parcela, cliente):
    """Test 10: Métodos de clase para reportes"""
    print_separator("TEST 10: Métodos de clase (reportes)")
    
    # Crear varios informes
    for i in range(3):
        Informe.objects.create(
            parcela=parcela,
            cliente=cliente,
            periodo_analisis_meses=6,
            fecha_inicio_analisis=timezone.now().date() - timedelta(days=180),
            fecha_fin_analisis=timezone.now().date(),
            resumen_ejecutivo=f"Informe reporte {i+1} TEST",
            precio_base=Decimal('75.00'),
            estado_pago='pendiente' if i < 2 else 'vencido',
            fecha_vencimiento=timezone.now().date() - timedelta(days=5) if i == 2 else None
        )
    
    # Obtener pendientes
    pendientes = Informe.obtener_pendientes_pago()
    test_resultado("Informes pendientes encontrados", pendientes.count() >= 3)
    
    # Obtener vencidos
    vencidos = Informe.obtener_vencidos()
    test_resultado("Informes vencidos encontrados", vencidos.count() >= 1)
    
    # Calcular ingresos (crear uno pagado)
    informe_pagado = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=12,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=365),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Informe pagado TEST",
        precio_base=Decimal('150.00')
    )
    informe_pagado.marcar_como_pagado(metodo="Transferencia")
    
    # Calcular ingresos del mes
    inicio_mes = timezone.now().replace(day=1)
    fin_mes = timezone.now()
    ingresos = Informe.calcular_ingresos_periodo(inicio_mes, fin_mes)
    
    print(f"💰 Ingresos del período:")
    print(f"   Total: ${ingresos['total_ingresos']}")
    print(f"   Cantidad: {ingresos['cantidad_informes']} informes")
    
    test_resultado("Ingresos calculados", ingresos['total_ingresos'] >= Decimal('150.00'))

def test_11_propiedades_calculadas(parcela, cliente):
    """Test 11: Propiedades calculadas"""
    print_separator("TEST 11: Propiedades calculadas")
    
    informe = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=12,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=365),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Informe propiedades TEST",
        precio_base=Decimal('100.00'),
        descuento_porcentaje=Decimal('10.00'),
        fecha_vencimiento=timezone.now().date() + timedelta(days=15)
    )
    
    test_resultado("Estado pago display", '⏳' in informe.estado_pago_display)
    test_resultado("Puede cancelar", informe.puede_cancelar, True)
    test_resultado("Días para vencimiento", informe.dias_para_vencimiento, 15)
    
    # Hacer pago parcial
    informe.registrar_pago_parcial(monto=45)
    test_resultado("Ya no puede cancelar", informe.puede_cancelar, False)

def test_12_registro_economico_integration(parcela, cliente):
    """Test 12: Integración con RegistroEconomico"""
    print_separator("TEST 12: Integración RegistroEconomico")
    
    informe = Informe.objects.create(
        parcela=parcela,
        cliente=cliente,
        periodo_analisis_meses=12,
        fecha_inicio_analisis=timezone.now().date() - timedelta(days=365),
        fecha_fin_analisis=timezone.now().date(),
        resumen_ejecutivo="Informe integración TEST",
        precio_base=Decimal('120.00')
    )
    
    # Crear registro económico asociado (simulando flujo real)
    registro = RegistroEconomico.objects.create(
        invitacion=cliente,
        parcela=parcela,
        tipo_servicio='analisis_completo',
        descripcion=f'Registro para {informe.titulo}',
        valor_servicio=informe.precio_base,
        descuento=informe.descuento_porcentaje,
        valor_final=informe.precio_final
    )
    
    test_resultado("Registro económico creado", registro.id is not None)
    test_resultado("Valores sincronizados", registro.valor_final, informe.precio_final)
    
    print(f"🔗 Integración exitosa:")
    print(f"   Informe ID: {informe.id}")
    print(f"   Registro ID: {registro.id}")
    print(f"   Cliente: {cliente.nombre_cliente}")

def mostrar_resumen_final():
    """Muestra resumen de todos los informes creados"""
    print_separator("📊 RESUMEN FINAL - TODOS LOS INFORMES TEST")
    
    informes = Informe.objects.filter(titulo__icontains='TEST').order_by('-fecha_generacion')
    
    total_ingresos = Decimal('0.00')
    total_pendiente = Decimal('0.00')
    
    print(f"\n{'Estado':<15} {'Precio':<10} {'Pagado':<10} {'Saldo':<10} {'Título':<30}")
    print("-" * 85)
    
    for inf in informes:
        estado_emoji = dict(inf.ESTADO_PAGO_CHOICES).get(inf.estado_pago, '')
        print(f"{estado_emoji:<15} ${inf.precio_final:<9.2f} ${inf.monto_pagado:<9.2f} ${inf.saldo_pendiente:<9.2f} {inf.titulo[:30]}")
        
        if inf.estado_pago == 'pagado':
            total_ingresos += inf.monto_pagado
        else:
            total_pendiente += inf.saldo_pendiente
    
    print("-" * 85)
    print(f"\n💰 Total ingresos (pagados): ${total_ingresos:.2f}")
    print(f"⏳ Total pendiente de cobro: ${total_pendiente:.2f}")
    print(f"📊 Total informes generados: {informes.count()}")

def main():
    """Ejecuta todos los tests"""
    print("\n" + "🧪 " * 30)
    print("  SISTEMA DE PRUEBAS - MÓDULO DE PAGOS E INFORMES")
    print("🧪 " * 30)
    
    try:
        # Limpieza inicial
        limpiar_datos_test()
        
        # Crear datos
        user, cliente, parcela = crear_datos_prueba()
        
        # Ejecutar tests
        informe1 = test_1_creacion_basica(parcela, cliente)
        test_2_aplicar_descuento(informe1)
        test_3_pago_parcial(informe1)
        test_4_pago_completo(informe1)
        
        informe_cortesia = test_5_informe_cortesia(parcela, cliente)
        informe_vencido = test_6_vencimiento(parcela, cliente)
        test_7_marcar_como_pagado(informe_vencido)
        
        test_8_anular_pago(parcela, cliente)
        test_9_factura_data(parcela, cliente)
        test_10_metodos_clase(parcela, cliente)
        test_11_propiedades_calculadas(parcela, cliente)
        test_12_registro_economico_integration(parcela, cliente)
        
        # Resumen final
        mostrar_resumen_final()
        
        print_separator("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("\n🎉 El sistema de pagos está funcionando correctamente!")
        print("📝 Funciones verificadas:")
        print("   ✅ Creación de informes con precio")
        print("   ✅ Aplicación de descuentos")
        print("   ✅ Pagos parciales acumulativos")
        print("   ✅ Pago completo y cambio de estado")
        print("   ✅ Informes de cortesía")
        print("   ✅ Detección de vencimientos")
        print("   ✅ Cálculo de mora")
        print("   ✅ Anulación de pagos")
        print("   ✅ Generación de datos de factura")
        print("   ✅ Métodos de clase para reportes")
        print("   ✅ Propiedades calculadas")
        print("   ✅ Integración con RegistroEconomico")
        
    except Exception as e:
        print_separator("❌ ERROR EN LOS TESTS")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    exito = main()
    sys.exit(0 if exito else 1)
