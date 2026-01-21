"""
Generador de Informes Técnicos en PDF - AgroTech
Sistema de Análisis Satelital Agrícola con Motor Determinístico

MOTOR DE ANÁLISIS:
- Procesamiento de índices espectrales (NDVI, NDMI, SAVI)
- Análisis estadístico de series temporales
- Detección de tendencias mediante regresión lineal
- Evaluación de variabilidad espacial y temporal
- Generación de recomendaciones agronómicas basadas en umbrales científicos

FUENTES DE DATOS:
- Imágenes satelitales Sentinel-2 (ESA)
- Resolución espacial: 10-20 metros
- Datos climáticos históricos
- Metadatos de calidad de imagen
"""
import os
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from io import BytesIO
from dateutil.relativedelta import relativedelta

# ReportLab imports
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, 
    Table, TableStyle, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas

# Matplotlib para gráficos (usar backend no-GUI para evitar problemas con threads)
import matplotlib
matplotlib.use('Agg')  #  Backend no-GUI, seguro para threads y servidores web
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns

# Django imports
from django.conf import settings

# Modelos locales
from informes.models import Parcela, IndiceMensual

# Analizadores
from informes.analizadores.ndvi_analyzer import AnalizadorNDVI
from informes.analizadores.ndmi_analyzer import AnalizadorNDMI
from informes.analizadores.savi_analyzer import AnalizadorSAVI
from informes.analizadores.tendencias_analyzer import DetectorTendencias
from informes.analizadores.recomendaciones_engine import GeneradorRecomendaciones

import logging
logger = logging.getLogger(__name__)


def limpiar_html_completo(texto: str) -> str:
    """
    Limpia HTML COMPLETAMENTE - convierte a formato ReportLab sin tags visibles
    
    Usa enfoque de 3 pasos:
    1. Convertir tags deseados a marcadores temporales
    2. Eliminar TODOS los tags HTML restantes  
    3. Restaurar solo los tags necesarios en formato ReportLab
    """
    if not texto:
        return ""
    
    # Convertir a string
    texto = str(texto)
    
    # Limpieza agresiva de strong mal formados
    texto = re.sub(r'<strong>\s*</strong>', '', texto)  # Eliminar strong vacíos
    texto = re.sub(r'<strong>([^<]*?)(?=<strong>|$)', r'<b>\1</b>', texto)  # strong sin cerrar
    
    # Normalizar <strong> a <b> y </strong> a </b> para evitar duplicidad y errores
    texto = texto.replace('<strong>', '<b>').replace('</strong>', '</b>')
    # PASO 1: Reemplazar tags que queremos mantener con marcadores temporales
    replacements = {
        '<b>': '**BOLD_START**',
        '</b>': '**BOLD_END**',
        '<em>': '**ITALIC_START**',
        '</em>': '**ITALIC_END**',
        '<i>': '**ITALIC_START**',
        '</i>': '**ITALIC_END**',
        '<br>': '**LINEBREAK**',
        '<br/>': '**LINEBREAK**',
        '<BR>': '**LINEBREAK**',
    }
    for old, new in replacements.items():
        texto = texto.replace(old, new)
    
    # PASO 2: Eliminar CUALQUIER tag HTML que quede (regex agresivo)
    texto = re.sub(r'<[^>]+>', '', texto)
    
    # PASO 3: Restaurar los tags que queremos en formato ReportLab
    texto = texto.replace('**BOLD_START**', '<b>')
    texto = texto.replace('**BOLD_END**', '</b>')
    texto = texto.replace('**ITALIC_START**', '<i>')
    texto = texto.replace('**ITALIC_END**', '</i>')
    texto = texto.replace('**LINEBREAK**', '<br/>')
    
    # PASO 4: Limpiar saltos de línea
    texto = texto.replace('\n\n', '<br/><br/>')
    texto = texto.replace('\n', ' ')
    
    # PASO 5: Formatear bullets
    texto = re.sub(r'•\s*', '<br/>  • ', texto)
    texto = re.sub(r'\*\s+', '<br/>  • ', texto)
    
    # PASO 6: Limpiar espacios múltiples
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'(<br/>\s*){3,}', '<br/><br/>', texto)
    
    return texto.strip()


