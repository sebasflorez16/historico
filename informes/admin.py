"""
Configuración del administrador Django para AgroTech Histórico
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    Parcela, IndiceMensual, Informe, ConfiguracionAPI,
    ConfiguracionReporte, CacheDatosEOSDA, EstadisticaUsoEOSDA
)


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo Parcela
    """
    list_display = ('nombre', 'propietario', 'tipo_cultivo', 'area_hectareas', 
                    'fecha_registro', 'activa', 'estado_monitoreo')
    list_filter = ('activa', 'tipo_cultivo', 'fecha_registro')
    search_fields = ('nombre', 'propietario', 'tipo_cultivo')
    date_hierarchy = 'fecha_registro'
    ordering = ('-fecha_registro',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'propietario', 'tipo_cultivo', 'activa')
        }),
        ('Localización', {
            'fields': ('poligono_geojson', 'area_hectareas'),
            'description': 'Coordenadas en formato GeoJSON'
        }),
        ('Monitoreo', {
            'fields': ('fecha_inicio_monitoreo', 'fecha_fin_monitoreo')
        }),
        ('Información Adicional', {
            'fields': ('notas',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('area_hectareas', 'fecha_registro')
    
    def estado_monitoreo(self, obj):
        """Estado visual del monitoreo"""
        if obj.activa:
            if obj.fecha_fin_monitoreo and obj.fecha_fin_monitoreo < obj.fecha_registro.date():
                return format_html('<span class="badge badge-warning">Finalizado</span>')
            return format_html('<span class="badge badge-success">Activo</span>')
        return format_html('<span class="badge badge-danger">Inactivo</span>')
    
    estado_monitoreo.short_description = "Estado"
    
    actions = ['activar_parcelas', 'desactivar_parcelas']
    
    def activar_parcelas(self, request, queryset):
        count = queryset.update(activa=True)
        self.message_user(request, f'{count} parcelas activadas.')
    activar_parcelas.short_description = "Activar parcelas seleccionadas"
    
    def desactivar_parcelas(self, request, queryset):
        count = queryset.update(activa=False)
        self.message_user(request, f'{count} parcelas desactivadas.')
    desactivar_parcelas.short_description = "Desactivar parcelas seleccionadas"


@admin.register(IndiceMensual)
class IndiceMensualAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo IndiceMensual
    """
    list_display = ('parcela', 'periodo_display', 'ndvi_promedio', 
                    'ndmi_promedio', 'savi_promedio', 'calidad_datos', 'fecha_consulta_api')
    list_filter = ('calidad_datos', 'fuente_datos', 'año', 'mes')
    search_fields = ('parcela__nombre', 'parcela__propietario')
    date_hierarchy = 'fecha_consulta_api'
    ordering = ('-año', '-mes', 'parcela__nombre')
    
    fieldsets = (
        ('Información del Período', {
            'fields': ('parcela', 'año', 'mes')
        }),
        ('Índices de Vegetación', {
            'fields': (
                ('ndvi_promedio', 'ndvi_maximo', 'ndvi_minimo'),
                ('ndmi_promedio', 'ndmi_maximo', 'ndmi_minimo'),
                ('savi_promedio', 'savi_maximo', 'savi_minimo'),
            )
        }),
        ('Datos Climatológicos', {
            'fields': (
                ('temperatura_promedio', 'temperatura_maxima', 'temperatura_minima'),
                ('precipitacion_total', 'nubosidad_promedio'),
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fuente_datos', 'calidad_datos', 'fecha_consulta_api'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('fecha_consulta_api',)
    
    def periodo_display(self, obj):
        """Mostrar período en formato legible"""
        return obj.periodo_texto
    periodo_display.short_description = "Período"
    periodo_display.admin_order_field = 'año'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parcela')


@admin.register(Informe)
class InformeAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo Informe
    """
    list_display = ('titulo_corto', 'parcela', 'periodo_analisis_meses', 
                    'fecha_generacion', 'estado_salud', 'tiene_pdf')
    list_filter = ('periodo_analisis_meses', 'fecha_generacion')
    search_fields = ('titulo', 'parcela__nombre', 'resumen_ejecutivo')
    date_hierarchy = 'fecha_generacion'
    ordering = ('-fecha_generacion',)
    
    fieldsets = (
        ('Información del Informe', {
            'fields': ('titulo', 'parcela', 'periodo_analisis_meses')
        }),
        ('Período de Análisis', {
            'fields': ('fecha_inicio_analisis', 'fecha_fin_analisis')
        }),
        ('Contenido del Análisis', {
            'fields': ('resumen_ejecutivo', 'analisis_tendencias', 
                      'conclusiones_ia', 'recomendaciones')
        }),
        ('Estadísticas Calculadas', {
            'fields': (
                ('ndvi_promedio_periodo', 'ndmi_promedio_periodo', 'savi_promedio_periodo'),
            ),
            'classes': ('collapse',)
        }),
        ('Archivos Generados', {
            'fields': ('archivo_pdf', 'mapa_ndvi_imagen', 'grafico_tendencias'),
            'classes': ('collapse',)
        }),
        ('Metadatos Técnicos', {
            'fields': ('version_algoritmo', 'tiempo_procesamiento'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('fecha_generacion',)
    
    def titulo_corto(self, obj):
        """Título truncado para la lista"""
        return obj.titulo[:50] + '...' if len(obj.titulo) > 50 else obj.titulo
    titulo_corto.short_description = "Título"
    
    def estado_salud(self, obj):
        """Estado de salud visual"""
        estado = obj.estado_salud_general
        if 'excelente' in estado.lower():
            color = 'success'
        elif 'bueno' in estado.lower():
            color = 'info'
        elif 'regular' in estado.lower():
            color = 'warning'
        else:
            color = 'danger'
        
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, estado
        )
    estado_salud.short_description = "Estado de Salud"
    
    def tiene_pdf(self, obj):
        """Indicador de si tiene archivo PDF"""
        if obj.archivo_pdf:
            return format_html(
                '<a href="{}" target="_blank"><i class="fas fa-file-pdf"></i> Ver PDF</a>',
                obj.archivo_pdf.url
            )
        return format_html('<span class="text-muted">Sin PDF</span>')
    tiene_pdf.short_description = "Archivo PDF"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parcela')


@admin.register(ConfiguracionAPI)
class ConfiguracionAPIAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo ConfiguracionAPI
    """
    list_display = ('nombre_api', 'url_base', 'token_activo', 
                    'consultas_realizadas', 'limite_consultas_diarias', 'fecha_ultima_consulta')
    list_filter = ('token_activo', 'nombre_api')
    
    fieldsets = (
        ('Configuración Básica', {
            'fields': ('nombre_api', 'url_base', 'token_activo')
        }),
        ('Estadísticas de Uso', {
            'fields': ('consultas_realizadas', 'limite_consultas_diarias', 'fecha_ultima_consulta'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('fecha_ultima_consulta', 'consultas_realizadas')


@admin.register(ConfiguracionReporte)
class ConfiguracionReporteAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo ConfiguracionReporte
    """
    list_display = ('parcela', 'get_plan_display', 'periodo_display', 
                    'indices_display', 'costo_estimado', 'reporte_generado')
    list_filter = ('plan', 'reporte_generado', 'incluir_imagenes', 'creado_en')
    search_fields = ('parcela__nombre', 'usuario__username')
    date_hierarchy = 'creado_en'
    ordering = ('-creado_en',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('parcela', 'usuario', 'plan')
        }),
        ('Período de Análisis', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Índices Satelitales', {
            'fields': ('incluir_ndvi', 'incluir_ndmi', 'incluir_savi'),
            'description': 'Seleccione los índices a incluir en el reporte'
        }),
        ('Imágenes Satelitales', {
            'fields': ('incluir_imagenes', 'frecuencia_imagenes', 'max_nubosidad'),
            'classes': ('collapse',)
        }),
        ('Costos y Estado', {
            'fields': ('costo_estimado', 'reporte_generado', 'fecha_generacion'),
        }),
    )
    
    readonly_fields = ('costo_estimado', 'creado_en', 'actualizado_en')
    
    def periodo_display(self, obj):
        """Mostrar período con duración"""
        return f"{obj.fecha_inicio} a {obj.fecha_fin} ({obj.duracion_meses} meses)"
    periodo_display.short_description = "Período"
    
    def indices_display(self, obj):
        """Mostrar índices seleccionados"""
        indices = obj.indices_seleccionados
        if not indices:
            return format_html('<span class="text-muted">Ninguno</span>')
        
        badges = [format_html('<span class="badge badge-info">{}</span>', idx) 
                  for idx in indices]
        return format_html(' '.join([str(b) for b in badges]))
    indices_display.short_description = "Índices"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parcela', 'usuario')


@admin.register(CacheDatosEOSDA)
class CacheDatosEOSDAAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo CacheDatosEOSDA
    """
    list_display = ('field_id', 'periodo_display', 'indices', 
                    'num_escenas', 'calidad_promedio', 'veces_usado', 
                    'es_valido_display', 'creado_en')
    list_filter = ('creado_en', 'usado_en')
    search_fields = ('field_id', 'cache_key', 'indices')
    date_hierarchy = 'creado_en'
    ordering = ('-creado_en',)
    
    fieldsets = (
        ('Identificación', {
            'fields': ('field_id', 'cache_key')
        }),
        ('Período Consultado', {
            'fields': ('fecha_inicio', 'fecha_fin', 'indices')
        }),
        ('Metadatos', {
            'fields': ('task_id', 'num_escenas', 'calidad_promedio'),
        }),
        ('Control de Caché', {
            'fields': ('veces_usado', 'valido_hasta', 'creado_en', 'usado_en'),
        }),
    )
    
    readonly_fields = ('cache_key', 'creado_en', 'usado_en', 'veces_usado')
    
    def periodo_display(self, obj):
        """Mostrar período"""
        return f"{obj.fecha_inicio} a {obj.fecha_fin}"
    periodo_display.short_description = "Período"
    
    def es_valido_display(self, obj):
        """Estado de validez del caché"""
        if obj.es_valido:
            return format_html('<span class="badge badge-success">✅ Válido</span>')
        return format_html('<span class="badge badge-danger">❌ Expirado</span>')
    es_valido_display.short_description = "Estado"
    
    actions = ['limpiar_cache_expirado']
    
    def limpiar_cache_expirado(self, request, queryset):
        """Acción para limpiar cachés expirados"""
        count = CacheDatosEOSDA.limpiar_expirados()
        self.message_user(request, f'{count} cachés expirados eliminados.')
    limpiar_cache_expirado.short_description = "Limpiar cachés expirados"


@admin.register(EstadisticaUsoEOSDA)
class EstadisticaUsoEOSDAAdmin(admin.ModelAdmin):
    """
    Administrador para el modelo EstadisticaUsoEOSDA
    """
    list_display = ('usuario', 'tipo_operacion', 'exitoso_display', 
                    'requests_consumidos_display', 'desde_cache_display', 
                    'tiempo_respuesta', 'creado_en')
    list_filter = ('tipo_operacion', 'exitoso', 'desde_cache', 'creado_en')
    search_fields = ('usuario__username', 'parcela__nombre', 'endpoint')
    date_hierarchy = 'creado_en'
    ordering = ('-creado_en',)
    
    fieldsets = (
        ('Información de Usuario', {
            'fields': ('usuario', 'parcela')
        }),
        ('Operación Realizada', {
            'fields': ('tipo_operacion', 'endpoint', 'metodo')
        }),
        ('Resultado', {
            'fields': ('exitoso', 'codigo_respuesta', 'mensaje_error', 'tiempo_respuesta')
        }),
        ('Métricas de Uso', {
            'fields': ('requests_consumidos', 'desde_cache', 'cache_key'),
        }),
    )
    
    readonly_fields = ('creado_en',)
    
    def exitoso_display(self, obj):
        """Estado visual del resultado"""
        if obj.exitoso:
            return format_html('<span class="badge badge-success">✅ Exitoso</span>')
        return format_html('<span class="badge badge-danger">❌ Error</span>')
    exitoso_display.short_description = "Estado"
    
    def requests_consumidos_display(self, obj):
        """Mostrar requests con énfasis si es alto"""
        if obj.desde_cache:
            return format_html('<span class="badge badge-success">0 (CACHE)</span>')
        elif obj.requests_consumidos > 10:
            return format_html('<span class="badge badge-danger">{}</span>', obj.requests_consumidos)
        elif obj.requests_consumidos > 5:
            return format_html('<span class="badge badge-warning">{}</span>', obj.requests_consumidos)
        return format_html('<span class="badge badge-info">{}</span>', obj.requests_consumidos)
    requests_consumidos_display.short_description = "Requests"
    
    def desde_cache_display(self, obj):
        """Indicador visual de uso de caché"""
        if obj.desde_cache:
            return format_html('<span class="badge badge-success">✅ CACHE</span>')
        return format_html('<span class="text-muted">API</span>')
    desde_cache_display.short_description = "Fuente"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'parcela')


# Personalización del admin site
admin.site.site_header = "AgroTech Histórico - Administración"
admin.site.site_title = "AgroTech Admin"
admin.site.index_title = "Sistema de Análisis Satelital Agrícola"

# CSS personalizado para el admin
admin.site.enable_nav_sidebar = False
