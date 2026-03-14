"""
Modelos para el sistema de Demo - Links únicos de prueba
=========================================================
COMPLETAMENTE AISLADO del sistema principal de informes.
No tiene relación con Parcela, IndiceMensual, ni InformeGenerado.

Flujo:
1. Admin crea DemoToken → genera UUID
2. Se envía link por WhatsApp: /demo/<uuid>/
3. Cliente llena formulario → estado 'registrado'
4. Cliente dibuja parcela → se crea DemoLead
5. Ve 3 imágenes NDVI/NDMI/SAVI → token 'usado' (expira)
"""

import uuid
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class DemoToken(models.Model):
    """
    Token único para acceso a demo sin autenticación.
    Generado por admin y enviado por WhatsApp.
    """
    
    ESTADO_CHOICES = [
        ('activo', '🟢 Activo'),
        ('registrado', '📝 Registrado'),
        ('usado', '✅ Usado'),
        ('expirado', '⏰ Expirado'),
    ]
    
    METODO_ENVIO_CHOICES = [
        ('sin_enviar', 'Sin enviar'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('link', 'Solo Link'),
    ]
    
    # Token único (UUID4 = 128 bits, prácticamente imposible de adivinar)
    token = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False,
        db_index=True
    )
    
    # Datos del contacto (se llenan en el formulario de registro)
    nombre_completo = models.CharField(max_length=200, blank=True, default='')
    telefono = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    departamento = models.CharField(max_length=100, blank=True, default='')
    municipio = models.CharField(max_length=100, blank=True, default='')
    
    # Notas internas (el admin las llena al crear el token)
    notas_comerciales = models.TextField(
        blank=True, default='',
        help_text="Notas internas - contexto de la conversación por WhatsApp"
    )
    
    # Datos de envío (cómo se envió el demo)
    metodo_envio = models.CharField(
        max_length=15, choices=METODO_ENVIO_CHOICES, default='sin_enviar'
    )
    telefono_envio = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Teléfono al que se envió el link (WhatsApp)"
    )
    email_envio = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Email al que se envió el link"
    )
    nombre_prospecto = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Nombre del prospecto (se llena al crear, antes de que se registre)"
    )
    fecha_envio = models.DateTimeField(null=True, blank=True)
    
    # Estado y control de expiración
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    
    # Tracking de acceso
    ip_acceso = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Token de Demo'
        verbose_name_plural = 'Tokens de Demo'
    
    def __str__(self):
        nombre = self.nombre_completo or 'Sin registrar'
        return f"Demo {self.token.hex[:8]} - {nombre} ({self.get_estado_display()})"
    
    def save(self, *args, **kwargs):
        """Asigna fecha de expiración por defecto: 7 días"""
        if not self.fecha_expiracion:
            self.fecha_expiracion = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
    
    @property
    def esta_disponible(self):
        """Token válido para usar (activo o registrado, no expirado)"""
        if self.estado in ('usado', 'expirado'):
            return False
        if self.fecha_expiracion and timezone.now() > self.fecha_expiracion:
            self.estado = 'expirado'
            self.save(update_fields=['estado'])
            return False
        return True
    
    @property
    def ya_registro_datos(self):
        """El usuario ya llenó el formulario de registro"""
        return self.estado in ('registrado', 'usado') and self.nombre_completo
    
    @property
    def ya_dibujo_parcela(self):
        """El usuario ya dibujó una parcela en el mapa"""
        return hasattr(self, 'lead') and self.lead.geometria is not None
    
    def registrar_datos_contacto(self, nombre, telefono, email='', departamento='', municipio=''):
        """Guardar datos del formulario de registro"""
        self.nombre_completo = nombre
        self.telefono = telefono
        self.email = email
        self.departamento = departamento
        self.municipio = municipio
        self.estado = 'registrado'
        self.fecha_registro = timezone.now()
        self.save()
    
    def marcar_como_usado(self, ip=None, user_agent=''):
        """Marcar token como usado (el cliente ya vio las imágenes)"""
        self.estado = 'usado'
        self.fecha_uso = timezone.now()
        if ip:
            self.ip_acceso = ip
        if user_agent:
            self.user_agent = user_agent[:500]
        self.save()


