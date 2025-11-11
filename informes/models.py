"""
Modelos para la aplicación de informes AgroTech Histórico
Sistema completo de análisis satelital agrícola con PostGIS
"""

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import json

# Importar modelos de gestión de clientes
from .models_clientes import ClienteInvitacion, RegistroEconomico

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
        srid=4326,  # WGS84 - Sistema de coordenadas estándar GPS
        null=True, blank=True  # Permitir NULL temporalmente para migración
    )
    
    # Campo de respaldo para compatibilidad con sistemas que requieren GeoJSON
    coordenadas = models.TextField(
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
    
    # ========= INTEGRACIÓN EOSDA =========
    # Campos para sincronización con EOSDA Field Management API
    eosda_field_id = models.CharField(
        max_length=100, null=True, blank=True,
        verbose_name="EOSDA Field ID",
        help_text="ID único del campo en EOSDA después de sincronización",
        unique=True  # Cada field_id de EOSDA es único
    )
    eosda_sincronizada = models.BooleanField(
        default=False,
        verbose_name="Sincronizada con EOSDA",
        help_text="Indica si la parcela fue creada exitosamente en EOSDA"
    )
    eosda_fecha_sincronizacion = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Fecha Sincronización EOSDA",
        help_text="Cuándo se sincronizó por última vez con EOSDA"
    )
    eosda_nombre_campo = models.CharField(
        max_length=200, null=True, blank=True,
        verbose_name="Nombre en EOSDA",
        help_text="Nombre del campo tal como aparece en EOSDA"
    )
    eosda_errores = models.TextField(
        null=True, blank=True,
        verbose_name="Errores EOSDA",
        help_text="Último error durante sincronización con EOSDA"
    )
    
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
    
    def __str__(self):
        return f"{self.nombre} - {self.propietario}"
    
    @property 
    def poligono_geojson(self):
        """Retorna las coordenadas como GeoJSON string"""
        if self.geometria:
            return self.geometria.geojson
        elif self.coordenadas:
            # Compatibilidad con datos antiguos
            if isinstance(self.coordenadas, str):
                return self.coordenadas
            else:
                return json.dumps(self.coordenadas)
        return None
    
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
            
            # Actualizar GeoJSON de respaldo para compatibilidad
            self.coordenadas = self.geometria.geojson
        
        super().save(*args, **kwargs)
    
    def marcar_sincronizada_eosda(self, field_id: str, nombre_campo: str = None):
        """
        Marca la parcela como sincronizada exitosamente con EOSDA
        """
        self.eosda_field_id = field_id
        self.eosda_sincronizada = True
        self.eosda_fecha_sincronizacion = timezone.now()
        self.eosda_nombre_campo = nombre_campo or self.nombre
        self.eosda_errores = None  # Limpiar errores previos
        self.save(update_fields=[
            'eosda_field_id', 'eosda_sincronizada', 
            'eosda_fecha_sincronizacion', 'eosda_nombre_campo', 'eosda_errores'
        ])
    
    def marcar_error_eosda(self, error_mensaje: str):
        """
        Registra un error durante la sincronización con EOSDA
        """
        self.eosda_sincronizada = False
        self.eosda_errores = error_mensaje
        self.eosda_fecha_sincronizacion = timezone.now()
        self.save(update_fields=[
            'eosda_sincronizada', 'eosda_errores', 'eosda_fecha_sincronizacion'
        ])
    
    @property
    def requiere_sincronizacion_eosda(self) -> bool:
        """
        Determina si la parcela necesita ser sincronizada con EOSDA
        """
        return not self.eosda_sincronizada or self.eosda_field_id is None
    
    @property
    def puede_obtener_datos_eosda(self) -> bool:
        """
        Determina si se pueden obtener datos satellitales de EOSDA
        """
        return self.eosda_sincronizada and self.eosda_field_id is not None
    
    @property
    def coordenadas_dict(self):
        """Convierte la geometría a diccionario Python para compatibilidad"""
        if self.geometria:
            return json.loads(self.geometria.geojson)
        elif self.coordenadas:
            try:
                return json.loads(self.coordenadas)
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
        max_length=20, default="2.1",
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
    
    def __str__(self):
        return f"{self.nombre} - {self.propietario}"
    
    @property
    def coordenadas_dict(self):
        """Convierte el GeoJSON string a diccionario Python"""
        try:
            return json.loads(self.poligono_geojson)
        except json.JSONDecodeError:
            return None
    
    @property
    def centro_parcela(self):
        """Calcula el centro geográfico de la parcela"""
        coords = self.coordenadas_dict
        if not coords or 'coordinates' not in coords:
            return None
            
        # Asumiendo que es un polígono
        try:
            polygon_coords = coords['coordinates'][0]
            lats = [coord[1] for coord in polygon_coords]
            lngs = [coord[0] for coord in polygon_coords]
            
            center_lat = sum(lats) / len(lats)
            center_lng = sum(lngs) / len(lngs)
            
            return {'lat': center_lat, 'lng': center_lng}
        except (IndexError, KeyError, TypeError):
            return None


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
        max_length=20, default="1.0",
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
            self.titulo = f"Análisis Satelital - {self.parcela.nombre} ({self.periodo_analisis_meses} meses)"
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


