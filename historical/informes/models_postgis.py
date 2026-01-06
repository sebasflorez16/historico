"""
Modelos optimizados para datos geoespaciales con PostGIS
Incluye campos geográficos nativos para mejor rendimiento
"""

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.contrib.auth.models import User
import json


class Parcela(gis_models.Model):
    """
    Modelo para gestionar las parcelas agrícolas con geometría PostGIS nativa
    """
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Parcela")
    propietario = models.CharField(max_length=200, verbose_name="Propietario")
    
    # Campo geoespacial nativo PostGIS - MUCHO más eficiente
    geometria = gis_models.PolygonField(
        verbose_name="Geometría de la Parcela",
        help_text="Polígono definiendo los límites de la parcela",
        srid=4326  # WGS84 - Sistema de coordenadas estándar GPS
    )
    
    # Campo de respaldo para compatibilidad con sistemas que requieren GeoJSON
    poligono_geojson = models.TextField(
        blank=True,
        verbose_name="GeoJSON (respaldo)",
        help_text="Representación GeoJSON para compatibilidad"
    )
    
    area_hectareas = models.FloatField(
        null=True, blank=True,
        verbose_name="Área (hectáreas)",
        help_text="Área calculada automáticamente usando PostGIS"
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    fecha_inicio_monitoreo = models.DateField(verbose_name="Inicio Monitoreo")
    fecha_fin_monitoreo = models.DateField(
        null=True, blank=True,
        verbose_name="Fin Monitoreo"
    )
    activa = models.BooleanField(default=True, verbose_name="Activa")
    
    # Metadatos adicionales
    tipo_cultivo = models.CharField(
        max_length=100, blank=True,
        verbose_name="Tipo de Cultivo"
    )
    notas = models.TextField(blank=True, verbose_name="Notas")
    
    # Metadatos geoespaciales calculados automáticamente
    centroide = gis_models.PointField(
        null=True, blank=True,
        verbose_name="Punto Central",
        help_text="Centro geométrico calculado automáticamente",
        srid=4326
    )
    
    perimetro_metros = models.FloatField(
        null=True, blank=True,
        verbose_name="Perímetro (metros)",
        help_text="Perímetro calculado automáticamente"
    )
    
    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        ordering = ['-fecha_registro']
        # Índice espacial automático para consultas geográficas ultra-rápidas
        indexes = [
            gis_models.Index(fields=['geometria'], name='idx_parcela_geometria'),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.propietario}"
    
    def save(self, *args, **kwargs):
        """
        Override save para calcular automáticamente área, perímetro y centroide
        """
        if self.geometria:
            # Calcular área en hectáreas (PostGIS en metros cuadrados)
            # Usar proyección apropiada para cálculos precisos
            geom_utm = self.geometria.transform(3857, clone=True)  # Web Mercator para cálculos
            self.area_hectareas = geom_utm.area / 10000  # m² a hectáreas
            
            # Calcular perímetro en metros
            self.perimetro_metros = geom_utm.length
            
            # Calcular centroide
            self.centroide = self.geometria.centroid
            
            # Actualizar GeoJSON de respaldo
            self.poligono_geojson = self.geometria.geojson
        
        super().save(*args, **kwargs)
    
    @property
    def coordenadas_dict(self):
        """Convierte la geometría a diccionario Python para compatibilidad"""
        if self.geometria:
            return json.loads(self.geometria.geojson)
        elif self.poligono_geojson:
            try:
                return json.loads(self.poligono_geojson)
            except json.JSONDecodeError:
                return None
        return None
    
    @property
    def centro_parcela(self):
        """Retorna el centro como diccionario lat/lng"""
        if self.centroide:
            return {
                'lat': self.centroide.y,
                'lng': self.centroide.x
            }
        return None
    
    def parcelas_cercanas(self, radio_km=10):
        """
        Encuentra parcelas dentro de un radio específico
        Ejemplo de funcionalidad geoespacial avanzada con PostGIS
        """
        from django.contrib.gis.measure import D
        
        return Parcela.objects.filter(
            geometria__distance_lte=(self.centroide, D(km=radio_km)),
            activa=True
        ).exclude(id=self.id)
    
    def intersecta_con(self, otra_geometria):
        """
        Verifica si la parcela intersecta con otra geometría
        Útil para análisis de superposición de cultivos, zonas protegidas, etc.
        """
        return self.geometria.intersects(otra_geometria)


class ZonaInteres(gis_models.Model):
    """
    Modelo para definir zonas de interés especiales
    Ejemplo: zonas de protección ambiental, áreas de riego, etc.
    """
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Zona")
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('proteccion', 'Área de Protección'),
            ('riego', 'Sistema de Riego'),
            ('acceso', 'Vía de Acceso'),
            ('infraestructura', 'Infraestructura'),
            ('exclusion', 'Zona de Exclusión'),
        ],
        verbose_name="Tipo de Zona"
    )
    
    geometria = gis_models.GeometryField(
        verbose_name="Geometría de la Zona",
        help_text="Puede ser punto, línea o polígono según el tipo",
        srid=4326
    )
    
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Zona de Interés"
        verbose_name_plural = "Zonas de Interés"
        indexes = [
            gis_models.Index(fields=['geometria'], name='idx_zona_geometria'),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
    def parcelas_afectadas(self):
        """
        Encuentra parcelas que intersectan con esta zona
        """
        return Parcela.objects.filter(
            geometria__intersects=self.geometria,
            activa=True
        )


# Mantener modelos originales para compatibilidad
class IndiceMensual(models.Model):
    """
    Almacena los índices satelitales mensuales obtenidos desde EOSDA
    """
    parcela = models.ForeignKey(
        Parcela, on_delete=models.CASCADE,
        related_name='indices_mensuales'
    )
    
    # Período
    año = models.PositiveIntegerField(verbose_name="Año")
    mes = models.PositiveIntegerField(verbose_name="Mes")
    
    # Índices satelitales principales
    ndvi_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="NDVI Promedio",
        help_text="Índice de Vegetación de Diferencia Normalizada (0 a 1)"
    )
    ndvi_maximo = models.FloatField(null=True, blank=True, verbose_name="NDVI Máximo")
    ndvi_minimo = models.FloatField(null=True, blank=True, verbose_name="NDVI Mínimo")
    
    ndmi_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="NDMI Promedio",
        help_text="Índice de Humedad de Diferencia Normalizada (-1 a 1)"
    )
    ndmi_maximo = models.FloatField(null=True, blank=True, verbose_name="NDMI Máximo")
    ndmi_minimo = models.FloatField(null=True, blank=True, verbose_name="NDMI Mínimo")
    
    savi_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="SAVI Promedio",
        help_text="Índice de Vegetación Ajustado al Suelo"
    )
    savi_maximo = models.FloatField(null=True, blank=True, verbose_name="SAVI Máximo")
    savi_minimo = models.FloatField(null=True, blank=True, verbose_name="SAVI Mínimo")
    
    # Datos climatológicos y condiciones
    temperatura_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="Temperatura Promedio (°C)"
    )
    temperatura_maxima = models.FloatField(null=True, blank=True, verbose_name="Temperatura Máxima")
    temperatura_minima = models.FloatField(null=True, blank=True, verbose_name="Temperatura Mínima")
    
    precipitacion_total = models.FloatField(
        null=True, blank=True,
        verbose_name="Precipitación Total (mm)"
    )
    
    nubosidad_promedio = models.FloatField(
        null=True, blank=True,
        verbose_name="Nubosidad Promedio (%)",
        help_text="Porcentaje promedio de nubosidad durante el mes"
    )
    
    # Metadatos de la consulta
    fecha_consulta_api = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Consulta API"
    )
    fuente_datos = models.CharField(
        max_length=50, default="EOSDA",
        verbose_name="Fuente de Datos"
    )
    calidad_datos = models.CharField(
        max_length=20,
        choices=[
            ('excelente', 'Excelente'),
            ('buena', 'Buena'),
            ('regular', 'Regular'),
            ('pobre', 'Pobre'),
        ],
        default='buena',
        verbose_name="Calidad de Datos"
    )
    
    class Meta:
        verbose_name = "Índice Mensual"
        verbose_name_plural = "Índices Mensuales"
        ordering = ['-año', '-mes']
        unique_together = ('parcela', 'año', 'mes')
        indexes = [
            models.Index(fields=['parcela', 'año', 'mes'], name='idx_indice_temporal'),
        ]
    
    def __str__(self):
        return f"{self.parcela.nombre} - {self.mes:02d}/{self.año}"
    
    @property
    def periodo_texto(self):
        """Retorna el período en formato legible"""
        meses = [
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        return f"{meses[self.mes]} {self.año}"
    
    @property
    def salud_vegetacion(self):
        """Evalúa la salud de la vegetación basada en NDVI"""
        if not self.ndvi_promedio:
            return "Sin datos"
            
        if self.ndvi_promedio >= 0.7:
            return "Excelente"
        elif self.ndvi_promedio >= 0.5:
            return "Buena"
        elif self.ndvi_promedio >= 0.3:
            return "Regular"
        else:
            return "Pobre"


class Informe(models.Model):
    """
    Informes generados automáticamente con análisis de datos satelitales
    """
    parcela = models.ForeignKey(
        Parcela, on_delete=models.CASCADE,
        related_name='informes'
    )
    
    # Configuración del informe
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Generación")
    periodo_analisis_meses = models.PositiveIntegerField(
        verbose_name="Período Análisis (meses)",
        help_text="Número de meses analizados (6, 12, 24)"
    )
    fecha_inicio_analisis = models.DateField(verbose_name="Inicio Período")
    fecha_fin_analisis = models.DateField(verbose_name="Fin Período")
    
    # Contenido del informe
    titulo = models.CharField(max_length=300, verbose_name="Título del Informe")
    resumen_ejecutivo = models.TextField(
        verbose_name="Resumen Ejecutivo",
        help_text="Resumen generado automáticamente por IA"
    )
    analisis_tendencias = models.TextField(
        blank=True,
        verbose_name="Análisis de Tendencias",
        help_text="Análisis detallado de tendencias NDVI, NDMI, SAVI"
    )
    conclusiones_ia = models.TextField(
        blank=True,
        verbose_name="Conclusiones IA",
        help_text="Conclusiones generadas por análisis IA local"
    )
    recomendaciones = models.TextField(
        blank=True,
        verbose_name="Recomendaciones",
        help_text="Recomendaciones técnicas basadas en los datos"
    )
    
    # Archivos generados
    archivo_pdf = models.FileField(
        upload_to='informes/pdfs/%Y/%m/',
        null=True, blank=True,
        verbose_name="Archivo PDF"
    )
    mapa_ndvi_imagen = models.ImageField(
        upload_to='informes/mapas/%Y/%m/',
        null=True, blank=True,
        verbose_name="Mapa NDVI"
    )
    grafico_tendencias = models.ImageField(
        upload_to='informes/graficos/%Y/%m/',
        null=True, blank=True,
        verbose_name="Gráfico Tendencias"
    )
    
    # Estadísticas del análisis
    ndvi_promedio_periodo = models.FloatField(
        null=True, blank=True,
        verbose_name="NDVI Promedio del Período"
    )
    ndmi_promedio_periodo = models.FloatField(
        null=True, blank=True,
        verbose_name="NDMI Promedio del Período"
    )
    savi_promedio_periodo = models.FloatField(
        null=True, blank=True,
        verbose_name="SAVI Promedio del Período"
    )
    
    # Metadatos
    version_algoritmo = models.CharField(
        max_length=20, default="2.0",
        verbose_name="Versión Algoritmo"
    )
    tiempo_procesamiento = models.DurationField(
        null=True, blank=True,
        verbose_name="Tiempo Procesamiento"
    )
    
    class Meta:
        verbose_name = "Informe"
        verbose_name_plural = "Informes"
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['parcela', 'fecha_generacion'], name='idx_informe_parcela_fecha'),
        ]
    
    def __str__(self):
        return f"Informe {self.parcela.nombre} - {self.fecha_generacion.strftime('%d/%m/%Y')}"
    
    @property
    def estado_salud_general(self):
        """Evalúa el estado general de salud de la parcela"""
        if not self.ndvi_promedio_periodo:
            return "Sin datos suficientes"
            
        ndvi = self.ndvi_promedio_periodo
        if ndvi >= 0.7:
            return "Excelente estado de salud"
        elif ndvi >= 0.5:
            return "Buen estado de salud"
        elif ndvi >= 0.3:
            return "Estado regular"
        else:
            return "Requiere atención"
    
    def save(self, *args, **kwargs):
        """Override save para generar título automáticamente"""
        if not self.titulo:
            self.titulo = f"Análisis Satelital PostGIS - {self.parcela.nombre} ({self.periodo_analisis_meses} meses)"
        super().save(*args, **kwargs)


class ConfiguracionAPI(models.Model):
    """
    Configuración para APIs externas (EOSDA, etc.)
    """
    nombre_api = models.CharField(max_length=50, unique=True, verbose_name="Nombre API")
    url_base = models.URLField(verbose_name="URL Base")
    token_activo = models.BooleanField(default=True, verbose_name="Token Activo")
    fecha_ultima_consulta = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Última Consulta"
    )
    consultas_realizadas = models.PositiveIntegerField(
        default=0,
        verbose_name="Consultas Realizadas"
    )
    limite_consultas_diarias = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name="Límite Diario"
    )
    
    class Meta:
        verbose_name = "Configuración API"
        verbose_name_plural = "Configuraciones API"
    
    def __str__(self):
        return f"API {self.nombre_api}"