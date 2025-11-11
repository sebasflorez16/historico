#!/usr/bin/env python
"""
Script de prueba para el sistema optimizado de EOSDA con caché y tracking
"""
import os
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.contrib.auth.models import User
from informes.models import Parcela, CacheDatosEOSDA, EstadisticaUsoEOSDA
from informes.services.eosda_api import eosda_service


def test_optimizado():
    """Prueba completa del sistema optimizado"""
    
    print("\n" + "="*70)
    print("🧪 PRUEBA DE SISTEMA OPTIMIZADO CON CACHÉ")
    print("="*70)
    
    # 1. Obtener datos necesarios
    try:
        user = User.objects.first()
        if not user:
            print("❌ No hay usuarios en el sistema")
            return
        
        parcela = Parcela.objects.filter(eosda_field_id__isnull=False).first()
        if not parcela:
            print("❌ No hay parcelas sincronizadas con EOSDA")
            return
        
        print(f"\n📍 Parcela: {parcela.nombre} (field_id: {parcela.eosda_field_id})")
        print(f"👤 Usuario: {user.username}")
        
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return
    
    # 2. Limpiar estadísticas anteriores para prueba limpia
    print(f"\n🧹 Limpiando estadísticas anteriores...")
    estadisticas_anteriores = EstadisticaUsoEOSDA.objects.filter(
        usuario=user,
        parcela=parcela
    ).count()
    print(f"   Estadísticas anteriores: {estadisticas_anteriores}")
    
    # 3. Limpiar caché anterior
    print(f"\n🧹 Limpiando caché anterior...")
    cache_anterior = CacheDatosEOSDA.objects.filter(field_id=parcela.eosda_field_id).count()
    if cache_anterior > 0:
        CacheDatosEOSDA.objects.filter(field_id=parcela.eosda_field_id).delete()
        print(f"   ✅ Eliminados {cache_anterior} registros de caché")
    
    # 4. Configurar parámetros de prueba
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=30)  # Últimos 30 días
    indices = ['ndvi', 'ndmi', 'savi']  # 3 índices
    
    print(f"\n📅 Periodo: {fecha_inicio} a {fecha_fin}")
    print(f"📊 Índices: {', '.join(indices)}")
    print(f"☁️  Nubosidad máxima: 50%")
    
    # 5. PRIMERA LLAMADA - Sin caché (debe consumir 1 request)
    print(f"\n" + "-"*70)
    print("🔥 PRIMERA LLAMADA (sin caché)")
    print("-"*70)
    
    try:
        resultado1 = eosda_service.obtener_datos_optimizado(
            field_id=parcela.eosda_field_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            indices=indices,
            usuario=user,
            parcela=parcela,
            max_nubosidad=50
        )
        
        if 'error' in resultado1:
            print(f"❌ Error: {resultado1['error']}")
        else:
            num_escenas = len(resultado1.get('resultados', []))
            print(f"✅ Éxito: {num_escenas} escenas obtenidas")
            
            # Verificar estadísticas
            stats1 = EstadisticaUsoEOSDA.objects.filter(
                usuario=user,
                parcela=parcela
            ).latest('fecha')
            
            print(f"\n📊 Estadísticas de la llamada:")
            print(f"   • Requests consumidos: {stats1.requests_consumidos}")
            print(f"   • Desde caché: {stats1.desde_cache}")
            print(f"   • Tiempo respuesta: {stats1.tiempo_respuesta:.2f}s")
            print(f"   • Exitoso: {stats1.exitoso}")
            
            # Verificar caché guardado
            cache_guardado = CacheDatosEOSDA.objects.filter(
                field_id=parcela.eosda_field_id
            ).count()
            print(f"\n💾 Registros en caché: {cache_guardado}")
            
    except Exception as e:
        print(f"❌ Error en primera llamada: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. SEGUNDA LLAMADA - Con caché (debe consumir 0 requests)
    print(f"\n" + "-"*70)
    print("⚡ SEGUNDA LLAMADA (con caché)")
    print("-"*70)
    
    try:
        resultado2 = eosda_service.obtener_datos_optimizado(
            field_id=parcela.eosda_field_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            indices=indices,
            usuario=user,
            parcela=parcela,
            max_nubosidad=50
        )
        
        if 'error' in resultado2:
            print(f"❌ Error: {resultado2['error']}")
        else:
            num_escenas = len(resultado2.get('resultados', []))
            print(f"✅ Éxito: {num_escenas} escenas obtenidas")
            
            # Verificar estadísticas
            stats2 = EstadisticaUsoEOSDA.objects.filter(
                usuario=user,
                parcela=parcela
            ).latest('fecha')
            
            print(f"\n📊 Estadísticas de la llamada:")
            print(f"   • Requests consumidos: {stats2.requests_consumidos}")
            print(f"   • Desde caché: {stats2.desde_cache}")
            print(f"   • Tiempo respuesta: {stats2.tiempo_respuesta:.4f}s")
            print(f"   • Cache key: {stats2.cache_key[:50]}...")
            
    except Exception as e:
        print(f"❌ Error en segunda llamada: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. RESUMEN FINAL
    print(f"\n" + "="*70)
    print("📈 RESUMEN DE OPTIMIZACIÓN")
    print("="*70)
    
    try:
        stats = EstadisticaUsoEOSDA.estadisticas_usuario(user)
        
        print(f"\n🔢 Totales:")
        print(f"   • Total operaciones: {stats['total_operaciones']}")
        print(f"   • Requests consumidos: {stats['total_requests']}")
        print(f"   • Operaciones exitosas: {stats['operaciones_exitosas']}")
        print(f"   • Desde caché: {stats['desde_cache']}")
        
        if stats['desde_cache'] > 0:
            tasa_cache = (stats['desde_cache'] / stats['total_operaciones']) * 100
            print(f"   • Tasa de acierto caché: {tasa_cache:.1f}%")
        
        ahorro = stats['desde_cache'] * len(indices)
        print(f"\n💰 Ahorro estimado:")
        print(f"   • Requests ahorrados por caché: ~{ahorro}")
        print(f"   • Sin optimización habrían sido: {stats['total_operaciones'] * len(indices)} requests")
        print(f"   • Con optimización fueron: {stats['total_requests']} requests")
        
        if stats['total_operaciones'] > 0:
            eficiencia = ((stats['total_operaciones'] * len(indices) - stats['total_requests']) / 
                         (stats['total_operaciones'] * len(indices))) * 100
            print(f"   • Eficiencia de optimización: {eficiencia:.1f}%")
        
    except Exception as e:
        print(f"❌ Error calculando estadísticas: {e}")
    
    print(f"\n" + "="*70)
    print("✅ PRUEBA COMPLETADA")
    print("="*70 + "\n")


if __name__ == '__main__':
    test_optimizado()
