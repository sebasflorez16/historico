"""
Exportador de video profesional MULTI-ESCENA para Timeline de AgroTech Histórico
Genera videos MP4 con estructura completa: Portada + Mapas Mensuales + Análisis + Recomendaciones + Cierre

ESTRICTAMENTE SIGUE LAS ESPECIFICACIONES DE finalizando_timeline.md
- NO inventa valores
- NO analiza datos
- Solo presenta información del motor de análisis

@author: AgroTech Team
@version: 3.0.0 - Multi-escena profesional
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

from .video_content_helpers import (
    obtener_info_indice,
    generar_texto_aplicacion_terreno,
    detectar_proximo_mes_disponible,
    formatear_coordenadas,
    truncar_texto,
    limpiar_texto_analisis,
    parsear_recomendaciones_desde_texto,
    calcular_estadisticas_periodo
)

logger = logging.getLogger(__name__)


class TimelineVideoExporterMultiScene:
    """
    Exportador profesional de videos de timeline con estructura multi-escena
    """
    
    # Configuración de calidad
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    DEFAULT_FPS = 24
    DEFAULT_BITRATE = '10000k'
    DEFAULT_CRF = 18
    
    # Duraciones por escena (en segundos) - ACTUALIZADAS
    COVER_COMPLETE_DURATION = 4.0         # Portada completa con info de parcela
    INDEX_EXPLANATION_DURATION = 5.0      # Explicación del índice
    FULL_ANALYSIS_DURATION = 7.0          # Análisis completo del motor
    MONTHLY_MAP_DURATION = 2.5            # Mapas mensuales
    UNAVAILABLE_IMAGE_DURATION = 2.5      # Imagen no disponible por nubosidad
    RECOMMENDATIONS_DURATION = 5.0        # Recomendaciones o resumen
    CLOSING_DURATION = 3.0                # Cierre
    
    def __init__(self, 
                 width: int = DEFAULT_WIDTH,
                 height: int = DEFAULT_HEIGHT,
                 fps: int = DEFAULT_FPS,
                 bitrate: str = DEFAULT_BITRATE,
                 crf: int = DEFAULT_CRF):
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.crf = crf
        
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg no está instalado")
        
        logger.info(f"✅ TimelineVideoExporterMultiScene inicializado: {width}x{height} @ {fps}fps")
    
    def _check_ffmpeg(self) -> bool:
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except:
            return False
    
    def export_timeline(self,
                       frames_data: List[Dict],
                       indice: str,
                       output_path: Optional[str] = None,
                       parcela_info: Optional[Dict] = None,
                       analisis_texto: Optional[str] = None,
                       recomendaciones_texto: Optional[str] = None) -> str:
        """
        Exporta video multi-escena completo
        """
        if not frames_data:
            raise ValueError("No hay frames para exportar")
        
        if indice not in ['ndvi', 'ndmi', 'savi']:
            raise ValueError(f"Índice inválido: {indice}")
        
        logger.info(f"🎬 Iniciando exportación multi-escena: {len(frames_data)} meses, índice={indice}")
        
        temp_dir = tempfile.mkdtemp(prefix='agrotech_video_')
        
        try:
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
            
            if output_path is None:
                output_path = self._get_default_output_path(indice)
            
            self._create_video_ffmpeg(frame_paths, output_path)
            
            logger.info(f"✅ Video generado: {output_path}")
            return output_path
            
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def _generate_all_scenes(self,
                            frames_data: List[Dict],
                            indice: str,
                            temp_dir: str,
                            parcela_info: Optional[Dict] = None,
                            analisis_texto: Optional[str] = None,
                            recomendaciones_texto: Optional[str] = None) -> List[str]:
        """
        Genera TODAS las escenas del video en NUEVO ORDEN:
        1. Portada completa (4s)
        2. Explicación del índice (5s)
        3. Análisis completo del motor (7s) - si existe
        4. Mapas mensuales (2.5s c/u) o "no disponible"
        5. Recomendaciones o resumen (5s)
        6. Cierre (3s)
        """
        all_frames = []
        counter = 0
        
        # 1️⃣ PORTADA COMPLETA
        logger.info("📝 Generando portada completa...")
        cover_frames = self._generate_cover_complete_scene(parcela_info, frames_data, indice, temp_dir, counter)
        all_frames.extend(cover_frames)
        counter += len(cover_frames)
        logger.info(f"✅ Portada completa: {len(cover_frames)} frames")
        
        # 2️⃣ EXPLICACIÓN DEL ÍNDICE
        logger.info(f"� Generando explicación del índice {indice.upper()}...")
        explanation_frames = self._generate_index_explanation_scene(indice, parcela_info, temp_dir, counter)
        all_frames.extend(explanation_frames)
        counter += len(explanation_frames)
        logger.info(f"✅ Explicación: {len(explanation_frames)} frames")
        
        # 3️⃣ ANÁLISIS COMPLETO DEL MOTOR (solo si existe)
        if analisis_texto and analisis_texto.strip():
            logger.info("📊 Generando análisis completo del motor...")
            analysis_frames = self._generate_full_analysis_scene(analisis_texto, indice, temp_dir, counter)
            all_frames.extend(analysis_frames)
            counter += len(analysis_frames)
            logger.info(f"✅ Análisis completo: {len(analysis_frames)} frames")
        
        # 4️⃣ MAPAS MENSUALES (con detección de imágenes no disponibles)
        logger.info(f"🗺️ Generando {len(frames_data)} mapas mensuales...")
        for i, frame_data in enumerate(frames_data):
            monthly_frames = self._generate_monthly_map_or_unavailable(frame_data, indice, frames_data, i, temp_dir, counter)
            all_frames.extend(monthly_frames)
            counter += len(monthly_frames)
        logger.info(f"✅ Mapas mensuales: {len(frames_data)} escenas")
        
        # 5️⃣ RECOMENDACIONES O RESUMEN
        logger.info("💡 Generando recomendaciones o resumen...")
        if recomendaciones_texto and recomendaciones_texto.strip():
            reco_frames = self._generate_recommendations_scene(recomendaciones_texto, indice, temp_dir, counter)
        else:
            # Generar resumen si no hay recomendaciones
            reco_frames = self._generate_summary_scene(frames_data, indice, temp_dir, counter)
        all_frames.extend(reco_frames)
        counter += len(reco_frames)
        logger.info(f"✅ Recomendaciones/Resumen: {len(reco_frames)} frames")
        
        # 6️⃣ CIERRE
        logger.info("🎬 Generando cierre...")
        closing_frames = self._generate_closing_scene(indice, temp_dir, counter)
        all_frames.extend(closing_frames)
        counter += len(closing_frames)
        logger.info(f"✅ Cierre: {len(closing_frames)} frames")
        
        logger.info(f"🎞️ TOTAL: {len(all_frames)} frames generados")
        return all_frames
    
    def _generate_cover_scene(self, indice, frames_data, parcela_info, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 1: PORTADA
        - Logo AgroTech
        - Índice analizado
        - Parcela/lote
        - Rango temporal
        """
        num_frames = int(self.COVER_DURATION * self.fps)
        frames = []
        
        # Obtener rango temporal
        if frames_data:
            primer_mes = frames_data[0].get('periodo_texto', '')
            ultimo_mes = frames_data[-1].get('periodo_texto', '')
            rango_temporal = f"{primer_mes} - {ultimo_mes}"
        else:
            rango_temporal = "Sin datos"
        
        # Nombre de parcela
        parcela_nombre = parcela_info.get('nombre', 'Parcela') if parcela_info else 'Parcela'
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
                font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
                font_info = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            except:
                font_title = font_subtitle = font_info = ImageFont.load_default()
            
            center_x = self.width // 2
            y_pos = 300
            
            # Logo/Título AgroTech
            draw.text((center_x, y_pos), "AGROTECH", font=font_title, fill='#00ff88', anchor='mm')
            y_pos += 100
            
            # Índice analizado
            indice_texto = f"Análisis {indice.upper()}"
            draw.text((center_x, y_pos), indice_texto, font=font_subtitle, fill='white', anchor='mm')
            y_pos += 80
            
            # Parcela
            draw.text((center_x, y_pos), parcela_nombre, font=font_info, fill='#cccccc', anchor='mm')
            y_pos += 60
            
            # Rango temporal
            draw.text((center_x, y_pos), rango_temporal, font=font_info, fill='#999999', anchor='mm')
            
            # Guardar frame
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _generate_monthly_map_scene(self, frame_data, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 2: MAPA MENSUAL
        - Imagen NDVI (sin modificar estilo)
        - NDVI promedio
        - Estado general
        - Cambio vs mes anterior
        - Calidad de imagen
        - Clima del mes
        """
        num_frames = int(self.MONTHLY_MAP_DURATION * self.fps)
        frames = []
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            # Cargar imagen satelital
            imagen_url = frame_data.get('imagenes', {}).get(indice)
            if imagen_url:
                try:
                    sat_img = self._load_satellite_image(imagen_url)
                    if sat_img:
                        sat_img = sat_img.filter(ImageFilter.SMOOTH_MORE)
                        sat_img_resized = self._resize_and_center(sat_img, self.width, self.height)
                        img.paste(sat_img_resized, (0, 0))
                except:
                    pass
            
            # Overlay de información
            self._draw_monthly_overlay(img, draw, frame_data, indice)
            
            # Guardar
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _draw_monthly_overlay(self, img, draw, frame_data, indice):
        """
        Dibuja overlay de información mensual sobre el mapa
        INCLUYE: Leyenda de colores en lenguaje natural
        """
        try:
            font_header = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
            font_data = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        except:
            font_header = font_data = font_small = ImageFont.load_default()
        
        # Header: NDVI · Mes Año
        periodo = frame_data.get('periodo_texto', '')
        header = f"{indice.upper()} · {periodo}"
        draw.text((20, 20), header, font=font_header, fill='white', anchor='lt')
        
        # LEYENDA DE COLORES (esquina inferior izquierda)
        self._draw_color_legend(draw, indice, font_small)
        
        # Columna derecha de información
        info_x = int(self.width * 0.78)
        y = 150
        spacing = 30
        
        # NDVI promedio
        valor = frame_data.get(indice, {}).get('promedio')
        if valor is not None:
            draw.text((info_x, y), f"{indice.upper()}: {valor:.3f}", font=font_data, fill='white', anchor='lt')
            y += spacing
        
        # Estado general
        clasificacion = frame_data.get('clasificaciones', {}).get(indice, {})
        if clasificacion:
            estado = clasificacion.get('etiqueta', '')
            draw.text((info_x, y), f"Estado: {estado}", font=font_data, fill='#00ff88', anchor='lt')
            y += spacing * 2
        
        # Cambio mensual
        comparacion = frame_data.get('comparacion', {})
        if comparacion and indice in comparacion:
            porcentaje = comparacion[indice].get('porcentaje')
            if porcentaje is not None:
                signo = '+' if porcentaje >= 0 else ''
                color = '#00ff00' if porcentaje > 0 else '#ff4444'
                draw.text((info_x, y), "Cambio mensual:", font=font_data, fill='white', anchor='lt')
                y += spacing
                draw.text((info_x, y), f"{signo}{porcentaje:.1f}%", font=font_data, fill=color, anchor='lt')
                y += spacing
                draw.text((info_x, y), "vs mes anterior", font=font_data, fill='#888888', anchor='lt')
                y += spacing * 2
        
        # Calidad de imagen
        metadata = frame_data.get('imagen_metadata', {})
        nubosidad = metadata.get('nubosidad')
        if nubosidad is not None:
            nubosidad_pct = nubosidad * 100 if nubosidad <= 1.0 else nubosidad
            if nubosidad_pct < 30:
                calidad = "Buena"
                color_calidad = '#00ff00'
            elif nubosidad_pct < 50:
                calidad = "Moderada"
                color_calidad = '#ffcc00'
            else:
                calidad = "Baja"
                color_calidad = '#ff4444'
            
            draw.text((info_x, y), f"Calidad: {calidad}", font=font_data, fill=color_calidad, anchor='lt')
            y += spacing
            draw.text((info_x, y), f"Nubosidad: {nubosidad_pct:.1f}%", font=font_data, fill='#888888', anchor='lt')
            y += spacing * 2
        
        # Clima
        temperatura = frame_data.get('temperatura')
        precipitacion = frame_data.get('precipitacion')
        
        if temperatura is not None or precipitacion is not None:
            draw.text((info_x, y), "CLIMA DEL MES", font=font_data, fill='white', anchor='lt')
            y += spacing
            
            if temperatura is not None:
                draw.text((info_x, y), f"Temp: {temperatura:.1f}°C", font=font_data, fill='#ffcc66', anchor='lt')
                y += spacing
            
            if precipitacion is not None:
                draw.text((info_x, y), f"Precip: {precipitacion:.1f} mm", font=font_data, fill='#6699ff', anchor='lt')
    
    def _draw_color_legend(self, draw, indice, font):
        """
        Dibuja leyenda de colores en la esquina inferior izquierda del mapa
        En lenguaje natural y fácil de entender
        """
        # Posición de la leyenda (esquina inferior izquierda)
        legend_x = 30
        legend_y = self.height - 180
        box_size = 18
        spacing_y = 28
        
        # Obtener rangos de colores según el índice
        info_indice = obtener_info_indice(indice)
        rangos = info_indice.get('rangos', [])
        
        # Título de la leyenda
        draw.text((legend_x, legend_y - 35), "Escala de colores:", font=font, fill='white', anchor='lt')
        
        # Dibujar cada rango
        for i, rango in enumerate(rangos):
            y_pos = legend_y + (i * spacing_y)
            
            # Cuadro de color
            box_coords = [
                (legend_x, y_pos),
                (legend_x + box_size, y_pos + box_size)
            ]
            draw.rectangle(box_coords, fill=rango['color'], outline='white', width=1)
            
            # Etiqueta del rango
            label = rango['label']
            draw.text((legend_x + box_size + 10, y_pos + box_size // 2), label, font=font, fill='white', anchor='lm')
    
    def _generate_analysis_scene(self, analisis_texto, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 3: ANÁLISIS IA
        - Muestra SOLO el texto generado por el motor
        - Máximo 2-3 frases
        - Texto claro y legible
        - Sin tecnicismos innecesarios
        - Sin animaciones agresivas
        
        ESTRICTAMENTE según finalizando_timeline.md
        """
        num_frames = int(self.ANALYSIS_DURATION * self.fps)
        frames = []
        
        # Limpiar y limitar el texto a 2-3 frases máximo
        frases = self._limpiar_analisis_texto(analisis_texto, max_frases=3)
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
                font_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                font_title = font_text = ImageFont.load_default()
            
            # Título centrado
            draw.text((self.width // 2, 180), "ANÁLISIS", font=font_title, fill='#00ff88', anchor='mm')
            
            # Texto del análisis limpio y claro
            self._draw_wrapped_text(draw, frases, font_text, 'white', y_start=350, max_width=1650, line_spacing=50)
            
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _generate_recommendations_scene(self, recomendaciones_texto, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 4: RECOMENDACIONES
        - Muestra SOLO las recomendaciones del motor
        - Máximo 3 recomendaciones
        - Formato en bullets
        - Ordenadas por prioridad
        - Enfocadas en acción práctica
        
        ESTRICTAMENTE según finalizando_timeline.md
        """
        num_frames = int(self.RECOMMENDATIONS_DURATION * self.fps)
        frames = []
        
        # Parsear y limpiar recomendaciones
        recos = self._parsear_recomendaciones(recomendaciones_texto, max_recos=3)
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
                font_bullet = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
            except:
                font_title = font_bullet = ImageFont.load_default()
            
            # Título centrado
            draw.text((self.width // 2, 180), "RECOMENDACIONES", font=font_title, fill='#00ff88', anchor='mm')
            
            # Bullets de recomendaciones
            y_pos = 350
            spacing_entre_bullets = 140
            
            for idx, reco in enumerate(recos, 1):
                # Número de prioridad + bullet
                bullet_text = f"{idx}. {reco}"
                self._draw_wrapped_text(
                    draw, 
                    bullet_text, 
                    font_bullet, 
                    'white', 
                    y_start=y_pos, 
                    max_width=1650,
                    line_spacing=45,
                    align='left',
                    x_start=200
                )
                y_pos += spacing_entre_bullets
            
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _generate_closing_scene(self, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 5: CIERRE
        - Logo AgroTech
        - Mensaje de cierre
        - Estilo sobrio
        """
        num_frames = int(self.CLOSING_DURATION * self.fps)
        frames = []
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_logo = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
                font_msg = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            except:
                font_logo = font_msg = ImageFont.load_default()
            
            center_x = self.width // 2
            
            # Logo
            draw.text((center_x, 400), "AGROTECH", font=font_logo, fill='#00ff88', anchor='mm')
            
            # Mensaje
            draw.text((center_x, 550), "Análisis satelital para agricultura de precisión", font=font_msg, fill='#888888', anchor='mm')
            
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _draw_wrapped_text(self, draw, text, font, fill, y_start, max_width, line_spacing=10, align='center', x_start=None):
        """
        Helper para texto multilínea con opciones de alineación
        
        Args:
            draw: ImageDraw object
            text: Texto a dibujar
            font: Fuente a usar
            fill: Color del texto
            y_start: Posición Y inicial
            max_width: Ancho máximo del texto
            line_spacing: Espaciado extra entre líneas (default 10)
            align: 'center' o 'left' (default 'center')
            x_start: Posición X para alineación izquierda (solo con align='left')
        """
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        line_height = font.size + line_spacing
        
        for i, line in enumerate(lines):
            y_pos = y_start + i * line_height
            
            if align == 'left' and x_start is not None:
                draw.text((x_start, y_pos), line, font=font, fill=fill, anchor='lm')
            else:
                # Centrado por defecto
                center_x = self.width // 2
                draw.text((center_x, y_pos), line, font=font, fill=fill, anchor='mm')
    
    def _load_satellite_image(self, url: str) -> Optional[Image.Image]:
        """Carga imagen satelital desde URL o archivo local"""
        try:
            if url.startswith('/media/') or url.startswith('media/'):
                relative_path = url.replace('/media/', '').replace('media/', '')
                local_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                if os.path.exists(local_path):
                    return Image.open(local_path).convert('RGB')
            
            if url.startswith('http'):
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                return Image.open(BytesIO(response.content)).convert('RGB')
        except:
            pass
        return None
    
    def _resize_and_center(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Redimensiona y centra imagen satelital"""
        img_w, img_h = img.size
        img_ratio = img_w / img_h
        target_ratio = target_w / target_h
        scale_factor = 0.88
        
        if img_ratio > target_ratio:
            new_w = int(target_w * scale_factor)
            new_h = int((target_w * scale_factor) / img_ratio)
        else:
            new_h = int(target_h * scale_factor)
            new_w = int((target_h * scale_factor) * img_ratio)
        
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new('RGB', (target_w, target_h), color='black')
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        canvas.paste(img_resized, (offset_x, offset_y))
        return canvas
    
    def _create_video_ffmpeg(self, frame_paths: List[str], output_path: str):
        """Crea video con FFmpeg"""
        frames_dir = os.path.dirname(frame_paths[0])
        list_file = os.path.join(frames_dir, 'frames.txt')
        
        with open(list_file, 'w') as f:
            for i, frame_path in enumerate(frame_paths):
                f.write(f"file '{frame_path}'\n")
                # Última escena no necesita duración
                if i < len(frame_paths) - 1:
                    f.write(f"duration {1.0 / self.fps}\n")
        
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file,
            '-c:v', 'libx264', '-preset', 'veryslow', '-crf', str(self.crf),
            '-b:v', self.bitrate, '-pix_fmt', 'yuv420p',
            '-vf', f'fps={self.fps}',
            '-movflags', '+faststart',
            output_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    def _get_default_output_path(self, indice: str) -> str:
        """Genera ruta de salida por defecto"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'timeline_{indice}_multiscene_{timestamp}.mp4'
        output_dir = os.path.join(settings.MEDIA_ROOT, 'timeline_videos')
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, filename)
    
    def _limpiar_analisis_texto(self, texto: str, max_frases: int = 3) -> str:
        """
        Limpia y limita el texto de análisis a máximo 2-3 frases claras
        Sin tecnicismos innecesarios
        
        Args:
            texto: Texto original del análisis
            max_frases: Número máximo de frases (default 3)
            
        Returns:
            Texto limpio y limitado
        """
        if not texto:
            return "No hay análisis disponible para este periodo."
        
        # Dividir por puntos para obtener frases
        frases = [f.strip() for f in texto.split('.') if f.strip()]
        
        # Limitar a max_frases
        frases_seleccionadas = frases[:max_frases]
        
        # Reconstruir texto con puntos
        texto_limpio = '. '.join(frases_seleccionadas)
        if not texto_limpio.endswith('.'):
            texto_limpio += '.'
        
        return texto_limpio
    
    def _parsear_recomendaciones(self, texto: str, max_recos: int = 3) -> List[str]:
        """
        Parsea y limpia recomendaciones del texto
        Retorna máximo 3 recomendaciones ordenadas por prioridad
        
        Args:
            texto: Texto original de recomendaciones
            max_recos: Número máximo de recomendaciones (default 3)
            
        Returns:
            Lista de strings con recomendaciones limpias
        """
        if not texto:
            return []
        
        recos = []
        
        # Intentar parsear por líneas con bullets
        for line in texto.split('\n'):
            line = line.strip()
            
            # Detectar bullets comunes
            if line.startswith(('-', '•', '*', '→', '►')):
                # Remover bullet y limpiar
                reco = line.lstrip('-•*→► ').strip()
                if reco:
                    recos.append(reco)
            
            # Si empieza con número (1., 2., etc)
            elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
                reco = line[2:].strip()
                if reco:
                    recos.append(reco)
            
            # Línea simple sin bullet (si aún no tenemos suficientes)
            elif line and len(recos) < max_recos and len(line) > 10:
                # Evitar títulos (muy cortos o en mayúsculas)
                if not line.isupper() and not line.endswith(':'):
                    recos.append(line)
        
        # Si no se encontraron bullets, dividir por puntos
        if not recos:
            frases = [f.strip() for f in texto.split('.') if f.strip() and len(f.strip()) > 10]
            recos = frases[:max_recos]
        
        # Limitar a max_recos y limpiar
        recos = recos[:max_recos]
        
        # Limpiar cada recomendación
        recos_limpias = []
        for reco in recos:
            # Remover posibles prefijos residuales
            reco = reco.strip()
            if reco:
                recos_limpias.append(reco)
        
        return recos_limpias
    
    def _generate_cover_complete_scene(self, parcela_info, frames_data, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 1: PORTADA COMPLETA
        - Logo AgroTech Histórico
        - Nombre de la parcela/lote
        - Coordenadas del centro
        - Área en hectáreas
        - Tipo de cultivo
        - Rango de fechas completo
        - Índice a analizar
        - Total de meses analizados
        """
        num_frames = int(self.COVER_COMPLETE_DURATION * self.fps)
        frames = []
        
        # Obtener información de la parcela
        parcela_nombre = parcela_info.get('nombre', 'Parcela') if parcela_info else 'Parcela'
        area = parcela_info.get('area_hectareas', 0) if parcela_info else 0
        cultivo = parcela_info.get('tipo_cultivo', 'Sin especificar') if parcela_info else 'Sin especificar'
        
        # Coordenadas del centro
        centro_lat = parcela_info.get('centro_lat', 0) if parcela_info else 0
        centro_lon = parcela_info.get('centro_lon', 0) if parcela_info else 0
        lat_texto, lon_texto = formatear_coordenadas(centro_lat, centro_lon)
        
        # Rango temporal
        if frames_data:
            primer_mes = frames_data[0].get('periodo_texto', '')
            ultimo_mes = frames_data[-1].get('periodo_texto', '')
            rango_temporal = f"{primer_mes} - {ultimo_mes}"
            total_meses = len(frames_data)
        else:
            rango_temporal = "Sin datos"
            total_meses = 0
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
                font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
                font_info = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
            except:
                font_title = font_subtitle = font_info = font_small = ImageFont.load_default()
            
            center_x = self.width // 2
            y_pos = 200
            
            # Logo/Título
            draw.text((center_x, y_pos), "AGROTECH HISTÓRICO", font=font_title, fill='#00ff88', anchor='mm')
            y_pos += 100
            
            # Subtítulo: Análisis Satelital - INDICE
            indice_texto = f"Análisis Satelital - {indice.upper()}"
            draw.text((center_x, y_pos), indice_texto, font=font_subtitle, fill='white', anchor='mm')
            y_pos += 90
            
            # Información de la parcela (alineado a la izquierda)
            left_x = 150
            
            # Parcela
            draw.text((left_x, y_pos), f"• Parcela: {parcela_nombre}", font=font_info, fill='white', anchor='lm')
            y_pos += 50
            
            # Coordenadas
            draw.text((left_x, y_pos), f"• Centro: {lat_texto}, {lon_texto}", font=font_small, fill='#cccccc', anchor='lm')
            y_pos += 45
            
            # Área
            if area > 0:
                draw.text((left_x, y_pos), f"• Área: {area:.2f} hectáreas", font=font_info, fill='white', anchor='lm')
                y_pos += 50
            
            # Cultivo
            if cultivo and cultivo.lower() != 'sin especificar':
                draw.text((left_x, y_pos), f"• Cultivo: {cultivo}", font=font_info, fill='white', anchor='lm')
                y_pos += 50
            
            y_pos += 20
            
            # Período
            draw.text((left_x, y_pos), f"• Período: {rango_temporal}", font=font_info, fill='#00ff88', anchor='lm')
            y_pos += 50
            
            # Total meses
            draw.text((left_x, y_pos), f"• Total meses analizados: {total_meses}", font=font_info, fill='#00ff88', anchor='lm')
            
            # Guardar frame
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _generate_index_explanation_scene(self, indice, parcela_info, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 2: EXPLICACIÓN DEL ÍNDICE
        - Título: ¿Qué es el INDICE?
        - Nombre completo
        - Cómo funciona
        - Rangos de valores
        - Aplicación en este terreno
        """
        num_frames = int(self.INDEX_EXPLANATION_DURATION * self.fps)
        frames = []
        
        # Obtener información del índice
        info_indice = obtener_info_indice(indice)
        aplicacion_terreno = generar_texto_aplicacion_terreno(indice, parcela_info or {})
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
                font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 38)
                font_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
            except:
                font_title = font_subtitle = font_text = font_small = ImageFont.load_default()
            
            center_x = self.width // 2
            y_pos = 150
            
            # Título
            titulo = f"¿Qué es el {info_indice['siglas']}?"
            draw.text((center_x, y_pos), titulo, font=font_title, fill='#00ff88', anchor='mm')
            y_pos += 90
            
            # Nombre completo
            draw.text((center_x, y_pos), info_indice['nombre_completo'], font=font_subtitle, fill='white', anchor='mm')
            y_pos += 70
            
            # Cómo funciona (en lenguaje natural)
            for linea in info_indice.get('como_funciona', []):
                draw.text((center_x, y_pos), linea, font=font_text, fill='#cccccc', anchor='mm')
                y_pos += 42
            
            y_pos += 30
            
            # Rangos de valores en lenguaje natural
            draw.text((center_x, y_pos), "¿Cómo se interpretan los valores?", font=font_subtitle, fill='white', anchor='mm')
            y_pos += 55
            
            for rango_texto in info_indice.get('rangos_texto', []):
                draw.text((center_x, y_pos), rango_texto, font=font_small, fill='#999999', anchor='mm')
                y_pos += 40
            
            y_pos += 30
            
            # Aplicación en este terreno
            draw.text((center_x, y_pos), "En su terreno:", font=font_text, fill='#00ff88', anchor='mm')
            y_pos += 48
            
            # Wrap del texto de aplicación
            self._draw_wrapped_text(draw, aplicacion_terreno, font_small, '#cccccc', y_pos, max_width=1600, line_spacing=40)
            
            # Guardar frame
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _generate_full_analysis_scene(self, analisis_texto, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 3: ANÁLISIS COMPLETO DEL MOTOR
        - Análisis generado por el motor de informes
        - Tendencias del período
        - Conclusiones principales
        """
        num_frames = int(self.FULL_ANALYSIS_DURATION * self.fps)
        frames = []
        
        # Limpiar y truncar texto
        texto_limpio = limpiar_texto_analisis(analisis_texto, max_lineas=14)
        texto_truncado = truncar_texto(texto_limpio, max_chars=700)
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
                font_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            except:
                font_title = font_text = ImageFont.load_default()
            
            # Título centrado
            draw.text((self.width // 2, 180), "ANÁLISIS INTEGRAL DEL PERÍODO", font=font_title, fill='#00ff88', anchor='mm')
            
            # Texto del análisis
            self._draw_wrapped_text(draw, texto_truncado, font_text, 'white', y_start=320, max_width=1650, line_spacing=45)
            
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _generate_monthly_map_or_unavailable(self, frame_data, indice, frames_data, frame_index, temp_dir, start_idx) -> List[str]:
        """
        ESCENA 4-N: MAPA MENSUAL o IMAGEN NO DISPONIBLE
        Detecta si hay imagen satelital disponible o si hay alta nubosidad
        """
        # Verificar disponibilidad de imagen
        imagen_url = frame_data.get('imagenes', {}).get(indice)
        metadata = frame_data.get('imagen_metadata', {})
        nubosidad = metadata.get('nubosidad')
        
        # Manejar caso de nubosidad None o inválida
        if nubosidad is None:
            nubosidad = 0.0  # Asumir calidad perfecta si no hay datos
        
        # Convertir nubosidad a porcentaje si es necesario
        if nubosidad <= 1.0:
            nubosidad_pct = nubosidad * 100
        else:
            nubosidad_pct = nubosidad
        
        # Decidir si mostrar imagen o "no disponible"
        if not imagen_url or nubosidad_pct > 70:
            # Generar escena de "imagen no disponible"
            return self._generate_unavailable_image_scene(frame_data, frames_data, frame_index, indice, temp_dir, start_idx)
        else:
            # Generar escena normal con mapa
            return self._generate_monthly_map_scene(frame_data, indice, temp_dir, start_idx)
    
    def _generate_unavailable_image_scene(self, frame_data, frames_data, frame_index, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA: IMAGEN NO DISPONIBLE
        Pantalla informativa cuando no hay imagen por alta nubosidad
        """
        num_frames = int(self.UNAVAILABLE_IMAGE_DURATION * self.fps)
        frames = []
        
        periodo = frame_data.get('periodo_texto', 'Mes desconocido')
        metadata = frame_data.get('imagen_metadata', {})
        nubosidad = metadata.get('nubosidad')
        
        # Manejar caso de nubosidad None
        if nubosidad is None:
            nubosidad = 1.0  # Asumir mala calidad si no hay datos
        
        # Convertir nubosidad a porcentaje
        if nubosidad <= 1.0:
            nubosidad_pct = nubosidad * 100
        else:
            nubosidad_pct = nubosidad
        
        # Detectar próximo mes disponible
        proximo_mes = detectar_proximo_mes_disponible(frames_data, frame_index)
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
                font_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
            except:
                font_title = font_text = font_small = ImageFont.load_default()
            
            center_x = self.width // 2
            y_pos = 300
            
            # Título
            draw.text((center_x, y_pos), "IMAGEN NO DISPONIBLE", font=font_title, fill='#ff6666', anchor='mm')
            y_pos += 80
            
            # Mes
            draw.text((center_x, y_pos), f"Mes: {periodo}", font=font_text, fill='white', anchor='mm')
            y_pos += 80
            
            # Razón
            razon = f"Debido a alta nubosidad durante este período ({nubosidad_pct:.0f}%),"
            draw.text((center_x, y_pos), razon, font=font_small, fill='#cccccc', anchor='mm')
            y_pos += 45
            
            draw.text((center_x, y_pos), "no fue posible obtener imágenes satelitales de", font=font_small, fill='#cccccc', anchor='mm')
            y_pos += 45
            
            draw.text((center_x, y_pos), "calidad suficiente para el análisis.", font=font_small, fill='#cccccc', anchor='mm')
            y_pos += 80
            
            # Próximo mes disponible
            if proximo_mes:
                draw.text((center_x, y_pos), "La siguiente imagen disponible", font=font_small, fill='#999999', anchor='mm')
                y_pos += 45
                draw.text((center_x, y_pos), f"corresponde a: {proximo_mes}", font=font_text, fill='#00ff88', anchor='mm')
            
            # Guardar frame
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
    
    def _generate_summary_scene(self, frames_data, indice, temp_dir, start_idx) -> List[str]:
        """
        ESCENA: ANÁLISIS PROFESIONAL Y DETALLADO DEL PERÍODO
        Análisis técnico pero en lenguaje natural, completo y preciso
        """
        num_frames = int(self.RECOMMENDATIONS_DURATION * self.fps)
        frames = []
        
        # Calcular estadísticas completas
        stats = calcular_estadisticas_periodo(frames_data, indice)
        
        # Calcular tendencia y variabilidad
        valores = []
        for frame in frames_data:
            valor = frame.get(indice, {}).get('promedio')
            if valor is not None:
                valores.append(valor)
        
        # Análisis de tendencia
        tendencia_texto = "estable"
        cambio_pct = 0
        if len(valores) >= 2:
            # Comparar primera mitad vs segunda mitad
            mitad = len(valores) // 2
            primera_mitad = sum(valores[:mitad]) / mitad
            segunda_mitad = sum(valores[mitad:]) / (len(valores) - mitad)
            cambio_pct = ((segunda_mitad - primera_mitad) / primera_mitad) * 100 if primera_mitad > 0 else 0
            
            if cambio_pct > 15:
                tendencia_texto = "creciente"
            elif cambio_pct > 5:
                tendencia_texto = "levemente creciente"
            elif cambio_pct < -15:
                tendencia_texto = "decreciente"
            elif cambio_pct < -5:
                tendencia_texto = "levemente decreciente"
        
        # Calcular variabilidad
        if len(valores) > 1:
            promedio = sum(valores) / len(valores)
            varianza = sum((x - promedio) ** 2 for x in valores) / len(valores)
            desv_std = varianza ** 0.5
            coef_variacion = (desv_std / promedio * 100) if promedio > 0 else 0
            
            if coef_variacion < 10:
                variabilidad = "muy estable"
            elif coef_variacion < 20:
                variabilidad = "estable"
            elif coef_variacion < 30:
                variabilidad = "moderadamente variable"
            else:
                variabilidad = "variable"
        else:
            variabilidad = "sin datos suficientes"
            coef_variacion = 0
        
        # Clasificar estado y generar análisis detallado según índice
        if indice == 'ndvi':
            if stats['promedio'] >= 0.7:
                estado = "Excelente Estado Vegetativo"
                analisis = f"El cultivo exhibe un vigor vegetativo excepcional durante el período analizado. El valor promedio de NDVI ({stats['promedio']:.3f}) se encuentra en el rango óptimo, indicando cobertura vegetal densa, biomasa verde abundante y alta actividad fotosintética. Este nivel es característico de cultivos en pleno desarrollo vegetativo o cosecha, con manejo agronómico efectivo y condiciones ambientales favorables. La variación entre {stats['minimo']:.3f} y {stats['maximo']:.3f} refleja la dinámica natural del ciclo fenológico del cultivo."
            elif stats['promedio'] >= 0.5:
                estado = "Buen Desarrollo Vegetativo"
                analisis = f"El cultivo presenta un desarrollo vegetativo saludable y dentro de parámetros aceptables. Con un NDVI promedio de {stats['promedio']:.3f}, la cobertura verde es adecuada para sustentar un crecimiento normal. Este rango indica que el dosel vegetal está establecido, aunque con margen de mejora. La fluctuación observada ({stats['minimo']:.3f} a {stats['maximo']:.3f}) sugiere respuesta positiva a las prácticas de manejo implementadas, con posibilidad de optimización en nutrición o riego para alcanzar niveles superiores."
            elif stats['promedio'] >= 0.3:
                estado = "Desarrollo Moderado"
                analisis = f"El cultivo muestra un vigor vegetativo moderado. El NDVI promedio de {stats['promedio']:.3f} indica una cobertura vegetal establecida pero limitada, lo cual puede corresponder a etapas fenológicas intermedias, condiciones de estrés moderado, o densidades de plantación bajas. El rango de variación ({stats['minimo']:.3f} a {stats['maximo']:.3f}) sugiere que el cultivo está respondiendo a los factores ambientales y de manejo, aunque podría beneficiarse de intervenciones dirigidas en fertilización, riego o manejo fitosanitario."
            elif stats['promedio'] >= 0.1:
                estado = "Desarrollo Inicial o Estrés"
                analisis = f"El cultivo presenta bajo vigor vegetativo. Con un NDVI de {stats['promedio']:.3f}, la biomasa verde es reducida, lo que puede atribuirse a cultivos en fase de establecimiento temprano, estrés ambiental significativo (hídrico, nutricional o térmico), o problemas fitosanitarios. La oscilación entre {stats['minimo']:.3f} y {stats['maximo']:.3f} requiere análisis detallado para identificar si se trata de una condición normal del ciclo o si demanda correcciones en el manejo agronómico."
            else:
                estado = "Área Sin Cultivo o Estrés Severo"
                analisis = f"Los valores de NDVI registrados (promedio {stats['promedio']:.3f}) están por debajo del umbral de vegetación activa. Esto indica que el área evaluada corresponde principalmente a suelo desnudo, agua, infraestructura o cultivo en estrés crítico. El rango observado ({stats['minimo']:.3f} a {stats['maximo']:.3f}) sugiere ausencia de cobertura vegetal significativa durante el período. Se recomienda verificar las fechas de siembra, evaluar condiciones del suelo y revisar sistemas de riego si se esperaba tener cultivo establecido."
                
        elif indice == 'ndmi':
            if stats['promedio'] >= 0.4:
                estado = "Óptima Hidratación"
                analisis = f"El cultivo mantiene niveles de humedad excelentes durante el período analizado. El NDMI promedio de {stats['promedio']:.3f} indica que el contenido hídrico de la vegetación es superior, reflejando un balance adecuado entre el agua disponible en el suelo y la demanda evapotranspirativa. Este nivel sugiere que el programa de riego está funcionando eficientemente o que las precipitaciones han sido suficientes. La estabilidad en el rango ({stats['minimo']:.3f} a {stats['maximo']:.3f}) demuestra consistencia en la disponibilidad hídrica."
            elif stats['promedio'] >= 0.2:
                estado = "Buena Disponibilidad Hídrica"
                analisis = f"El cultivo presenta contenido de humedad adecuado. Con un NDMI de {stats['promedio']:.3f}, la vegetación mantiene niveles de agua que permiten su desarrollo normal, aunque existe potencial de mejora. Este rango indica que el sistema de riego o las lluvias están cubriendo las necesidades básicas del cultivo, pero podrían optimizarse para alcanzar estados superiores de hidratación. La variación entre {stats['minimo']:.3f} y {stats['maximo']:.3f} refleja la respuesta del cultivo a eventos de riego o precipitación."
            elif stats['promedio'] >= 0.0:
                estado = "Estrés Hídrico Moderado"
                analisis = f"El cultivo muestra señales de déficit hídrico moderado. El NDMI promedio de {stats['promedio']:.3f} sugiere que la disponibilidad de agua es limitada, lo que puede afectar procesos fisiológicos como la fotosíntesis, crecimiento y desarrollo de estructuras reproductivas. El rango de variación ({stats['minimo']:.3f} a {stats['maximo']:.3f}) indica fluctuaciones en el estado hídrico que requieren atención. Se recomienda revisar la frecuencia y cantidad de riego, verificar la uniformidad del sistema y considerar las condiciones climáticas locales."
            elif stats['promedio'] >= -0.4:
                estado = "Estrés Hídrico Significativo"
                analisis = f"El cultivo presenta déficit hídrico considerable. Con un NDMI de {stats['promedio']:.3f}, el contenido de agua en la vegetación está por debajo de niveles óptimos, lo que compromete el rendimiento potencial. Este estado puede resultar en marchitez, reducción del crecimiento, aborto de flores o frutos, y disminución de la calidad del producto final. La oscilación entre {stats['minimo']:.3f} y {stats['maximo']:.3f} sugiere que el cultivo enfrenta períodos críticos de sequía. Se requiere intervención urgente en el sistema de riego."
            else:
                estado = "Estrés Hídrico Severo o Suelo Seco"
                analisis = f"Los valores de NDMI registrados (promedio {stats['promedio']:.3f}) indican estrés hídrico extremo o ausencia de vegetación activa. Este nivel crítico puede causar daños irreversibles al cultivo, incluyendo pérdida de área foliar, muerte de tejidos y reducción drástica del rendimiento. El rango observado ({stats['minimo']:.3f} a {stats['maximo']:.3f}) confirma condiciones de sequía prolongada. Se requiere evaluación inmediata del sistema de riego, verificación de disponibilidad de agua y consideración de pérdidas económicas potenciales."
        
        else:  # SAVI
            if stats['promedio'] >= 0.6:
                estado = "Excelente Cobertura Vegetal"
                analisis = f"El cultivo ha alcanzado una cobertura vegetal óptima. El SAVI promedio de {stats['promedio']:.3f} indica que la densidad de plantación es adecuada y que el dosel vegetal cubre eficientemente el suelo, minimizando la influencia del reflejo del suelo en las mediciones satelitales. Este nivel es característico de cultivos bien establecidos con distancias de siembra apropiadas y desarrollo foliar completo. La variación entre {stats['minimo']:.3f} y {stats['maximo']:.3f} refleja la progresión natural del crecimiento del cultivo."
            elif stats['promedio'] >= 0.4:
                estado = "Buena Cobertura en Desarrollo"
                analisis = f"El cultivo presenta una cobertura vegetal en progreso adecuado. Con un SAVI de {stats['promedio']:.3f}, el dosel está en proceso de cierre, con áreas de suelo aún visibles, lo cual es normal en etapas intermedias del ciclo fenológico o en cultivos con distancias de siembra amplias. El rango de valores ({stats['minimo']:.3f} a {stats['maximo']:.3f}) sugiere un crecimiento progresivo satisfactorio. Este índice es especialmente útil en esta fase para evaluar el establecimiento del cultivo sin interferencia significativa del color del suelo."
            elif stats['promedio'] >= 0.2:
                estado = "Cobertura Inicial o Irregular"
                analisis = f"El cultivo muestra cobertura vegetal limitada. El SAVI promedio de {stats['promedio']:.3f} indica que predomina el suelo expuesto sobre la vegetación, lo cual puede corresponder a cultivos recién emergidos, densidades de plantación bajas, o problemas de establecimiento. La variación observada ({stats['minimo']:.3f} a {stats['maximo']:.3f}) sugiere heterogeneidad en el desarrollo del cultivo. Se recomienda evaluar la uniformidad de siembra, verificar la germinación y considerar factores que puedan estar afectando el crecimiento inicial."
            else:
                estado = "Sin Cobertura Vegetal Significativa"
                analisis = f"Los valores de SAVI registrados (promedio {stats['promedio']:.3f}) indican ausencia de cobertura vegetal activa. Este nivel sugiere que el área analizada corresponde principalmente a suelo desnudo, agua, o vegetación en etapa muy temprana de germinación. El rango entre {stats['minimo']:.3f} y {stats['maximo']:.3f} confirma que no existe dosel vegetal establecido. Si se esperaba tener cultivo en desarrollo, se recomienda verificar las fechas de siembra, evaluar problemas de germinación o emergencia, y revisar las condiciones del suelo."
        
        for i in range(num_frames):
            img = Image.new('RGB', (self.width, self.height), color='#0a0a0a')
            draw = ImageDraw.Draw(img)
            
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
                font_subtitle = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
                font_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
            except:
                font_title = font_subtitle = font_text = ImageFont.load_default()
            
            center_x = self.width // 2
            y_pos = 120
            
            # Título
            draw.text((center_x, y_pos), "ANÁLISIS DEL PERÍODO", font=font_title, fill='#00ff88', anchor='mm')
            y_pos += 80
            
            # Estado general
            draw.text((center_x, y_pos), f"Estado General: {estado}", font=font_subtitle, fill='white', anchor='mm')
            y_pos += 65
            
            # Análisis detallado (wrapped text)
            self._draw_wrapped_text(draw, analisis, font_text, '#cccccc', y_pos, max_width=1700, line_spacing=38)
            y_pos += 160
            
            # Estadísticas técnicas
            draw.text((center_x, y_pos), "Datos del Análisis:", font=font_subtitle, fill='#00ff88', anchor='mm')
            y_pos += 55
            
            stats_text = [
                f"• Meses analizados: {stats['meses_con_datos']} de {stats['total_meses']}",
                f"• Valor promedio: {stats['promedio']:.3f}  |  Rango: {stats['minimo']:.3f} - {stats['maximo']:.3f}",
                f"• Tendencia: {tendencia_texto.capitalize()} ({cambio_pct:+.1f}%)  |  Comportamiento: {variabilidad.capitalize()}"
            ]
            
            for stat in stats_text:
                draw.text((center_x, y_pos), stat, font=font_text, fill='white', anchor='mm')
                y_pos += 42
            
            # Guardar frame
            frame_path = os.path.join(temp_dir, f'frame_{start_idx + i:05d}.png')
            img.save(frame_path, 'PNG')
            frames.append(frame_path)
        
        return frames