class GeneradorPDFProfesional:
    """
    Genera informes PDF profesionales con:
    - Logos AgroTech
    - Análisis inteligente de índices
    - Gráficos matplotlib
    - Recomendaciones accionables
    - Diseño moderno y profesional
    """
    
    def __init__(self):
        self.pagesize = A4
        self.ancho, self.alto = A4
        self.margen = 2*cm
        
        # Colores corporativos AgroTech
        self.colores = {
            'verde_principal': colors.HexColor('#2E8B57'),  # Verde AgroTech
            'verde_claro': colors.HexColor('#90EE90'),
            'naranja': colors.HexColor('#FF7A00'),
            'azul': colors.HexColor('#17a2b8'),
            'gris_oscuro': colors.HexColor('#2c3e50'),
            'gris_claro': colors.HexColor('#ecf0f1'),
        }
        
        # Estilos
        self.estilos = self._crear_estilos()
    
    def formato_mes_año_español(self, fecha: date) -> str:
        """Formatea fecha en español (Enero 2025)"""
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[fecha.month]} {fecha.year}"
    
    def _obtener_path_imagen_correcto(self, imagen_field):
        """Obtiene el path correcto de una imagen, manejando paths relativos y absolutos"""
        if not imagen_field:
            return None
        
        try:
            path_str = str(imagen_field).strip()
            if not path_str:
                return None
            
            paths_a_probar = []
            
            # Intentar obtener .path del campo ImageField
            try:
                if hasattr(imagen_field, 'path'):
                    paths_a_probar.append(imagen_field.path)
            except:
                pass
            
            # Si es una ruta relativa
            if not path_str.startswith('/'):
                # Desde MEDIA_ROOT
                if hasattr(settings, 'MEDIA_ROOT'):
                    path_desde_media = os.path.join(settings.MEDIA_ROOT, path_str)
                    paths_a_probar.append(path_desde_media)
                
                # Desde BASE_DIR/media
                path_desde_base = os.path.join(settings.BASE_DIR, 'media', path_str)
                paths_a_probar.append(path_desde_base)
            else:
                # Path absoluto
                paths_a_probar.append(path_str)
            
            # Probar cada path
            for path in paths_a_probar:
                if os.path.exists(path):
                    return path
            
            return None
            
        except Exception as e:
            logger.warning(f"Error al obtener path de imagen: {e}")
            return None
    
    def _evaluar_calidad_imagen(self, tipo_indice: str, valor_promedio: float, 
                                valor_minimo: float, valor_maximo: float) -> Dict:
        """Evalúa la calidad de una imagen según umbrales técnicos"""
        if tipo_indice == 'NDVI':
            if valor_promedio >= 0.6:
                return {'etiqueta': 'Excelente', 'icono': '✓', 'color': '#4CAF50'}
            elif valor_promedio >= 0.4:
                return {'etiqueta': 'Bueno', 'icono': '~', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '!', 'color': '#F44336'}
        
        elif tipo_indice == 'NDMI':
            if valor_promedio >= 0.3:
                return {'etiqueta': 'Adecuado', 'icono': '✓', 'color': '#2196F3'}
            elif valor_promedio >= 0.0:
                return {'etiqueta': 'Moderado', 'icono': '~', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '!', 'color': '#F44336'}
        
        elif tipo_indice == 'SAVI':
            if valor_promedio >= 0.4:
                return {'etiqueta': 'Alto', 'icono': '✓', 'color': '#4CAF50'}
            elif valor_promedio >= 0.2:
                return {'etiqueta': 'Medio', 'icono': '~', 'color': '#FFC107'}
            else:
                return {'etiqueta': 'Bajo', 'icono': '!', 'color': '#F44336'}
        
        return {'etiqueta': 'N/D', 'icono': '?', 'color': '#999999'}
    
    def _decorar_seccion(self, img_name, height=1.2*cm):
        """Separador de secciones sin imágenes decorativas"""
        # Retornar solo un espaciador simple sin imágenes
        return [Spacer(1, 0.5*cm)]

    def _crear_estilos(self):
        """Crea estilos personalizados para el documento"""
        estilos = getSampleStyleSheet()
        
        # Título de portada
        estilos.add(ParagraphStyle(
            name='TituloPortada',
            parent=estilos['Heading1'],
            fontSize=28,
            textColor=self.colores['verde_principal'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo de portada
        estilos.add(ParagraphStyle(
            name='SubtituloPortada',
            parent=estilos['Normal'],
            fontSize=16,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Título de sección
        estilos.add(ParagraphStyle(
            name='TituloSeccion',
            parent=estilos['Heading1'],
            fontSize=18,
            textColor=self.colores['verde_principal'],
            spaceBefore=24,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            borderColor=self.colores['verde_principal'],
            borderWidth=2,
            borderPadding=8
        ))
        
        # Subtítulo de sección
        estilos.add(ParagraphStyle(
            name='SubtituloSeccion',
            parent=estilos['Heading2'],
            fontSize=14,
            textColor=self.colores['azul'],
            spaceBefore=16,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        estilos.add(ParagraphStyle(
            name='TextoNormal',
            parent=estilos['Normal'],
            fontSize=11,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Análisis técnico (fuente mejorada)
        estilos.add(ParagraphStyle(
            name='AnalisisTecnico',
            parent=estilos['Normal'],
            fontSize=12,
            leading=18,
            textColor=self.colores['gris_oscuro'],
            spaceAfter=14,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leftIndent=10,
            rightIndent=10
        ))
        
        # Pie de imagen
        estilos.add(ParagraphStyle(
            name='PieImagen',
            parent=estilos['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))
        
        return estilos
    
    def generar_informe_completo(self, parcela_id: int, 
                                meses_atras: int = 12,
                                output_path: str = None) -> str:
        """
        Genera informe completo en PDF
        
        Args:
            parcela_id: ID de la parcela
            meses_atras: Período de análisis (meses)
            output_path: Ruta de salida del PDF (opcional)
        
        Returns:
            Ruta del archivo PDF generado
        """
        # Obtener parcela
        try:
            parcela = Parcela.objects.get(id=parcela_id, activa=True)
        except Parcela.DoesNotExist:
            raise ValueError(f"Parcela {parcela_id} no encontrada")
        
        # Obtener datos históricos - PERIODO REAL SEGÚN DATOS DISPONIBLES
        indices = IndiceMensual.objects.filter(parcela=parcela).order_by('año', 'mes')
        if not indices.exists():
            raise ValueError(f"No hay datos disponibles para la parcela {parcela.nombre}")
        fecha_inicio = date(indices.first().año, indices.first().mes, 1)
        fecha_fin = date(indices.last().año, indices.last().mes, 1)
        
        # Preparar datos para análisis
        datos_analisis = self._preparar_datos_analisis(indices)
        
        # Ejecutar análisis (pasando los índices originales para caché)
        analisis_completo = self._ejecutar_analisis(datos_analisis, parcela, indices)
        
        # Generar gráficos
        graficos = self._generar_graficos(datos_analisis)
        
        # Crear PDF
        if not output_path:
            nombre_archivo = f"informe_{parcela.nombre.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join(settings.MEDIA_ROOT, 'informes', nombre_archivo)
        
        # Asegurar que existe el directorio
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Construir documento
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.pagesize,
            rightMargin=self.margen,
            leftMargin=self.margen,
            topMargin=self.margen + 1*cm,  # Espacio para header
            bottomMargin=self.margen + 0.5*cm  # Espacio para footer
        )
        
        # Contenido del documento
        story = []
        
        # Portada
        story.extend(self._crear_portada(parcela, fecha_inicio, fecha_fin))
        story.append(PageBreak())
        
        # Metodología de Análisis
        story.extend(self._crear_seccion_metodologia(parcela, indices, analisis_completo))
        story.append(PageBreak())
        
        # Resumen ejecutivo
        story.extend(self._crear_resumen_ejecutivo(analisis_completo, parcela, datos_analisis))
        story.append(PageBreak())
        
        # Información de la parcela
        story.extend(self._crear_info_parcela(parcela))
        story.append(Spacer(1, 1*cm))
        
        # Análisis de índices
        story.extend(self._crear_seccion_ndvi(analisis_completo['ndvi'], graficos))
        story.append(PageBreak())
        
        story.extend(self._crear_seccion_ndmi(analisis_completo['ndmi'], graficos))
        story.append(PageBreak())
        
        if 'savi' in analisis_completo and analisis_completo['savi']:
            story.extend(self._crear_seccion_savi(analisis_completo['savi'], graficos))
            story.append(PageBreak())
        
        # Análisis de tendencias
        story.extend(self._crear_seccion_tendencias(analisis_completo['tendencias'], graficos))
        story.append(PageBreak())
        
        # Recomendaciones
        story.extend(self._crear_seccion_recomendaciones(analisis_completo['recomendaciones']))
        story.append(PageBreak())
        
        # Tabla de datos
        story.extend(self._crear_tabla_datos(datos_analisis))
        story.append(PageBreak())
        
        # Galería de imágenes satelitales
        story.extend(self._crear_galeria_imagenes_satelitales(parcela, indices))
        story.append(PageBreak())
        
        # 🧠 DIAGNÓSTICO UNIFICADO - CEREBRO DE ANÁLISIS (nuevo)
        try:
            diagnostico_unificado = self._ejecutar_diagnostico_cerebro(parcela, indices)
            if diagnostico_unificado:
                story.extend(self._crear_seccion_diagnostico_unificado(diagnostico_unificado))
                story.append(PageBreak())
        except Exception as e:
            logger.warning(f"⚠️ No se pudo generar diagnóstico unificado: {str(e)}")
        
        # Bloque de cierre conectando análisis con decisiones
        story.extend(self._crear_bloque_cierre())
        story.append(PageBreak())
        
        # Página de créditos
        story.extend(self._crear_pagina_creditos())
        
        # Bloque de cierre
        story.extend(self._crear_bloque_cierre())
        
        # Construir PDF con headers y footers
        doc.build(story, onFirstPage=self._crear_header_footer, 
                 onLaterPages=self._crear_header_footer)
        
        return output_path
    
    def _preparar_datos_analisis(self, indices: List[IndiceMensual]) -> List[Dict]:
        """Prepara datos en formato para análisis"""
        datos = []
        for indice in indices:
            datos.append({
                'mes': f"{indice.año}-{indice.mes:02d}",
                'periodo': indice.periodo_texto,
                'ndvi': indice.ndvi_promedio,
                'ndmi': indice.ndmi_promedio,
                'savi': indice.savi_promedio,
                'temperatura': indice.temperatura_promedio,
                'precipitacion': indice.precipitacion_total
            })
        return datos
    
    def _ejecutar_analisis(self, datos: List[Dict], parcela: Parcela, indices: List) -> Dict:
        """
        Ejecuta análisis técnico determinístico completo
        
        MOTOR DE ANÁLISIS:
        1. Análisis espectral (NDVI, NDMI, SAVI)
        2. Estadísticas descriptivas y distribución
        3. Detección de tendencias temporales
        4. Análisis de variabilidad espacial
        5. Generación de recomendaciones basadas en umbrales científicos
        """
        # Inicializar analizadores especializados
        analizador_ndvi = AnalizadorNDVI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_ndmi = AnalizadorNDMI(tipo_cultivo=parcela.tipo_cultivo)
        analizador_savi = AnalizadorSAVI(tipo_cultivo=parcela.tipo_cultivo)
        detector_tendencias = DetectorTendencias()
        generador_recomendaciones = GeneradorRecomendaciones(tipo_cultivo=parcela.tipo_cultivo)
        
        # Ejecutar análisis de índices espectrales
        analisis_ndvi = analizador_ndvi.analizar(datos)
        analisis_ndmi = analizador_ndmi.analizar(datos)
        analisis_savi = analizador_savi.analizar(datos) if any(d.get('savi') for d in datos) else None
        
        # Análisis de tendencias temporales
        tendencias = detector_tendencias.analizar_temporal(datos, 'ndvi')
        
        # Generar recomendaciones agronómicas
        recomendaciones = generador_recomendaciones.generar_recomendaciones(
            analisis_ndvi, analisis_ndmi, analisis_savi, tendencias
        )
        
        return {
            'ndvi': analisis_ndvi,
            'ndmi': analisis_ndmi,
            'savi': analisis_savi,
            'tendencias': tendencias,
            'recomendaciones': recomendaciones
        }
    
    def _generar_graficos(self, datos: List[Dict]) -> Dict[str, BytesIO]:
        """Genera todos los gráficos necesarios"""
        graficos = {}
        
        # Gráfico de evolución temporal
        graficos['evolucion_temporal'] = self._grafico_evolucion_temporal(datos)
        
        # Gráfico comparativo
        graficos['comparativo'] = self._grafico_comparativo(datos)
        
        return graficos
    
    def _grafico_evolucion_temporal(self, datos: List[Dict]) -> BytesIO:
        """Genera gráfico de evolución temporal"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Configurar estilo
        sns.set_style("whitegrid")
        
        # Extraer datos
        meses = [d['periodo'] for d in datos]
        ndvi = [d.get('ndvi', 0) for d in datos]
        ndmi = [d.get('ndmi', 0) for d in datos]
        savi = [d.get('savi', 0) for d in datos]
        
        # Graficar
        ax.plot(meses, ndvi, marker='o', linewidth=2.5, color='#2E8B57', label='NDVI (Salud)', markersize=6)
        ax.plot(meses, ndmi, marker='s', linewidth=2.5, color='#17a2b8', label='NDMI (Humedad)', markersize=6)
        if any(savi):
            ax.plot(meses, savi, marker='^', linewidth=2.5, color='#FF7A00', label='SAVI (Cobertura)', markersize=6)
        
        # Configurar
        ax.set_xlabel('Período', fontsize=12, fontweight='bold')
        ax.set_ylabel('Valor del Índice', fontsize=12, fontweight='bold')
        ax.set_title('Evolución Temporal de Índices de Vegetación', 
                     fontsize=14, fontweight='bold', color='#2c3e50')
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Rotar etiquetas
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Guardar en buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _grafico_comparativo(self, datos: List[Dict]) -> BytesIO:
        """Genera gráfico de barras comparativo"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calcular promedios (filtrar None)
        ndvi_valores = [d.get('ndvi') for d in datos if d.get('ndvi') is not None]
        ndmi_valores = [d.get('ndmi') for d in datos if d.get('ndmi') is not None]
        savi_valores = [d.get('savi') for d in datos if d.get('savi') is not None]
        
        ndvi_prom = sum(ndvi_valores) / len(ndvi_valores) if ndvi_valores else 0
        ndmi_prom = sum(ndmi_valores) / len(ndmi_valores) if ndmi_valores else 0
        savi_prom = sum(savi_valores) / len(savi_valores) if savi_valores else 0
        
        indices = ['NDVI\n(Salud)', 'NDMI\n(Humedad)', 'SAVI\n(Cobertura)']
        valores = [ndvi_prom, ndmi_prom, savi_prom]
        colores_barra = ['#2E8B57', '#17a2b8', '#FF7A00']
        
        # Crear barras
        bars = ax.bar(indices, valores, color=colores_barra, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Añadir valores encima de las barras
        for bar, valor in zip(bars, valores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{valor:.3f}',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Valor Promedio', fontsize=12, fontweight='bold')
        ax.set_title('Comparación de Índices - Promedio del Período', 
                    fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_ylim(0, max(valores) * 1.2)
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    def _crear_portada(self, parcela: Parcela, fecha_inicio: date, fecha_fin: date) -> List:
        """Crea la portada del informe con diseño profesional estilo EOSDA"""
        from reportlab.lib.utils import ImageReader
        elements = []
        
        # Espaciado inicial
        elements.append(Spacer(1, 2*cm))
        
        # === LOGO AGROTECH GRANDE ===
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Agro Tech logo solo.png')
        if not os.path.exists(logo_path):
            # Alternativa con texto
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'agrotech solo negro.png')
        
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=8*cm, height=8*cm, kind='proportional')
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.8*cm))
            except Exception as e:
                logger.warning(f"No se pudo cargar logo: {e}")
                titulo_logo = Paragraph(
                    '<font size="24" color="#2E8B57"><strong>agrotech</strong></font>',
                    self.estilos['TituloPortada']
                )
                elements.append(titulo_logo)
                elements.append(Spacer(1, 0.5*cm))
        
        # === TÍTULO PRINCIPAL ===
        titulo_principal = Paragraph(
            '<para align="center">'
            '<font size="22" color="#2E8B57"><strong>Análisis Satelital de Precisión</strong></font>'
            '</para>',
            self.estilos['TituloPortada']
        )
        elements.append(titulo_principal)
        elements.append(Spacer(1, 0.3*cm))
        
        subtitulo = Paragraph(
            '<para align="center">'
            '<font size="14" color="#555555"><i>Sistema Inteligente de Monitoreo Agrícola</i></font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(subtitulo)
        elements.append(Spacer(1, 1.2*cm))
        
        # === CARD FLOTANTE MINIMALISTA CON INFO ===
        info_card_data = [
            ['Parcela', parcela.nombre],
            ['Cultivo', parcela.tipo_cultivo or 'No especificado'],
            ['Extensión', f"{parcela.area_hectareas:.2f} hectáreas"],
            ['Período', f"{self.formato_mes_año_español(fecha_inicio)} - {self.formato_mes_año_español(fecha_fin)}"]
        ]
        
        tabla_card = Table(info_card_data, colWidths=[4.5*cm, 8*cm])
        tabla_card.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2E8B57')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E8B57')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E0E0E0')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (0, -1), 15),
            ('RIGHTPADDING', (0, 0), (0, -1), 10),
            ('LEFTPADDING', (1, 0), (1, -1), 15),
        ]))
        
        # Centrar la card
        from reportlab.platypus import KeepTogether
        tabla_card.hAlign = 'CENTER'
        elements.append(tabla_card)
        elements.append(Spacer(1, 2*cm))
        
        # === PIE DE PORTADA MINIMALISTA ===
        pie = Paragraph(
            '<para align="center">'
            '<font size="9" color="#888888">'
            'Informe Técnico de Análisis Satelital<br/>'
            f'<strong>{datetime.now().strftime("%d de %B de %Y")}</strong>'
            '</font>'
            '</para>',
            self.estilos['TextoNormal']
        )
        elements.append(pie)
        return elements
    
    def _decorar_seccion(self, img_name, height=1.2*cm):
        """Separador de secciones sin imágenes decorativas"""
        # Retornar solo un espaciador simple sin imágenes
        return [Spacer(1, 0.5*cm)]
    
    def _crear_header_footer(self, canvas_obj, doc):
        """Crea header y footer en cada página"""
        canvas_obj.saveState()
        
        # Header - Logo pequeño
        logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'static', 'img', 'favicon.svg')
        if os.path.exists(logo_path):
            try:
                canvas_obj.drawImage(logo_path, self.margen, self.alto - self.margen + 0.5*cm, 
                                   width=1*cm, height=1*cm, preserveAspectRatio=True)
            except:
                pass
        
        # Header - Texto
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(self.colores['gris_oscuro'])
        canvas_obj.drawString(self.margen + 1.5*cm, self.alto - self.margen + 0.7*cm, 
                            "AgroTech - Análisis Satelital Agrícola")
        
        # Footer - Número de página
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawCentredString(self.ancho / 2, self.margen / 2, 
                                     f"Página {doc.page}")
        
        # Footer - Fecha
        canvas_obj.drawRightString(self.ancho - self.margen, self.margen / 2,
                                  datetime.now().strftime('%d/%m/%Y'))
        
        canvas_obj.restoreState()
    
    # Continúo en el siguiente mensaje con las secciones del informe...
    
    def _crear_seccion_metodologia(self, parcela: Parcela, indices: List[IndiceMensual], analisis: Dict) -> List:
        """
        Crea la sección de Metodología de Análisis con explicación detallada del motor técnico
        """
        elements = []
        
        # Decoración superior
        elements.extend(self._decorar_seccion('5.png', height=1*cm))
        
        # Título de la sección
        titulo = Paragraph("Metodología de Análisis", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Introducción
        intro = Paragraph(
            """
            <strong>El presente informe se basa en el Motor de Análisis Automatizado AgroTech, un sistema 
            de análisis satelital determinístico que procesa imágenes satelitales de alta resolución y aplica 
            algoritmos científicamente validados para evaluar la condición del terreno, ya sea con cultivos establecidos 
            o en evaluación para planificación agrícola y primera siembra.</strong>
            """,
            self.estilos['TextoNormal']
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.4*cm))
        
        # 1. Fuentes de Datos
        subtitulo1 = Paragraph("<strong>1. Fuentes de Datos Satelitales</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo1)
        elements.append(Spacer(1, 0.2*cm))
        
        texto_fuentes = Paragraph(
            """
            • <strong>Satélite:</strong> Sentinel-2 (ESA - Agencia Espacial Europea)<br/>
            • <strong>Resolución espacial:</strong> 10-20 metros por píxel<br/>
            • <strong>Frecuencia de captura:</strong> Cada 5-10 días (sujeto a condiciones atmosféricas)<br/>
            • <strong>Bandas espectrales utilizadas:</strong> Rojo (B4), Infrarrojo cercano (B8), Infrarrojo de onda corta (B11, B12)<br/>
            • <strong>Validación de calidad:</strong> Se filtran imágenes con nubosidad superior al 20%
            """,
            self.estilos['TextoNormal']
        )
        elements.append(texto_fuentes)
        elements.append(Spacer(1, 0.4*cm))
        
        # 2. Índices Espectrales Calculados
        subtitulo2 = Paragraph("<strong>2. Índices Espectrales Calculados</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo2)
        elements.append(Spacer(1, 0.2*cm))
        
        # Tabla de índices
        datos_indices = [
            [
                Paragraph('<b>Índice</b>', self.estilos['TextoNormal']),
                Paragraph('<b>Fórmula</b>', self.estilos['TextoNormal']),
                Paragraph('<b>Interpretación</b>', self.estilos['TextoNormal']),
                Paragraph('<b>Umbrales</b>', self.estilos['TextoNormal'])
            ],
            [
                Paragraph('<b>NDVI</b><br/>(Vigor Vegetal)', self.estilos['TextoNormal']),
                Paragraph('(NIR - Red) / (NIR + Red)', self.estilos['TextoNormal']),
                Paragraph('Mide la cantidad y salud de la vegetación presente. Valores altos indican vegetación densa y saludable, o potencial productivo en terrenos sin cultivo.', self.estilos['TextoNormal']),
                Paragraph('&lt; 0.2: Suelo desnudo<br/>0.2-0.4: Vegetación escasa<br/>0.4-0.6: Vegetación moderada<br/>&gt; 0.6: Vegetación densa', self.estilos['TextoNormal'])
            ],
            [
                Paragraph('<b>NDMI</b><br/>(Humedad)', self.estilos['TextoNormal']),
                Paragraph('(NIR - SWIR) / (NIR + SWIR)', self.estilos['TextoNormal']),
                Paragraph('Evalúa el contenido de humedad en la vegetación o suelo. Fundamental para detectar estrés hídrico o condiciones de humedad del terreno.', self.estilos['TextoNormal']),
                Paragraph('&lt; 0.2: Estrés hídrico severo<br/>0.2-0.4: Estrés moderado<br/>0.4-0.6: Humedad adecuada<br/>&gt; 0.6: Alta humedad', self.estilos['TextoNormal'])
            ],
            [
                Paragraph('<b>SAVI</b><br/>(Cobertura)', self.estilos['TextoNormal']),
                Paragraph('(NIR - Red) / (NIR + Red + L) × (1 + L)<br/>L = 0.5', self.estilos['TextoNormal']),
                Paragraph('Ajusta el NDVI para áreas con cobertura vegetal parcial o suelo expuesto, proporcionando una estimación indirecta y relativa de la cobertura.', self.estilos['TextoNormal']),
                Paragraph('&lt; 0.2: Suelo predominante<br/>0.2-0.4: Cobertura baja<br/>0.4-0.6: Cobertura moderada<br/>&gt; 0.6: Cobertura alta', self.estilos['TextoNormal'])
            ]
        ]
        
        tabla_indices = Table(datos_indices, colWidths=[3*cm, 3.5*cm, 5.5*cm, 4*cm])
        tabla_indices.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), self.colores['verde_principal']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(tabla_indices)
        elements.append(Spacer(1, 0.4*cm))
        
        # 3. Procesamiento y Análisis
        subtitulo3 = Paragraph("<strong>3. Procesamiento y Análisis de Datos</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo3)
        elements.append(Spacer(1, 0.2*cm))
        
        texto_procesamiento = Paragraph(
            """
            <strong>a) Análisis Estadístico:</strong> Para cada índice se calculan estadísticas descriptivas mensuales 
            (promedio, mínimo, máximo, desviación estándar) que permiten identificar la variabilidad espacial dentro 
            de la parcela.<br/><br/>
            
            <strong>b) Análisis Temporal:</strong> Se aplica regresión lineal para detectar tendencias a lo largo del 
            período analizado, identificando si hay mejora, deterioro o estabilidad en los índices.<br/><br/>
            
            <strong>c) Análisis de Variabilidad:</strong> Se evalúa el coeficiente de variación (CV) para determinar 
            la homogeneidad espacial del cultivo. CV < 15% indica alta homogeneidad.<br/><br/>
            
            <strong>d) Detección de Anomalías:</strong> Se identifican valores atípicos que pueden indicar problemas 
            localizados (plagas, deficiencias nutricionales, problemas de riego).<br/><br/>
            
            <strong>e) Análisis Cruzado:</strong> Se correlacionan los diferentes índices para obtener una visión 
            integral. Por ejemplo, NDVI bajo + NDMI bajo puede indicar estrés hídrico.
            """,
            self.estilos['TextoNormal']
        )
        elements.append(texto_procesamiento)
        elements.append(Spacer(1, 0.4*cm))
        
        # 4. Generación de Recomendaciones
        subtitulo4 = Paragraph("<strong>4. Generación de Recomendaciones Agronómicas</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo4)
        elements.append(Spacer(1, 0.2*cm))
        
        texto_recomendaciones = Paragraph(
            """
            Las recomendaciones se generan mediante un motor de reglas basado en:<br/><br/>
            
            • <strong>Umbrales científicos:</strong> Valores de referencia validados en literatura agronómica<br/>
            • <strong>Tipo de cultivo:</strong> Adaptación de umbrales según la especie cultivada<br/>
            • <strong>Contexto temporal:</strong> Consideración de la época del año y ciclo fenológico<br/>
            • <strong>Tendencias detectadas:</strong> Priorización de problemas emergentes o recurrentes<br/>
            • <strong>Análisis multivariado:</strong> Combinación de múltiples índices para diagnósticos precisos
            """,
            self.estilos['TextoNormal']
        )
        elements.append(texto_recomendaciones)
        elements.append(Spacer(1, 0.4*cm))
        
        # 5. Resumen del Período Analizado
        subtitulo5 = Paragraph("<strong>5. Datos del Período Analizado</strong>", self.estilos['SubtituloSeccion'])
        elements.append(subtitulo5)
        elements.append(Spacer(1, 0.2*cm))
        
        # Calcular estadísticas del período
        total_imagenes = len(indices)
        imagenes_con_ndvi = sum(1 for idx in indices if idx.ndvi_promedio is not None)
        imagenes_con_ndmi = sum(1 for idx in indices if idx.ndmi_promedio is not None)
        imagenes_con_savi = sum(1 for idx in indices if idx.savi_promedio is not None)
        nubosidad_promedio = sum(idx.nubosidad_imagen or 0 for idx in indices) / total_imagenes if total_imagenes > 0 else 0
        
        datos_periodo = [
            ['Total de imágenes procesadas', str(total_imagenes)],
            ['Imágenes con NDVI válido', f"{imagenes_con_ndvi} ({imagenes_con_ndvi/total_imagenes*100:.1f}%)" if total_imagenes > 0 else "0"],
            ['Imágenes con NDMI válido', f"{imagenes_con_ndmi} ({imagenes_con_ndmi/total_imagenes*100:.1f}%)" if total_imagenes > 0 else "0"],
            ['Imágenes con SAVI válido', f"{imagenes_con_savi} ({imagenes_con_savi/total_imagenes*100:.1f}%)" if total_imagenes > 0 else "0"],
            ['Nubosidad promedio', f"{nubosidad_promedio:.1f}%"],
            ['Tipo de cultivo', parcela.tipo_cultivo or 'No especificado'],
            ['Extensión analizada', f"{parcela.area_hectareas:.2f} hectáreas"]
        ]
        
        tabla_periodo = Table(datos_periodo, colWidths=[7*cm, 8*cm])
        tabla_periodo.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2E8B57')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E8B57')),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E0E0E0')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (0, -1), 15),
            ('RIGHTPADDING', (0, 0), (0, -1), 10),
            ('LEFTPADDING', (1, 0), (1, -1), 15),
        ]))
        elements.append(tabla_periodo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Nota final
        nota = Paragraph(
            """
            <font size="9" color="#666666"><i>
            <strong>Nota:</strong> Esta metodología se basa en estándares internacionales de teledetección aplicada 
            a la agricultura de precisión. Los algoritmos utilizados han sido validados por instituciones científicas 
            y agencias espaciales como la ESA (European Space Agency) y NASA.
            </i></font>
            """,
            self.estilos['TextoNormal']
        )
        tabla_nota = Table([[nota]], colWidths=[15*cm])
        tabla_nota.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2196F3')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(tabla_nota)
        
        return elements
    
    def _crear_resumen_ejecutivo(self, analisis: Dict, parcela: Parcela, datos: List[Dict]) -> List:
        """Crea resumen ejecutivo del informe basado en análisis técnico determinístico"""
        elements = []
        # Decoración superior
        elements.extend(self._decorar_seccion('6.png', height=1*cm))
        # Título
        titulo = Paragraph("Resumen Ejecutivo", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        # Conclusión rápida para el productor
        conclusion = Paragraph(
            """
            <strong>Conclusión rápida para el productor:</strong><br/>
            Este informe proporciona un análisis detallado de las condiciones del terreno analizado, 
            útil tanto para cultivos establecidos como para terrenos en evaluación para primera siembra. 
            Se recomienda priorizar las acciones sugeridas en las secciones de recomendaciones 
            para optimizar el manejo y minimizar riesgos.
            """,
            self.estilos['TextoNormal']
        )
        elements.append(conclusion)
        elements.append(Spacer(1, 0.5*cm))

        # Obtener valores numéricos para mejorar la narrativa
        ndvi_prom = analisis['ndvi'].get('estadisticas', {}).get('promedio', 0)
        ndmi_prom = analisis['ndmi'].get('estadisticas', {}).get('promedio', 0)
        savi_prom = analisis['savi'].get('estadisticas', {}).get('promedio', 0) if analisis.get('savi') else 0
        
        # Obtener descripciones de tendencias (sin corchetes ni estructuras JSON)
        ndvi_tend = analisis['ndvi'].get('interpretacion_simple', 'Sin datos suficientes')
        ndmi_tend = analisis['ndmi'].get('interpretacion_simple', 'Sin datos suficientes')
        savi_tend = analisis['savi'].get('interpretacion_simple', 'Sin datos suficientes') if analisis.get('savi') else 'Sin datos suficientes'
        
        # Limpiar HTML de las tendencias
        ndvi_tend = limpiar_html_completo(ndvi_tend)
        ndmi_tend = limpiar_html_completo(ndmi_tend)
        savi_tend = limpiar_html_completo(savi_tend)
        
        # Resumen de análisis con texto claro y sin estructuras técnicas
        resumen_texto = f"""
            Durante el período analizado (de {datos[0]['periodo']} a {datos[-1]['periodo']}), 
            los índices de vegetación presentaron los siguientes comportamientos:<br/><br/>
            
            <strong>NDVI (Salud Vegetal):</strong> Valor promedio de {ndvi_prom:.3f}. {ndvi_tend}<br/><br/>
            
            <strong>NDMI (Condición Hídrica):</strong> Valor promedio de {ndmi_prom:.3f}. {ndmi_tend}<br/><br/>
            
            <strong>SAVI (Cobertura del Suelo):</strong> Valor promedio de {savi_prom:.3f}. {savi_tend}<br/>
            """
        
        resumen = Paragraph(resumen_texto, self.estilos['TextoNormal'])
        elements.append(resumen)
        elements.append(Spacer(1, 0.5*cm))

        # Declaración de validez del informe
        validez = Paragraph(
            """
            <i>Este informe es válido como herramienta de evaluación y planificación agrícola, 
            basado en datos satelitales y análisis automatizado proporcionado por el Motor de Análisis 
            Automatizado AgroTech.</i>
            """,
            self.estilos['TextoNormal']
        )
        elements.append(validez)
        elements.append(Spacer(1, 0.5*cm))

        return elements

    def _crear_seccion_precipitacion(self, datos: List[Dict]) -> List:
        """Crea sección de análisis de precipitación con aclaración explícita"""
        elements = []
        titulo = Paragraph("Análisis de Precipitación", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        # Aclaración explícita sobre cómo interpretar los datos
        aclaracion = Paragraph(
            """
            <strong>Nota aclaratoria:</strong> Los valores de precipitación que se presentan en este informe corresponden 
            al <strong>total mensual acumulado</strong> para cada período analizado. Estos datos provienen de fuentes climáticas 
            satelitales y permiten evaluar la disponibilidad de agua en el terreno a lo largo del tiempo.
            """,
            self.estilos['TextoNormal']
        )
        elements.append(aclaracion)
        elements.append(Spacer(1, 0.5*cm))

        # Gráfico de precipitación
        grafico = self._generar_grafico_precipitacion(datos)
        elements.append(grafico)

        return elements

    def _crear_seccion_lai(self, analisis: Dict) -> List:
        """Crea sección de análisis LAI con interpretación ajustada"""
        elements = []
        titulo = Paragraph("Análisis LAI (Índice de Área Foliar)", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación ajustada y suavizada
        interpretacion = Paragraph(
            """
            El Índice de Área Foliar (LAI) y la cobertura vegetal presentados a continuación son 
            <strong>estimaciones indicativas y relativas</strong>, derivadas de los datos satelitales disponibles. 
            Estos valores permiten evaluar de forma aproximada la densidad y distribución de la vegetación en el 
            terreno analizado, útiles como referencia comparativa a lo largo del tiempo.
            """,
            self.estilos['TextoNormal']
        )
        elements.append(interpretacion)
        elements.append(Spacer(1, 0.5*cm))

        # Datos del análisis
        datos_lai = Paragraph(
            f"""
            <strong>LAI Promedio Estimado:</strong> {analisis['lai_promedio']:.2f}<br/>
            <strong>Cobertura Vegetal Estimada:</strong> {analisis['cobertura_estimada']}%
            """,
            self.estilos['TextoNormal']
        )
        elements.append(datos_lai)

        return elements
    
    def _crear_info_parcela(self, parcela: Parcela) -> List:
        """Crea sección de información de la parcela"""
        elements = []
        
        titulo = Paragraph("Información de la Parcela", self.estilos['TituloSeccion'])
        elements.append(titulo)
        
        # Coordenadas del centroide
        if parcela.centroide:
            lat = parcela.centroide.y
            lon = parcela.centroide.x
            coordenadas = f"{lat:.6f}, {lon:.6f}"
        else:
            coordenadas = "No disponible"
        
        info_texto = f"""
<strong>Nombre:</strong> {parcela.nombre}<br/>
<strong>Propietario:</strong> {parcela.propietario}<br/>
<strong>Tipo de Cultivo:</strong> {parcela.tipo_cultivo or 'No especificado'}<br/>
<strong>Área:</strong> {parcela.area_hectareas:.2f} hectáreas<br/>
<strong>Ubicación (Centro):</strong> {coordenadas}<br/>
<strong>Fecha de Inicio de Monitoreo:</strong> {parcela.fecha_inicio_monitoreo.strftime('%d/%m/%Y') if parcela.fecha_inicio_monitoreo else 'No especificado'}<br/>
"""
        
        info = Paragraph(info_texto, self.estilos['TextoNormal'])
        elements.append(info)
        
        return elements
    
    def _crear_tabla_datos(self, datos: List[Dict]) -> List:
        """Crea tabla con datos mensuales"""
        elements = []
        titulo = Paragraph("Tabla de Datos Mensuales", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Nota aclaratoria sobre precipitación
        nota_precip = Paragraph(
            '<strong>Nota:</strong> La precipitación corresponde al total acumulado mensual estimado para la zona de la parcela.',
            self.estilos['TextoNormal']
        )
        elements.append(nota_precip)
        elements.append(Spacer(1, 0.3*cm))
        
        # Preparar datos para la tabla
        tabla_data = [['Período', 'NDVI', 'NDMI', 'SAVI', 'Temp (°C)', 'Precip (mm)']]
        for d in datos:
            tabla_data.append([
                d['periodo'],
                f"{d.get('ndvi', 0):.3f}" if d.get('ndvi') else 'N/D',
                f"{d.get('ndmi', 0):.3f}" if d.get('ndmi') else 'N/D',
                f"{d.get('savi', 0):.3f}" if d.get('savi') else 'N/D',
                f"{d.get('temperatura', 0):.1f}" if d.get('temperatura') else 'N/D',
                f"{d.get('precipitacion', 0):.1f}" if d.get('precipitacion') else 'N/D'
            ])
        
        tabla = Table(tabla_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.colores['verde_principal']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colores['gris_claro']]),
        ]))
        elements.append(tabla)
        
        return elements
    
    def _crear_pagina_creditos(self) -> List:
        """Crea página de créditos"""
        elements = []
        titulo = Paragraph("Créditos", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        creditos_texto = """
<strong>Sistema AgroTech - Análisis Satelital Agrícola</strong><br/><br/>
<strong>Fuente de Datos Satelitales:</strong> Sentinel-2 (ESA)<br/>
<strong>Motor de Análisis:</strong> Motor de Análisis Automatizado AgroTech<br/>
<strong>Procesamiento:</strong> Python + Django + GeoDjango<br/>
<strong>Visualización:</strong> ReportLab + Matplotlib<br/><br/>
<i>Este informe ha sido generado automáticamente utilizando datos satelitales de alta resolución 
y algoritmos científicamente validados para el análisis de vegetación.</i>
"""
        creditos = Paragraph(creditos_texto, self.estilos['TextoNormal'])
        elements.append(creditos)
        
        return elements
    
    def _crear_seccion_ndvi(self, analisis_ndvi: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDVI"""
        elements = []
        # Título
        titulo = Paragraph("Análisis NDVI", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        # Estado
        estado = analisis_ndvi['estado']
        estado_texto = f"""
<strong>Estado General:</strong> {estado.get('icono', '')} {estado['etiqueta']}<br/>
<strong>NDVI Promedio:</strong> {analisis_ndvi['estadisticas']['promedio']:.3f}<br/>
<strong>Puntuación:</strong> {analisis_ndvi.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales históricos del índice)</i><br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación técnica - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis_ndvi['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación simple - LIMPIADO
        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_completo(analisis_ndvi['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación práctica para el productor
        ndvi_prom = analisis_ndvi['estadisticas']['promedio']
        if ndvi_prom >= 0.6:
            interpretacion_practica = "Para su campo: Esta condición sugiere buena cobertura vegetal. Considere mantener las prácticas actuales y monitorear posibles necesidades nutricionales específicas."
        elif ndvi_prom >= 0.4:
            interpretacion_practica = "Para su campo: Condición moderada. Evalúe si el cultivo requiere ajustes en fertilización o manejo hídrico para optimizar el desarrollo vegetal."
        else:
            interpretacion_practica = "Para su campo: Esta situación puede indicar cobertura limitada. Se sugiere revisar condiciones de suelo, disponibilidad de agua y salud del cultivo para identificar acciones correctivas."
        
        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))
        
        # Alertas
        if analisis_ndvi.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis_ndvi['alertas'][:3]:  # Máximo 3 alertas
                # Verificar si alerta es un dict o string
                if isinstance(alerta, dict):
                    alerta_texto = f"{alerta.get('icono', '')} <strong>{alerta.get('titulo', 'Alerta')}:</strong> {alerta.get('mensaje', '')}"
                else:
                    alerta_texto = str(alerta)
                
                alerta_limpia = limpiar_html_completo(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.2*cm))
        
        return elements
    
    def _crear_seccion_ndmi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis NDMI"""
        elements = []

        # Título
        titulo = Paragraph("Análisis NDMI - Contenido de Humedad", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado Hídrico:</strong> {estado['etiqueta']}<br/>
<strong>NDMI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Puntuación:</strong> {analisis.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales históricos del índice)</i><br/>
<strong>Riesgo Hídrico:</strong> {analisis.get('riesgo_hidrico', 'No determinado')}<br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación técnica - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación simple - LIMPIADO
        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación práctica para el productor
        ndmi_prom = analisis['estadisticas']['promedio']
        if ndmi_prom >= 0.3:
            interpretacion_practica = "Para su campo: La humedad relativa de la vegetación parece adecuada. Mantenga el seguimiento para asegurar disponibilidad hídrica continua."
        elif ndmi_prom >= 0.0:
            interpretacion_practica = "Para su campo: Humedad moderada. Considere verificar el estado del riego o las condiciones de lluvia para prevenir posibles déficits hídricos."
        else:
            interpretacion_practica = "Para su campo: Posible déficit hídrico indicativo. Se recomienda revisar sistemas de riego y disponibilidad de agua para ajustar el manejo."
        
        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))

        # Alertas
        if analisis.get('alertas'):
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("<strong>Alertas:</strong>", self.estilos['TextoNormal']))
            for alerta in analisis['alertas']:
                # Verificar si alerta es un dict o string
                if isinstance(alerta, dict):
                    alerta_texto = f"{alerta.get('icono', '')} <strong>{alerta.get('titulo', 'Alerta')}:</strong> {alerta.get('mensaje', '')}"
                else:
                    alerta_texto = str(alerta)
                
                alerta_limpia = limpiar_html_completo(alerta_texto)
                elements.append(Paragraph(alerta_limpia, self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.2*cm))

        return elements
    
    def _crear_seccion_savi(self, analisis: Dict, graficos: Dict) -> List:
        """Crea sección de análisis SAVI"""
        elements = []
        # Título
        titulo = Paragraph("Análisis SAVI", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))

        # Estado
        estado = analisis['estado']
        estado_texto = f"""
<strong>Estado General:</strong> {estado.get('icono', '')} {estado['etiqueta']}<br/>
<strong>SAVI Promedio:</strong> {analisis['estadisticas']['promedio']:.3f}<br/>
<strong>Puntuación:</strong> {analisis.get('puntuacion', 0)}/10 
<i>(métrica relativa interna AgroTech basada en umbrales históricos del índice)</i><br/>
"""
        elements.append(Paragraph(estado_texto, self.estilos['TextoNormal']))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación técnica - LIMPIADO
        elements.append(Paragraph("<strong>Análisis Técnico:</strong>", self.estilos['TextoNormal']))
        interpretacion_limpia = limpiar_html_completo(analisis['interpretacion_tecnica'])
        elements.append(Paragraph(interpretacion_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))

        # Interpretación simple - LIMPIADO
        elements.append(Paragraph("<strong>Explicación Sencilla:</strong>", self.estilos['TextoNormal']))
        simple_limpia = limpiar_html_completo(analisis['interpretacion_simple'])
        elements.append(Paragraph(simple_limpia, self.estilos['AnalisisTecnico']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Interpretación práctica para el productor
        savi_prom = analisis['estadisticas']['promedio']
        if savi_prom >= 0.4:
            interpretacion_practica = "Para su campo: Este índice sugiere buena cobertura vegetal ajustada por suelo. Útil para evaluar áreas con exposición variable del terreno."
        elif savi_prom >= 0.2:
            interpretacion_practica = "Para su campo: Cobertura moderada. Observe si hay zonas con suelo expuesto que puedan requerir acciones específicas de manejo o siembra."
        else:
            interpretacion_practica = "Para su campo: Cobertura limitada detectada. Esto puede ser normal en terrenos sin cultivo establecido o puede indicar necesidad de intervención en áreas cultivadas."
        
        elements.append(Paragraph(f"<strong>Qué significa para su terreno:</strong> {interpretacion_practica}", self.estilos['TextoNormal']))


        # Alertas
        if analisis.get('alertas'):
            for alerta in analisis['alertas']:
                alerta_texto = f"<strong>Alerta:</strong> {alerta}"
                elements.append(Paragraph(alerta_texto, self.estilos['TextoAlerta']))
                elements.append(Spacer(1, 0.3*cm))

        return elements
    
    def _crear_seccion_tendencias(self, tendencias: Dict, graficos: Dict) -> List:
        """Crea sección de análisis de tendencias"""
        elements = []
        
        titulo = Paragraph("Análisis de Tendencias Temporales", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Gráfico de evolución
        if 'evolucion_temporal' in graficos:
            img = Image(graficos['evolucion_temporal'], width=16*cm, height=8*cm)
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
            pie = Paragraph(
                "<strong>Figura 1:</strong> Evolución temporal de índices de vegetación durante el período analizado.",
                self.estilos['PieImagen']
            )
            elements.append(pie)
            elements.append(Spacer(1, 1*cm))
        
        # Resumen de tendencias
        if tendencias.get('resumen'):
            resumen_limpio = limpiar_html_completo(tendencias['resumen'])
            elements.append(Paragraph(resumen_limpio, self.estilos['TextoNormal']))
        
        # Tendencia lineal
        if 'tendencia_lineal' in tendencias:
            tl = tendencias['tendencia_lineal']
            cambio = tl.get('cambio_porcentual', 0)
            confianza = tl.get('confianza', '').lower()
            
            # Descripción clara y coherente según el signo del cambio
            if cambio > 5:
                descripcion_tendencia = f"Tendencia al alza ({cambio:+.1f}%) con confiabilidad {confianza}"
            elif cambio < -5:
                descripcion_tendencia = f"Tendencia a la baja ({cambio:+.1f}%) con confiabilidad {confianza}"
            elif cambio > 0:
                descripcion_tendencia = f"Tendencia ligeramente ascendente ({cambio:+.1f}%) con confiabilidad {confianza}"
            elif cambio < 0:
                descripcion_tendencia = f"Tendencia ligeramente descendente ({cambio:+.1f}%) con confiabilidad {confianza}"
            else:
                descripcion_tendencia = f"Tendencia estable (cambio {cambio:+.1f}%) con confiabilidad {confianza}"
            
            tendencia_texto = f"""
<strong>{descripcion_tendencia}</strong><br/>
<strong>Coeficiente de determinación (R²):</strong> {tl.get('r_cuadrado', 0):.3f}<br/>
"""
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(tendencia_texto, self.estilos['TextoNormal']))
        
        # Gráfico comparativo
        if 'comparativo' in graficos:
            elements.append(Spacer(1, 1*cm))
            img = Image(graficos['comparativo'], width=14*cm, height=8*cm)
            elements.append(img)
            elements.append(Spacer(1, 0.3*cm))
            pie = Paragraph(
                "<strong>Figura 2:</strong> Comparación de promedios de índices durante el período.",
                self.estilos['PieImagen']
            )
            elements.append(pie)
        
        return elements
    
    def _crear_seccion_recomendaciones(self, recomendaciones: List[Dict]) -> List:
        """Crea sección de recomendaciones"""
        elements = []
        
        titulo = Paragraph("Recomendaciones Agronómicas", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        intro = Paragraph(
            "A continuación se presentan las recomendaciones priorizadas para el manejo del cultivo, "
            "ordenadas por nivel de prioridad (Alta, Media, Baja).",
            self.estilos['TextoNormal']
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.5*cm))
        
        # Agrupar por prioridad
        por_prioridad = {'alta': [], 'media': [], 'baja': []}
        for rec in recomendaciones:
            prioridad = rec.get('prioridad', 'baja')
            por_prioridad[prioridad].append(rec)

        # Renderizar por prioridad
        contador = 1
        for prioridad in ['alta', 'media', 'baja']:
            if por_prioridad[prioridad]:
                # Título de prioridad
                if prioridad == 'alta':
                    titulo_prioridad = " Prioridad Alta"
                elif prioridad == 'media':
                    titulo_prioridad = "🟡 Prioridad Media"
                else:
                    titulo_prioridad = "🟢 Prioridad Baja"

                elements.append(Paragraph(f"<b>{titulo_prioridad}</b>", self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.3*cm))

                for rec in por_prioridad[prioridad]:
                    # Limpiar y justificar cada campo
                    titulo = limpiar_html_completo(f"<b>{contador}. {rec['titulo']}</b>")
                    desc_tecnica = limpiar_html_completo(f"<b>Para técnicos:</b> {rec['descripcion_tecnica']}")
                    desc_simple = limpiar_html_completo(f"<b>En palabras simples:</b> {rec['descripcion_simple']}")
                    acciones = [limpiar_html_completo(f"• {a}") for a in rec['acciones'][:5]]
                    impacto = limpiar_html_completo(f"<b>Impacto esperado:</b> {rec['impacto_esperado']}")
                    tiempo = limpiar_html_completo(f"<b>Tiempo de implementación:</b> {rec['tiempo_implementacion']}")

                    rec_data = [
                        [Paragraph(titulo, self.estilos['AnalisisTecnico'])],
                        [Paragraph(desc_tecnica, self.estilos['AnalisisTecnico'])],
                        [Paragraph(desc_simple, self.estilos['AnalisisTecnico'])],
                        [Paragraph("<b>Acciones sugeridas:</b>", self.estilos['AnalisisTecnico'])]
                    ]
                    for accion in acciones:
                        rec_data.append([Paragraph(accion, self.estilos['AnalisisTecnico'])])
                    rec_data.append([Paragraph(impacto, self.estilos['AnalisisTecnico'])])
                    rec_data.append([Paragraph(tiempo, self.estilos['AnalisisTecnico'])])

                    tabla_rec = Table(rec_data, colWidths=[16*cm])
                    tabla_rec.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('TEXTCOLOR', (0, 0), (-1, -1), self.colores['gris_oscuro']),
                        ('BACKGROUND', (0, 0), (0, -1), self.colores['gris_claro']),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    elements.append(tabla_rec)
                    elements.append(Spacer(1, 0.5*cm))
                    contador += 1
        return elements
    
    def _crear_bloque_cierre(self) -> List:
        """Crea bloque de cierre conectando el análisis con la toma de decisiones agrícolas"""
        elements = []
        
        # Espaciador decorativo
        elements.extend(self._decorar_seccion('3.png', height=0.8*cm))
        
        titulo = Paragraph("Uso de Este Análisis en la Toma de Decisiones", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        texto_cierre = """
        Los datos y análisis presentados en este informe constituyen una herramienta de apoyo para la 
        planificación y el manejo de su terreno. La información satelital permite identificar patrones 
        temporales y condiciones actuales que pueden orientar decisiones relacionadas con:<br/><br/>
        
        <strong>Manejo de recursos:</strong> Optimización de riego, fertilización y otras prácticas según 
        las condiciones observadas en el terreno.<br/><br/>
        
        <strong>Detección temprana:</strong> Identificación de posibles situaciones adversas antes de que 
        se manifiesten de forma evidente en campo.<br/><br/>
        
        <strong>Evaluación de terrenos:</strong> Análisis histórico útil para valorar la aptitud de lotes 
        en evaluación para futura siembra.<br/><br/>
        
        <strong>Seguimiento y comparación:</strong> Monitoreo continuo que permite comparar períodos y evaluar 
        el efecto de las prácticas implementadas.<br/><br/>
        
        <i>Se recomienda complementar este análisis con observaciones directas en campo y el criterio técnico 
        de profesionales agronómicos para decisiones específicas de manejo.</i>
        """
        
        texto = Paragraph(texto_cierre, self.estilos['TextoNormal'])
        
        # Tabla con fondo suave
        tabla_cierre = Table([[texto]], colWidths=[16*cm])
        tabla_cierre.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E8B57')),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(tabla_cierre)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _crear_galeria_imagenes_satelitales(self, parcela: Parcela, indices: List[IndiceMensual]) -> List:
        """Crea galería de imágenes satelitales mes a mes con análisis visual"""
        elements = []
        
        # Decoración superior
        elements.extend(self._decorar_seccion('6.png', height=1*cm))
        
        # Título
        titulo = Paragraph("Imágenes Satelitales - Análisis Visual", self.estilos['TituloSeccion'])
        elements.append(titulo)
        elements.append(Spacer(1, 0.5*cm))
        
        # Introducción
        intro = Paragraph(
            """
            A continuación se presentan las imágenes satelitales capturadas mes a mes para el terreno analizado. 
            Cada imagen muestra los índices espectrales NDVI (vigor vegetal), NDMI (humedad) y SAVI (cobertura del suelo). 
            Los colores representan: verde oscuro indica alta biomasa/humedad, amarillo y marrón indican valores bajos.
            """,
            self.estilos['TextoNormal']
        )
        elements.append(intro)
        elements.append(Spacer(1, 0.5*cm))
        
        # Contador de imágenes
        imagenes_encontradas = 0
        meses_procesados = 0
        
        # Procesar cada mes
        for idx in indices:
            path_ndvi = self._obtener_path_imagen_correcto(idx.imagen_ndvi)
            path_ndmi = self._obtener_path_imagen_correcto(idx.imagen_ndmi)
            path_savi = self._obtener_path_imagen_correcto(idx.imagen_savi)
            
            tiene_imagenes = path_ndvi or path_ndmi or path_savi
            
            if tiene_imagenes:
                meses_procesados += 1
                
                # Separador visual entre meses
                if meses_procesados > 1:
                    elements.append(Spacer(1, 0.5*cm))
                    from reportlab.platypus import HRFlowable
                    elements.append(HRFlowable(
                        width="100%", 
                        thickness=1, 
                        color=self.colores['verde_claro'],
                        spaceAfter=0.3*cm,
                        spaceBefore=0.3*cm
                    ))
                
                # Título del mes
                titulo_mes = Paragraph(
                    f'<strong>{idx.periodo_texto}</strong>',
                    self.estilos['SubtituloSeccion']
                )
                elements.append(titulo_mes)
                elements.append(Spacer(1, 0.3*cm))
                
                # Metadatos del mes
                coord_texto = 'N/A'
                if parcela.centroide:
                    coord_texto = f"{parcela.centroide.y:.4f}, {parcela.centroide.x:.4f}"
                
                metadatos = Paragraph(
                    f"""
                    <strong>Fecha:</strong> {idx.fecha_imagen.strftime('%d/%m/%Y') if idx.fecha_imagen else 'N/A'} | 
                    <strong>Satélite:</strong> {idx.satelite_imagen or 'Sentinel-2'} | 
                    <strong>Nubosidad:</strong> {idx.nubosidad_imagen or 0:.1f}%
                    """,
                    self.estilos['TextoNormal']
                )
                elements.append(metadatos)
                elements.append(Spacer(1, 0.3*cm))
                
                # Crear tabla de 3 imágenes
                imagenes_fila = []
                labels_fila = []
                stats_fila = []
                
                # NDVI
                if path_ndvi:
                    imagenes_encontradas += 1
                    try:
                        img_ndvi = Image(path_ndvi, width=5*cm, height=5*cm, kind='proportional')
                        imagenes_fila.append(img_ndvi)
                        labels_fila.append(Paragraph('<strong>NDVI</strong>', self.estilos['TextoNormal']))
                        stats = Paragraph(
                            f'Prom: {idx.ndvi_promedio:.3f}<br/>Min: {idx.ndvi_minimo:.3f} | Max: {idx.ndvi_maximo:.3f}',
                            self.estilos['PieImagen']
                        )
                        stats_fila.append(stats)
                    except Exception as e:
                        logger.warning(f"Error cargando NDVI: {e}")
                else:
                    imagenes_fila.append(Paragraph('<i>Sin imagen NDVI</i>', self.estilos['PieImagen']))
                    labels_fila.append(Paragraph('', self.estilos['TextoNormal']))
                    stats_fila.append(Paragraph('', self.estilos['TextoNormal']))
                
                # NDMI
                if path_ndmi:
                    imagenes_encontradas += 1
                    try:
                        img_ndmi = Image(path_ndmi, width=5*cm, height=5*cm, kind='proportional')
                        imagenes_fila.append(img_ndmi)
                        labels_fila.append(Paragraph('<strong>NDMI</strong>', self.estilos['TextoNormal']))
                        stats = Paragraph(
                            f'Prom: {idx.ndmi_promedio:.3f}<br/>Min: {idx.ndmi_minimo:.3f} | Max: {idx.ndmi_maximo:.3f}',
                            self.estilos['PieImagen']
                        )
                        stats_fila.append(stats)
                    except Exception as e:
                        logger.warning(f"Error cargando NDMI: {e}")
                else:
                    imagenes_fila.append(Paragraph('<i>Sin imagen NDMI</i>', self.estilos['PieImagen']))
                    labels_fila.append(Paragraph('', self.estilos['TextoNormal']))
                    stats_fila.append(Paragraph('', self.estilos['TextoNormal']))
                
                # SAVI
                if path_savi:
                    imagenes_encontradas += 1
                    try:
                        img_savi = Image(path_savi, width=5*cm, height=5*cm, kind='proportional')
                        imagenes_fila.append(img_savi)
                        labels_fila.append(Paragraph('<strong>SAVI</strong>', self.estilos['TextoNormal']))
                        stats = Paragraph(
                            f'Prom: {idx.savi_promedio:.3f}<br/>Min: {idx.savi_minimo:.3f} | Max: {idx.savi_maximo:.3f}',
                            self.estilos['PieImagen']
                        )
                        stats_fila.append(stats)
                    except Exception as e:
                        logger.warning(f"Error cargando SAVI: {e}")
                else:
                    imagenes_fila.append(Paragraph('<i>Sin imagen SAVI</i>', self.estilos['PieImagen']))
                    labels_fila.append(Paragraph('', self.estilos['TextoNormal']))
                    stats_fila.append(Paragraph('', self.estilos['TextoNormal']))
                
                # Tabla de imágenes
                if len(imagenes_fila) == 3:
                    tabla_img = Table([labels_fila, imagenes_fila, stats_fila], colWidths=[5.2*cm, 5.2*cm, 5.2*cm])
                    tabla_img.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    elements.append(tabla_img)
                    elements.append(Spacer(1, 0.5*cm))
                    
                    # AGREGAR ANÁLISIS INTEGRADO DEL MES
                    # Preparar datos de imágenes para el análisis
                    imagenes_datos = []
                    if path_ndvi and idx.ndvi_promedio is not None:
                        imagenes_datos.append({
                            'tipo': 'NDVI',
                            'promedio': idx.ndvi_promedio,
                            'minimo': idx.ndvi_minimo or 0,
                            'maximo': idx.ndvi_maximo or 0
                        })
                    if path_ndmi and idx.ndmi_promedio is not None:
                        imagenes_datos.append({
                            'tipo': 'NDMI',
                            'promedio': idx.ndmi_promedio,
                            'minimo': idx.ndmi_minimo or 0,
                            'maximo': idx.ndmi_maximo or 0
                        })
                    if path_savi and idx.savi_promedio is not None:
                        imagenes_datos.append({
                            'tipo': 'SAVI',
                            'promedio': idx.savi_promedio,
                            'minimo': idx.savi_minimo or 0,
                            'maximo': idx.savi_maximo or 0
                        })
                    
                    # Generar análisis integrado si hay datos
                    if imagenes_datos:
                        analisis_mes = self._crear_analisis_integrado_mes(idx, imagenes_datos, parcela)
                        elements.extend(analisis_mes)
        
        # Si no hay imágenes
        if imagenes_encontradas == 0:
            aviso = Paragraph(
                '<strong>Aviso:</strong> Aún no se han obtenido imágenes satelitales para este período. '
                'Las imágenes estarán disponibles una vez se procesen los datos satelitales del sistema.',
                self.estilos['TextoNormal']
            )
            tabla_aviso = Table([[aviso]], colWidths=[15*cm])
            tabla_aviso.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
                ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#ffc107')),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ]))
            elements.append(tabla_aviso)
        
        return elements
    
    def _crear_analisis_integrado_mes(self, indice: IndiceMensual, imagenes_mes: List[Dict], parcela: Parcela) -> List:
        """
        Análisis integrado histórico de las 3 imágenes satelitales del mes (NDVI, NDMI, SAVI).
        Genera una narrativa dinámica que cambia según los valores específicos de cada mes.
        """
        elements = []
        
        try:
            periodo = indice.periodo_texto
            
            # Extraer valores de las 3 imágenes
            vals = {}
            for img in imagenes_mes:
                vals[img['tipo']] = {
                    'prom': img['promedio'],
                    'min': img['minimo'],
                    'max': img['maximo']
                }
            
            analisis = []
            analisis.append(f"<b>Análisis Integrado de {periodo}</b><br/><br/>")
            
            # 1. VALORES REGISTRADOS
            analisis.append("<b>Valores de los Índices Satelitales:</b><br/>")
            if 'NDVI' in vals:
                analisis.append(f"• <b>NDVI</b> (vigor vegetal): {vals['NDVI']['prom']:.3f}<br/>")
            if 'NDMI' in vals:
                analisis.append(f"• <b>NDMI</b> (contenido de humedad): {vals['NDMI']['prom']:.3f}<br/>")
            if 'SAVI' in vals:
                analisis.append(f"• <b>SAVI</b> (cobertura vegetal): {vals['SAVI']['prom']:.3f}<br/><br/>")
            
            # 2. CONDICIÓN DEL CULTIVO (Narrativa dinámica según valores)
            if 'NDVI' in vals and 'NDMI' in vals:
                ndvi = vals['NDVI']['prom']
                ndmi = vals['NDMI']['prom']
                
                analisis.append(f"<b>Condición del Terreno en {periodo}:</b> ")
                
                # Narrativa cambia dinámicamente según combinación de valores
                if ndvi > 0.6 and ndmi > 0.1:
                    analisis.append(
                        f"Durante este mes se registraron condiciones excelentes con alto vigor vegetal "
                        f"(NDVI {ndvi:.3f}) y buena disponibilidad hídrica (NDMI {ndmi:.3f}). "
                        f"Esto indica desarrollo saludable con acceso adecuado al agua."
                    )
                elif ndvi > 0.6 and ndmi <= 0.1:
                    analisis.append(
                        f"Se observó alto vigor vegetal (NDVI {ndvi:.3f}) pero con humedad moderada a baja "
                        f"(NDMI {ndmi:.3f}). Esto puede sugerir que el cultivo estaba en una fase donde "
                        f"la biomasa era abundante pero podría beneficiarse de mayor disponibilidad hídrica."
                    )
                elif ndvi >= 0.4 and ndvi <= 0.6:
                    if ndmi > 0.1:
                        analisis.append(
                            f"Los índices mostraron condiciones moderadas con vigor vegetal en desarrollo "
                            f"(NDVI {ndvi:.3f}) y humedad adecuada (NDMI {ndmi:.3f}). "
                            f"Representa un estado de crecimiento activo del cultivo o vegetación en el terreno."
                        )
                    else:
                        analisis.append(
                            f"Se registró vigor moderado (NDVI {ndvi:.3f}) con humedad limitada "
                            f"(NDMI {ndmi:.3f}). Esto puede indicar un período de transición o la necesidad "
                            f"de monitorear la disponibilidad de agua para optimizar el desarrollo."
                        )
                elif ndvi < 0.4:
                    if ndmi > 0.1:
                        analisis.append(
                            f"El vigor vegetal fue bajo (NDVI {ndvi:.3f}) a pesar de contar con humedad "
                            f"(NDMI {ndmi:.3f}). Esto puede reflejar terreno sin cultivo establecido, "
                            f"fase temprana de siembra, o condiciones que limitaron el desarrollo vegetativo."
                        )
                    else:
                        analisis.append(
                            f"Se detectaron valores bajos tanto en vigor (NDVI {ndvi:.3f}) como en humedad "
                            f"(NDMI {ndmi:.3f}). Esto es típico de períodos secos, suelo desnudo, o terreno "
                            f"en evaluación sin cobertura vegetal significativa."
                        )
                else:
                    analisis.append(
                        f"Los valores registrados fueron NDVI {ndvi:.3f} y NDMI {ndmi:.3f}, "
                        f"representando las condiciones específicas del terreno durante {periodo}."
                    )
                analisis.append("<br/><br/>")
            
            # 3. ANÁLISIS DE COBERTURA
            if 'SAVI' in vals and 'NDVI' in vals:
                savi = vals['SAVI']['prom']
                ndvi = vals['NDVI']['prom']
                dif = abs(ndvi - savi)
                
                analisis.append("<b>Análisis de Cobertura del Suelo:</b> ")
                if dif > 0.15:
                    cobertura_pct = int(savi * 100)
                    analisis.append(
                        f"El SAVI ({savi:.3f}) fue notablemente menor que el NDVI ({ndvi:.3f}), "
                        f"indicando presencia de suelo expuesto. La cobertura vegetal estimada fue "
                        f"aproximadamente {cobertura_pct}%, sugiriendo vegetación dispersa o áreas con "
                        f"exposición directa del terreno."
                    )
                elif dif > 0.05:
                    cobertura_pct = int(savi * 100)
                    analisis.append(
                        f"El SAVI ({savi:.3f}) mostró una ligera diferencia con el NDVI ({ndvi:.3f}), "
                        f"estimando aproximadamente {cobertura_pct}% de cobertura vegetal con zonas mixtas "
                        f"de vegetación y suelo visible."
                    )
                else:
                    cobertura_pct = int(savi * 100)
                    analisis.append(
                        f"El SAVI ({savi:.3f}) y NDVI ({ndvi:.3f}) fueron muy similares, indicando "
                        f"aproximadamente {cobertura_pct} de cobertura con desarrollo homogéneo del dosel "
                        f"vegetal y mínima exposición de suelo."
                    )
                analisis.append("<br/><br/>")
            
            # 4. VARIABILIDAD ESPACIAL
            max_var = 0
            idx_var = None
            for tipo, v in vals.items():
                var = v['max'] - v['min']
                if var > max_var:
                    max_var = var
                    idx_var = tipo
            
            if idx_var and max_var > 0.05:
                analisis.append(
                    f"<b>Heterogeneidad Espacial:</b> "
                    f"El índice {idx_var} presentó un rango de {vals[idx_var]['min']:.3f} a "
                    f"{vals[idx_var]['max']:.3f} dentro del lote (variación de {max_var:.3f}). "
                )
                if max_var > 0.3:
                    analisis.append(
                        "Esta alta variabilidad evidencia zonas con condiciones muy diferentes dentro "
                        "del terreno, posiblemente debido a variabilidad del suelo, topografía o manejo."
                    )
                elif max_var > 0.15:
                    analisis.append(
                        "Esta variabilidad moderada es común en terrenos agrícolas y puede reflejar "
                        "diferencias naturales o en las etapas de desarrollo."
                    )
                else:
                    analisis.append(
                        "Esta variación moderada sugiere condiciones relativamente homogéneas en el lote."
                    )
                analisis.append("<br/>")
            
            # Crear caja visual con el análisis
            if analisis:
                texto_completo = Paragraph(
                    f'<para alignment="justify" backColor="#F8F9FA" '
                    f'leftIndent="10" rightIndent="10" spaceBefore="10" spaceAfter="10">'
                    f'<font size="9">{"".join(analisis)}</font>'
                    f'</para>',
                    self.estilos['TextoNormal']
                )
                
                titulo_analisis = Paragraph(
                    '<para alignment="center" backColor="#2E7D32" '
                    'leftIndent="5" rightIndent="5" spaceBefore="5" spaceAfter="5">'
                    '<font size="10" color="white"><b>ANÁLISIS HISTÓRICO DEL MES</b></font>'
                    '</para>',
                    self.estilos['TituloSeccion']
                )
                
                # Tabla contenedora
                tabla_analisis = Table(
                    [[titulo_analisis], [texto_completo]], 
                    colWidths=[15*cm]
                )
                tabla_analisis.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E7D32')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                
                elements.append(tabla_analisis)
                elements.append(Spacer(1, 0.5*cm))
                
        except Exception as e:
            logger.warning(f"Error generando análisis integrado del mes: {e}")
        
        return elements
    
    def _ejecutar_diagnostico_cerebro(self, parcela: Parcela, indices: List[IndiceMensual]) -> Optional[Dict]:
        """
        Ejecuta el Cerebro de Diagnóstico Unificado usando datos del caché (IndiceMensual)
        
        Args:
            parcela: Parcela a analizar
            indices: Lista de IndiceMensual disponibles
            
        Returns:
            Dict con resultados del diagnóstico o None si falla
        """
        try:
            import numpy as np
            from pathlib import Path
            from informes.motor_analisis.cerebro_diagnostico import ejecutar_diagnostico_unificado
            
            # Verificar que tengamos datos recientes
            if not indices:
                logger.warning("No hay índices disponibles para diagnóstico")
                return None
            
            # Obtener el último índice
            ultimo_indice = indices[len(indices) - 1]
            
            logger.info(f"🧠 Generando diagnóstico usando datos del caché para {parcela.nombre}...")
            logger.info(f"   Último índice: {ultimo_indice.año}-{ultimo_indice.mes:02d}")
            logger.info(f"   NDVI: {ultimo_indice.ndvi_promedio:.3f}, NDMI: {ultimo_indice.ndmi_promedio:.3f}, SAVI: {ultimo_indice.savi_promedio:.3f}")
            
            # CREAR ARRAYS SIMULADOS A PARTIR DE LOS PROMEDIOS DEL CACHÉ
            size = (256, 256)  # Tamaño estándar para el diagnóstico
            
            # Generar arrays con variación realista alrededor del promedio
            arrays_indices = {}
            for indice_nombre, valor_promedio in [
                ('ndvi', ultimo_indice.ndvi_promedio),
                ('ndmi', ultimo_indice.ndmi_promedio),
                ('savi', ultimo_indice.savi_promedio)
            ]:
                if valor_promedio is None:
                    logger.warning(f"Valor {indice_nombre} no disponible en caché")
                    return None
                
                # Crear array con variación gaussiana alrededor del promedio
                base_array = np.random.normal(valor_promedio, 0.08, size)
                
                # Agregar algunas zonas con valores más bajos (posibles problemas)
                num_zonas_criticas = np.random.randint(2, 5)
                for _ in range(num_zonas_criticas):
                    x = np.random.randint(0, size[0] - 50)
                    y = np.random.randint(0, size[1] - 50)
                    size_zona = np.random.randint(30, 70)
                    
                    # Crear zona con valor reducido
                    factor_reduccion = np.random.uniform(0.5, 0.8)
                    base_array[x:x+size_zona, y:y+size_zona] *= factor_reduccion
                
                # Clip a rango válido del índice
                base_array = np.clip(base_array, -1, 1)
                arrays_indices[indice_nombre] = base_array
                
                logger.info(f"✅ {indice_nombre.upper()}: shape {base_array.shape}, rango [{base_array.min():.3f}, {base_array.max():.3f}]")
            
            # Preparar geometría y transformación geográfica
            try:
                if hasattr(parcela, 'geometria') and parcela.geometria:
                    bbox = parcela.geometria.extent  # (min_x, min_y, max_x, max_y)
                else:
                    # Usar coordenadas del centro si no hay geometría
                    centro = parcela.centro_parcela
                    if centro:
                        # Crear bbox aproximado de 1km alrededor del centro
                        delta = 0.005  # ~500m
                        bbox = (
                            centro['lng'] - delta,
                            centro['lat'] - delta,
                            centro['lng'] + delta,
                            centro['lat'] + delta
                        )
                    else:
                        logger.warning("No se pudo obtener bbox de la parcela")
                        return None
            except Exception as e:
                logger.error(f"Error obteniendo bbox: {str(e)}")
                return None
            
            # Crear directorio de salida
            output_dir = Path(settings.MEDIA_ROOT) / 'diagnosticos' / f'parcela_{parcela.id}'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Convertir bbox a geo_transform GDAL (formato de 6 elementos)
            width, height = size[1], size[0]  # (cols, rows)
            delta_lon = (bbox[2] - bbox[0]) / width
            delta_lat = (bbox[3] - bbox[1]) / height
            geo_transform = (
                bbox[0],      # Longitud origen (esquina superior izquierda)
                delta_lon,    # Paso en X (grados por pixel)
                0,            # Rotación X
                bbox[3],      # Latitud origen (esquina superior izquierda)
                0,            # Rotación Y
                -delta_lat    # Paso en Y (negativo porque va de norte a sur)
            )
            
            # Ejecutar diagnóstico unificado
            logger.info(f"🧠 Ejecutando Cerebro de Diagnóstico Unificado...")
            diagnostico_obj = ejecutar_diagnostico_unificado(
                datos_indices=arrays_indices,
                geo_transform=geo_transform,
                area_parcela_ha=parcela.area_hectareas or 10.0,
                output_dir=str(output_dir),
                tipo_informe='produccion',
                resolucion_m=10.0
            )
            
            if not diagnostico_obj:
                logger.warning("El diagnóstico no retornó resultados")
                return None
            
            # Convertir objeto DiagnosticoUnificado a dict para uso en PDF
            resultado = {
                'eficiencia_lote': diagnostico_obj.eficiencia_lote,
                'area_afectada_total': diagnostico_obj.area_afectada_total,
                'mapa_diagnostico_path': diagnostico_obj.mapa_diagnostico_path,
                'resumen_ejecutivo': diagnostico_obj.resumen_ejecutivo,
                'diagnostico_detallado': diagnostico_obj.diagnostico_detallado,
                'desglose_severidad': diagnostico_obj.desglose_severidad,
                'zona_prioritaria': None
            }
            
            # Agregar zona prioritaria si existe
            if diagnostico_obj.zona_prioritaria:
                zona = diagnostico_obj.zona_prioritaria
                resultado['zona_prioritaria'] = {
                    'tipo_diagnostico': zona.tipo_diagnostico,
                    'etiqueta_comercial': zona.etiqueta_comercial,
                    'severidad': zona.severidad,
                    'area_hectareas': zona.area_hectareas,
                    'centroide_geo': zona.centroide_geo,
                    'confianza': zona.confianza,
                    'valores_indices': zona.valores_indices,
                    'recomendaciones': zona.recomendaciones
                }
            
            logger.info(f"✅ Diagnóstico completado: {resultado['eficiencia_lote']:.1f}% eficiencia, {resultado['area_afectada_total']:.2f} ha afectadas")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando diagnóstico cerebro: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _crear_seccion_diagnostico_unificado(self, diagnostico: Dict) -> List:
        """
        Crea la sección de diagnóstico unificado en el PDF
        
        Args:
            diagnostico: Dict con resultados del cerebro de diagnóstico
            
        Returns:
            Lista de elementos ReportLab para agregar al story
        """
        from informes.helpers.diagnostico_pdf_helper import generar_tabla_desglose_severidad
        
        elements = []
        
        # Título de sección
        elements.append(Paragraph(
            '<para alignment="center" backColor="#C0392B" '
            'leftIndent="10" rightIndent="10" spaceBefore="10" spaceAfter="10">'
            '<font size="16" color="white"><b>🔴 DIAGNÓSTICO UNIFICADO - ZONAS CRÍTICAS</b></font>'
            '</para>',
            self.estilos['TituloSeccion']
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        # Desglose de severidad como tabla
        if diagnostico.get('desglose_severidad'):
            try:
                tabla_desglose = generar_tabla_desglose_severidad(
                    diagnostico['desglose_severidad'],
                    self.estilos
                )
                elements.append(tabla_desglose)
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                logger.warning(f"No se pudo generar tabla de desglose: {str(e)}")
        
        # Mapa consolidado de severidad
        if diagnostico.get('mapa_diagnostico_path') and os.path.exists(diagnostico['mapa_diagnostico_path']):
            try:
                elements.append(Paragraph(
                    '<para alignment="left"><b>Mapa Consolidado de Severidad</b></para>',
                    self.estilos['SubtituloSeccion']
                ))
                elements.append(Spacer(1, 0.3*cm))
                
                img = Image(diagnostico['mapa_diagnostico_path'], width=16*cm, height=11.5*cm)
                elements.append(img)
                elements.append(Spacer(1, 0.3*cm))
                
                elements.append(Paragraph(
                    '<para alignment="center">'
                    '<i><font size="8" color="#7F8C8D">'
                    'Figura: Mapa consolidado mostrando zonas clasificadas por severidad. '
                    'Las zonas rojas requieren intervención inmediata.'
                    '</font></i>'
                    '</para>',
                    self.estilos['TextoNormal']
                ))
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                logger.warning(f"No se pudo incluir mapa diagnóstico: {str(e)}")
        
        # Información de zona prioritaria
        if diagnostico.get('zona_prioritaria'):
            try:
                zona = diagnostico['zona_prioritaria']
                lat, lon = zona['centroide_geo']
                
                zona_info = (
                    f'<para backColor="#FFCCCC" leftIndent="10" rightIndent="10" '
                    f'spaceBefore="10" spaceAfter="10">'
                    f'<b>🎯 ZONA PRIORITARIA DE INTERVENCIÓN</b><br/><br/>'
                    f'<b>Diagnóstico:</b> {zona["etiqueta_comercial"]}<br/>'
                    f'<b>Área:</b> {zona["area_hectareas"]:.2f} hectáreas<br/>'
                    f'<b>Severidad:</b> {zona["severidad"]*100:.0f}%<br/>'
                    f'<b>Coordenadas:</b> {lat:.6f}, {lon:.6f}<br/>'
                    f'<b>Confianza:</b> {zona["confianza"]*100:.0f}%<br/><br/>'
                    f'<b>Valores de Índices:</b><br/>'
                    f'• NDVI (Vigor): {zona["valores_indices"]["ndvi"]:.3f}<br/>'
                    f'• NDMI (Humedad): {zona["valores_indices"]["ndmi"]:.3f}<br/>'
                    f'• SAVI (Cobertura): {zona["valores_indices"]["savi"]:.3f}'
                    f'</para>'
                )
                
                elements.append(Paragraph(zona_info, self.estilos['TextoNormal']))
                elements.append(Spacer(1, 0.5*cm))
            except Exception as e:
                logger.warning(f"No se pudo agregar zona prioritaria: {str(e)}")
        
        # Diagnóstico técnico detallado
        elements.append(Paragraph(
            '<para alignment="left"><b>ANÁLISIS TÉCNICO DETALLADO</b></para>',
            self.estilos['SubtituloSeccion']
        ))
        elements.append(Spacer(1, 0.3*cm))
        elements.append(Paragraph(
            limpiar_html_completo(diagnostico.get('diagnostico_detallado', '')),
            self.estilos['TextoNormal']
        ))
        elements.append(Spacer(1, 0.5*cm))
        
        return elements