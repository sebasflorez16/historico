"""
Modelos para configuración de reportes y caché de datos EOSDA
Optimiza el consumo de requests y permite personalización de reportes
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, timedelta
from decimal import Decimal
import json


class PlanReporte(models.TextChoices):
    """Planes predefinidos para reportes históricos"""
    BASICO_6M = 'basico_6m', '6 Meses - Básico'
    ESTANDAR_1Y = 'estandar_1y', '1 Año - Estándar'
    AVANZADO_2Y = 'avanzado_2y', '2 Años - Avanzado'
    PERSONALIZADO = 'personalizado', 'Personalizado'


class ConfiguracionReporte(models.Model):
    """
    Configuración de un reporte personalizado
    Define qué datos solicitar a EOSDA y cómo generarlos
    """
    # Relaciones
    parcela = models.ForeignKey(
        'Parcela',
        on_delete=models.CASCADE,
        related_name='configuraciones_reporte',
        verbose_name='Parcela'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='configuraciones_reporte',
        verbose_name='Usuario'
    )
    
    # Período de análisis
    fecha_inicio = models.DateField(
        verbose_name='Fecha de Inicio',
        help_text='Inicio del período de análisis'
    )
    fecha_fin = models.DateField(
        verbose_name='Fecha de Fin',
        help_text='Fin del período de análisis',
        default=date.today
    )
    
    # Plan seleccionado
    plan = models.CharField(
        max_length=20,
        choices=PlanReporte.choices,
        default=PlanReporte.BASICO_6M,
        verbose_name='Plan'
    )
    
    # Índices a incluir
    incluir_ndvi = models.BooleanField(
        default=True,
        verbose_name='Incluir NDVI',
        help_text='Índice de Vegetación (salud del cultivo)'
    )
    incluir_ndmi = models.BooleanField(
        default=False,
        verbose_name='Incluir NDMI',
        help_text='Índice de Humedad (estrés hídrico)'
    )
    incluir_savi = models.BooleanField(
        default=False,
        verbose_name='Incluir SAVI',
        help_text='Índice Ajustado de Suelo (cobertura)'
    )
    
    # Imágenes satelitales
    incluir_imagenes = models.BooleanField(
        default=False,
        verbose_name='Incluir Imágenes',
        help_text='Imágenes satelitales en el reporte PDF'
    )
    frecuencia_imagenes = models.CharField(
        max_length=20,
        choices=[
            ('mensual', 'Mensual (1 imagen/mes)'),
            ('bimensual', 'Bimensual (1 imagen cada 2 meses)'),
            ('trimestral', 'Trimestral (1 imagen cada 3 meses)')
        ],
        default='mensual',
        verbose_name='Frecuencia de Imágenes'
    )
    
    # Configuración de nubosidad
    max_nubosidad = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Máxima Nubosidad Permitida (%)',
        help_text='Porcentaje máximo de nubes (30% ideal, 50% aceptable)'
    )
    
    # Pricing
    costo_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo Estimado (USD)',
        help_text='Cálculo automático según configuración'
    )
    
    # Metadatos
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    reporte_generado = models.BooleanField(
        default=False,
        verbose_name='Reporte Generado'
    )
    fecha_generacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Generación'
    )
    
    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['parcela', '-creado_en']),
            models.Index(fields=['usuario', '-creado_en']),
        ]
    
    def __str__(self):
        return f"{self.parcela.nombre} - {self.get_plan_display()} ({self.fecha_inicio} a {self.fecha_fin})"
    
    @property
    def duracion_dias(self):
        """Calcula la duración del período en días"""
        return (self.fecha_fin - self.fecha_inicio).days
    
    @property
    def duracion_meses(self):
        """Calcula la duración aproximada en meses"""
        return round(self.duracion_dias / 30)
    
    @property
    def indices_seleccionados(self):
        """Retorna lista de índices seleccionados"""
        indices = []
        if self.incluir_ndvi:
            indices.append('NDVI')
        if self.incluir_ndmi:
            indices.append('NDMI')
        if self.incluir_savi:
            indices.append('SAVI')
        return indices
    
    @property
    def num_indices(self):
        """Cuenta el número de índices seleccionados"""
        return len(self.indices_seleccionados)
    
    def calcular_costo(self):
        """
        Calcula el costo estimado según la configuración
        Precios en USD
        """
        # Precios base por plan
        precios_base = {
            'basico_6m': Decimal('50.00'),
            'estandar_1y': Decimal('80.00'),
            'avanzado_2y': Decimal('140.00'),
        }
        
        # Precios por índice adicional
        precios_indice_adicional = {
            'basico_6m': Decimal('15.00'),
            'estandar_1y': Decimal('10.00'),
            'avanzado_2y': Decimal('8.00'),
        }
        
        # Precios por imágenes
        precios_imagenes = {
            'basico_6m': Decimal('20.00'),
            'estandar_1y': Decimal('30.00'),
            'avanzado_2y': Decimal('50.00'),
        }
        
        if self.plan == PlanReporte.PERSONALIZADO:
            # Cálculo personalizado
            meses = self.duracion_meses
            costo = Decimal('10.00') * meses  # Base: $10/mes
            
            # Agregar costo por índice
            costo += Decimal('8.00') * self.num_indices * meses
            
            # Agregar costo por imágenes
            if self.incluir_imagenes:
                frecuencia_map = {
                    'mensual': meses,
                    'bimensual': meses // 2,
                    'trimestral': meses // 3
                }
                num_imagenes = frecuencia_map.get(self.frecuencia_imagenes, meses)
                costo += Decimal('2.00') * num_imagenes
        else:
            # Plan predefinido
            costo = precios_base.get(self.plan, Decimal('50.00'))
            
            # Índices incluidos por plan
            indices_incluidos = {
                'basico_6m': 1,  # Solo NDVI
                'estandar_1y': 2,  # NDVI + NDMI
                'avanzado_2y': 3,  # NDVI + NDMI + SAVI
            }
            
            # Cobrar por índices adicionales
            num_incluidos = indices_incluidos.get(self.plan, 1)
            if self.num_indices > num_incluidos:
                indices_extra = self.num_indices - num_incluidos
                costo += precios_indice_adicional.get(self.plan, Decimal('15.00')) * indices_extra
            
            # Agregar costo de imágenes
            if self.incluir_imagenes:
                costo += precios_imagenes.get(self.plan, Decimal('20.00'))
        
        self.costo_estimado = costo
        return costo
    
    def save(self, *args, **kwargs):
        """Calcula el costo antes de guardar"""
        self.calcular_costo()
        super().save(*args, **kwargs)


class CacheDatosEOSDA(models.Model):
    """
    Caché de respuestas de EOSDA para evitar requests duplicados
    Almacena datos ya consultados para reutilización
    """
    # Identificación única del request
    field_id = models.CharField(
        max_length=100,
        verbose_name='Field ID de EOSDA',
        db_index=True
    )
    fecha_inicio = models.DateField(
        verbose_name='Fecha Inicio',
        db_index=True
    )
    fecha_fin = models.DateField(
        verbose_name='Fecha Fin',
        db_index=True
    )
    indices = models.CharField(
        max_length=100,
        verbose_name='Índices Solicitados',
        help_text='Formato: ndvi,ndmi,savi'
    )
    
    # Hash único para identificación rápida
    cache_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Clave de Caché',
        help_text='Hash único generado: field_id + fechas + indices'
    )
    
    # Datos almacenados
    datos_json = models.JSONField(
        verbose_name='Datos en JSON',
        help_text='Respuesta completa de EOSDA en formato JSON'
    )
    
    # Metadatos de la petición
    task_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Task ID de EOSDA'
    )
    num_escenas = models.IntegerField(
        default=0,
        verbose_name='Número de Escenas',
        help_text='Cantidad de escenas satelitales retornadas'
    )
    calidad_promedio = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Calidad Promedio',
        help_text='Nubosidad promedio de las escenas (%)'
    )
    
    # Control de caché
    creado_en = models.DateTimeField(auto_now_add=True)
    usado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Último Uso',
        help_text='Actualizado cada vez que se reutiliza el caché'
    )
    veces_usado = models.IntegerField(
        default=0,
        verbose_name='Veces Reutilizado',
        help_text='Contador de cuántas veces se ha reutilizado este caché'
    )
    valido_hasta = models.DateTimeField(
        verbose_name='Válido Hasta',
        help_text='Fecha de expiración del caché (7 días típicamente)'
    )
    
    class Meta:
        verbose_name = 'Caché de Datos EOSDA'
        verbose_name_plural = 'Caché de Datos EOSDA'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['field_id', 'fecha_inicio', 'fecha_fin']),
            models.Index(fields=['cache_key']),
            models.Index(fields=['valido_hasta']),
        ]
    
    def __str__(self):
        return f"Cache {self.field_id} ({self.fecha_inicio} - {self.fecha_fin}) - {self.indices}"
    
    @staticmethod
    def generar_cache_key(field_id: str, fecha_inicio: date, fecha_fin: date, indices: list) -> str:
        """
        Genera una clave única para identificar el caché
        """
        import hashlib
        indices_str = ','.join(sorted(indices))
        data_str = f"{field_id}_{fecha_inicio}_{fecha_fin}_{indices_str}"
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    @property
    def es_valido(self):
        """Verifica si el caché aún es válido"""
        from django.utils import timezone
        return timezone.now() < self.valido_hasta
    
    def incrementar_uso(self):
        """Incrementa el contador de uso y actualiza la fecha"""
        self.veces_usado += 1
        self.save(update_fields=['veces_usado', 'usado_en'])
    
    @classmethod
    def obtener_o_none(cls, field_id: str, fecha_inicio: date, fecha_fin: date, indices: list):
        """
        Busca en caché o retorna None si no existe/expiró
        """
        cache_key = cls.generar_cache_key(field_id, fecha_inicio, fecha_fin, indices)
        try:
            cache_obj = cls.objects.get(cache_key=cache_key)
            if cache_obj.es_valido:
                cache_obj.incrementar_uso()
                return cache_obj.datos_json
            else:
                # Caché expirado, eliminarlo
                cache_obj.delete()
                return None
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def guardar_datos(cls, field_id: str, fecha_inicio: date, fecha_fin: date, 
                     indices: list, datos: dict, task_id: str = None):
        """
        Guarda datos en caché con validez de 7 días
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cache_key = cls.generar_cache_key(field_id, fecha_inicio, fecha_fin, indices)
        indices_str = ','.join(sorted(indices))
        
        # Calcular metadatos
        num_escenas = len(datos.get('resultados', []))
        nubosidades = [r.get('metadatos', {}).get('cloud_coverage', 0) 
                       for r in datos.get('resultados', [])]
        calidad_promedio = sum(nubosidades) / len(nubosidades) if nubosidades else None
        
        # Crear o actualizar caché
        cache_obj, created = cls.objects.update_or_create(
            cache_key=cache_key,
            defaults={
                'field_id': field_id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'indices': indices_str,
                'datos_json': datos,
                'task_id': task_id,
                'num_escenas': num_escenas,
                'calidad_promedio': calidad_promedio,
                'valido_hasta': timezone.now() + timedelta(days=7),
                'veces_usado': 0
            }
        )
        
        return cache_obj
    
    @classmethod
    def limpiar_expirados(cls):
        """
        Elimina cachés expirados (ejecutar periódicamente)
        """
        from django.utils import timezone
        expirados = cls.objects.filter(valido_hasta__lt=timezone.now())
        count = expirados.count()
        expirados.delete()
        return count