class DemoLead(models.Model):
    """
    Parcela dibujada en la demo + imágenes generadas.
    
    AISLADO: No es el modelo Parcela del sistema principal.
    Guarda la geometría para reutilizar si el lead contrata.
    """
    
    # Relación 1:1 con el token
    token = models.OneToOneField(
        DemoToken, on_delete=models.CASCADE, related_name='lead'
    )
    
    # Geometría de la parcela demo (PostGIS)
    geometria = gis_models.PolygonField(srid=4326, null=True, blank=True)
    area_hectareas = models.FloatField(default=0)
    centroide_lat = models.FloatField(default=0)
    centroide_lon = models.FloatField(default=0)
    
    # URLs de imágenes EOSDA (las 3 de la demo)
    # CharField en vez de URLField porque se guardan paths relativos (/media/demo/xxx/ndvi.png)
    ndvi_url = models.CharField(blank=True, default='', max_length=500)
    ndmi_url = models.CharField(blank=True, default='', max_length=500)
    savi_url = models.CharField(blank=True, default='', max_length=500)
    
    # Metadata de la imagen satelital mostrada
    fecha_imagen_satelital = models.DateField(
        null=True, blank=True,
        help_text="Fecha real de captura de la imagen Sentinel-2"
    )
    nubosidad_imagen = models.FloatField(
        null=True, blank=True,
        help_text="Porcentaje de nubosidad de la imagen"
    )
    
    # Conversión comercial
    fecha_demo = models.DateTimeField(auto_now_add=True)
    convertido_a_cliente = models.BooleanField(
        default=False,
        help_text="¿El lead se convirtió en cliente pagante?"
    )
    parcela_real_id = models.IntegerField(
        null=True, blank=True,
        help_text="ID de la Parcela real si se convirtió en cliente"
    )
    
    class Meta:
        ordering = ['-fecha_demo']
        verbose_name = 'Lead de Demo'
        verbose_name_plural = 'Leads de Demo'
    
    def __str__(self):
        nombre = self.token.nombre_completo or f'Lead #{self.id}'
        return f"{nombre} - {self.area_hectareas:.1f}ha"


