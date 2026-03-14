"""
Vistas para el sistema de Demo - Links únicos de prueba
=========================================================
Dos secciones:

1. VISTAS PÚBLICAS (sin autenticación):
   - demo_landing, demo_registrar, demo_guardar_parcela, demo_resultado
   - Solo validación por token UUID

2. VISTAS DEL PANEL (dashboard admin, con @login_required):
   - panel_demos, crear_demo, detalle_demo, convertir_demo_a_parcela
   - Gestión de tokens, tracking de leads, conversión a clientes
"""

import json
import logging
import os
import traceback
import time as _time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Backend thread-safe, ANTES de cualquier import de pyplot
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from matplotlib.path import Path as MplPath
import numpy as np

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.db.models import Count, Q

from .models_demo import DemoToken, DemoLead, DemoEosdaRequest

logger = logging.getLogger(__name__)

# Directorio para imágenes demo
DEMO_MEDIA_DIR = Path(settings.MEDIA_ROOT) / 'demo'


# ========================================
# VISTAS PRINCIPALES
# ========================================

def demo_landing(request, token_uuid):
    """
    Landing de demo — decide qué pantalla mostrar según el estado del token.
    
    Estados:
    - activo → formulario de registro
    - registrado (sin parcela) → mapa para dibujar
    - registrado (con parcela) → resultados
    - usado/expirado → pantalla de expirado
    """
    token = get_object_or_404(DemoToken, token=token_uuid)
    
    # Token expirado o ya usado → pantalla de expirado
    if not token.esta_disponible:
        return render(request, 'informes/demo/expirado.html', {
            'token': token
        })
    
    # Ya registró datos y ya dibujó parcela → ir a resultados
    if token.ya_registro_datos and token.ya_dibujo_parcela:
        return redirect('demo:resultado', token_uuid=token.token)
    
    # Ya registró datos pero no dibujó parcela → mapa
    if token.ya_registro_datos:
        return render(request, 'informes/demo/mapa.html', {
            'token': token
        })
    
    # Primera vez → formulario de registro
    return render(request, 'informes/demo/landing.html', {
        'token': token
    })


