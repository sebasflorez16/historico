"""
Modelos para optimización de Gemini AI
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AnalisisImagen(models.Model):
    """
    Cachea análisis de imágenes satelitales generados por Gemini AI
    para evitar peticiones duplicadas y reducir consumo de API
    """
    parcela = models.ForeignKey('Parcela', on_delete=models.CASCADE, related_name='analisis_imagenes')
    fecha_imagen = models.DateField()
    indice = models.CharField(max_length=10, choices=[('ndvi', 'NDVI'), ('ndmi', 'NDMI'), ('savi', 'SAVI')])
    url_imagen = models.URLField(max_length=500)
    resultado_gemini = models.JSONField()
    fecha_analisis = models.DateTimeField(auto_now_add=True)
    hash_imagen = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    class Meta:
        unique_together = ('parcela', 'fecha_imagen', 'indice', 'url_imagen')
        verbose_name = 'Análisis de Imagen Satelital (Gemini)'
        verbose_name_plural = 'Análisis de Imágenes Satelitales (Gemini)'

    def __str__(self):
        return f"{self.parcela.nombre} | {self.fecha_imagen} | {self.indice}"


class InformeGenerado(models.Model):
    """
    Registra informes PDF generados para control de cuota diaria
    y monitoreo de consumo de API Gemini
    """
    parcela = models.ForeignKey('Parcela', on_delete=models.CASCADE, related_name='informes_generados')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    tipo_analisis = models.CharField(max_length=20, choices=[
        ('rapido', 'Análisis Rápido (10 imágenes)'),
        ('completo', 'Análisis Completo (30 imágenes)')
    ], default='rapido')
    num_imagenes_analizadas = models.IntegerField(default=0)
    tokens_consumidos = models.IntegerField(default=0)
    peticiones_api = models.IntegerField(default=0)
    ruta_archivo = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Informe Generado'
        verbose_name_plural = 'Informes Generados'
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['fecha_generacion', 'usuario']),
        ]
    
    def __str__(self):
        return f"{self.parcela.nombre} | {self.fecha_generacion.strftime('%Y-%m-%d %H:%M')} | {self.tipo_analisis}"
    
    @classmethod
    def contar_informes_hoy(cls, usuario=None):
        """Cuenta cuántos informes se han generado hoy (por usuario o global)"""
        hoy = timezone.now().date()
        query = cls.objects.filter(fecha_generacion__date=hoy)
        if usuario:
            query = query.filter(usuario=usuario)
        return query.count()
    
    @classmethod
    def puede_generar_informe(cls, usuario=None, limite_diario=3):
        """Verifica si se puede generar un nuevo informe según el límite diario"""
        informes_hoy = cls.contar_informes_hoy(usuario)
        return informes_hoy < limite_diario
