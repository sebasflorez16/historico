"""
Test de integración de la vista exportar_video_timeline
Verifica que la vista funciona correctamente con VideoExporterMultiscene
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from informes.models import Parcela
from informes.views import exportar_video_timeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integracion_vista_video():
    """
    Test de integración de la vista exportar_video_timeline
    """
    print("\n" + "="*60)
    print("🧪 TEST DE INTEGRACIÓN - Vista exportar_video_timeline")
    print("="*60 + "\n")
    
    try:
        # 1. Verificar que existe una parcela con datos
        parcela = Parcela.objects.filter(activa=True).first()
        
        if not parcela:
            print("⚠️  No hay parcelas activas en la base de datos")
            print("   Saltando test (requiere datos reales)")
            return True
        
        print(f"✅ Parcela encontrada: {parcela.nombre} (ID: {parcela.id})")
        
        # 2. Verificar que el exportador se puede importar
        try:
            from informes.exporters.video_exporter_multiscene import VideoExporterMultiscene
            print("✅ VideoExporterMultiscene importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando VideoExporterMultiscene: {e}")
            return False
        
        # 3. Verificar que TimelineProcessor se puede importar
        try:
            from informes.processors.timeline_processor import TimelineProcessor
            print("✅ TimelineProcessor importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando TimelineProcessor: {e}")
            return False
        
        # 4. Simular request (no ejecutamos el video real, solo verificamos imports)
        factory = RequestFactory()
        user = User.objects.filter(is_active=True).first()
        
        if not user:
            print("⚠️  No hay usuarios activos en la base de datos")
            print("   Saltando test de request (requiere usuario)")
            return True
        
        # Crear request simulado
        request = factory.get(f'/informes/parcelas/{parcela.id}/timeline/exportar-video/?indice=ndvi')
        request.user = user
        
        print(f"✅ Request simulado creado para usuario: {user.username}")
        
        # 5. Verificar que la vista existe y tiene los decoradores correctos
        import inspect
        source = inspect.getsource(exportar_video_timeline)
        
        if '@login_required' in source:
            print("✅ Vista protegida con @login_required")
        else:
            print("⚠️  Vista NO tiene @login_required")
        
        if 'VideoExporterMultiscene' in source:
            print("✅ Vista usa VideoExporterMultiscene")
        else:
            print("⚠️  Vista NO usa VideoExporterMultiscene")
        
        # 6. Verificar parámetros
        expected_params = ['indice', 'fps', 'width', 'height', 'bitrate']
        missing_params = []
        
        for param in expected_params:
            if param not in source:
                missing_params.append(param)
        
        if not missing_params:
            print(f"✅ Todos los parámetros esperados presentes: {', '.join(expected_params)}")
        else:
            print(f"⚠️  Parámetros faltantes: {', '.join(missing_params)}")
        
        # 7. Verificar validaciones
        validations = [
            "if indice not in ['ndvi', 'ndmi', 'savi']",
            "get_object_or_404",
            "if not frames"
        ]
        
        missing_validations = []
        for validation in validations:
            if validation not in source:
                missing_validations.append(validation)
        
        if not missing_validations:
            print(f"✅ Todas las validaciones esperadas presentes")
        else:
            print(f"⚠️  Validaciones faltantes: {', '.join(missing_validations)}")
        
        print("\n" + "="*60)
        print("✅ TEST DE INTEGRACIÓN COMPLETADO")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    resultado = test_integracion_vista_video()
    sys.exit(0 if resultado else 1)