class EstadisticaUsoEOSDA(models.Model):
    """
    Registro de uso de la API de EOSDA para monitoreo de costos
    """
    # Identificación
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='estadisticas_eosda',
        verbose_name='Usuario'
    )
    parcela = models.ForeignKey(
        'Parcela',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='estadisticas_eosda',
        verbose_name='Parcela'
    )
    
    # Tipo de operación
    tipo_operacion = models.CharField(
        max_length=50,
        choices=[
            ('field_management', 'Field Management (Crear Campo)'),
            ('statistics', 'Statistics (Obtener Datos)'),
            ('images', 'Images (Imágenes Satelitales)'),
            ('tiles', 'Tiles (Mosaicos)'),
        ],
        verbose_name='Tipo de Operación'
    )
    
    # Detalles
    endpoint = models.CharField(max_length=200, verbose_name='Endpoint')
    metodo = models.CharField(max_length=10, default='POST', verbose_name='Método HTTP')
    
    # Resultado
    exitoso = models.BooleanField(default=True, verbose_name='Exitoso')
    codigo_respuesta = models.IntegerField(null=True, blank=True, verbose_name='Código HTTP')
    mensaje_error = models.TextField(null=True, blank=True, verbose_name='Mensaje de Error')
    
    # Métricas
    tiempo_respuesta = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Tiempo de Respuesta (segundos)'
    )
    requests_consumidos = models.IntegerField(
        default=1,
        verbose_name='Requests Consumidos',
        help_text='Número de requests de API consumidos'
    )
    
    # Cache
    desde_cache = models.BooleanField(
        default=False,
        verbose_name='Desde Caché',
        help_text='Si los datos se obtuvieron de caché (0 requests)'
    )
    cache_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Clave de Caché'
    )
    
    # Timestamp
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Estadística de Uso EOSDA'
        verbose_name_plural = 'Estadísticas de Uso EOSDA'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['usuario', '-creado_en']),
            models.Index(fields=['parcela', '-creado_en']),
            models.Index(fields=['tipo_operacion', '-creado_en']),
        ]
    
    def __str__(self):
        status = "✅" if self.exitoso else "❌"
        cache = " (CACHE)" if self.desde_cache else ""
        return f"{status} {self.tipo_operacion} - {self.usuario.username}{cache}"
    
    @classmethod
    def registrar_uso(cls, usuario, tipo_operacion: str, endpoint: str, 
                     exitoso: bool = True, parcela=None, tiempo_respuesta: float = None,
                     requests_consumidos: int = 1, desde_cache: bool = False,
                     cache_key: str = None, codigo_respuesta: int = None,
                     mensaje_error: str = None, metodo: str = 'POST'):
        """
        Registra un uso de la API de EOSDA
        """
        return cls.objects.create(
            usuario=usuario,
            parcela=parcela,
            tipo_operacion=tipo_operacion,
            endpoint=endpoint,
            metodo=metodo,
            exitoso=exitoso,
            codigo_respuesta=codigo_respuesta,
            mensaje_error=mensaje_error,
            tiempo_respuesta=tiempo_respuesta,
            requests_consumidos=requests_consumidos if not desde_cache else 0,
            desde_cache=desde_cache,
            cache_key=cache_key
        )
    
    @classmethod
    def estadisticas_usuario(cls, usuario, dias: int = 30):
        """
        Obtiene estadísticas de uso para un usuario
        """
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_inicio = timezone.now() - timedelta(days=dias)
        stats = cls.objects.filter(usuario=usuario, creado_en__gte=fecha_inicio)
        
        return {
            'total_requests': stats.filter(desde_cache=False).aggregate(
                total=models.Sum('requests_consumidos')
            )['total'] or 0,
            'requests_cache': stats.filter(desde_cache=True).count(),
            'ahorro_cache': stats.filter(desde_cache=True).count(),
            'exitosos': stats.filter(exitoso=True).count(),
            'fallidos': stats.filter(exitoso=False).count(),
            'tiempo_promedio': stats.aggregate(
                avg=models.Avg('tiempo_respuesta')
            )['avg'] or 0,
        }
