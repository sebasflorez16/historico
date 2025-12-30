"""
Script de prueba completa del flujo de registro de parcela
Simula el registro de una parcela por un usuario invitado y verifica:
1. Creación del token de invitación
2. Registro de parcela con datos ficticios
3. Envío de email de notificación al admin
"""
import os
import django
import sys
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.auth.models import User
from informes.models import Parcela
from informes.models_clientes import ClienteInvitacion
from informes.services.email_service import EmailService

def limpiar_datos_prueba():
    """Limpia datos de pruebas anteriores"""
    print("\n=== Limpiando datos de pruebas anteriores ===")
    
    # Eliminar parcelas de prueba
    parcelas_prueba = Parcela.objects.filter(nombre__icontains="Parcela Prueba")
    if parcelas_prueba.exists():
        print(f"Eliminando {parcelas_prueba.count()} parcelas de prueba anteriores...")
        parcelas_prueba.delete()
    
    # Eliminar tokens de prueba
    tokens_prueba = ClienteInvitacion.objects.filter(email_cliente__icontains="prueba@example.com")
    if tokens_prueba.exists():
        print(f"Eliminando {tokens_prueba.count()} tokens de prueba anteriores...")
        tokens_prueba.delete()
    
    print("✓ Datos de prueba limpiados")

def crear_token_invitacion():
    """Crea un token de invitación para la prueba"""
    print("\n=== Paso 1: Creando token de invitación ===")
    
    # Obtener superusuario
    superuser = User.objects.filter(is_superuser=True).first()
    if not superuser:
        print("❌ Error: No hay superusuario en el sistema")
        return None
    
    print(f"Superusuario: {superuser.username}")
    
    # Generar token único
    import secrets
    token_str = secrets.token_urlsafe(24)
    
    # Crear token
    token = ClienteInvitacion.objects.create(
        token=token_str,
        nombre_cliente="Juan Pérez Agricultor",
        email_cliente="prueba@example.com",
        telefono_cliente="+57 300 123 4567",
        descripcion_servicio="Análisis satelital agrícola - Prueba",
        creado_por=superuser,
        fecha_expiracion=datetime.now() + timedelta(days=7)
    )
    
    print(f"✓ Token creado exitosamente")
    print(f"  - Email: {token.email_cliente}")
    print(f"  - Nombre: {token.nombre_cliente}")
    print(f"  - Token: {token.token}")
    print(f"  - Expira: {token.fecha_expiracion.strftime('%d/%m/%Y %H:%M')}")
    
    return token

def simular_registro_parcela(token):
    """Simula el registro de una parcela"""
    print("\n=== Paso 2: Registrando parcela ===")
    
    from django.contrib.gis.geos import GEOSGeometry
    import json
    
    # Datos ficticios de la parcela
    datos_parcela = {
        'nombre': 'Parcela Prueba Test 2025',
        'area_hectareas': 15.5,
        'poligono_geojson': {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-75.5636, 6.2518],
                    [-75.5636, 6.2600],
                    [-75.5500, 6.2600],
                    [-75.5500, 6.2518],
                    [-75.5636, 6.2518]
                ]]
            },
            "properties": {}
        }
    }
    
    # Convertir GeoJSON a geometría PostGIS
    geometria = GEOSGeometry(json.dumps(datos_parcela['poligono_geojson']['geometry']))
    
    from django.utils import timezone
    
    # Crear la parcela
    parcela = Parcela.objects.create(
        nombre=datos_parcela['nombre'],
        propietario=token.nombre_cliente,
        geometria=geometria,
        coordenadas=json.dumps(datos_parcela['poligono_geojson']),
        area_hectareas=datos_parcela['area_hectareas'],
        fecha_inicio_monitoreo=timezone.now().date()
    )
    
    print(f"✓ Parcela registrada exitosamente")
    print(f"  - Nombre: {parcela.nombre}")
    print(f"  - Área: {parcela.area_hectareas} hectáreas")
    print(f"  - Propietario: {parcela.propietario}")
    
    # Marcar token como usado usando el método del modelo
    token.marcar_como_utilizada(parcela)
    print(f"✓ Token marcado como usado")
    
    return parcela

def enviar_notificacion_admin(parcela, token):
    """Envía email de notificación al administrador"""
    print("\n=== Paso 3: Enviando notificación al administrador ===")
    
    email_service = EmailService()
    
    # Email del administrador (del superusuario)
    admin_email = token.creado_por.email
    if not admin_email:
        # Usar el email configurado por defecto
        admin_email = "agrotechdigitalcolombia@gmail.com"
    
    print(f"Enviando email a: {admin_email}")
    
    try:
        resultado = email_service.notificar_nueva_parcela_admin(token, parcela)
        
        if resultado.get('exito'):
            print("✓ Email de notificación enviado exitosamente")
            print(f"  - Destinatario: {admin_email}")
            print(f"  - Asunto: Nueva parcela registrada - {parcela.nombre}")
            return True
        else:
            print("❌ Error al enviar email de notificación")
            return False
            
    except Exception as e:
        print(f"❌ Error al enviar email: {str(e)}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("PRUEBA COMPLETA DE REGISTRO DE PARCELA")
    print("=" * 60)
    
    try:
        # Limpiar datos previos
        limpiar_datos_prueba()
        
        # Paso 1: Crear token de invitación
        token = crear_token_invitacion()
        if not token:
            return
        
        # Paso 2: Simular registro de parcela
        parcela = simular_registro_parcela(token)
        
        # Paso 3: Enviar notificación al admin
        email_enviado = enviar_notificacion_admin(parcela, token)
        
        # Resumen final
        print("\n" + "=" * 60)
        print("RESUMEN DE LA PRUEBA")
        print("=" * 60)
        print(f"Token creado: ✓")
        print(f"Parcela registrada: ✓")
        print(f"Email enviado: {'✓' if email_enviado else '❌'}")
        print("\n📧 Revisa tu bandeja de entrada en:")
        print("   agrotechdigitalcolombia@gmail.com")
        print("\n" + "=" * 60)
        
        if email_enviado:
            print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE")
            print("\nDatos de la parcela creada:")
            print(f"ID: {parcela.id}")
            print(f"Nombre: {parcela.nombre}")
            print(f"Propietario: {parcela.propietario}")
            print(f"Área: {parcela.area_hectareas:.2f} ha")
            print(f"Fecha de registro: {parcela.fecha_registro.strftime('%d/%m/%Y %H:%M')}")
        else:
            print("\n⚠️  PRUEBA COMPLETADA CON ADVERTENCIAS")
            print("La parcela se creó pero no se pudo enviar el email")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