class DemoEosdaRequest(models.Model):
    """
    Log de cada petición EOSDA realizada por el sistema de demos.
    Permite tracking detallado de costos por demo/lead.
    """
    
    TIPO_CHOICES = [
        ('stats', 'Statistics API'),
        ('imagery', 'Imagery API'),
        ('other', 'Otro'),
    ]
    
    RESULTADO_CHOICES = [
        ('ok', '✅ Exitoso'),
        ('error', '❌ Error'),
        ('timeout', '⏰ Timeout'),
        ('no_data', '⚠️ Sin datos'),
    ]
    
    # Relación con el lead (puede ser null si falla antes de crear lead)
    lead = models.ForeignKey(
        DemoLead, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='eosda_requests'
    )
    token = models.ForeignKey(
        DemoToken, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='eosda_requests'
    )
    
    # Detalles de la petición
    tipo_peticion = models.CharField(max_length=15, choices=TIPO_CHOICES, default='stats')
    endpoint = models.CharField(max_length=200, default='')
    resultado = models.CharField(max_length=15, choices=RESULTADO_CHOICES, default='ok')
    
    # Metadata
    fecha = models.DateTimeField(auto_now_add=True)
    tiempo_respuesta_ms = models.IntegerField(default=0, help_text="Tiempo de respuesta en ms")
    status_code = models.IntegerField(default=0)
    num_escenas = models.IntegerField(default=0, help_text="Escenas devueltas por EOSDA")
    indices_solicitados = models.CharField(
        max_length=50, default='NDVI,NDMI,SAVI',
        help_text="Índices solicitados separados por coma"
    )
    
    # Detalles para debug
    error_detalle = models.TextField(blank=True, default='')
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Request EOSDA Demo'
        verbose_name_plural = 'Requests EOSDA Demo'
    
    def __str__(self):
        nombre = 'Sin lead'
        if self.token and self.token.nombre_completo:
            nombre = self.token.nombre_completo
        elif self.token and self.token.nombre_prospecto:
            nombre = self.token.nombre_prospecto
        return f"EOSDA {self.get_tipo_peticion_display()} - {nombre} ({self.get_resultado_display()})"
    
    @classmethod
    def registrar(cls, lead=None, token=None, tipo='stats', endpoint='', 
                  resultado='ok', tiempo_ms=0, status_code=0, num_escenas=0,
                  indices='NDVI,NDMI,SAVI', error=''):
        """
        Registra una petición EOSDA para demos.
        Método de conveniencia para registrar desde views_demo.py
        """
        return cls.objects.create(
            lead=lead,
            token=token,
            tipo_peticion=tipo,
            endpoint=endpoint,
            resultado=resultado,
            tiempo_respuesta_ms=tiempo_ms,
            status_code=status_code,
            num_escenas=num_escenas,
            indices_solicitados=indices,
            error_detalle=error,
        )
    
    @classmethod
    def stats_globales(cls):
        """
        Devuelve estadísticas globales de uso EOSDA por demos.
        Retorna dict con total_requests, exitosas, fallidas, costo_estimado, etc.
        """
        from django.db.models import Sum, Avg, Count, Q
        
        qs = cls.objects.all()
        total = qs.count()
        exitosas = qs.filter(resultado='ok').count()
        fallidas = qs.exclude(resultado='ok').count()
        
        # Escenas totales procesadas
        escenas_total = qs.filter(resultado='ok').aggregate(
            total=Sum('num_escenas')
        )['total'] or 0
        
        # Tiempo promedio de respuesta (solo exitosas)
        tiempo_promedio = qs.filter(resultado='ok').aggregate(
            promedio=Avg('tiempo_respuesta_ms')
        )['promedio'] or 0
        
        # Requests por mes actual
        ahora = timezone.now()
        primer_dia_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        requests_mes = qs.filter(fecha__gte=primer_dia_mes).count()
        
        # Requests hoy
        hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        requests_hoy = qs.filter(fecha__gte=hoy_inicio).count()
        
        # Demos únicos que usaron EOSDA
        demos_con_eosda = qs.values('token').distinct().count()
        
        # Leads convertidos que usaron EOSDA
        leads_convertidos_eosda = qs.filter(
            lead__convertido_a_cliente=True
        ).values('lead').distinct().count()
        
        # Costo estimado (EOSDA cobra por request o por área — aquí usamos
        # un estimado configurable desde settings)
        costo_por_request = getattr(settings, 'EOSDA_COSTO_POR_REQUEST_USD', 0.01)
        costo_total = round(total * costo_por_request, 2)
        
        # Costo por venta (solo leads convertidos)
        costo_por_venta = 0
        if leads_convertidos_eosda > 0:
            costo_por_venta = round(costo_total / leads_convertidos_eosda, 2)
        
        return {
            'total_requests': total,
            'exitosas': exitosas,
            'fallidas': fallidas,
            'escenas_total': escenas_total,
            'tiempo_promedio_ms': round(tiempo_promedio),
            'requests_mes': requests_mes,
            'requests_hoy': requests_hoy,
            'demos_con_eosda': demos_con_eosda,
            'leads_convertidos_eosda': leads_convertidos_eosda,
            'costo_por_request_usd': costo_por_request,
            'costo_total_usd': costo_total,
            'costo_por_venta_usd': costo_por_venta,
        }
