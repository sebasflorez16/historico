"""
Modelos de gestión de clientes y registros económicos
"""

from django.db import models
from django.utils import timezone

class ClienteInvitacion(models.Model):
    """
    Sistema de invitaciones para clientes con gestión económica
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('utilizada', 'Utilizada'),
        ('expirada', 'Expirada'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Datos de la invitación
    token = models.CharField(max_length=32, unique=True)
    nombre_cliente = models.CharField(max_length=200)
    email_cliente = models.EmailField(blank=True, null=True)
    telefono_cliente = models.CharField(max_length=20, blank=True, null=True)
    descripcion_servicio = models.TextField(default='Análisis satelital agrícola', blank=True)
    
    # Control de estado
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    fecha_utilizacion = models.DateTimeField(blank=True, null=True)
    
    # Usuario administrativo que creó la invitación
    creado_por = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    # Datos económicos
    costo_servicio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    notas_pago = models.TextField(blank=True, null=True)
    
    # Parcela asociada (cuando se registre)
    parcela = models.OneToOneField('informes.Parcela', on_delete=models.SET_NULL, blank=True, null=True, related_name='invitacion_cliente')
    
    class Meta:
        verbose_name = "Invitación de Cliente"
        verbose_name_plural = "Invitaciones de Clientes"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre_cliente} - {self.get_estado_display()}"
    
    @property
    def esta_expirada(self):
        """Verificar si la invitación ha expirado"""
        return timezone.now() > self.fecha_expiracion and self.estado == 'pendiente'
    
    @property
    def url_invitacion(self):
        """URL completa de la invitación"""
        from django.urls import reverse
        return reverse('informes:registro_invitacion', kwargs={'token': self.token})
    
    def marcar_como_utilizada(self, parcela=None):
        """Marcar invitación como utilizada"""
        self.estado = 'utilizada'
        self.fecha_utilizacion = timezone.now()
        if parcela:
            self.parcela = parcela
        self.save()


class RegistroEconomico(models.Model):
    """
    Registro económico de servicios prestados
    """
    TIPO_SERVICIO_CHOICES = [
        ('analisis_basico', 'Análisis Básico'),
        ('analisis_completo', 'Análisis Completo'),
        ('monitoreo_mensual', 'Monitoreo Mensual'),
        ('informe_personalizado', 'Informe Personalizado'),
        ('consultoria', 'Consultoría'),
    ]
    
    # Relaciones
    invitacion = models.ForeignKey(ClienteInvitacion, on_delete=models.CASCADE, related_name='registros_economicos')
    parcela = models.ForeignKey('informes.Parcela', on_delete=models.CASCADE, related_name='registros_economicos')
    
    # Datos del servicio
    tipo_servicio = models.CharField(max_length=30, choices=TIPO_SERVICIO_CHOICES, default='analisis_basico')
    descripcion = models.TextField()
    
    # Datos económicos
    valor_servicio = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Porcentaje
    valor_final = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Control de pagos
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    metodo_pago = models.CharField(max_length=100, blank=True, null=True)
    referencia_pago = models.CharField(max_length=200, blank=True, null=True)
    
    # Control temporal
    fecha_servicio = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Registro Económico"
        verbose_name_plural = "Registros Económicos"
        ordering = ['-fecha_servicio']
    
    def save(self, *args, **kwargs):
        """Calcular valor final al guardar"""
        if self.descuento > 0:
            descuento_valor = self.valor_servicio * (self.descuento / 100)
            self.valor_final = self.valor_servicio - descuento_valor
        else:
            self.valor_final = self.valor_servicio
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_tipo_servicio_display()} - {self.invitacion.nombre_cliente} - ${self.valor_final}"