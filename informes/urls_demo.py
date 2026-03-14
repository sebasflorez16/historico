"""
URLs del sistema Demo - Completamente aisladas del sistema principal
====================================================================
Estas URLs NO requieren autenticación. Solo validación por token UUID.
"""
from django.urls import path
from . import views_demo

app_name = 'demo'

urlpatterns = [
    # Landing: formulario de registro (primera pantalla)
    path('<uuid:token_uuid>/', views_demo.demo_landing, name='landing'),
    
    # API: registrar datos del formulario
    path('<uuid:token_uuid>/registrar/', views_demo.demo_registrar, name='registrar'),
    
    # API: guardar parcela dibujada + obtener imágenes
    path('<uuid:token_uuid>/guardar-parcela/', views_demo.demo_guardar_parcela, name='guardar_parcela'),
    
    # Resultado: ver 3 imágenes + CTA (marca token como usado)
    path('<uuid:token_uuid>/resultado/', views_demo.demo_resultado, name='resultado'),
]