# ========== MODELOS DE CONFIGURACIÓN DE REPORTES Y CACHÉ EOSDA ==========

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
    fecha_inicio = models.DateField(verbose_name='Fecha de Inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de Fin', default=timezone.now)
    plan = models.CharField(
        max_length=20,
        choices=PlanReporte.choices,
        default=PlanReporte.BASICO_6M,
        verbose_name='Plan'
    )
    incluir_ndvi = models.BooleanField(default=True, verbose_name='Incluir NDVI')
    incluir_ndmi = models.BooleanField(default=False, verbose_name='Incluir NDMI')
    incluir_savi = models.BooleanField(default=False, verbose_name='Incluir SAVI')
    incluir_imagenes = models.BooleanField(default=False, verbose_name='Incluir Imágenes')
    frecuencia_imagenes = models.CharField(
        max_length=20,
        choices=[
            ('mensual', 'Mensual'),
            ('bimensual', 'Bimensual'),
            ('trimestral', 'Trimestral')
        ],
        default='mensual'
    )
    max_nubosidad = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    costo_estimado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    reporte_generado = models.BooleanField(default=False)
    fecha_generacion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'
        ordering = ['-creado_en']
    
    def __str__(self):
        return f"{self.parcela.nombre} - {self.get_plan_display()}"
    
    @property
    def indices_seleccionados(self):
        indices = []
        if self.incluir_ndvi:
            indices.append('ndvi')
        if self.incluir_ndmi:
            indices.append('ndmi')
        if self.incluir_savi:
            indices.append('savi')
        return indices


class CacheDatosEOSDA(models.Model):
    """Caché de respuestas de EOSDA"""
    field_id = models.CharField(max_length=100, db_index=True)
    fecha_inicio = models.DateField(db_index=True)
    fecha_fin = models.DateField(db_index=True)
    indices = models.CharField(max_length=100)
    cache_key = models.CharField(max_length=255, unique=True, db_index=True)
    datos_json = models.JSONField()
    task_id = models.CharField(max_length=100, null=True, blank=True)
    num_escenas = models.IntegerField(default=0)
    calidad_promedio = models.FloatField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    usado_en = models.DateTimeField(auto_now=True)
    veces_usado = models.IntegerField(default=0)
    valido_hasta = models.DateTimeField()
    
    class Meta:
        verbose_name = 'Caché de Datos EOSDA'
        verbose_name_plural = 'Caché de Datos EOSDA'
        ordering = ['-creado_en']
    
    def __str__(self):
        return f"Cache {self.field_id} ({self.fecha_inicio} - {self.fecha_fin})"
    
    @staticmethod
    def generar_cache_key(field_id, fecha_inicio, fecha_fin, indices):
        import hashlib
        indices_str = ','.join(sorted(indices))
        data_str = f"{field_id}_{fecha_inicio}_{fecha_fin}_{indices_str}"
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    @property
    def es_valido(self):
        return timezone.now() < self.valido_hasta
    
    @classmethod
    def obtener_o_none(cls, field_id, fecha_inicio, fecha_fin, indices):
        """
        Busca en caché si existe un registro válido
        Returns: datos_json si existe y es válido, None si no
        """
        cache_key = cls.generar_cache_key(field_id, fecha_inicio, fecha_fin, indices)
        
        try:
            cache_obj = cls.objects.get(cache_key=cache_key)
            
            # Verificar validez
            if cache_obj.es_valido:
                # Actualizar estadísticas de uso
                cache_obj.veces_usado += 1
                cache_obj.usado_en = timezone.now()
                cache_obj.save(update_fields=['veces_usado', 'usado_en'])
                
                return cache_obj.datos_json
            else:
                # Caché expirado, eliminar
                cache_obj.delete()
                return None
                
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def guardar_datos(cls, field_id, fecha_inicio, fecha_fin, indices, datos, task_id=None):
        """
        Guarda datos en caché con validez de 7 días
        """
        from datetime import timedelta
        
        cache_key = cls.generar_cache_key(field_id, fecha_inicio, fecha_fin, indices)
        
        # Calcular estadísticas
        resultados = datos.get('resultados', [])
        num_escenas = len(resultados)
        
        # Calcular calidad promedio si hay datos
        calidad_promedio = None
        if resultados and isinstance(resultados, list):
            calidades = []
            for r in resultados:
                if isinstance(r, dict):
                    stats = r.get('statistics', {})
                    if isinstance(stats, dict):
                        for indice_data in stats.values():
                            if isinstance(indice_data, dict) and 'pixels_analyzed' in indice_data:
                                px_total = indice_data.get('pixels_in_aoi', 1)
                                px_analizados = indice_data.get('pixels_analyzed', 0)
                                if px_total > 0:
                                    calidades.append((px_analizados / px_total) * 100)
            
            if calidades:
                calidad_promedio = sum(calidades) / len(calidades)
        
        # Crear o actualizar registro
        valido_hasta = timezone.now() + timedelta(days=7)
        
        cls.objects.update_or_create(
            cache_key=cache_key,
            defaults={
                'field_id': field_id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'indices': ','.join(sorted(indices)),
                'datos_json': datos,
                'task_id': task_id,
                'num_escenas': num_escenas,
                'calidad_promedio': calidad_promedio,
                'valido_hasta': valido_hasta,
                'veces_usado': 0
            }
        )
    
    @classmethod
    def limpiar_expirados(cls):
        """Elimina registros expirados"""
        expirados = cls.objects.filter(valido_hasta__lt=timezone.now())
        count = expirados.count()
        expirados.delete()
        return count


