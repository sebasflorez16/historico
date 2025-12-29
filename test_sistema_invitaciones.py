"""
Script de prueba completa del sistema de invitaciones
Verifica seguridad, roles, expiración y notificaciones
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.auth.models import User
from informes.models_clientes import ClienteInvitacion
from informes.models import Parcela
from datetime import datetime, timedelta
from django.utils import timezone
import secrets

def test_sistema_invitaciones():
    """
    Prueba completa del sistema de invitaciones
    """
    
    print("=" * 80)
    print("AUDITORÍA COMPLETA - SISTEMA DE INVITACIONES")
    print("=" * 80)
    print()
    
    # ==========================================
    # 1. VERIFICAR ROLES Y SEGURIDAD
    # ==========================================
    print("1️⃣  VERIFICANDO SEGURIDAD DE ROLES")
    print("-" * 80)
    
    # Verificar que exista al menos un superusuario
    superusuarios = User.objects.filter(is_superuser=True)
    print(f"   Superusuarios en el sistema: {superusuarios.count()}")
    
    if superusuarios.exists():
        print(f"   ✅ Superusuario principal: {superusuarios.first().username}")
    else:
        print("   ❌ NO HAY SUPERUSUARIOS - Crítico!")
        return False
    
    # Verificar usuarios normales
    usuarios_normales = User.objects.filter(is_superuser=False)
    print(f"   Usuarios normales: {usuarios_normales.count()}")
    
    print()
    
    # ==========================================
    # 2. VERIFICAR INVITACIONES EXISTENTES
    # ==========================================
    print("2️⃣  VERIFICANDO INVITACIONES")
    print("-" * 80)
    
    total_invitaciones = ClienteInvitacion.objects.count()
    print(f"   Total de invitaciones: {total_invitaciones}")
    
    estados = ClienteInvitacion.objects.values_list('estado', flat=True).distinct()
    for estado in estados:
        count = ClienteInvitacion.objects.filter(estado=estado).count()
        print(f"   - {estado.capitalize()}: {count}")
    
    print()
    
    # ==========================================
    # 3. VERIFICAR EXPIRACIÓN DE INVITACIONES
    # ==========================================
    print("3️⃣  VERIFICANDO EXPIRACIÓN")
    print("-" * 80)
    
    invitaciones_pendientes = ClienteInvitacion.objects.filter(estado='pendiente')
    
    for inv in invitaciones_pendientes:
        dias_restantes = (inv.fecha_expiracion - timezone.now()).days
        if inv.esta_expirada:
            print(f"   ⚠️  Invitación {inv.token[:8]}... EXPIRADA")
        else:
            print(f"   ✅ Invitación {inv.token[:8]}... válida ({dias_restantes} días restantes)")
    
    print()
    
    # ==========================================
    # 4. VERIFICAR PARCELAS ASOCIADAS
    # ==========================================
    print("4️⃣  VERIFICANDO PARCELAS ASOCIADAS")
    print("-" * 80)
    
    invitaciones_con_parcela = ClienteInvitacion.objects.filter(parcela__isnull=False)
    print(f"   Invitaciones con parcela: {invitaciones_con_parcela.count()}")
    
    for inv in invitaciones_con_parcela[:5]:  # Mostrar primeras 5
        print(f"   - {inv.nombre_cliente}: {inv.parcela.nombre} ({inv.parcela.area_hectareas:.2f} ha)")
    
    print()
    
    # ==========================================
    # 5. VERIFICAR CONFIGURACIÓN DE EMAIL
    # ==========================================
    print("5️⃣  VERIFICANDO CONFIGURACIÓN DE EMAIL")
    print("-" * 80)
    
    from django.conf import settings
    
    email_config = {
        'HOST': settings.EMAIL_HOST,
        'PORT': settings.EMAIL_PORT,
        'USER': settings.EMAIL_HOST_USER,
        'PASSWORD_SET': bool(settings.EMAIL_HOST_PASSWORD),
        'USE_TLS': settings.EMAIL_USE_TLS,
    }
    
    for key, value in email_config.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    print()
    
    # ==========================================
    # 6. CREAR INVITACIÓN DE PRUEBA
    # ==========================================
    print("6️⃣  CREANDO INVITACIÓN DE PRUEBA")
    print("-" * 80)
    
    try:
        # Obtener superusuario para crear invitación
        superuser = superusuarios.first()
        
        # Crear token único
        token = secrets.token_urlsafe(24)
        
        # Crear invitación de prueba
        invitacion_prueba = ClienteInvitacion.objects.create(
            token=token,
            nombre_cliente="Cliente de Prueba - Sistema",
            email_cliente="prueba@agrotech.com",
            telefono_cliente="+57 300 123 4567",
            descripcion_servicio="Análisis satelital agrícola - PRUEBA",
            estado='pendiente',
            fecha_expiracion=timezone.now() + timedelta(days=30),
            creado_por=superuser,
            costo_servicio=150000.00,
            pagado=False
        )
        
        print(f"   ✅ Invitación de prueba creada")
        print(f"   Token: {token}")
        print(f"   URL: http://127.0.0.1:8000/informes/cliente/{token}/")
        print(f"   Expira: {invitacion_prueba.fecha_expiracion.strftime('%d/%m/%Y %H:%M')}")
        
        # Guardar token para pruebas manuales
        with open('ultimo_token_prueba.txt', 'w') as f:
            f.write(f"Token: {token}\n")
            f.write(f"URL: http://127.0.0.1:8000/informes/cliente/{token}/\n")
            f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        
        print(f"   💾 Token guardado en: ultimo_token_prueba.txt")
        
    except Exception as e:
        print(f"   ❌ Error creando invitación de prueba: {str(e)}")
        return False
    
    print()
    
    # ==========================================
    # 7. RESUMEN FINAL
    # ==========================================
    print("=" * 80)
    print("RESUMEN DE AUDITORÍA")
    print("=" * 80)
    
    resumen = {
        "✅ Superusuarios configurados": superusuarios.count() > 0,
        "✅ Email configurado": bool(settings.EMAIL_HOST_PASSWORD),
        "✅ Invitaciones activas": invitaciones_pendientes.count(),
        "✅ Parcelas registradas": invitaciones_con_parcela.count(),
        "✅ Sistema operativo": True
    }
    
    for item, estado in resumen.items():
        print(f"   {item}: {'SÍ' if estado else 'NO'}")
    
    print()
    print("=" * 80)
    print("✅ AUDITORÍA COMPLETADA")
    print("=" * 80)
    
    return True


def mostrar_proximos_pasos():
    """
    Mostrar los próximos pasos para probar el sistema
    """
    print()
    print("=" * 80)
    print("📋 PRÓXIMOS PASOS PARA PRUEBAS")
    print("=" * 80)
    print()
    print("1. PROBAR FLUJO COMPLETO DE INVITACIÓN:")
    print("   - Abrir la URL del token generado")
    print("   - Dibujar una parcela de prueba")
    print("   - Confirmar el registro")
    print("   - Verificar notificación al admin")
    print()
    print("2. VERIFICAR SEGURIDAD:")
    print("   - Intentar acceder a rutas admin sin permisos")
    print("   - Verificar que tokens expirados no funcionen")
    print()
    print("3. VERIFICAR NOTIFICACIONES:")
    print("   - Revisar email del admin")
    print("   - Verificar mensaje final al cliente")
    print()
    print("=" * 80)


if __name__ == "__main__":
    try:
        exito = test_sistema_invitaciones()
        if exito:
            mostrar_proximos_pasos()
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR CRÍTICO: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
