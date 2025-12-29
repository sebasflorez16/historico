"""
Script para crear y enviar invitación real por email
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.auth.models import User
from informes.models_clientes import ClienteInvitacion
from informes.services.email_service import email_service
from datetime import timedelta
from django.utils import timezone
import secrets

def crear_y_enviar_invitacion():
    """
    Crear invitación y enviarla por email
    """
    
    print("=" * 80)
    print("CREAR Y ENVIAR INVITACIÓN POR EMAIL")
    print("=" * 80)
    print()
    
    # Datos de la invitación
    nombre_cliente = "Juan Sebastián Flórez Escobar"
    email_cliente = "juansebastianflorezescobar@gmail.com"
    telefono_cliente = "+57 300 123 4567"  # Cambia si quieres
    costo_servicio = 150000.00  # $150,000 COP
    dias_vigencia = 15  # 15 días de vigencia
    
    print("📋 DATOS DE LA INVITACIÓN:")
    print("-" * 80)
    print(f"   Cliente: {nombre_cliente}")
    print(f"   Email: {email_cliente}")
    print(f"   Teléfono: {telefono_cliente}")
    print(f"   Costo: ${costo_servicio:,.2f} COP")
    print(f"   Vigencia: {dias_vigencia} días")
    print()
    
    try:
        # Obtener superusuario
        superuser = User.objects.filter(is_superuser=True).first()
        
        if not superuser:
            print("❌ No se encontró superusuario en el sistema")
            return False
        
        # Crear token único
        token = secrets.token_urlsafe(24)
        
        # Crear invitación
        print("1️⃣  Creando invitación en la base de datos...")
        
        invitacion = ClienteInvitacion.objects.create(
            token=token,
            nombre_cliente=nombre_cliente,
            email_cliente=email_cliente,
            telefono_cliente=telefono_cliente,
            descripcion_servicio="Análisis satelital agrícola - Paquete Básico",
            estado='pendiente',
            fecha_expiracion=timezone.now() + timedelta(days=dias_vigencia),
            creado_por=superuser,
            costo_servicio=costo_servicio,
            pagado=False
        )
        
        print(f"   ✅ Invitación creada con ID: {invitacion.id}")
        print(f"   Token: {token}")
        print()
        
        # Generar URL completa
        url_invitacion = f"http://127.0.0.1:8000/informes/cliente/{token}/"
        
        print("2️⃣  Enviando invitación por email...")
        print(f"   A: {email_cliente}")
        print(f"   URL: {url_invitacion}")
        print()
        
        # Enviar email
        resultado = email_service.enviar_invitacion(invitacion, url_invitacion)
        
        if resultado['exito']:
            print("   ✅ Email enviado exitosamente")
            print(f"   {resultado['mensaje']}")
        else:
            print("   ❌ Error enviando email")
            print(f"   {resultado['error']}")
            return False
        
        print()
        print("=" * 80)
        print("✅ INVITACIÓN CREADA Y ENVIADA EXITOSAMENTE")
        print("=" * 80)
        print()
        print("📧 INFORMACIÓN PARA EL CLIENTE:")
        print("-" * 80)
        print(f"URL de Registro: {url_invitacion}")
        print(f"Vigencia: Hasta {invitacion.fecha_expiracion.strftime('%d/%m/%Y %H:%M')}")
        print(f"Costo del Servicio: ${invitacion.costo_servicio:,.2f} COP")
        print()
        print("📋 PRÓXIMOS PASOS:")
        print("-" * 80)
        print("1. Revisar el email en: juansebastianflorezescobar@gmail.com")
        print("2. Abrir el enlace de la invitación")
        print("3. Registrar una parcela de prueba")
        print("4. Verificar el flujo completo:")
        print("   - Confirmación doble")
        print("   - Creación de parcela")
        print("   - Notificación al admin")
        print("   - Mensaje final y cierre")
        print()
        print("=" * 80)
        
        # Guardar información
        with open('invitacion_real.txt', 'w') as f:
            f.write(f"INVITACIÓN ENVIADA\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"Cliente: {nombre_cliente}\n")
            f.write(f"Email: {email_cliente}\n")
            f.write(f"Token: {token}\n")
            f.write(f"URL: {url_invitacion}\n")
            f.write(f"Fecha Creación: {invitacion.fecha_creacion.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Fecha Expiración: {invitacion.fecha_expiracion.strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Costo: ${invitacion.costo_servicio:,.2f} COP\n")
        
        print("💾 Información guardada en: invitacion_real.txt")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ ERROR: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    crear_y_enviar_invitacion()
