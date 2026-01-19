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
    
    # Duraciones por escena (en segundos)
    COVER_DURATION = 3.0
    MONTHLY_MAP_DURATION = 2.5
    ANALYSIS_DURATION = 5.0
    RECOMMENDATIONS_DURATION = 5.0
    CLOSING_DURATION = 3.0
    
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
        Genera TODAS las escenas del video en orden
        """
        all_frames = []
        counter = 0
        
        # 1️⃣ PORTADA
        logger.info("📝 Generando portada...")
        cover_frames = self._generate_cover_scene(indice, frames_data, parcela_info, temp_dir, counter)
        all_frames.extend(cover_frames)
        counter += len(cover_frames)
        logger.info(f"✅ Portada: {len(cover_frames)} frames")
        
        # 2️⃣ MAPAS MENSUALES
        logger.info(f"🗺️ Generando {len(frames_data)} mapas mensuales...")
        for i, frame_data in enumerate(frames_data):
            monthly_frames = self._generate_monthly_map_scene(frame_data, indice, temp_dir, counter)
            all_frames.extend(monthly_frames)
            counter += len(monthly_frames)
        logger.info(f"✅ Mapas: {len(frames_data)} escenas")
        
        # 3️⃣ ANÁLISIS (solo si hay texto)
        if analisis_texto and analisis_texto.strip():
            logger.info("🤖 Generando análisis...")
            analysis_frames = self._generate_analysis_scene(analisis_texto, indice, temp_dir, counter)
            all_frames.extend(analysis_frames)
            counter += len(analysis_frames)
            logger.info(f"✅ Análisis: {len(analysis_frames)} frames")
        
        # 4️⃣ RECOMENDACIONES (solo si hay texto)
        if recomendaciones_texto and recomendaciones_texto.strip():
            logger.info("💡 Generando recomendaciones...")
            reco_frames = self._generate_recommendations_scene(recomendaciones_texto, indice, temp_dir, counter)
            all_frames.extend(reco_frames)
            counter += len(reco_frames)
            logger.info(f"✅ Recomendaciones: {len(reco_frames)} frames")
        
        # 5️⃣ CIERRE
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
        """
        try:
            font_header = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
            font_data = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
        except:
            font_header = font_data = ImageFont.load_default()
        
        # Header: NDVI · Mes Año
        periodo = frame_data.get('periodo_texto', '')
        header = f"{indice.upper()} · {periodo}"
        draw.text((20, 20), header, font=font_header, fill='white', anchor='lt')
        
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
