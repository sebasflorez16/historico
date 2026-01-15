"""
Comando de gestión Django para limpiar videos temporales del timeline

Uso:
    python manage.py cleanup_timeline_videos
    python manage.py cleanup_timeline_videos --days 7
    python manage.py cleanup_timeline_videos --dry-run
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Limpia videos temporales del timeline más antiguos que N días'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Días de antigüedad para eliminar videos (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin eliminar archivos'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('🧹 Limpieza de Videos Temporales del Timeline'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        
        # Directorio de videos
        videos_dir = Path(settings.MEDIA_ROOT) / 'timeline_videos'
        
        if not videos_dir.exists():
            self.stdout.write(self.style.WARNING('⚠️  Directorio de videos no existe'))
            return
        
        self.stdout.write(f'📁 Directorio: {videos_dir}')
        self.stdout.write(f'📅 Eliminando videos > {days} días')
        self.stdout.write(f'🔧 Modo: {"DRY RUN (simulación)" if dry_run else "PRODUCCIÓN"}')
        self.stdout.write('')
        
        # Calcular fecha límite
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        # Buscar archivos
        video_files = list(videos_dir.glob('*.mp4'))
        
        if not video_files:
            self.stdout.write(self.style.WARNING('ℹ️  No hay videos para revisar'))
            return
        
        self.stdout.write(f'🔍 Encontrados {len(video_files)} videos')
        self.stdout.write('')
        
        # Procesar archivos
        deleted_count = 0
        deleted_size = 0
        kept_count = 0
        
        for video_file in video_files:
            try:
                # Obtener información del archivo
                file_mtime = video_file.stat().st_mtime
                file_size = video_file.stat().st_size
                file_date = datetime.fromtimestamp(file_mtime)
                age_days = (datetime.now() - file_date).days
                
                # Verificar si debe eliminarse
                if file_mtime < cutoff_timestamp:
                    size_mb = file_size / (1024 * 1024)
                    
                    if dry_run:
                        self.stdout.write(
                            f'  [DRY RUN] {video_file.name} '
                            f'({size_mb:.2f} MB, {age_days} días)'
                        )
                    else:
                        video_file.unlink()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ Eliminado: {video_file.name} '
                                f'({size_mb:.2f} MB, {age_days} días)'
                            )
                        )
                    
                    deleted_count += 1
                    deleted_size += file_size
                else:
                    kept_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error con {video_file.name}: {e}')
                )
        
        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('📊 Resumen'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        if dry_run:
            self.stdout.write(f'🗑️  Videos a eliminar: {deleted_count}')
            self.stdout.write(f'💾 Espacio a liberar: {deleted_size / (1024 * 1024):.2f} MB')
        else:
            self.stdout.write(f'🗑️  Videos eliminados: {deleted_count}')
            self.stdout.write(f'💾 Espacio liberado: {deleted_size / (1024 * 1024):.2f} MB')
        
        self.stdout.write(f'📁 Videos conservados: {kept_count}')
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('ℹ️  Modo DRY RUN: No se eliminaron archivos reales')
            )
            self.stdout.write(
                self.style.WARNING('   Ejecuta sin --dry-run para eliminar')
            )
        else:
            self.stdout.write(self.style.SUCCESS('✅ Limpieza completada'))

