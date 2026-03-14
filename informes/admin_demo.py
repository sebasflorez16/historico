"""
Admin para gestión de Demos - Generación de tokens y seguimiento de leads
=========================================================================
Desde aquí el admin genera tokens, copia links y hace seguimiento comercial.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models_demo import DemoToken, DemoLead, DemoEosdaRequest


@admin.register(DemoToken)
class DemoTokenAdmin(admin.ModelAdmin):
    list_display = [
        'token_corto', 'nombre_completo', 'telefono', 'departamento',
        'estado_badge', 'fecha_creacion', 'link_whatsapp'
    ]
    list_filter = ['estado', 'departamento', 'fecha_creacion']
    search_fields = ['nombre_completo', 'telefono', 'email', 'notas_comerciales']
    readonly_fields = [
        'token', 'fecha_creacion', 'fecha_registro', 'fecha_uso',
        'ip_acceso', 'user_agent', 'link_demo_display'
    ]
    
    fieldsets = (
        ('🔗 Link de Demo', {
            'fields': ('token', 'link_demo_display', 'estado', 'fecha_expiracion')
        }),
        ('📱 Datos del Contacto (se llenan al registrarse)', {
            'fields': ('nombre_completo', 'telefono', 'email', 'departamento', 'municipio')
        }),
        ('📝 Notas Comerciales', {
            'fields': ('notas_comerciales',)
        }),
        ('📊 Tracking', {
            'fields': ('fecha_creacion', 'fecha_registro', 'fecha_uso', 'ip_acceso', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def token_corto(self, obj):
        return obj.token.hex[:8]
    token_corto.short_description = 'Token'
    
    def estado_badge(self, obj):
        colores = {
            'activo': '#2e7d32', 'registrado': '#1565c0',
            'usado': '#f57c00', 'expirado': '#d32f2f',
        }
        color = colores.get(obj.estado, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def link_demo_display(self, obj):
        """Muestra el link completo para copiar"""
        from django.conf import settings
        base = getattr(settings, 'SITE_URL', '')
        if not base:
            # Intentar construir desde el request o usar Railway
            base = 'https://historical-production.up.railway.app'
        url = f"{base}/demo/{obj.token}/"
        return format_html(
            '<div style="background:#f5f5f5; padding:12px; border-radius:6px; margin:5px 0;">'
            '<code style="font-size:13px; word-break:break-all; display:block; margin-bottom:8px;">{}</code>'
            '<a href="{}" target="_blank" style="background:#2d5a27; color:white; '
            'padding:6px 16px; border-radius:20px; text-decoration:none; font-size:12px; '
            'margin-right:8px;">🔗 Abrir Link</a>'
            '</div>',
            url, url
        )
    link_demo_display.short_description = '🔗 Link de Demo'
    
    def link_whatsapp(self, obj):
        """Botón para enviar el link por WhatsApp"""
        if not obj.esta_disponible:
            return format_html('<span style="color:#999;">—</span>')
        from django.conf import settings
        base = getattr(settings, 'SITE_URL', 'https://historical-production.up.railway.app')
        url = f"{base}/demo/{obj.token}/"
        texto = (
            f"¡Hola! 🌾 Te envío el acceso a tu demo gratuita de análisis "
            f"satelital AgroTech. Podrás dibujar tu parcela y ver imágenes "
            f"satelitales reales de tu terreno: {url}"
        )
        import urllib.parse
        wa_url = f"https://wa.me/?text={urllib.parse.quote(texto)}"
        return format_html(
            '<a href="{}" target="_blank" style="background:#25D366; color:white; '
            'padding:4px 12px; border-radius:15px; text-decoration:none; font-size:11px;">'
            '📤 WhatsApp</a>', wa_url
        )
    link_whatsapp.short_description = 'Enviar'


@admin.register(DemoLead)
class DemoLeadAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_lead', 'telefono_lead', 'area_hectareas',
        'departamento_lead', 'fecha_demo', 'convertido_badge'
    ]
    list_filter = ['convertido_a_cliente', 'fecha_demo']
    readonly_fields = [
        'token', 'geometria', 'area_hectareas', 'centroide_lat', 'centroide_lon',
        'ndvi_url', 'ndmi_url', 'savi_url', 'fecha_imagen_satelital',
        'nubosidad_imagen', 'fecha_demo'
    ]
    actions = ['marcar_como_convertido']
    
    def nombre_lead(self, obj):
        return obj.token.nombre_completo or f'Lead #{obj.id}'
    nombre_lead.short_description = 'Contacto'
    
    def telefono_lead(self, obj):
        return obj.token.telefono or '—'
    telefono_lead.short_description = 'Teléfono'
    
    def departamento_lead(self, obj):
        return obj.token.departamento or '—'
    departamento_lead.short_description = 'Depto.'
    
    def convertido_badge(self, obj):
        if obj.convertido_a_cliente:
            return format_html('<span style="color:#2e7d32; font-weight:bold;">✅ Cliente</span>')
        return format_html('<span style="color:#f57c00;">⏳ Pendiente</span>')
    convertido_badge.short_description = 'Conversión'
    
    @admin.action(description='✅ Marcar como convertido a cliente')
    def marcar_como_convertido(self, request, queryset):
        actualizados = queryset.update(convertido_a_cliente=True)
        self.message_user(request, f'{actualizados} lead(s) marcado(s) como convertido(s).')


@admin.register(DemoEosdaRequest)
class DemoEosdaRequestAdmin(admin.ModelAdmin):
    """Admin para el log de peticiones EOSDA realizadas por demos."""
    
    list_display = [
        'id', 'fecha', 'nombre_demo', 'tipo_peticion', 
        'resultado_badge', 'status_code', 'num_escenas',
        'tiempo_respuesta_ms', 'indices_solicitados',
    ]
    list_filter = ['resultado', 'tipo_peticion', 'fecha']
    search_fields = ['token__nombre_completo', 'token__nombre_prospecto', 'endpoint', 'error_detalle']
    readonly_fields = [
        'lead', 'token', 'tipo_peticion', 'endpoint', 'resultado',
        'fecha', 'tiempo_respuesta_ms', 'status_code', 'num_escenas',
        'indices_solicitados', 'error_detalle',
    ]
    ordering = ['-fecha']
    date_hierarchy = 'fecha'
    
    def nombre_demo(self, obj):
        if obj.token and obj.token.nombre_completo:
            return obj.token.nombre_completo
        elif obj.token and obj.token.nombre_prospecto:
            return f"({obj.token.nombre_prospecto})"
        return f'Token #{obj.token_id or "?"}'
    nombre_demo.short_description = 'Demo'
    
    def resultado_badge(self, obj):
        colores = {
            'ok': '#2e7d32', 'error': '#d32f2f',
            'timeout': '#f57c00', 'no_data': '#ff9800',
        }
        color = colores.get(obj.resultado, '#666')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; '
            'border-radius:10px; font-size:11px;">{}</span>',
            color, obj.get_resultado_display()
        )
    resultado_badge.short_description = 'Resultado'
    
    def has_add_permission(self, request):
        """No se pueden crear manualmente — solo desde el sistema"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo lectura"""
        return False
