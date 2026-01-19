"""
Exportador de video profesional para Timeline de AgroTech Histórico
Genera videos MP4 de alta calidad usando FFmpeg directamente

Características:
- Resolución Full HD (1920x1080) o superior
- Frames generados con PIL/Pillow sin compresión
- FFmpeg con control total de calidad (bitrate, FPS, codec)
- Replica exactamente la visualización del timeline web
- Sin dependencias innecesarias (no usa MoviePy como motor)

@author: AgroTech Team
@version: 2.0.0 - Refactorizado para calidad profesional vendible
"""

import os
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TimelineVideoExporter:
    """
    Exportador profesional de videos de timeline
    Genera frames individuales en alta resolución y los une con FFmpeg
    """
    
    # Configuración de calidad PROFESIONAL para producto final vendible
    DEFAULT_WIDTH = 1920  # Full HD (mínimo requerido)
    DEFAULT_HEIGHT = 1080
    DEFAULT_FPS = 24  # FPS cinematográfico para transiciones suaves
    DEFAULT_BITRATE = '10000k'  # 10 Mbps para raster satelital de alta calidad
    DEFAULT_CRF = 18  # CRF 18 = calidad broadcast sin pérdidas perceptibles
    
    # Duración mínima por frame (2-3 segundos según especificación)
    FRAME_DURATION = 2.5  # segundos por mes/frame
    
    # Configuración de diseño
    OVERLAY_HEIGHT_RATIO = 0.20  # 20% de la altura para overlay
    PADDING_RATIO = 0.02  # 2% de padding
    
    def __init__(self, 
                 width: int = DEFAULT_WIDTH,
                 height: int = DEFAULT_HEIGHT,
                 fps: int = DEFAULT_FPS,
                 bitrate: str = DEFAULT_BITRATE,
                 crf: int = DEFAULT_CRF):
        """
        Inicializa el exportador con parámetros de calidad
        
        Args:
            width: Ancho del video en píxeles
            height: Alto del video en píxeles
            fps: Frames por segundo (velocidad del video)
            bitrate: Bitrate del video (calidad)
            crf: Constant Rate Factor (0-51, menor = mejor calidad)
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.crf = crf
        
        # Verificar FFmpeg
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg no está instalado o no está disponible en PATH")
        
        logger.info(f"TimelineVideoExporter inicializado: {width}x{height} @ {fps}fps, bitrate={bitrate}, CRF={crf}")
    
    def _check_ffmpeg(self) -> bool:
        """Verifica que FFmpeg esté disponible"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def export_timeline(self,
                       frames_data: List[Dict],
                       indice: str,
                       output_path: Optional[str] = None,
                       parcela_info: Optional[Dict] = None,
                       analisis_texto: Optional[str] = None,
                       recomendaciones_texto: Optional[str] = None) -> str:
        """
        Exporta el timeline completo a video MP4 con estructura multi-escena profesional
        
        Estructura del video:
        1. Escena de portada (3 segundos)
        2. Escenas de mapas mensuales (2.5 segundos cada una)
        3. Escena de análisis IA (5 segundos si hay análisis)
        4. Escena de recomendaciones (5 segundos si hay recomendaciones)
        5. Escena de cierre (3 segundos)
        
        Args:
            frames_data: Lista de frames del timeline (del TimelineProcessor)
            indice: Índice a exportar ('ndvi', 'ndmi', 'savi')
            output_path: Ruta de salida del video (opcional)
            parcela_info: Información de la parcela (nombre, área, cultivo, etc.)
            analisis_texto: Texto del análisis IA generado por Gemini
            recomendaciones_texto: Texto de recomendaciones generadas por Gemini
        
        Returns:
            Ruta del archivo de video generado
        
        Raises:
            ValueError: Si no hay frames o datos inválidos
            RuntimeError: Si falla la generación del video
        """
        if not frames_data:
            raise ValueError("No hay frames para exportar")
        
        if indice not in ['ndvi', 'ndmi', 'savi']:
            raise ValueError(f"Índice inválido: {indice}")
        
        logger.info(f"🎬 Iniciando exportación de video multi-escena: {len(frames_data)} frames, índice={indice}")
        
        # Crear directorio temporal para frames
        temp_dir = tempfile.mkdtemp(prefix='agrotech_video_')
        
        try:
            # Generar todas las escenas del video
            frame_paths = self._generate_all_scenes(
                frames_data=frames_data,
                indice=indice,
                temp_dir=temp_dir,
                parcela_info=parcela_info,
                analisis_texto=analisis_texto,
                recomendaciones_texto=recomendaciones_texto
            )
            
            if not frame_paths:
                raise RuntimeError("No se generaron frames")
            
            # Generar video con FFmpeg
            if output_path is None:
                output_path = self._get_default_output_path(indice)
            
            self._create_video_ffmpeg(frame_paths, output_path)
            
            logger.info(f"✅ Video generado exitosamente: {output_path}")
            return output_path
            
        finally:
            # Limpiar archivos temporales
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"🗑️ Directorio temporal eliminado: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar directorio temporal: {e}")
    
    def _generate_frames(self, 
                        frames_data: List[Dict],
                        indice: str,
                        output_dir: str) -> List[str]:
        """
        Genera frames individuales como imágenes PNG de alta calidad
        
        Args:
            frames_data: Datos de los frames
            indice: Índice seleccionado
            output_dir: Directorio donde guardar los frames
        
        Returns:
            Lista de rutas de los frames generados
        """
        frame_paths = []
        
        for i, frame_data in enumerate(frames_data):
            try:
                frame_path = os.path.join(output_dir, f'frame_{i:04d}.png')
                
                # Generar frame individual
                self._generate_single_frame(frame_data, indice, frame_path)
                
                frame_paths.append(frame_path)
                
                if (i + 1) % 10 == 0 or i == len(frames_data) - 1:
                    logger.info(f"Progreso: {i + 1}/{len(frames_data)} frames generados")
                    
            except Exception as e:
                logger.error(f"Error generando frame {i}: {e}")
                # Continuar con el siguiente frame
                continue
        
        return frame_paths
    
    def _generate_single_frame(self,
                              frame_data: Dict,
                              indice: str,
                              output_path: str):
        """
        Genera frame profesional con estructura obligatoria:
        1. Encabezado: Parcela #X - [Índice] - [Mes Año]
        2. Subtítulo educativo
        3. Imagen satelital (alta resolución, centrada, raster suavizado)
        4. Leyenda de colores fija
        5. Indicador de estado agronómico
        6. Texto interpretativo
        SIN emojis, narrativa clara para agricultores
        """
        # Crear imagen base con fondo neutro profesional (#1a1a1a más oscuro que #2a2a2a)
        img = Image.new('RGB', (self.width, self.height), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        # Obtener imagen satelital
        imagen_url = frame_data.get('imagenes', {}).get(indice)
        
        if imagen_url:
            try:
                sat_img = self._load_satellite_image(imagen_url)
                if sat_img:
                    # Aplicar suavizado de raster para calidad profesional vendible
                    sat_img_suavizada = sat_img.filter(ImageFilter.SMOOTH_MORE)
                    # Raster suavizado LANCZOS, polígono centrado, proporción real
                    sat_img_resized = self._resize_and_center(sat_img_suavizada, self.width, self.height)
                    img.paste(sat_img_resized, (0, 0))
                else:
                    # Placeholder profesional cuando no hay imagen
                    self._draw_placeholder(img, draw, frame_data, indice)
            except Exception as e:
                logger.warning(f"Error cargando imagen satelital: {e}")
                self._draw_placeholder(img, draw, frame_data, indice)
        else:
            # Sin imagen disponible - usar placeholder
            self._draw_placeholder(img, draw, frame_data, indice)
        
        # ESTRUCTURA OBLIGATORIA del frame (profesional para agricultores)
        self._draw_professional_structure(img, draw, frame_data, indice)
        
        # Guardar frame sin compresión para máxima calidad
        img.save(output_path, 'PNG', compress_level=0)
        logger.debug(f"Frame guardado: {output_path}")
    
    def _load_satellite_image(self, url: str) -> Optional[Image.Image]:
        """
        Descarga y carga una imagen satelital desde URL
        
        Args:
            url: URL de la imagen
        
        Returns:
            Imagen PIL o None si falla
        """
        try:
            # Si es URL relativa, convertir a absoluta
            if url.startswith('/media/') or url.startswith('media/'):
                # Buscar archivo local
                relative_path = url.replace('/media/', '').replace('media/', '')
                local_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                
                if os.path.exists(local_path):
                    logger.debug(f"Cargando imagen local: {local_path}")
                    return Image.open(local_path).convert('RGB')
                else:
                    logger.warning(f"Archivo local no encontrado: {local_path}")
            
            # Si es URL completa, descargar
            if url.startswith('http://') or url.startswith('https://'):
                logger.debug(f"Descargando imagen desde URL: {url}")
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                img = Image.open(BytesIO(response.content)).convert('RGB')
                return img
            
            logger.warning(f"URL no reconocida: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error cargando imagen desde {url}: {e}")
            return None
    
    def _resize_and_center(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """
        Redimensiona y centra imagen satelital con MÁXIMA calidad
        Usa interpolación LANCZOS (la mejor calidad para downsampling)
        y aplica scaleFactor 0.88 como en la interfaz web
        
        Args:
            img: Imagen a redimensionar
            target_w: Ancho objetivo
            target_h: Alto objetivo
        
        Returns:
            Imagen redimensionada y centrada con marco visual
        """
        img_w, img_h = img.size
        img_ratio = img_w / img_h
        target_ratio = target_w / target_h
        
        # CRÍTICO: Aplicar mismo scaleFactor que la interfaz web (0.88)
        # para dejar espacio al overlay y crear marco visual limpio
        scale_factor = 0.88
        
        if img_ratio > target_ratio:
            # Imagen más ancha - ajustar por anchura
            new_w = int(target_w * scale_factor)
            new_h = int((target_w * scale_factor) / img_ratio)
        else:
            # Imagen más alta - ajustar por altura
            new_h = int(target_h * scale_factor)
            new_w = int((target_h * scale_factor) * img_ratio)
        
        # MÁXIMA CALIDAD: LANCZOS para preservar detalles espaciales
        # LANCZOS es el mejor algoritmo para imágenes satelitales/raster
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Centrar en canvas negro (igual que en la interfaz)
        canvas = Image.new('RGB', (target_w, target_h), color='black')
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        canvas.paste(img_resized, (offset_x, offset_y))
        
        return canvas
    
    def _draw_placeholder(self, img: Image.Image, draw: ImageDraw.Draw,
                         frame_data: Dict, indice: str):
        """
        Dibuja un placeholder profesional cuando no hay imagen satelital
        FASE 3: Diseño mejorado con degradados elegantes
        """
        clasificacion = frame_data.get('clasificaciones', {}).get(indice, {})
        valor = frame_data.get(indice, {}).get('promedio')
        
        if not clasificacion or valor is None:
            return
        
        # Color base de la clasificación
        color_hex = clasificacion.get('color', '#2e8b57')
        color_rgb = self._hex_to_rgb(color_hex)
        
        # Fondo degradado de dos colores
        color_oscuro = tuple(max(0, c - 40) for c in color_rgb)
        for y in range(self.height):
            ratio = y / self.height
            r = int(color_oscuro[0] + (color_rgb[0] - color_oscuro[0]) * ratio)
            g = int(color_oscuro[1] + (color_rgb[1] - color_oscuro[1]) * ratio)
            b = int(color_oscuro[2] + (color_rgb[2] - color_oscuro[2]) * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        # Área de parcela con sombra
        center_x, center_y = self.width // 2, self.height // 2
        parcela_w = int(self.width * 0.75)
        parcela_h = int(self.height * 0.65)
        parcela_x = (self.width - parcela_w) // 2
        parcela_y = (self.height - parcela_h) // 2
        
        # Sombra
        shadow_offset = 8
        draw.rounded_rectangle(
            [parcela_x + shadow_offset, parcela_y + shadow_offset, 
             parcela_x + parcela_w + shadow_offset, parcela_y + parcela_h + shadow_offset],
            radius=25,
            fill=(0, 0, 0, 100)
        )
        
        # Rectángulo principal con degradado más claro
        color_claro = tuple(min(255, c + 50) for c in color_rgb)
        draw.rounded_rectangle(
            [parcela_x, parcela_y, parcela_x + parcela_w, parcela_y + parcela_h],
            radius=25,
            fill=color_claro,
            outline='white',
            width=4
        )
        
        # Fuentes más grandes y legibles
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 90)
            font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
            font_small_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
        except:
            font_large = font_medium = font_small_text = ImageFont.load_default()
        
        # Texto profesional SIN EMOJIS
        etiqueta_estado = clasificacion.get('etiqueta', 'Datos')
        
        # Título del índice (grande)
        texto_indice = indice.upper()
        draw.text((center_x, center_y - 100), texto_indice, font=font_large, fill='white', anchor='mm')
        
        # Valor del índice con sombra
        texto_valor = f"{valor:.3f}"
        draw.text((center_x + 2, center_y + 2), texto_valor, font=font_large, fill=(0, 0, 0, 100), anchor='mm')
        draw.text((center_x, center_y), texto_valor, font=font_large, fill='white', anchor='mm')
        
        # Estado agronómico (debajo del valor)
        draw.text((center_x, center_y + 100), etiqueta_estado, font=font_medium, fill='white', anchor='mm')
    
    def _draw_professional_structure(self, img: Image.Image, draw: ImageDraw.Draw,
                                      frame_data: Dict, indice: str):
        """
        FIXED PROFESSIONAL GIS VIDEO TEMPLATE
        STRICT LAYOUT - NO DEVIATIONS
        - Raster occupies 85-90% of frame, centered
        - Text only at fixed coordinates, no boxes
        - Small, subtle header and footer text
        - Fixed legend bottom-left
        - Right-side dynamic information column
        """
        # Fixed font sizes optimized for 1080p legibility
        # Increased by 2-4px for better readability without changing design
        try:
            font_header = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
            font_footer = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
            font_legend = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
            font_info = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
            font_info_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
        except:
            font_header = font_footer = font_legend = font_info = font_info_bold = ImageFont.load_default()
        
        # Get data
        clasificacion = frame_data.get('clasificaciones', {}).get(indice, {})
        valor = frame_data.get(indice, {}).get('promedio')
        periodo_texto = frame_data.get('periodo_texto', '')
        
        # 1. HEADER (TOP-LEFT, SMALL)
        # Fixed coordinates: (20, 20)
        # Single line: "NDVI · Marzo 2025"
        header_text = f"{indice.upper()} · {periodo_texto}"
        draw.text((20, 20), header_text, font=font_header, fill='white', anchor='lt')
        
        # 2. FOOTER LEFT (SMALL, SUBTLE)
        # Fixed coordinates: (20, height - 30)
        # Content: "NDVI promedio: 0.44"
        if valor is not None:
            footer_left = f"{indice.upper()} promedio: {valor:.2f}"
            draw.text((20, self.height - 30), footer_left, font=font_footer, fill='white', anchor='lb')
        
        # 3. FOOTER RIGHT (SMALL, SUBTLE)
        # Fixed coordinates: (width - 20, height - 30)
        # Content: "Estado general: Salud moderada"
        if clasificacion:
            etiqueta = clasificacion.get('etiqueta', 'Desconocido')
            footer_right = f"Estado general: {etiqueta}"
            draw.text((self.width - 20, self.height - 30), footer_right, font=font_footer, fill='white', anchor='rb')
        
        # 4. LEGEND (BOTTOM-LEFT, FIXED)
        # Small vertical legend with color squares
        # Must NOT overlap raster
        legend_x = 20
        legend_y_start = self.height - 200
        legend_box_size = 20
        legend_spacing = 30
        
        rangos = self._get_rangos_agronomicos(indice)
        
        for i, rango in enumerate(rangos):
            y_pos = legend_y_start + (i * legend_spacing)
            
            # Color square
            draw.rectangle(
                [legend_x, y_pos, legend_x + legend_box_size, y_pos + legend_box_size],
                fill=rango['color'],
                outline='white',
                width=1
            )
            
            # Label text
            draw.text(
                (legend_x + legend_box_size + 8, y_pos + legend_box_size // 2),
                rango['significado'],
                font=font_legend,
                fill='white',
                anchor='lm'
            )
        
        # 5. RIGHT-SIDE DYNAMIC INFORMATION COLUMN
        # Fixed coordinates, text-only overlay (no background panels)
        # Must NOT overlap raster
        self._draw_dynamic_info_column(draw, frame_data, indice, font_info, font_info_bold)

    def _draw_dynamic_info_column(self, draw: ImageDraw.Draw, frame_data: Dict, 
                                   indice: str, font_info, font_info_bold):
        """
        Dibuja columna dinámica de información en el lado derecho del video
        - Cambio mensual (vs mes anterior)
        - Calidad de imagen (nubosidad)
        - Resumen climático mensual
        
        REGLAS ESTRICTAS:
        - Solo texto, sin paneles de fondo
        - Coordenadas fijas en píxeles
        - Todos los valores dinámicos por frame
        - Mostrar advertencia si faltan datos
        """
        # Fixed starting position (right side, away from raster)
        # X position: 85% of width to avoid raster overlap
        info_x = int(self.width * 0.85)
        info_y_start = 150  # Start below header
        line_spacing = 32  # Increased by 2px for better readability
        
        current_y = info_y_start
        
        # SECCIÓN 1: CAMBIO MENSUAL
        draw.text((info_x, current_y), "CAMBIO MENSUAL", font=font_info_bold, fill='white', anchor='lt')
        current_y += line_spacing
        
        comparacion = frame_data.get('comparacion', {})
        if comparacion and indice in comparacion:
            diff = comparacion[indice].get('diferencia')
            porcentaje = comparacion[indice].get('porcentaje')
            
            if diff is not None and porcentaje is not None:
                signo = '+' if diff >= 0 else ''
                color = '#00ff00' if diff > 0 else '#ff4444' if diff < 0 else 'white'
                texto_cambio = f"{signo}{porcentaje:.1f}%"
                draw.text((info_x, current_y), texto_cambio, font=font_info, fill=color, anchor='lt')
                current_y += line_spacing
                
                # Tendencia textual
                tendencia = comparacion[indice].get('tendencia', 'estable')
                texto_tendencia = {
                    'mejora': 'Mejora',
                    'deterioro': 'Deterioro',
                    'estable': 'Estable'
                }.get(tendencia, tendencia.capitalize())
                draw.text((info_x, current_y), f"vs mes anterior", font=font_info, fill='#999999', anchor='lt')
                current_y += line_spacing
            else:
                draw.text((info_x, current_y), "[Sin datos]", font=font_info, fill='#ffaa00', anchor='lt')
                current_y += line_spacing
        else:
            # Primer mes sin comparación
            draw.text((info_x, current_y), "Primer periodo", font=font_info, fill='#999999', anchor='lt')
            current_y += line_spacing
        
        current_y += 18  # Increased spacing between sections for clarity
        
        # SECCIÓN 2: CALIDAD DE IMAGEN
        draw.text((info_x, current_y), "CALIDAD IMAGEN", font=font_info_bold, fill='white', anchor='lt')
        current_y += line_spacing
        
        metadata = frame_data.get('imagen_metadata', {})
        nubosidad = metadata.get('nubosidad')
        
        if nubosidad is not None:
            # Convertir a porcentaje
            nubosidad_pct = nubosidad * 100 if nubosidad <= 1.0 else nubosidad
            
            # Color y etiqueta según calidad
            if nubosidad_pct < 10:
                color_calidad = '#00ff00'
                etiqueta_calidad = "Excelente"
            elif nubosidad_pct < 30:
                color_calidad = '#90ee90'
                etiqueta_calidad = "Buena"
            elif nubosidad_pct < 50:
                color_calidad = '#ffcc00'
                etiqueta_calidad = "Moderada"
            else:
                color_calidad = '#ff4444'
                etiqueta_calidad = "Baja"
            
            draw.text((info_x, current_y), etiqueta_calidad, font=font_info, fill=color_calidad, anchor='lt')
            current_y += line_spacing
            texto_nubosidad = f"Nubosidad: {nubosidad_pct:.1f}%"
            draw.text((info_x, current_y), texto_nubosidad, font=font_info, fill='#999999', anchor='lt')
            current_y += line_spacing
        else:
            draw.text((info_x, current_y), "[Sin datos]", font=font_info, fill='#ff8800', anchor='lt')
            current_y += line_spacing
        
        current_y += 18  # Increased spacing between sections for clarity
        
        # SECCIÓN 3: RESUMEN CLIMÁTICO
        draw.text((info_x, current_y), "CLIMA DEL MES", font=font_info_bold, fill='white', anchor='lt')
        current_y += line_spacing
        
        temperatura = frame_data.get('temperatura')
        precipitacion = frame_data.get('precipitacion')
        
        if temperatura is not None:
            texto_temp = f"Temp: {temperatura:.1f}°C"
            draw.text((info_x, current_y), texto_temp, font=font_info, fill='#ffcc66', anchor='lt')
            current_y += line_spacing
        else:
            draw.text((info_x, current_y), "Temp: [N/D]", font=font_info, fill='#ffaa00', anchor='lt')
            current_y += line_spacing
        
        if precipitacion is not None:
            # Color según nivel de precipitación
            if precipitacion < 20:
                color_precip = '#ffaa66'
            elif precipitacion < 100:
                color_precip = '#6699ff'
            else:
                color_precip = '#0066cc'
            
            texto_precip = f"Precip: {precipitacion:.1f} mm"
            draw.text((info_x, current_y), texto_precip, font=font_info, fill=color_precip, anchor='lt')
            current_y += line_spacing
        else:
            draw.text((info_x, current_y), "Precip: [N/D]", font=font_info, fill='#ffaa00', anchor='lt')
            current_y += line_spacing

    def _draw_multiline_text_with_shadow(self, draw, position, text, font, fill, anchor='lt', max_width=900):
        """
        Dibuja texto multilínea con sombra negra para máxima legibilidad
        """
        x, y = position
        shadow_offset = 2
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        line_height = font.size + 6
        for i, line in enumerate(lines):
            # Sombra
            draw.text((x+shadow_offset, y + i*line_height + shadow_offset), line, font=font, fill='black', anchor=anchor)
            # Texto principal
            draw.text((x, y + i*line_height), line, font=font, fill=fill, anchor=anchor)
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convierte color hexadecimal a RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _create_video_ffmpeg(self, frame_paths: List[str], output_path: str):
        """
        Crea video MP4 usando FFmpeg con máxima calidad
        
        Args:
            frame_paths: Lista de rutas de frames PNG
            output_path: Ruta del video de salida
        """
        if not frame_paths:
            raise ValueError("No hay frames para crear el video")
        
        # Crear archivo de lista para FFmpeg
        frames_dir = os.path.dirname(frame_paths[0])
        list_file = os.path.join(frames_dir, 'frames.txt')
        
        # CRÍTICO: Usar FRAME_DURATION (2.5 segundos) para que sea entendible
        # No usar 1.0/fps que hace video muy rápido
        with open(list_file, 'w') as f:
            for frame_path in frame_paths:
                f.write(f"file '{frame_path}'\n")
                f.write(f"duration {self.FRAME_DURATION}\n")
            # Último frame sin duración (necesario para FFmpeg)
            f.write(f"file '{frame_paths[-1]}'\n")
        
        logger.info(f"Lista de frames creada: {list_file} (duración: {self.FRAME_DURATION}s/frame)")
        
        # Comando FFmpeg OPTIMIZADO para MÁXIMA CALIDAD de imágenes satelitales
        # Configuración broadcast-quality para entrega comercial
        # CRÍTICO: Agregar transiciones suaves fade in/out entre frames
        fade_duration = 0.3  # 300ms de fade para transiciones profesionales
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Sobrescribir sin preguntar
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c:v', 'libx264',  # Codec H.264 (máxima compatibilidad)
            '-preset', 'veryslow',  # VERYSLOW = máxima calidad (lento pero vale la pena)
            '-crf', str(self.crf),  # CRF 18 = calidad broadcast
            '-b:v', self.bitrate,  # Bitrate alto para preservar detalles raster
            '-maxrate', str(int(self.bitrate.replace('k', '')) * 1.5) + 'k',  # Picos de bitrate permitidos
            '-bufsize', str(int(self.bitrate.replace('k', '')) * 3) + 'k',  # Buffer grande
            '-pix_fmt', 'yuv420p',  # Formato de píxel compatible con todos los reproductores
            # CRÍTICO: Filtros de video para calidad profesional
            '-vf', (
                f'fps={self.fps},'  # FPS fijo
                f'scale={self.width}:{self.height}:flags=lanczos,'  # Escalado LANCZOS para máxima calidad
                f'fade=t=in:st=0:d={fade_duration},'  # Fade in al inicio
                f'fade=t=out:st={len(frame_paths) * self.FRAME_DURATION - fade_duration}:d={fade_duration}'  # Fade out al final
            ),
            '-movflags', '+faststart',  # Optimización para streaming (meta al inicio del archivo)
            '-profile:v', 'high',  # Profile High (mejor compresión/calidad)
            '-level', '4.2',  # Level 4.2 (soporta 4K)
            output_path
        ]
        
        logger.info(f"Ejecutando FFmpeg: {' '.join(ffmpeg_cmd)}")
        
        try:
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            logger.info("Video creado exitosamente con FFmpeg")
            
            # Verificar que el archivo fue creado
            if not os.path.exists(output_path):
                raise RuntimeError("FFmpeg ejecutado pero archivo no encontrado")
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            logger.info(f"Tamaño del video: {file_size:.2f} MB")
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
            logger.error(f"Error ejecutando FFmpeg: {error_msg}")
            raise RuntimeError(f"FFmpeg falló: {error_msg}")
    
    def _get_default_output_path(self, indice: str) -> str:
        """Genera ruta de salida por defecto"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'timeline_{indice}_{timestamp}.mp4'
        
        # Guardar en directorio de medios temporales
        output_dir = os.path.join(settings.MEDIA_ROOT, 'timeline_videos')
        os.makedirs(output_dir, exist_ok=True)
        
        return os.path.join(output_dir, filename)
    
    def _get_rangos_agronomicos(self, indice: str) -> List[Dict]:
        """
        Retorna rangos agronómicos con colores y significado claro
        SIN tecnicismos, para que el agricultor entienda
        """
        if indice == 'ndvi':
            return [
                {'min': 0.0, 'max': 0.2, 'color': '#8B0000', 'significado': 'Muy bajo'},
                {'min': 0.2, 'max': 0.4, 'color': '#FF8C00', 'significado': 'Bajo'},
                {'min': 0.4, 'max': 0.6, 'color': '#FFD700', 'significado': 'Moderado'},
                {'min': 0.6, 'max': 0.8, 'color': '#9ACD32', 'significado': 'Bueno'},
                {'min': 0.8, 'max': 1.0, 'color': '#228B22', 'significado': 'Excelente'}
            ]
        elif indice == 'ndmi':
            return [
                {'min': -0.8, 'max': -0.4, 'color': '#8B0000', 'significado': 'Muy seco'},
                {'min': -0.4, 'max': 0.0, 'color': '#FF8C00', 'significado': 'Seco'},
                {'min': 0.0, 'max': 0.2, 'color': '#FFD700', 'significado': 'Moderado'},
                {'min': 0.2, 'max': 0.4, 'color': '#4682B4', 'significado': 'Humedo'},
                {'min': 0.4, 'max': 0.8, 'color': '#1E90FF', 'significado': 'Muy humedo'}
            ]
        else:  # savi
            return [
                {'min': 0.0, 'max': 0.2, 'color': '#8B0000', 'significado': 'Muy bajo'},
                {'min': 0.2, 'max': 0.4, 'color': '#FF8C00', 'significado': 'Bajo'},
                {'min': 0.4, 'max': 0.6, 'color': '#FFD700', 'significado': 'Moderado'},
                {'min': 0.6, 'max': 0.8, 'color': '#9ACD32', 'significado': 'Bueno'},
                {'min': 0.8, 'max': 1.0, 'color': '#228B22', 'significado': 'Excelente'}
            ]
    
    def _generar_texto_interpretativo_breve(self, indice: str, valor: float, 
                                             etiqueta: str, descripcion: str,
                                             frame_data: Dict) -> str:
        """
        Genera texto interpretativo BREVE y CLARO para agricultores
        Máximo 2-3 líneas, lenguaje simple
        """
        comparacion = frame_data.get('comparacion', {}).get(indice)
        
        # Interpretaciones simplificadas por rango
        if valor >= 0.7:
            base = "La mayor parte del lote presenta vegetacion saludable."
        elif valor >= 0.5:
            base = "El lote muestra desarrollo moderado de vegetacion."
        elif valor >= 0.3:
            base = "Se observan areas con desarrollo limitado de vegetacion."
        else:
            base = "El lote requiere atencion por bajo desarrollo vegetal."
        
        # Agregar detalle sobre variabilidad si es alta
        variabilidad = frame_data.get(indice, {}).get('desviacion_estandar', 0)
        if variabilidad and variabilidad > 0.15:
            base += " Se observan areas puntuales con menor vigor."
        
        return base
