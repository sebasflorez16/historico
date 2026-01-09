#!/usr/bin/env python
"""
Simula exactamente lo que hace la interfaz web al obtener datos históricos
Usa la parcela 6 con un rango de 1 año
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela, IndiceMensual
from informes.services.eosda_api import eosda_service
from django.contrib.auth import get_user_model

User = get_user_model()

def print_banner(text):
    """Imprime un banner decorativo"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def simular_interfaz_web():
    """
    Simula exactamente el flujo de obtener_datos_historicos desde la interfaz
    """
    
    print_banner("🌐 SIMULACIÓN DE INTERFAZ WEB - OBTENER DATOS HISTÓRICOS")
    
    # 1. Obtener usuario (simular request.user)
    print("\n📋 1. Preparando usuario...")
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        usuario, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@agrotech.com', 'is_superuser': True}
        )
        if created:
            usuario.set_password('admin123')
            usuario.save()
    print(f"   ✅ Usuario: {usuario.username}")
    
    # 2. Obtener parcela 6
    print("\n📋 2. Obteniendo parcela 6...")
    try:
        parcela = Parcela.objects.get(id=6, activa=True)
        print(f"   ✅ Parcela: {parcela.nombre}")
        print(f"   📍 Área: {parcela.area_hectareas:.2f} hectáreas")
        print(f"   🗺️ EOSDA Field ID: {parcela.eosda_field_id}")
        print(f"   🔗 Sincronizada: {'Sí' if parcela.eosda_sincronizada else 'No'}")
    except Parcela.DoesNotExist:
        print("   ❌ Parcela 6 no encontrada")
        return
    
    # 3. Definir rango de fechas (1 año)
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=365)
    print(f"\n📅 3. Rango de fechas:")
    print(f"   Inicio: {fecha_inicio}")
    print(f"   Fin: {fecha_fin}")
    print(f"   Días: 365 (~12 meses)")
    
    # 4. Verificar sincronización (igual que en la vista)
    if not parcela.eosda_sincronizada or not parcela.eosda_field_id:
        print("\n⚠️  Parcela no sincronizada con EOSDA, sincronizando primero...")
        resultado_sync = eosda_service.sincronizar_parcela_con_eosda(parcela)
        if not resultado_sync['exito']:
            print(f"   ❌ Error sincronizando: {resultado_sync.get('error', '')}")
            return
        parcela.refresh_from_db()
        print(f"   ✅ Parcela sincronizada: {parcela.eosda_field_id}")
    
    # 5. ⭐ PRIMERO: Verificar qué datos hay disponibles SIN filtro de nubosidad
    print_banner("🔍 PASO 1: VERIFICANDO DISPONIBILIDAD DE DATOS (SIN FILTRO)")
    print("\n   Consultando EOSDA Statistics API sin filtro de nubosidad...")
    print(f"   Field ID: {parcela.eosda_field_id}")
    print(f"   Período: {fecha_inicio} a {fecha_fin}")
    
    # Llamar directamente a obtener_datos_optimizado con umbral 100% para ver TODO
    datos_sin_filtro = eosda_service.obtener_datos_optimizado(
        parcela=parcela,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        indices=['NDVI', 'NDMI', 'SAVI'],
        usuario=usuario,
        max_nubosidad=100  # Ver TODAS las imágenes disponibles
    )
    
    if datos_sin_filtro and 'resultados' in datos_sin_filtro:
        escenas_totales = datos_sin_filtro.get('resultados', [])
        print(f"\n   ✅ Total de imágenes disponibles: {len(escenas_totales)}")
        
        if escenas_totales:
            # Analizar por mes y nubosidad
            from collections import defaultdict
            por_mes = defaultdict(list)
            
            for escena in escenas_totales:
                fecha_str = escena.get('date', '')
                nubosidad = escena.get('cloud', 0)
                if fecha_str:
                    from datetime import datetime
                    fecha = datetime.fromisoformat(fecha_str).date()
                    mes_key = f"{fecha.year}-{fecha.month:02d}"
                    por_mes[mes_key].append({
                        'fecha': fecha,
                        'nubosidad': nubosidad,
                        'escena': escena
                    })
            
            print(f"\n   📅 Imágenes disponibles por mes:")
            print(f"   " + "="*70)
            
            for mes in sorted(por_mes.keys()):
                escenas_mes = por_mes[mes]
                nubosidades = [e['nubosidad'] for e in escenas_mes]
                nub_min = min(nubosidades)
                nub_max = max(nubosidades)
                nub_prom = sum(nubosidades) / len(nubosidades)
                
                # Clasificar por calidad
                excelentes = sum(1 for n in nubosidades if n < 20)
                buenas = sum(1 for n in nubosidades if 20 <= n < 50)
                aceptables = sum(1 for n in nubosidades if 50 <= n < 80)
                malas = sum(1 for n in nubosidades if n >= 80)
                
                print(f"\n   📆 {mes}: {len(escenas_mes)} imágenes")
                print(f"      Nubosidad: {nub_min:.1f}% - {nub_max:.1f}% (promedio: {nub_prom:.1f}%)")
                print(f"      🌟 Excelentes (<20%): {excelentes}  |  ☁️ Buenas (20-50%): {buenas}")
                print(f"      ⚠️ Aceptables (50-80%): {aceptables}  |  ❌ Malas (≥80%): {malas}")
                
                # Mostrar la mejor imagen del mes
                mejor = min(escenas_mes, key=lambda x: x['nubosidad'])
                print(f"      🎯 Mejor: {mejor['fecha']} con {mejor['nubosidad']:.1f}% nubosidad")
            
            print(f"\n   " + "="*70)
            
            # Resumen por calidad
            todas_nubosidades = [e.get('cloud', 0) for e in escenas_totales]
            total_excelentes = sum(1 for n in todas_nubosidades if n < 20)
            total_buenas = sum(1 for n in todas_nubosidades if 20 <= n < 50)
            total_aceptables = sum(1 for n in todas_nubosidades if 50 <= n < 80)
            total_malas = sum(1 for n in todas_nubosidades if n >= 80)
            
            print(f"\n   � RESUMEN DE CALIDAD GLOBAL:")
            print(f"      🌟 Excelentes (<20%): {total_excelentes} ({total_excelentes/len(escenas_totales)*100:.1f}%)")
            print(f"      ☁️ Buenas (20-50%): {total_buenas} ({total_buenas/len(escenas_totales)*100:.1f}%)")
            print(f"      ⚠️ Aceptables (50-80%): {total_aceptables} ({total_aceptables/len(escenas_totales)*100:.1f}%)")
            print(f"      ❌ Malas (≥80%): {total_malas} ({total_malas/len(escenas_totales)*100:.1f}%)")
            
        else:
            print(f"\n   ⚠️ No se encontraron imágenes disponibles")
    else:
        print(f"\n   ❌ Error consultando EOSDA o no hay datos")
        if 'error' in datos_sin_filtro:
            print(f"   Error: {datos_sin_filtro.get('error')}")
    
    # 6. ⭐ AHORA SÍ: Ejecutar búsqueda con umbrales múltiples
    print_banner("🔍 PASO 2: BÚSQUEDA INTELIGENTE CON UMBRALES MÚLTIPLES")
    
    resultado_busqueda = eosda_service.obtener_datos_con_umbrales_multiples(
        parcela=parcela,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        indices=['NDVI', 'NDMI', 'SAVI'],
        usuario=usuario
    )
    
    # 6. Procesar resultados (igual que en views.py)
    print_banner("📊 RESULTADOS DE LA BÚSQUEDA")
    
    datos_satelitales = resultado_busqueda.get('datos')
    umbral_usado = resultado_busqueda.get('umbral_usado')
    calidad_datos = resultado_busqueda.get('calidad_datos')
    emoji_calidad = resultado_busqueda.get('emoji_calidad', '')
    cobertura_pct = resultado_busqueda.get('cobertura_porcentaje', 0)
    cobertura_mensual = resultado_busqueda.get('cobertura_mensual', 0)
    meses_esperados = resultado_busqueda.get('meses_esperados', 0)
    
    if not datos_satelitales:
        error_msg = resultado_busqueda.get('error', 'No se pudieron obtener datos')
        print(f"\n❌ ERROR: {error_msg}")
        return
    
    # 7. Mostrar mensaje según calidad (igual que en views.py)
    print(f"\n{emoji_calidad} CALIDAD DE DATOS: {calidad_datos.upper()}")
    print(f"   📏 Umbral usado: {umbral_usado}%")
    print(f"   📅 Cobertura: {cobertura_mensual}/{meses_esperados} meses ({cobertura_pct:.1f}%)")
    
    if calidad_datos == 'excelente':
        print(f"\n   ✅ MENSAJE AL USUARIO:")
        print(f"   {emoji_calidad} Imágenes de calidad EXCELENTE obtenidas")
        print(f"   (nubosidad < 20%, cobertura {cobertura_pct:.0f}%)")
    elif calidad_datos == 'buena':
        print(f"\n   ℹ️ MENSAJE AL USUARIO:")
        print(f"   {emoji_calidad} Imágenes de calidad BUENA obtenidas")
        print(f"   (nubosidad < 50%, cobertura {cobertura_pct:.0f}%)")
    elif calidad_datos == 'aceptable':
        print(f"\n   ⚠️ MENSAJE AL USUARIO:")
        print(f"   {emoji_calidad} Imágenes de calidad ACEPTABLE obtenidas")
        print(f"   (nubosidad < 80%, cobertura {cobertura_pct:.0f}%)")
        print(f"   Considera que algunas imágenes pueden tener nubes visibles.")
    
    # 8. Guardar metadatos en parcela (igual que en views.py)
    print(f"\n💾 Guardando metadatos de calidad en la parcela...")
    parcela.ultima_calidad_datos = calidad_datos
    parcela.ultimo_umbral_nubosidad = umbral_usado
    parcela.save(update_fields=['ultima_calidad_datos', 'ultimo_umbral_nubosidad'])
    print(f"   ✅ Calidad guardada: {parcela.ultima_calidad_datos}")
    print(f"   ✅ Umbral guardado: {parcela.ultimo_umbral_nubosidad}%")
    
    # 9. Mostrar estadísticas de escenas DETALLADAS POR MES
    escenas = datos_satelitales.get('resultados', [])
    print(f"\n📊 ESTADÍSTICAS DE ESCENAS:")
    print(f"   🛰️ Total de escenas: {len(escenas)}")
    
    if escenas:
        # Organizar escenas por mes
        from collections import defaultdict
        from datetime import datetime
        
        escenas_por_mes = defaultdict(list)
        
        for escena in escenas:
            fecha_str = escena.get('date', '')
            if fecha_str:
                try:
                    fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    mes_clave = fecha_obj.strftime('%Y-%m')  # Formato: 2024-01
                    escenas_por_mes[mes_clave].append(escena)
                except:
                    pass
        
        # Mostrar disponibilidad por mes
        print(f"\n📅 DISPONIBILIDAD POR MES (de más reciente a más antiguo):")
        print("="*80)
        
        meses_ordenados = sorted(escenas_por_mes.keys(), reverse=True)
        
        for mes_clave in meses_ordenados:
            escenas_mes = escenas_por_mes[mes_clave]
            mes_obj = datetime.strptime(mes_clave, '%Y-%m')
            mes_nombre = mes_obj.strftime('%B %Y')  # Ej: "Enero 2025"
            
            print(f"\n   📆 {mes_nombre.upper()}")
            print(f"   {'─'*76}")
            print(f"   Imágenes disponibles: {len(escenas_mes)}")
            
            # Ordenar por nubosidad (mejor primero)
            escenas_mes_ordenadas = sorted(
                escenas_mes, 
                key=lambda x: x.get('cloud', 100)
            )
            
            # Mostrar cada imagen disponible
            for i, escena in enumerate(escenas_mes_ordenadas, 1):
                fecha = escena.get('date', 'N/A')
                nub = escena.get('cloud', 0)
                indices_data = escena.get('indexes', {})
                ndvi = indices_data.get('NDVI', {}).get('average', 'N/A')
                ndmi = indices_data.get('NDMI', {}).get('average', 'N/A')
                savi = indices_data.get('SAVI', {}).get('average', 'N/A')
                
                # Emoji según calidad
                if nub < 20:
                    emoji = "🌟"
                    calidad = "EXCELENTE"
                elif nub < 50:
                    emoji = "☁️"
                    calidad = "BUENA"
                elif nub < 80:
                    emoji = "⚠️"
                    calidad = "ACEPTABLE"
                else:
                    emoji = "❌"
                    calidad = "MALA"
                
                print(f"   {emoji} Imagen #{i}: {fecha[:10]}")
                print(f"      Nubosidad: {nub:.1f}% ({calidad})")
                print(f"      NDVI: {ndvi if isinstance(ndvi, str) else f'{ndvi:.3f}'}")
                print(f"      NDMI: {ndmi if isinstance(ndmi, str) else f'{ndmi:.3f}'}")
                print(f"      SAVI: {savi if isinstance(savi, str) else f'{savi:.3f}'}")
                
                # Destacar la mejor imagen del mes (la primera, ya están ordenadas)
                if i == 1 and len(escenas_mes_ordenadas) > 1:
                    print(f"      ⭐ MEJOR IMAGEN DEL MES (será usada en el informe)")
        
        # Resumen general de nubosidad
        print(f"\n" + "="*80)
        nubosidades = [e.get('cloud', 0) for e in escenas if e.get('cloud') is not None]
        
        if nubosidades:
            nub_min = min(nubosidades)
            nub_max = max(nubosidades)
            nub_prom = sum(nubosidades) / len(nubosidades)
            
            print(f"\n   📊 RESUMEN GENERAL DE NUBOSIDAD:")
            print(f"      Mínima: {nub_min:.1f}%")
            print(f"      Máxima: {nub_max:.1f}%")
            print(f"      Promedio: {nub_prom:.1f}%")
            
            # Clasificar por calidad
            excelentes = sum(1 for n in nubosidades if n < 20)
            buenas = sum(1 for n in nubosidades if 20 <= n < 50)
            aceptables = sum(1 for n in nubosidades if 50 <= n < 80)
            malas = sum(1 for n in nubosidades if n >= 80)
            
            print(f"\n   🎯 DISTRIBUCIÓN DE CALIDAD:")
            print(f"      🌟 Excelentes (< 20%): {excelentes} imágenes")
            print(f"      ☁️ Buenas (20-50%): {buenas} imágenes")
            print(f"      ⚠️ Aceptables (50-80%): {aceptables} imágenes")
            print(f"      ❌ Malas (>= 80%): {malas} imágenes")
    
    # 10. Resumen final
    print_banner("✅ SIMULACIÓN COMPLETADA")
    print(f"""
   La función obtener_datos_con_umbrales_multiples() funcionó correctamente.
   
   Resumen:
   - Parcela: {parcela.nombre} (ID: {parcela.id})
   - Umbral usado: {umbral_usado}%
   - Calidad: {calidad_datos}
   - Escenas obtenidas: {len(escenas)}
   - Cobertura: {cobertura_mensual}/{meses_esperados} meses
   
   Metadatos guardados en BD para mostrar en el PDF.
    """)

if __name__ == '__main__':
    try:
        simular_interfaz_web()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulación interrumpida")
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
