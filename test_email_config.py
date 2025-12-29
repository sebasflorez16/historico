"""
Script de prueba para verificar configuración de email
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.services.email_service import email_service
from django.conf import settings

def test_email_configuration():
    """Probar configuración de email"""
    
    print("=" * 70)
    print("PRUEBA DE CONFIGURACIÓN DE EMAIL - AGROTECH HISTÓRICO")
    print("=" * 70)
    print()
    
    # 1. Validar configuración
    print("1️⃣  Validando configuración de email...")
    print("-" * 70)
    
    validacion = email_service.validar_configuracion_email()
    
    if validacion['valido']:
        print("✅ Configuración válida")
        print(f"   {validacion['mensaje']}")
    else:
        print("❌ Configuración inválida")
        print(f"   Error: {validacion['error']}")
        return False
    
    print()
    
    # 2. Mostrar configuración actual
    print("2️⃣  Configuración actual:")
    print("-" * 70)
    print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"   EMAIL_PASSWORD: {'*' * 10}... (configurada: {bool(settings.EMAIL_HOST_PASSWORD)})")
    print()
    
    # 3. Probar envío de email
    print("3️⃣  Probando envío de email de prueba...")
    print("-" * 70)
    
    # Email de destino para la prueba
    email_destino = input("Ingrese el email de destino para la prueba (Enter para usar agrotechdigitalcolombia@gmail.com): ").strip()
    if not email_destino:
        email_destino = "agrotechdigitalcolombia@gmail.com"
    
    print(f"   Enviando email a: {email_destino}...")
    
    resultado = email_service.probar_configuracion_email(email_destino)
    
    print()
    if resultado['exito']:
        print("✅ Email enviado exitosamente")
        print(f"   {resultado['mensaje']}")
        print()
        print("👉 Revisa tu bandeja de entrada (y carpeta de spam)")
        return True
    else:
        print("❌ Error al enviar email")
        print(f"   {resultado['error']}")
        print()
        print("🔍 Posibles soluciones:")
        print("   1. Verifica que la contraseña de aplicación sea correcta")
        print("   2. Asegúrate de tener conexión a internet")
        print("   3. Verifica que la cuenta de Gmail tenga 2FA activado")
        print("   4. Genera una nueva contraseña de aplicación si es necesario")
        return False

if __name__ == "__main__":
    try:
        exito = test_email_configuration()
        print()
        print("=" * 70)
        if exito:
            print("🎉 PRUEBA COMPLETADA EXITOSAMENTE")
        else:
            print("⚠️  PRUEBA COMPLETADA CON ERRORES")
        print("=" * 70)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ERROR CRÍTICO: {str(e)}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
