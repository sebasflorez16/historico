"""
Vistas de eliminación segura para parcelas e informes
Solo accesibles por superusuarios con confirmación
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging
import os

from .models import Parcela, Informe

logger = logging.getLogger(__name__)


def es_superusuario(user):
    """Verificar que el usuario es superusuario"""
    return user.is_superuser


@login_required
@user_passes_test(es_superusuario, login_url='informes:dashboard')
@require_http_methods(["POST"])
def eliminar_parcela(request, parcela_id):
    """
    Vista para eliminar una parcela.
    SOLO accesible por superusuarios.
    Requiere confirmación explícita.
    """
    try:
        # Validación de seguridad adicional
        if not request.user.is_superuser:
            logger.warning(
                f"Intento de eliminación de parcela {parcela_id} por usuario no autorizado: {request.user.username}"
            )
            messages.error(request, '⛔ No tienes permisos para eliminar parcelas.')
            return redirect('informes:lista_parcelas')
        
        # Obtener la parcela
        parcela = get_object_or_404(Parcela, id=parcela_id)
        
        # Verificar confirmación explícita
        confirmacion = request.POST.get('confirmacion', '')
        if confirmacion != parcela.nombre:
            messages.error(
                request,
                f'La confirmación no coincide con el nombre de la parcela. '
                f'Debe escribir exactamente: "{parcela.nombre}"'
            )
            return redirect('informes:detalle_parcela', parcela_id=parcela_id)
        
        # Obtener información para auditoría antes de eliminar
        nombre_parcela = parcela.nombre
        propietario = parcela.propietario
        area = parcela.area_hectareas
        num_informes = parcela.informes.count()
        num_indices = parcela.indices_mensuales.count()
        eosda_field_id = parcela.eosda_field_id
        eosda_sincronizada = parcela.eosda_sincronizada
        
        # Si la parcela está sincronizada con EOSDA, intentar eliminarla allí también
        mensaje_eosda = ""
        if eosda_sincronizada and eosda_field_id:
            try:
                from .services.eosda_api import eosda_service
                
                logger.info(f"Intentando eliminar campo en EOSDA: {eosda_field_id}")
                resultado_eosda = eosda_service.eliminar_campo_eosda(eosda_field_id)
                
                if resultado_eosda.get('exito'):
                    mensaje_eosda = f" Campo eliminado en EOSDA: {eosda_field_id}."
                    logger.info(f"✓ Campo {eosda_field_id} eliminado en EOSDA")
                else:
                    mensaje_eosda = f" ⚠️ No se pudo eliminar en EOSDA: {resultado_eosda.get('error', 'Error desconocido')}"
                    logger.warning(f"No se pudo eliminar campo en EOSDA: {resultado_eosda.get('error')}")
                    
            except Exception as e:
                mensaje_eosda = f" ⚠️ Error al intentar eliminar en EOSDA: {str(e)}"
                logger.error(f"Error eliminando campo en EOSDA: {str(e)}")
        
        # Eliminar archivos asociados si existen
        try:
            # Eliminar informes PDF asociados
            for informe in parcela.informes.all():
                if informe.archivo_pdf:
                    try:
                        if os.path.exists(informe.archivo_pdf.path):
                            os.remove(informe.archivo_pdf.path)
                            logger.info(f"Archivo PDF eliminado: {informe.archivo_pdf.path}")
                    except Exception as e:
                        logger.warning(f"Error eliminando PDF {informe.archivo_pdf.path}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error eliminando archivos asociados a parcela {parcela_id}: {str(e)}")
        
        # Eliminar la parcela (cascade eliminará informes e índices)
        parcela.delete()
        
        # Log de auditoría
        logger.warning(
            f"🗑️ PARCELA ELIMINADA por {request.user.username}: "
            f"ID={parcela_id}, Nombre='{nombre_parcela}', Propietario='{propietario}', "
            f"Área={area}ha, Informes={num_informes}, Índices={num_indices}, "
            f"EOSDA_ID={eosda_field_id if eosda_field_id else 'No sincronizada'}"
        )
        
        messages.success(
            request,
            f'✅ Parcela "{nombre_parcela}" eliminada exitosamente. '
            f'Se eliminaron {num_informes} informes y {num_indices} registros de índices asociados.'
            f'{mensaje_eosda}'
        )
        
        return redirect('informes:lista_parcelas')
        
    except Exception as e:
        logger.error(f"Error eliminando parcela {parcela_id}: {str(e)}")
        logger.exception(e)
        messages.error(request, f'❌ Error eliminando la parcela: {str(e)}')
        return redirect('informes:lista_parcelas')


@login_required
@user_passes_test(es_superusuario, login_url='informes:dashboard')
@require_http_methods(["POST"])
def eliminar_informe(request, informe_id):
    """
    Vista para eliminar un informe.
    SOLO accesible por superusuarios.
    Requiere confirmación explícita.
    """
    try:
        # Validación de seguridad adicional
        if not request.user.is_superuser:
            logger.warning(
                f"Intento de eliminación de informe {informe_id} por usuario no autorizado: {request.user.username}"
            )
            messages.error(request, '⛔ No tienes permisos para eliminar informes.')
            return redirect('informes:lista_informes')
        
        # Obtener el informe
        informe = get_object_or_404(Informe, id=informe_id)
        
        # Verificar confirmación explícita
        confirmacion = request.POST.get('confirmacion_informe', '')
        if confirmacion.lower() != 'eliminar':
            messages.error(
                request,
                'La confirmación no es correcta. Debe escribir exactamente: "eliminar"'
            )
            return redirect('informes:detalle_informe', informe_id=informe_id)
        
        # Obtener información para auditoría
        titulo_informe = informe.titulo
        parcela_nombre = informe.parcela.nombre
        parcela_id = informe.parcela.id
        fecha_generacion = informe.fecha_generacion
        
        # Eliminar archivo PDF si existe
        if informe.archivo_pdf:
            try:
                if os.path.exists(informe.archivo_pdf.path):
                    os.remove(informe.archivo_pdf.path)
                    logger.info(f"Archivo PDF eliminado: {informe.archivo_pdf.path}")
            except Exception as e:
                logger.warning(f"Error eliminando archivo PDF: {str(e)}")
        
        # Eliminar el informe
        informe.delete()
        
        # Log de auditoría
        logger.warning(
            f"🗑️ INFORME ELIMINADO por {request.user.username}: "
            f"ID={informe_id}, Título='{titulo_informe}', Parcela='{parcela_nombre}', "
            f"Fecha={fecha_generacion}"
        )
        
        messages.success(
            request,
            f'✅ Informe "{titulo_informe}" eliminado exitosamente.'
        )
        
        # Redirigir a la lista de informes o detalle de la parcela
        redirect_to = request.POST.get('redirect_to', 'lista_informes')
        if redirect_to == 'detalle_parcela':
            return redirect('informes:detalle_parcela', parcela_id=parcela_id)
        else:
            return redirect('informes:lista_informes')
        
    except Exception as e:
        logger.error(f"Error eliminando informe {informe_id}: {str(e)}")
        logger.exception(e)
        messages.error(request, f'❌ Error eliminando el informe: {str(e)}')
        return redirect('informes:lista_informes')
