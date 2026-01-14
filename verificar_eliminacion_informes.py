#!/usr/bin/env python
"""
Script de verificación para la funcionalidad de eliminación de informes
en la vista de facturación (arqueo_caja).
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Informe
from django.contrib.auth.models import User

def verificar_eliminacion():
    """Verificar que la vista de eliminación está correctamente configurada"""
    
    print("🔍 Verificando configuración de eliminación de informes...\n")
    
    # 1. Verificar que existen informes
    total_informes = Informe.objects.count()
    print(f"✅ Total de informes en la base de datos: {total_informes}")
    
    # 2. Verificar que existen usuarios superusuarios
    superusers = User.objects.filter(is_superuser=True)
    print(f"✅ Superusuarios configurados: {superusers.count()}")
    for su in superusers:
        print(f"   - {su.username}")
    
    # 3. Listar algunos informes para pruebas
    if total_informes > 0:
        print("\n📋 Últimos 5 informes generados:")
        informes = Informe.objects.order_by('-fecha_generacion')[:5]
        for informe in informes:
            pdf_path = str(informe.archivo_pdf) if informe.archivo_pdf else None
            estado_pdf = "✅ Existe" if pdf_path and os.path.exists(pdf_path) else "❌ No existe"
            print(f"   ID {informe.id}: {informe.parcela.nombre} - {informe.fecha_generacion.strftime('%d/%m/%Y')} - PDF: {estado_pdf}")
    
    # 4. Verificar configuración CSRF
    from django.conf import settings
    print(f"\n🔒 Configuración CSRF:")
    print(f"   - CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}")
    print(f"   - CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}")
    print(f"   - CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
    
    if settings.CSRF_COOKIE_HTTPONLY:
        print("   ⚠️  CSRF_COOKIE_HTTPONLY está en True")
        print("   ℹ️  Esto es correcto - usamos {{ csrf_token }} en el template en lugar de cookies")
    
    print("\n✅ Verificación completada.")
    print("\n📝 Para probar la eliminación:")
    print("   1. Inicia el servidor: python manage.py runserver")
    print("   2. Accede a: http://localhost:8000/informes/arqueo-caja/")
    print("   3. Haz clic en el botón 🗑️ de cualquier informe")
    print("   4. Confirma la eliminación")
    print("   5. Verifica que el informe fue eliminado y el PDF borrado")

if __name__ == '__main__':
    try:
        verificar_eliminacion()
    except Exception as e:
        print(f"❌ Error durante la verificación: {str(e)}")
        sys.exit(1)