class EstadisticaUsoEOSDA(models.Model):
    """Registro de uso de la API de EOSDA"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='estadisticas_eosda')
    parcela = models.ForeignKey('Parcela', on_delete=models.CASCADE, null=True, blank=True, related_name='estadisticas_eosda')
    tipo_operacion = models.CharField(
        max_length=50,
        choices=[
            ('field_management', 'Field Management'),
            ('statistics', 'Statistics'),
            ('images', 'Images'),
            ('tiles', 'Tiles'),
        ]
    )
    endpoint = models.CharField(max_length=200)
    metodo = models.CharField(max_length=10, default='POST')
    exitoso = models.BooleanField(default=True)
    codigo_respuesta = models.IntegerField(null=True, blank=True)
    mensaje_error = models.TextField(null=True, blank=True)
    tiempo_respuesta = models.FloatField(null=True, blank=True)
    requests_consumidos = models.IntegerField(default=1)
    desde_cache = models.BooleanField(default=False)
    cache_key = models.CharField(max_length=255, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Estadística de Uso EOSDA'
        verbose_name_plural = 'Estadísticas de Uso EOSDA'
        ordering = ['-creado_en']
    
    def __str__(self):
        status = "✅" if self.exitoso else "❌"
        cache = " (CACHE)" if self.desde_cache else ""
        return f"{status} {self.tipo_operacion} - {self.usuario.username}{cache}"
    
    @classmethod
    def registrar_uso(cls, usuario, tipo_operacion, endpoint, parcela=None, 
                     exitoso=True, tiempo_respuesta=None, requests_consumidos=1,
                     desde_cache=False, cache_key=None, codigo_respuesta=None, 
                     mensaje_error=None, metodo='POST'):
        """
        Registra una operación de API de EOSDA
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
            requests_consumidos=requests_consumidos,
            desde_cache=desde_cache,
            cache_key=cache_key
        )
    
    @classmethod
    def estadisticas_usuario(cls, usuario):
        """
        Calcula estadísticas agregadas para un usuario
        """
        from django.db.models import Sum, Count, Avg
        
        stats = cls.objects.filter(usuario=usuario).aggregate(
            total_operaciones=Count('id'),
            total_requests=Sum('requests_consumidos'),
            operaciones_exitosas=Count('id', filter=models.Q(exitoso=True)),
            desde_cache=Count('id', filter=models.Q(desde_cache=True)),
            tiempo_promedio=Avg('tiempo_respuesta')
        )
        
        # Valores por defecto si no hay datos
        return {
            'total_operaciones': stats['total_operaciones'] or 0,
            'total_requests': stats['total_requests'] or 0,
            'operaciones_exitosas': stats['operaciones_exitosas'] or 0,
            'desde_cache': stats['desde_cache'] or 0,
            'tiempo_promedio': stats['tiempo_promedio'] or 0
        }