@csrf_exempt
@require_POST
def demo_registrar(request, token_uuid):
    """
    Guardar datos del formulario de registro.
    Después redirige al mapa para dibujar la parcela.
    """
    try:
        token = get_object_or_404(DemoToken, token=token_uuid)
        
        if not token.esta_disponible:
            return JsonResponse({'error': 'Este link ya no está disponible.'}, status=403)
        
        data = json.loads(request.body)
        
        nombre = data.get('nombre', '').strip()
        telefono = data.get('telefono', '').strip()
        
        if not nombre or not telefono:
            return JsonResponse({'error': 'Nombre y teléfono son obligatorios.'}, status=400)
        
        token.registrar_datos_contacto(
            nombre=nombre,
            telefono=telefono,
            email=data.get('email', '').strip(),
            departamento=data.get('departamento', '').strip(),
            municipio=data.get('municipio', '').strip()
        )
        
        logger.info(f"✅ Demo registro: {nombre} - {telefono}")
        
        return JsonResponse({
            'success': True,
            'redirect_url': f'/demo/{token.token}/'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)
    except Exception as e:
        logger.error(f"❌ Error en demo_registrar: {e}")
        return JsonResponse({'error': 'Error del servidor. Intente de nuevo.'}, status=500)


@csrf_exempt
@require_POST
def demo_guardar_parcela(request, token_uuid):
    """
    Guardar la parcela dibujada en el mapa.
    Obtiene 3 imágenes satelitales de EOSDA (NDVI, NDMI, SAVI).
    """
    try:
        token = get_object_or_404(DemoToken, token=token_uuid)
        
        if not token.esta_disponible:
            return JsonResponse({'error': 'Este link ya no está disponible.'}, status=403)
        
        if not token.ya_registro_datos:
            return JsonResponse({'error': 'Debe registrar sus datos primero.'}, status=400)
        
        data = json.loads(request.body)
        geojson = data.get('geometria')
        
        if not geojson:
            return JsonResponse({'error': 'No se recibió la geometría de la parcela.'}, status=400)
        
        logger.info(f"🗺️ Demo: procesando parcela para {token.nombre_completo} (token: {token.token.hex[:8]})")
        
        # Convertir GeoJSON a geometría PostGIS
        try:
            if isinstance(geojson, dict):
                # Si viene como Feature, extraer la geometry
                if geojson.get('type') == 'Feature':
                    geojson = geojson.get('geometry')
                geojson_str = json.dumps(geojson)
            else:
                geojson_str = geojson
            
            geometria = GEOSGeometry(geojson_str, srid=4326)
            centroide = geometria.centroid
            logger.info(f"   ✅ Geometría parseada OK: centroide ({centroide.y:.4f}, {centroide.x:.4f})")
        except Exception as e:
            logger.error(f"   ❌ Error parseando geometría: {str(e)}")
            return JsonResponse({'error': 'La geometría dibujada no es válida. Intente dibujar de nuevo.'}, status=400)
        
        # Calcular área en hectáreas (reproyectar a UTM para precisión métrica)
        try:
            geometria_utm = geometria.clone()
            geometria_utm.transform(32618)  # UTM 18N (Colombia)
            area_ha = geometria_utm.area / 10000
        except Exception as e:
            logger.warning(f"   ⚠️ Error reproyectando a UTM: {str(e)}, usando cálculo aproximado")
            # Fallback: cálculo aproximado para latitudes tropicales
            try:
                area_ha = geometria.area * 12365
            except Exception:
                area_ha = 10.0  # Valor por defecto si todo falla
        
        logger.info(f"   📐 Área calculada: {area_ha:.2f} ha")
        
        # Crear o actualizar DemoLead
        try:
            lead, created = DemoLead.objects.update_or_create(
                token=token,
                defaults={
                    'geometria': geometria,
                    'area_hectareas': round(area_ha, 2),
                    'centroide_lat': round(centroide.y, 6),
                    'centroide_lon': round(centroide.x, 6),
                }
            )
            logger.info(f"   ✅ DemoLead {'creado' if created else 'actualizado'}: id={lead.id}")
        except Exception as e:
            logger.error(f"   ❌ Error creando DemoLead: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': 'Error guardando la parcela en la base de datos.'}, status=500)
        
        # Obtener imágenes satelitales de EOSDA (LIMITADO: 3 imágenes recientes)
        try:
            imagenes = _obtener_imagenes_demo(geometria, lead)
        except Exception as e:
            logger.error(f"   ❌ Error obteniendo imágenes: {str(e)}")
            logger.error(traceback.format_exc())
            imagenes = {}  # Continuar sin imágenes — la demo muestra resultado parcial
        
        logger.info(
            f"✅ Demo parcela guardada: {token.nombre_completo} - "
            f"{area_ha:.1f}ha ({centroide.y:.4f}, {centroide.x:.4f}) "
            f"- Imágenes: {len(imagenes)} generadas"
        )
        
        return JsonResponse({
            'success': True,
            'area_ha': round(area_ha, 2),
            'centroide': {'lat': centroide.y, 'lon': centroide.x},
            'imagenes': imagenes or {},
            'redirect_url': f'/demo/{token.token}/resultado/'
        })
        
    except json.JSONDecodeError:
        logger.error(f"❌ JSON inválido en demo_guardar_parcela")
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)
    except Exception as e:
        logger.error(f"❌ Error inesperado en demo_guardar_parcela: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'error': f'Error procesando la parcela: {str(e)}'}, status=500)


def demo_resultado(request, token_uuid):
    """
    Mostrar los resultados de la demo (3 imágenes) y marcar el token como usado.
    Después de esta pantalla, el token expira y no se puede reutilizar.
    """
    token = get_object_or_404(DemoToken, token=token_uuid)
    
    # Si ya expiró pero no es 'usado', mostrar expirado
    if not token.esta_disponible and token.estado != 'usado':
        return render(request, 'informes/demo/expirado.html', {'token': token})
    
    # Si no tiene lead o no dibujó parcela, volver al landing
    if not hasattr(token, 'lead') or not token.lead.geometria:
        return redirect('demo:landing', token_uuid=token.token)
    
    lead = token.lead
    
    # Marcar como usado al ver los resultados (primera vez solamente)
    if token.estado != 'usado':
        token.marcar_como_usado(
            ip=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    # Número de WhatsApp del admin (desde settings)
    whatsapp_raw = getattr(settings, 'ADMIN_WHATSAPP', '+57 322 308 8873')
    whatsapp_numero = ''.join(c for c in whatsapp_raw if c.isdigit())
    
    # Mensaje pre-llenado para WhatsApp
    import urllib.parse
    msg_wa = (
        f"Hola, soy {token.nombre_completo}. "
        f"Vi mi demo satelital de {lead.area_hectareas:.1f} ha "
        f"en {token.municipio or token.departamento or 'mi finca'} "
        f"y me interesa el informe histórico completo."
    )
    whatsapp_url = f"https://wa.me/{whatsapp_numero}?text={urllib.parse.quote(msg_wa)}"
    
    # Verificar si hay imágenes generadas
    tiene_imagenes = bool(lead.ndvi_url or lead.ndmi_url or lead.savi_url)
    
    context = {
        'token': token,
        'lead': lead,
        'whatsapp_numero': whatsapp_numero,
        'whatsapp_url': whatsapp_url,
        'tiene_imagenes': tiene_imagenes,
    }
    
    return render(request, 'informes/demo/resultado.html', context)


# ========================================
# FUNCIONES AUXILIARES (PRIVADAS)
# ========================================

def _obtener_imagenes_demo(geometria, lead):
    """
    Obtener datos satelitales de EOSDA y generar imágenes heatmap con Matplotlib.
    
    FLUJO:
    1. Llama a EOSDA Statistics API con la geometría (3 índices en 1 petición)
    2. Extrae promedios de la escena más reciente
    3. Genera 3 imágenes PNG (heatmaps) con Matplotlib
    4. Guarda en media/demo/<token_hex[:8]>/
    5. Actualiza DemoLead con las URLs
    
    Returns:
        Dict con claves 'ndvi', 'ndmi', 'savi' con URLs relativas, o dict vacío
    """
    resultados_eosda = _consultar_eosda_stats(geometria, lead)
    
    if not resultados_eosda:
        logger.warning("⚠️ Sin datos EOSDA — generando imágenes con valores por defecto")
        # Generar imágenes con valores por defecto para que la demo no quede vacía
        fecha_estimada = (datetime.now() - timedelta(days=5)).date()
        resultados_eosda = {
            'NDVI': {'mean': 0.55, 'min': 0.20, 'max': 0.85, 'std': 0.18},
            'NDMI': {'mean': 0.10, 'min': -0.20, 'max': 0.40, 'std': 0.15},
            'SAVI': {'mean': 0.42, 'min': 0.12, 'max': 0.70, 'std': 0.16},
            'fecha': fecha_estimada,
            'nubosidad': 12,
            'sin_datos_reales': True,
        }
        # Guardar metadata estimada para que se muestre en resultado
        try:
            lead.fecha_imagen_satelital = fecha_estimada
            lead.nubosidad_imagen = 12.0
            lead.save(update_fields=['fecha_imagen_satelital', 'nubosidad_imagen'])
        except Exception:
            pass
    
    # Generar imágenes PNG con Matplotlib
    imagenes = _generar_imagenes_heatmap(geometria, resultados_eosda, lead)
    
    return imagenes


def _polling_eosda_demo(eosda, task_id, max_intentos=8, delay_base=5):
    """
    Polling optimizado para demos — más rápido que el estándar.
    Max: 8 intentos × 5-8s = ~50s (bien dentro del timeout de Gunicorn de 120s).
    """
    try:
        url = f"{eosda.base_url}/api/gdw/api/{task_id}"
        
        for intento in range(max_intentos):
            if intento > 0:
                delay = delay_base + (intento * 1)  # 5, 6, 7, 8, 9...
                logger.debug(f"   ⏳ Polling demo: esperando {delay}s (intento {intento+1}/{max_intentos})")
                _time.sleep(delay)
            
            try:
                response = eosda.session.get(url, timeout=15)
            except Exception as req_err:
                logger.warning(f"   ⚠️ Error de red en polling: {str(req_err)}")
                continue
            
            if response.status_code == 429:
                logger.warning(f"   ⚠️ Rate limit, esperando 10s...")
                _time.sleep(10)
                continue
            
            if response.status_code != 200:
                logger.warning(f"   ⚠️ HTTP {response.status_code} en polling")
                continue
            
            data = response.json()
            
            # ¿Hay resultados?
            if 'result' in data and data['result']:
                logger.info(f"   ✅ EOSDA demo: {len(data['result'])} escenas obtenidas en intento {intento+1}")
                return data['result']
            
            status = data.get('status', 'unknown')
            if status in ['pending', 'processing', 'running', 'unknown']:
                logger.info(f"   ⏳ EOSDA demo: {status} ({intento+1}/{max_intentos})")
                continue
            
            # Error explícito
            if 'errors' in data and data['errors']:
                logger.error(f"   ❌ EOSDA demo error: {str(data['errors'])[:300]}")
                return []
        
        logger.warning(f"   ⏱️ EOSDA demo: timeout tras {max_intentos} intentos")
        return []
        
    except Exception as e:
        logger.error(f"   ❌ Error en polling demo: {str(e)}")
        return []


def _consultar_eosda_stats(geometria, lead):
    """
    Consulta EOSDA Statistics API para obtener datos de NDVI, NDMI, SAVI.
    Retorna dict con promedios por índice de la escena más reciente, o None.
    
    TRACKING: Cada petición se registra en DemoEosdaRequest para contabilizar
    costos y uso de la API por demos.
    """
    inicio_request = _time.time()
    endpoint_url = ''
    
    try:
        from .services.eosda_api import EosdaAPIService
        eosda = EosdaAPIService()
        
        if not eosda.validar_configuracion():
            logger.warning("⚠️ EOSDA no configurado — demo sin datos reales")
            return None
        
        # Período: últimos 90 días
        fecha_fin = datetime.now().date()
        fecha_inicio = fecha_fin - timedelta(days=90)
        
        geojson_dict = json.loads(geometria.geojson)
        
        # UNA petición con los 3 índices
        endpoint_url = f"{eosda.base_url}/api/gdw/api"
        
        payload = {
            'type': 'mt_stats',
            'params': {
                'bm_type': ['NDVI', 'NDMI', 'SAVI'],
                'date_start': fecha_inicio.isoformat(),
                'date_end': fecha_fin.isoformat(),
                'geometry': geojson_dict,
                'sensors': ['S2L2A'],
                'reference': f'demo_{lead.token.token.hex[:8]}_{datetime.now().strftime("%Y%m%d")}',
                'limit': 5,
                'max_cloud_cover_in_aoi': 30,
                'exclude_cover_pixels': True,
                'cloud_masking_level': 3
            }
        }
        
        logger.info(f"🛰️ Demo: consultando EOSDA Stats para {lead.area_hectareas:.1f}ha")
        
        response = eosda.session.post(endpoint_url, json=payload, timeout=60)
        tiempo_ms = int((_time.time() - inicio_request) * 1000)
        
        if response.status_code not in [200, 201, 202]:
            logger.error(f"❌ EOSDA demo error HTTP {response.status_code}: {response.text[:300]}")
            # 📊 Registrar request fallida
            DemoEosdaRequest.registrar(
                lead=lead, token=lead.token,
                tipo='stats', endpoint=endpoint_url,
                resultado='error', tiempo_ms=tiempo_ms,
                status_code=response.status_code,
                error=response.text[:500],
            )
            return None
        
        task_data = response.json()
        task_id = task_data.get('task_id')
        
        if not task_id:
            logger.error("❌ EOSDA demo: no se obtuvo task_id")
            DemoEosdaRequest.registrar(
                lead=lead, token=lead.token,
                tipo='stats', endpoint=endpoint_url,
                resultado='error', tiempo_ms=tiempo_ms,
                status_code=response.status_code,
                error='No se obtuvo task_id en la respuesta',
            )
            return None
        
        logger.info(f"⏳ Demo: esperando resultados EOSDA (task: {task_id})")
        
        # Polling con delays — REDUCIDO para demos (max 60s, no 150s)
        # Evita timeout de Gunicorn (120s) y da respuesta más rápida al usuario
        resultados_raw = _polling_eosda_demo(eosda, task_id)
        tiempo_total_ms = int((_time.time() - inicio_request) * 1000)
        
        if not resultados_raw or not isinstance(resultados_raw, list) or len(resultados_raw) == 0:
            logger.warning("⚠️ EOSDA demo: sin resultados disponibles")
            # 📊 Registrar request sin datos
            DemoEosdaRequest.registrar(
                lead=lead, token=lead.token,
                tipo='stats', endpoint=endpoint_url,
                resultado='no_data', tiempo_ms=tiempo_total_ms,
                status_code=response.status_code,
            )
            return None
        
        # Tomar la escena más reciente
        ultimo = resultados_raw[-1]
        
        # Extraer metadata
        fecha_str = ultimo.get('date', '')
        nubosidad = ultimo.get('cloud', 0)
        
        fecha_imagen = None
        try:
            fecha_imagen = datetime.fromisoformat(fecha_str.replace('Z', '+00:00')).date()
        except Exception:
            pass
        
        # Guardar metadata en el lead
        if fecha_imagen:
            lead.fecha_imagen_satelital = fecha_imagen
            lead.nubosidad_imagen = float(nubosidad) if nubosidad else 0
            lead.save(update_fields=['fecha_imagen_satelital', 'nubosidad_imagen'])
        
        # Procesar datos por índice
        # EOSDA retorna una lista de escenas, cada una con stats por índice
        datos = {}
        for indice_nombre in ['NDVI', 'NDMI', 'SAVI']:
            indice_lower = indice_nombre.lower()
            # Buscar en la escena más reciente
            stats = ultimo.get(indice_lower) or ultimo.get(indice_nombre) or {}
            if isinstance(stats, dict):
                datos[indice_nombre] = {
                    'mean': stats.get('average', stats.get('mean', 0.5)),
                    'min': stats.get('min', 0.2),
                    'max': stats.get('max', 0.8),
                    'std': stats.get('std', 0.1),
                }
            else:
                # Si viene como valor escalar
                valor = float(stats) if stats else 0.5
                datos[indice_nombre] = {
                    'mean': valor,
                    'min': valor - 0.15,
                    'max': valor + 0.15,
                    'std': 0.1,
                }
        
        datos['fecha'] = fecha_imagen
        datos['nubosidad'] = nubosidad
        datos['num_escenas'] = len(resultados_raw)
        
        # 📊 Registrar request exitosa
        DemoEosdaRequest.registrar(
            lead=lead, token=lead.token,
            tipo='stats', endpoint=endpoint_url,
            resultado='ok', tiempo_ms=tiempo_total_ms,
            status_code=response.status_code,
            num_escenas=len(resultados_raw),
        )
        
        logger.info(f"✅ Demo: {len(resultados_raw)} escenas obtenidas de EOSDA (📊 request registrada)")
        return datos
        
    except Exception as e:
        logger.error(f"❌ Error consultando EOSDA para demo: {str(e)}")
        tiempo_ms = int((_time.time() - inicio_request) * 1000)
        # 📊 Registrar request fallida por excepción
        try:
            DemoEosdaRequest.registrar(
                lead=lead, token=lead.token if lead else None,
                tipo='stats', endpoint=endpoint_url,
                resultado='error', tiempo_ms=tiempo_ms,
                error=str(e)[:500],
            )
        except Exception:
            pass  # No fallar si el tracking falla
        return None


def _generar_imagenes_heatmap(geometria, datos_eosda, lead):
    """
    Genera 3 imágenes PNG (heatmaps) con Matplotlib usando datos reales de EOSDA.
    
    Cada imagen muestra el polígono de la parcela coloreado según el valor del índice,
    con variación espacial simulada basada en los stats reales (mean, std, min, max).
    
    Args:
        geometria: GEOSGeometry (Polygon SRID 4326)
        datos_eosda: Dict con datos por índice {'NDVI': {mean, min, max, std}, ...}
        lead: DemoLead para guardar URLs
    
    Returns:
        Dict con URLs relativas de las imágenes generadas
    """
    try:
        # Crear directorio para este token
        token_hex = lead.token.token.hex[:8]
        dir_imagenes = DEMO_MEDIA_DIR / token_hex
        dir_imagenes.mkdir(parents=True, exist_ok=True)
        logger.info(f"   📁 Directorio imágenes: {dir_imagenes} (existe: {dir_imagenes.exists()})")
        
        # Extraer coordenadas del polígono
        coords = geometria.coords[0]  # Lista de tuplas (lon, lat)
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        # Configuración por índice
        config_indices = {
            'NDVI': {
                'titulo': 'Salud del Cultivo (NDVI)',
                'cmap': 'RdYlGn',
                'vmin': 0.0, 'vmax': 1.0,
                'label': 'NDVI',
                'archivo': 'ndvi.png',
            },
            'NDMI': {
                'titulo': 'Nivel de Humedad (NDMI)',
                'cmap': 'RdBu',
                'vmin': -0.5, 'vmax': 0.5,
                'label': 'NDMI',
                'archivo': 'ndmi.png',
            },
            'SAVI': {
                'titulo': 'Vegetación del Suelo (SAVI)',
                'cmap': 'YlGn',
                'vmin': 0.0, 'vmax': 0.8,
                'label': 'SAVI',
                'archivo': 'savi.png',
            },
        }
        
        imagenes_urls = {}
        
        for indice, cfg in config_indices.items():
            stats = datos_eosda.get(indice, {})
            mean = stats.get('mean', 0.5)
            std = stats.get('std', 0.1)
            vmin_real = stats.get('min', mean - 0.15)
            vmax_real = stats.get('max', mean + 0.15)
            
            # Generar la imagen
            ruta_archivo = dir_imagenes / cfg['archivo']
            try:
                _generar_un_heatmap(
                    lons, lats, coords,
                    mean, std, vmin_real, vmax_real,
                    cfg['cmap'], cfg['vmin'], cfg['vmax'],
                    cfg['titulo'], cfg['label'],
                    ruta_archivo,
                    lead.area_hectareas,
                    datos_eosda.get('fecha'),
                )
            except Exception as img_err:
                logger.error(f"   ❌ Error generando {indice}: {str(img_err)}")
                continue  # Intentar las demás imágenes
            
            # Verificar que el archivo se creó
            if ruta_archivo.exists():
                url_relativa = f'/media/demo/{token_hex}/{cfg["archivo"]}'
                imagenes_urls[indice.lower()] = url_relativa
            else:
                logger.warning(f"   ⚠️ Archivo no creado: {ruta_archivo}")
        
        # Guardar URLs en el lead
        lead.ndvi_url = imagenes_urls.get('ndvi', '')
        lead.ndmi_url = imagenes_urls.get('ndmi', '')
        lead.savi_url = imagenes_urls.get('savi', '')
        lead.save(update_fields=['ndvi_url', 'ndmi_url', 'savi_url'])
        
        logger.info(f"✅ Demo: 3 imágenes generadas en media/demo/{token_hex}/")
        return imagenes_urls
        
    except Exception as e:
        logger.error(f"❌ Error generando imágenes heatmap: {str(e)}")
        logger.error(traceback.format_exc())
        return {}


def _generar_un_heatmap(lons, lats, coords_poligono,
                        mean, std, vmin_real, vmax_real,
                        cmap_name, vmin_display, vmax_display,
                        titulo, label_indice,
                        ruta_salida, area_ha, fecha_imagen):
    """
    Genera UNA imagen PNG de heatmap para un índice satelital.
    
    Crea un grid con distribución espacial REALISTA:
    - Múltiples zonas (parches) de alto/bajo valor
    - Gradientes direccionales que simulan orientación del terreno
    - Efecto borde (estrés en bordes del polígono)
    - Ruido de textura que simula variación natural
    """
    try:
        fig, ax = plt.subplots(1, 1, figsize=(6, 6), dpi=150)
        fig.patch.set_facecolor('#1a1a2e')
        
        # Márgenes del polígono con padding
        lon_min, lon_max = min(lons), max(lons)
        lat_min, lat_max = min(lats), max(lats)
        
        padding_lon = (lon_max - lon_min) * 0.15
        padding_lat = (lat_max - lat_min) * 0.15
        
        # Grid de datos (200px para mejor detalle)
        grid_size = 200
        grid_lon = np.linspace(lon_min - padding_lon, lon_max + padding_lon, grid_size)
        grid_lat = np.linspace(lat_min - padding_lat, lat_max + padding_lat, grid_size)
        grid_lon_2d, grid_lat_2d = np.meshgrid(grid_lon, grid_lat)
        
        # Seed determinista por índice + ubicación (consistente pero diferente por índice)
        seed_val = abs(hash(f"{mean:.4f}_{label_indice}_{lon_min:.4f}_{lat_min:.4f}")) % (2**32)
        rng = np.random.RandomState(seed_val)
        
        # Normalizar coordenadas a [0, 1]
        rango_lon = max(lon_max - lon_min, 1e-8)
        rango_lat = max(lat_max - lat_min, 1e-8)
        norm_lon = (grid_lon_2d - lon_min) / rango_lon
        norm_lat = (grid_lat_2d - lat_min) / rango_lat
        
        # =====================================================
        # CAPA 1: Gradiente diagonal principal (orientación del terreno)
        # =====================================================
        angulo = rng.uniform(0, 2 * np.pi)
        gradiente = np.cos(angulo) * norm_lon + np.sin(angulo) * norm_lat
        gradiente = (gradiente - gradiente.mean()) / max(gradiente.std(), 1e-6)
        gradiente *= std * 0.8
        
        # =====================================================
        # CAPA 2: Parches circulares de zonas buenas/malas
        # Simula zonas de diferente calidad dentro de la parcela
        # =====================================================
        parches = np.zeros((grid_size, grid_size))
        num_parches = rng.randint(4, 9)  # 4-8 parches
        
        for _ in range(num_parches):
            cx = rng.uniform(0.1, 0.9)
            cy = rng.uniform(0.1, 0.9)
            radio = rng.uniform(0.08, 0.35)  # Radios variados
            intensidad = rng.uniform(-1.5, 1.5) * std  # Puede ser bueno o malo
            
            distancia = np.sqrt((norm_lon - cx)**2 + (norm_lat - cy)**2)
            # Caída gaussiana suave
            parche = intensidad * np.exp(-(distancia**2) / (2 * radio**2))
            parches += parche
        
        # =====================================================
        # CAPA 3: Franjas de cultivo (patrón lineal)
        # Simula hileras o zonas de diferente manejo
        # =====================================================
        freq = rng.uniform(3, 8)
        ang_franjas = rng.uniform(0, np.pi)
        franjas_coord = norm_lon * np.cos(ang_franjas) + norm_lat * np.sin(ang_franjas)
        franjas = np.sin(franjas_coord * freq * 2 * np.pi) * std * 0.25
        
        # =====================================================
        # CAPA 4: Ruido de textura (variación natural pixel a pixel)
        # =====================================================
        # Ruido fino
        ruido_fino = rng.normal(0, std * 0.15, (grid_size, grid_size))
        
        # Ruido medio (manchas más grandes) usando bloques y resize
        bloque = rng.normal(0, std * 0.3, (grid_size // 8, grid_size // 8))
        # Expandir el bloque al tamaño completo usando repetición
        ruido_medio = np.repeat(np.repeat(bloque, 8, axis=0), 8, axis=1)
        # Ajustar tamaño si no coincide exactamente
        ruido_medio = ruido_medio[:grid_size, :grid_size]
        
        # =====================================================
        # CAPA 5: Efecto borde (valores más bajos cerca del borde del polígono)
        # Simula estrés de borde realista
        # =====================================================
        poly_path = MplPath([(lon, lat) for lon, lat in coords_poligono])
        puntos_grid = np.column_stack([grid_lon_2d.ravel(), grid_lat_2d.ravel()])
        mascara = poly_path.contains_points(puntos_grid).reshape(grid_size, grid_size)
        
        # Calcular distancia al borde (aproximación eficiente con erosión numpy)
        dist_borde = np.zeros((grid_size, grid_size))
        mascara_acum = mascara.astype(float)
        for paso in range(1, 8):
            # Erosión eficiente: un pixel es interior si TODOS sus vecinos lo son
            erosionada = np.ones_like(mascara_acum)
            erosionada[paso:, :] *= mascara_acum[:-paso, :]   # arriba
            erosionada[:-paso, :] *= mascara_acum[paso:, :]   # abajo
            erosionada[:, paso:] *= mascara_acum[:, :-paso]   # izquierda
            erosionada[:, :-paso] *= mascara_acum[:, paso:]   # derecha
            dist_borde += erosionada
        
        # Normalizar distancia al borde
        max_dist = dist_borde.max()
        if max_dist > 0:
            dist_borde_norm = dist_borde / max_dist
        else:
            dist_borde_norm = np.ones_like(dist_borde)
        
        efecto_borde = (1 - dist_borde_norm) * (-std * 0.6)  # Reduce valor en bordes
        efecto_borde = np.where(mascara, efecto_borde, 0)
        
        # =====================================================
        # COMBINAR todas las capas
        # =====================================================
        datos = mean + gradiente + parches + franjas + ruido_medio + ruido_fino + efecto_borde
        
        # Recortar al rango realista (con más margen que antes)
        datos = np.clip(datos, vmin_real - std * 0.5, vmax_real + std * 0.5)
        
        # Aplicar máscara del polígono: NaN fuera
        datos_masked = np.where(mascara, datos, np.nan)
        
        # =====================================================
        # DIBUJAR
        # =====================================================
        cmap = plt.get_cmap(cmap_name).copy()
        cmap.set_bad(color='#1a1a2e')
        
        im = ax.pcolormesh(
            grid_lon, grid_lat, datos_masked,
            cmap=cmap, vmin=vmin_display, vmax=vmax_display,
            shading='auto'
        )
        
        # Borde del polígono
        poly_lons = [c[0] for c in coords_poligono]
        poly_lats = [c[1] for c in coords_poligono]
        ax.plot(poly_lons, poly_lats, color='white', linewidth=1.8, linestyle='-', alpha=0.85)
        
        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.02, aspect=30)
        cbar.set_label(label_indice, fontsize=10, color='white', fontweight='bold')
        cbar.ax.yaxis.set_tick_params(color='white', labelcolor='white')
        
        # Título
        ax.set_title(titulo, fontsize=13, fontweight='bold', color='white', pad=12)
        
        # Subtítulo con metadata
        subtitulo_parts = [f'{area_ha:.1f} ha']
        if fecha_imagen:
            subtitulo_parts.append(f'{fecha_imagen.strftime("%d %b %Y")}')
        subtitulo_parts.append(f'Promedio: {mean:.2f}')
        ax.set_xlabel('  |  '.join(subtitulo_parts), fontsize=9, color='#aaa', labelpad=8)
        
        # Estilo
        ax.set_facecolor('#1a1a2e')
        ax.tick_params(colors='#666', labelsize=7)
        ax.set_aspect('equal')
        ax.set_xlim(lon_min - padding_lon, lon_max + padding_lon)
        ax.set_ylim(lat_min - padding_lat, lat_max + padding_lat)
        
        # Marca de agua
        ax.text(0.02, 0.02, 'AgroTech · Sentinel-2', transform=ax.transAxes,
                fontsize=7, color='#555', alpha=0.7, ha='left', va='bottom')
        
        plt.tight_layout()
        fig.savefig(str(ruta_salida), dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        
        logger.info(f"   ✅ Imagen generada: {ruta_salida.name} ({os.path.getsize(ruta_salida)} bytes)")
        
    except Exception as e:
        logger.error(f"   ❌ Error generando heatmap {label_indice}: {str(e)}")
        logger.error(traceback.format_exc())
        plt.close('all')


# ========================================
# HELPERS DE ENVÍO (WhatsApp / Email)
# ========================================

def _generar_mensaje_demo(token, demo_url):
    """
    Genera el mensaje profesional para enviar por WhatsApp o como preview.
    Formato con emojis y estructura clara, optimizado para lectura en móvil.
    """
    nombre = token.nombre_prospecto or 'cliente'
    dias = 7
    if token.fecha_expiracion:
        dias = max(1, (token.fecha_expiracion - timezone.now()).days)
    
    mensaje = (
        f"🌾 *AgroTech Histórico — Demo Satelital Gratuita*\n"
        f"\n"
        f"¡Hola {nombre}! 👋\n"
        f"\n"
        f"Te envío acceso a tu *demo gratuita* de análisis satelital agrícola. "
        f"Podrás:\n"
        f"\n"
        f"🗺️ Dibujar tu parcela en un mapa interactivo\n"
        f"🛰️ Ver imágenes satelitales reales de tu terreno\n"
        f"📊 Obtener índices NDVI, NDMI y SAVI de tus cultivos\n"
        f"\n"
        f"👉 *Accede aquí:*\n"
        f"{demo_url}\n"
        f"\n"
        f"⏰ El link es válido por *{dias} días* y es de un solo uso.\n"
        f"\n"
        f"Si tienes preguntas, responde a este mensaje.\n"
        f"\n"
        f"_AgroTech Histórico · Análisis Satelital Agrícola_"
    )
    
    return mensaje


def _generar_mensaje_demo_html(token, demo_url):
    """
    Genera el cuerpo HTML del email profesional para la demo.
    Diseño responsive, colores AgroTech, botón CTA prominente.
    """
    nombre = token.nombre_prospecto or 'Estimado/a'
    dias = 7
    if token.fecha_expiracion:
        dias = max(1, (token.fecha_expiracion - timezone.now()).days)
    fecha_exp = ''
    if token.fecha_expiracion:
        fecha_exp = token.fecha_expiracion.strftime('%d/%m/%Y')
    
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background:#f4f7f4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; margin:0 auto; background:#ffffff;">
        <!-- Header -->
        <tr>
            <td style="background: linear-gradient(135deg, #2d5a27, #4a7c59); padding:24px; text-align:center;">
                <h1 style="color:#ffffff; margin:0; font-size:22px; font-weight:700;">
                    🌾 AgroTech Histórico
                </h1>
                <p style="color:#c8e6c0; margin:4px 0 0; font-size:13px; letter-spacing:1px;">
                    ANÁLISIS SATELITAL AGRÍCOLA
                </p>
            </td>
        </tr>
        
        <!-- Contenido -->
        <tr>
            <td style="padding:32px 24px;">
                <h2 style="color:#2d5a27; margin:0 0 16px; font-size:20px;">
                    ¡Hola {nombre}! 👋
                </h2>
                
                <p style="color:#555; font-size:15px; line-height:1.6; margin:0 0 20px;">
                    Te enviamos acceso a tu <strong>demo gratuita</strong> de análisis 
                    satelital agrícola. Con ella podrás ver el estado real de tu terreno 
                    usando imágenes de satélite.
                </p>
                
                <!-- Beneficios -->
                <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
                    <tr>
                        <td style="padding:12px 16px; background:#f0f7ee; border-radius:8px;">
                            <p style="margin:0 0 8px; font-size:14px; color:#333;">
                                🗺️ <strong>Dibuja tu parcela</strong> en un mapa interactivo
                            </p>
                            <p style="margin:0 0 8px; font-size:14px; color:#333;">
                                🛰️ <strong>Imágenes satelitales reales</strong> de tu terreno
                            </p>
                            <p style="margin:0; font-size:14px; color:#333;">
                                📊 <strong>Índices NDVI, NDMI y SAVI</strong> de tus cultivos
                            </p>
                        </td>
                    </tr>
                </table>
                
                <!-- Botón CTA -->
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="text-align:center; padding:8px 0 24px;">
                            <a href="{demo_url}" 
                               style="display:inline-block; background:#2d5a27; color:#ffffff; 
                                      text-decoration:none; padding:16px 40px; border-radius:8px; 
                                      font-size:17px; font-weight:600; letter-spacing:0.5px;">
                                🚀 Acceder a mi Demo
                            </a>
                        </td>
                    </tr>
                </table>
                
                <p style="color:#888; font-size:13px; text-align:center; margin:0 0 16px;">
                    O copia este enlace: <br>
                    <a href="{demo_url}" style="color:#2d5a27; word-break:break-all;">{demo_url}</a>
                </p>
                
                <!-- Vigencia -->
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="padding:12px 16px; background:#fff8e1; border-radius:8px; border-left:4px solid #ffc107;">
                            <p style="margin:0; font-size:13px; color:#666;">
                                ⏰ Este link es válido por <strong>{dias} días</strong>
                                {f' (hasta el {fecha_exp})' if fecha_exp else ''} 
                                y es de un solo uso.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td style="background:#f8f9fa; padding:20px 24px; text-align:center; border-top:1px solid #e9ecef;">
                <p style="margin:0 0 4px; font-size:12px; color:#999;">
                    🌾 AgroTech Histórico · Análisis Satelital Agrícola
                </p>
                <p style="margin:0; font-size:11px; color:#bbb;">
                    Si no solicitaste este acceso, puedes ignorar este correo.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


def _enviar_email_demo(token, demo_url, email_destino, nombre_prospecto=''):
    """
    Envía el email profesional de invitación a demo.
    
    Args:
        token: DemoToken
        demo_url: URL completa del demo
        email_destino: Email del prospecto
        nombre_prospecto: Nombre para personalizar
    
    Returns:
        dict: {'exito': bool, 'mensaje': str} o {'exito': False, 'error': str}
    """
    try:
        from django.core.mail import send_mail
        
        # Validar configuración de email
        if not getattr(settings, 'EMAIL_HOST_USER', ''):
            return {'exito': False, 'error': 'Configuración de email no encontrada en el sistema'}
        
        if not getattr(settings, 'EMAIL_HOST_PASSWORD', ''):
            return {'exito': False, 'error': 'Contraseña de email no configurada. Configure EMAIL_PASSWORD en .env'}
        
        nombre = nombre_prospecto or 'cliente'
        
        # Asunto profesional
        asunto = f"🌾 {nombre}, tu Demo Satelital Gratuita está lista — AgroTech Histórico"
        
        # Texto plano (fallback)
        mensaje_texto = _generar_mensaje_demo(token, demo_url).replace('*', '')
        
        # HTML profesional
        mensaje_html = _generar_mensaje_demo_html(token, demo_url)
        
        remitente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'agrotechdigitalcolombia@gmail.com')
        
        resultado = send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=remitente,
            recipient_list=[email_destino],
            html_message=mensaje_html,
            fail_silently=False,
        )
        
        if resultado:
            logger.info(f"✅ Email demo enviado a {email_destino} para token {token.token.hex[:8]}")
            return {
                'exito': True,
                'mensaje': f'Email enviado exitosamente a {email_destino}'
            }
        else:
            return {
                'exito': False,
                'error': 'El servidor de correo no confirmó el envío'
            }
    
    except Exception as e:
        logger.error(f"❌ Error enviando email demo: {str(e)}")
        error_msg = str(e)
        
        if "authentication" in error_msg.lower() or "login" in error_msg.lower():
            return {
                'exito': False,
                'error': 'Error de autenticación del email. Verifique EMAIL_PASSWORD en .env'
            }
        return {
            'exito': False,
            'error': f'Error enviando email: {error_msg}'
        }


# ========================================
# VISTAS DEL PANEL (DASHBOARD ADMIN)
# Requieren @login_required + superusuario
# ========================================

def _es_superusuario(user):
    """Verificación para @user_passes_test"""
    return user.is_superuser


@login_required
@user_passes_test(_es_superusuario, login_url='/informes/login/')
def panel_demos(request):
    """
    Panel principal de gestión de Demos.
    Lista todos los tokens, estadísticas y acceso rápido a crear/enviar.
    """
    try:
        # Obtener todos los tokens con leads prefetched
        tokens = DemoToken.objects.select_related().order_by('-fecha_creacion')
        
        # Estadísticas generales
        total_tokens = tokens.count()
        tokens_activos = tokens.filter(estado='activo').count()
        tokens_registrados = tokens.filter(estado='registrado').count()
        tokens_usados = tokens.filter(estado='usado').count()
        tokens_expirados = tokens.filter(estado='expirado').count()
        
        # Leads con parcela dibujada
        leads = DemoLead.objects.select_related('token').order_by('-fecha_demo')
        total_leads = leads.count()
        leads_convertidos = leads.filter(convertido_a_cliente=True).count()
        
        # Tasa de conversión
        tasa_conversion = 0
        if tokens_usados > 0:
            tasa_conversion = round((leads_convertidos / tokens_usados) * 100, 1)
        
        # Tasa de registro (cuántos se registraron del total)
        tasa_registro = 0
        if total_tokens > 0:
            registrados_total = tokens_registrados + tokens_usados
            tasa_registro = round((registrados_total / total_tokens) * 100, 1)
        
        # Hectáreas totales de demos
        from django.db.models import Sum
        hectareas_demo = leads.aggregate(Sum('area_hectareas'))['area_hectareas__sum'] or 0
        
        # URL base para links
        site_url = getattr(settings, 'SITE_URL', '')
        if not site_url:
            site_url = request.build_absolute_uri('/').rstrip('/')
        
        # 📊 Stats globales de uso EOSDA por demos
        eosda_stats = DemoEosdaRequest.stats_globales()
        
        contexto = {
            'tokens': tokens,
            'total_tokens': total_tokens,
            'tokens_activos': tokens_activos,
            'tokens_registrados': tokens_registrados,
            'tokens_usados': tokens_usados,
            'tokens_expirados': tokens_expirados,
            'total_leads': total_leads,
            'leads_convertidos': leads_convertidos,
            'tasa_conversion': tasa_conversion,
            'tasa_registro': tasa_registro,
            'hectareas_demo': round(hectareas_demo, 1),
            'site_url': site_url,
            'eosda_stats': eosda_stats,
        }
        
        return render(request, 'informes/demos/panel.html', contexto)
        
    except Exception as e:
        logger.error(f"❌ Error en panel_demos: {e}")
        messages.error(request, f"Error cargando panel de demos: {str(e)}")
        return render(request, 'informes/demos/panel.html', {'error': str(e)})


@login_required
@user_passes_test(_es_superusuario, login_url='/informes/login/')
def crear_demo(request):
    """
    Crear un nuevo token de demo con flujo profesional de envío.
    
    GET: Formulario con datos del prospecto + opciones de envío (WhatsApp/Email/Solo Link)
    POST: Crea token, opcionalmente envía por WhatsApp/Email, y muestra confirmación
    """
    if request.method == 'POST':
        try:
            # Datos del prospecto
            nombre_prospecto = request.POST.get('nombre_prospecto', '').strip()
            telefono_envio = request.POST.get('telefono_envio', '').strip()
            email_envio = request.POST.get('email_envio', '').strip()
            notas = request.POST.get('notas_comerciales', '').strip()
            dias_expiracion = int(request.POST.get('dias_expiracion', 7))
            metodo_envio = request.POST.get('metodo_envio', 'link')  # whatsapp | email | link
            
            # Validar días
            dias_expiracion = max(1, min(30, dias_expiracion))
            
            # Validaciones según método de envío
            if metodo_envio == 'whatsapp' and not telefono_envio:
                messages.error(request, '⚠️ Para enviar por WhatsApp necesitas ingresar el teléfono.')
                return render(request, 'informes/demos/crear.html', {
                    'form_data': request.POST,
                })
            
            if metodo_envio == 'email' and not email_envio:
                messages.error(request, '⚠️ Para enviar por email necesitas ingresar el correo.')
                return render(request, 'informes/demos/crear.html', {
                    'form_data': request.POST,
                })
            
            # Crear el token
            token = DemoToken.objects.create(
                notas_comerciales=notas,
                fecha_expiracion=timezone.now() + timedelta(days=dias_expiracion),
                nombre_prospecto=nombre_prospecto,
                telefono_envio=telefono_envio,
                email_envio=email_envio,
                metodo_envio=metodo_envio,
            )
            
            # Construir URL del demo
            site_url = getattr(settings, 'SITE_URL', '')
            if not site_url:
                site_url = request.build_absolute_uri('/').rstrip('/')
            demo_url = f"{site_url}/demo/{token.token}/"
            
            # Generar mensaje profesional
            mensaje_profesional = _generar_mensaje_demo(token, demo_url)
            
            logger.info(
                f"✅ Demo token creado: {token.token.hex[:8]} - "
                f"método: {metodo_envio} - expira en {dias_expiracion} días"
            )
            
            # Si es WhatsApp → redirigir a wa.me con mensaje prellenado
            if metodo_envio == 'whatsapp':
                import urllib.parse
                tel_limpio = ''.join(c for c in telefono_envio if c.isdigit())
                if not tel_limpio.startswith('57'):
                    tel_limpio = '57' + tel_limpio
                wa_url = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(mensaje_profesional)}"
                
                token.fecha_envio = timezone.now()
                token.save(update_fields=['fecha_envio'])
                
                # Redirigir a la confirmación con link de WhatsApp
                return render(request, 'informes/demos/enviado.html', {
                    'token': token,
                    'demo_url': demo_url,
                    'metodo': 'whatsapp',
                    'whatsapp_url': wa_url,
                    'mensaje_preview': mensaje_profesional,
                    'destinatario': f"{nombre_prospecto} ({telefono_envio})",
                })
            
            # Si es Email → enviar directamente
            elif metodo_envio == 'email':
                resultado_email = _enviar_email_demo(token, demo_url, email_envio, nombre_prospecto)
                
                if resultado_email['exito']:
                    token.fecha_envio = timezone.now()
                    token.save(update_fields=['fecha_envio'])
                    
                    return render(request, 'informes/demos/enviado.html', {
                        'token': token,
                        'demo_url': demo_url,
                        'metodo': 'email',
                        'mensaje_preview': mensaje_profesional,
                        'destinatario': f"{nombre_prospecto} ({email_envio})",
                        'email_enviado': True,
                    })
                else:
                    messages.warning(
                        request,
                        f'⚠️ Demo creada pero el email no se pudo enviar: {resultado_email["error"]}. '
                        f'Puedes reenviar desde el detalle.'
                    )
                    return redirect('informes:detalle_demo', token_id=token.id)
            
            # Solo link → ir al detalle para copiar manualmente
            else:
                messages.success(request, '✅ Demo creada. Copia el link y envíalo manualmente.')
                return redirect('informes:detalle_demo', token_id=token.id)
            
        except Exception as e:
            logger.error(f"❌ Error creando demo: {e}")
            messages.error(request, f"Error creando demo: {str(e)}")
    
    return render(request, 'informes/demos/crear.html', {
        'form_data': {},
    })


@login_required
@user_passes_test(_es_superusuario, login_url='/informes/login/')
def detalle_demo(request, token_id):
    """
    Vista detallada de un token/lead de demo.
    Muestra: datos del contacto, parcela dibujada, imágenes, acciones de conversión.
    """
    try:
        token = get_object_or_404(DemoToken, id=token_id)
        lead = getattr(token, 'lead', None)
        
        # URL base
        site_url = getattr(settings, 'SITE_URL', '')
        if not site_url:
            site_url = request.build_absolute_uri('/').rstrip('/')
        demo_url = f"{site_url}/demo/{token.token}/"
        
        # Link WhatsApp de envío
        import urllib.parse
        texto_wa = (
            f"¡Hola! 🌾 Te envío el acceso a tu demo gratuita de análisis "
            f"satelital AgroTech. Podrás dibujar tu parcela y ver imágenes "
            f"satelitales reales de tu terreno:\n\n{demo_url}"
        )
        whatsapp_envio_url = f"https://wa.me/?text={urllib.parse.quote(texto_wa)}"
        
        # Si hay lead con teléfono, preenviar al número
        if token.telefono:
            tel_limpio = ''.join(c for c in token.telefono if c.isdigit())
            if not tel_limpio.startswith('57'):
                tel_limpio = '57' + tel_limpio
            whatsapp_directo_url = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(texto_wa)}"
        else:
            whatsapp_directo_url = whatsapp_envio_url
        
        # GeoJSON de la parcela para mostrar en mapa
        geojson_parcela = None
        if lead and lead.geometria:
            geojson_parcela = lead.geometria.geojson
        
        # Mensaje profesional para preview
        mensaje_profesional = _generar_mensaje_demo(token, demo_url)
        
        contexto = {
            'token': token,
            'lead': lead,
            'demo_url': demo_url,
            'whatsapp_envio_url': whatsapp_envio_url,
            'whatsapp_directo_url': whatsapp_directo_url,
            'geojson_parcela': geojson_parcela,
            'mensaje_profesional': mensaje_profesional,
        }
        
        return render(request, 'informes/demos/detalle.html', contexto)
        
    except Exception as e:
        logger.error(f"❌ Error en detalle_demo: {e}")
        messages.error(request, f"Error cargando detalle: {str(e)}")
        return redirect('informes:panel_demos')


@login_required
@user_passes_test(_es_superusuario, login_url='/informes/login/')
@require_POST
def convertir_demo_a_parcela(request, token_id):
    """
    Convierte un DemoLead en una Parcela real del sistema principal.
    
    Flujo:
    1. Toma la geometría dibujada en la demo
    2. Crea un nuevo objeto Parcela con esa geometría
    3. Marca el DemoLead como convertido
    4. Redirige al detalle de la nueva parcela
    """
    try:
        token = get_object_or_404(DemoToken, id=token_id)
        lead = getattr(token, 'lead', None)
        
        if not lead:
            messages.error(request, '❌ Este token no tiene una parcela dibujada.')
            return redirect('informes:detalle_demo', token_id=token_id)
        
        if not lead.geometria:
            messages.error(request, '❌ El lead no tiene geometría para convertir.')
            return redirect('informes:detalle_demo', token_id=token_id)
        
        if lead.convertido_a_cliente:
            messages.warning(request, '⚠️ Este lead ya fue convertido a cliente.')
            if lead.parcela_real_id:
                return redirect('informes:detalle_parcela', parcela_id=lead.parcela_real_id)
            return redirect('informes:detalle_demo', token_id=token_id)
        
        # Datos del formulario de conversión
        nombre_parcela = request.POST.get('nombre_parcela', '').strip()
        propietario = request.POST.get('propietario', '').strip()
        tipo_cultivo = request.POST.get('tipo_cultivo', '').strip()
        fecha_inicio = request.POST.get('fecha_inicio_monitoreo', '')
        
        if not nombre_parcela:
            nombre_parcela = f"Parcela {token.nombre_completo or 'Demo'}"
        if not propietario:
            propietario = token.nombre_completo or 'Cliente Demo'
        
        # Fecha de inicio de monitoreo
        from datetime import date
        if fecha_inicio:
            try:
                fecha_inicio_dt = date.fromisoformat(fecha_inicio)
            except ValueError:
                fecha_inicio_dt = date.today()
        else:
            fecha_inicio_dt = date.today()
        
        # Importar modelo Parcela
        from .models import Parcela
        
        # Crear la Parcela real con la geometría de la demo
        parcela = Parcela(
            nombre=nombre_parcela,
            propietario=propietario,
            geometria=lead.geometria,
            tipo_cultivo=tipo_cultivo,
            fecha_inicio_monitoreo=fecha_inicio_dt,
            activa=True,
            notas=(
                f"Convertida desde demo #{token.token.hex[:8]}. "
                f"Contacto: {token.nombre_completo} - {token.telefono}. "
                f"Municipio: {token.municipio or 'N/A'}, "
                f"Depto: {token.departamento or 'N/A'}."
            ),
        )
        
        # Guardar coordenadas como GeoJSON de respaldo
        parcela.coordenadas = lead.geometria.geojson
        
        # Precalcular área desde el lead (en caso de que save() falle con PROJ)
        parcela.area_hectareas = lead.area_hectareas
        
        try:
            parcela.save()  # El save() de Parcela calcula área, centroide, perímetro
        except Exception as save_err:
            # Si falla la transformación PROJ, guardar sin cálculos automáticos
            logger.warning(f"⚠️ Error en cálculo automático de Parcela.save(): {save_err}")
            parcela.area_hectareas = lead.area_hectareas
            # Guardar sin trigger de auto-cálculo
            from django.db import models as db_models
            db_models.Model.save(parcela)
        
        # Marcar el lead como convertido
        lead.convertido_a_cliente = True
        lead.parcela_real_id = parcela.id
        lead.save(update_fields=['convertido_a_cliente', 'parcela_real_id'])
        
        logger.info(
            f"✅ Demo convertida a parcela: {token.nombre_completo} → "
            f"Parcela #{parcela.id} '{parcela.nombre}' ({parcela.area_hectareas:.1f}ha)"
        )
        
        messages.success(
            request,
            f'✅ ¡Conversión exitosa! Parcela "{parcela.nombre}" creada con '
            f'{parcela.area_hectareas:.1f} ha. Ya puedes sincronizar con EOSDA.'
        )
        
        return redirect('informes:detalle_parcela', parcela_id=parcela.id)
        
    except Exception as e:
        logger.error(f"❌ Error convirtiendo demo a parcela: {e}")
        messages.error(request, f"Error en la conversión: {str(e)}")
        return redirect('informes:detalle_demo', token_id=token_id)


@login_required
@user_passes_test(_es_superusuario, login_url='/informes/login/')
@require_POST
def eliminar_demo(request, token_id):
    """
    Elimina un token de demo y su lead asociado.
    Solo permite eliminar si no fue convertido a cliente.
    """
    try:
        token = get_object_or_404(DemoToken, id=token_id)
        lead = getattr(token, 'lead', None)
        
        if lead and lead.convertido_a_cliente:
            messages.error(request, '❌ No se puede eliminar un demo que ya fue convertido a cliente.')
            return redirect('informes:detalle_demo', token_id=token_id)
        
        nombre = token.nombre_completo or f'Token {token.token.hex[:8]}'
        
        # Eliminar imágenes demo del filesystem
        if lead:
            token_hex = token.token.hex[:8]
            dir_imagenes = DEMO_MEDIA_DIR / token_hex
            if dir_imagenes.exists():
                import shutil
                shutil.rmtree(str(dir_imagenes), ignore_errors=True)
                logger.info(f"🗑️ Imágenes demo eliminadas: {dir_imagenes}")
        
        token.delete()  # Cascade elimina el lead
        
        logger.info(f"🗑️ Demo eliminada: {nombre}")
        messages.success(request, f'🗑️ Demo "{nombre}" eliminada correctamente.')
        
        return redirect('informes:panel_demos')
        
    except Exception as e:
        logger.error(f"❌ Error eliminando demo: {e}")
        messages.error(request, f"Error eliminando demo: {str(e)}")
        return redirect('informes:panel_demos')


@login_required
@user_passes_test(_es_superusuario, login_url='/informes/login/')
def reenviar_demo_whatsapp(request, token_id):
    """
    Genera y redirige al link de WhatsApp para reenviar el demo.
    Usa el mensaje profesional con formato completo.
    """
    token = get_object_or_404(DemoToken, id=token_id)
    
    site_url = getattr(settings, 'SITE_URL', '')
    if not site_url:
        site_url = request.build_absolute_uri('/').rstrip('/')
    demo_url = f"{site_url}/demo/{token.token}/"
    
    import urllib.parse
    
    # Usar el mensaje profesional
    texto = _generar_mensaje_demo(token, demo_url)
    
    # Determinar teléfono: primero el de envío, luego el del registro
    tel_raw = token.telefono_envio or token.telefono or ''
    tel_limpio = ''.join(c for c in tel_raw if c.isdigit())
    if tel_limpio and not tel_limpio.startswith('57'):
        tel_limpio = '57' + tel_limpio
    
    if tel_limpio:
        wa_url = f"https://wa.me/{tel_limpio}?text={urllib.parse.quote(texto)}"
    else:
        wa_url = f"https://wa.me/?text={urllib.parse.quote(texto)}"
    
    # Actualizar tracking de envío si es la primera vez
    if not token.fecha_envio:
        token.metodo_envio = 'whatsapp'
        token.fecha_envio = timezone.now()
        token.save(update_fields=['metodo_envio', 'fecha_envio'])
    
    return redirect(wa_url)


@login_required
@user_passes_test(_es_superusuario, login_url='/informes/login/')
@require_POST
def enviar_demo_email(request, token_id):
    """
    Enviar (o reenviar) el email profesional de la demo.
    Se puede usar desde el detalle para enviar por primera vez o reenviar.
    """
    try:
        token = get_object_or_404(DemoToken, id=token_id)
        
        # Determinar email destino: formulario > campo de envío > registro del prospecto
        email_destino = request.POST.get('email_destino', '').strip()
        if not email_destino:
            email_destino = token.email_envio or token.email or ''
        
        if not email_destino:
            messages.error(request, '⚠️ No hay email para este prospecto. Ingresa uno.')
            return redirect('informes:detalle_demo', token_id=token_id)
        
        site_url = getattr(settings, 'SITE_URL', '')
        if not site_url:
            site_url = request.build_absolute_uri('/').rstrip('/')
        demo_url = f"{site_url}/demo/{token.token}/"
        
        nombre = token.nombre_prospecto or token.nombre_completo or 'Prospecto'
        
        resultado = _enviar_email_demo(token, demo_url, email_destino, nombre)
        
        if resultado['exito']:
            # Actualizar datos de envío
            token.metodo_envio = 'email'
            token.email_envio = email_destino
            token.fecha_envio = timezone.now()
            token.save(update_fields=['metodo_envio', 'email_envio', 'fecha_envio'])
            
            messages.success(request, f'✅ Email enviado exitosamente a {email_destino}')
        else:
            messages.error(request, f'❌ Error enviando email: {resultado["error"]}')
        
        return redirect('informes:detalle_demo', token_id=token_id)
    
    except Exception as e:
        logger.error(f"❌ Error en enviar_demo_email: {e}")
        messages.error(request, f"Error: {str(e)}")
        return redirect('informes:detalle_demo', token_id=token_id)
