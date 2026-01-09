#!/usr/bin/env python
"""
Prueba obtener datos satelitales de la parcela 11 recién sincronizada
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.services.eosda_api import eosda_service
from django.contrib.auth import get_user_model

User = get_user_model()

def main():
    print("\n" + "="*80)
    print("  🛰️ TEST DE DATOS SATELITALES - PARCELA 11")
    print("="*80)
    
    # Obtener parcela 11
    parcela = Parcela.objects.get(id=11)
    print(f"\n✅ Parcela: {parcela.nombre}")
    print(f"   Field ID: {parcela.eosda_field_id}")
    print(f"   Sincronizada: {parcela.eosda_sincronizada}")
    
    # Obtener usuario
    usuario = User.objects.filter(is_superuser=True).first()
    
    # Definir rango (últimos 6 meses)
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=180)
    
    print(f"\n📅 Período: {fecha_inicio} a {fecha_fin} (6 meses)")
    
    # Intentar obtener datos
    print("\n" + "="*80)
    print("  🔍 OBTENIENDO DATOS CON UMBRAL 100% (VER TODAS LAS IMÁGENES)")
    print("="*80)
    
    datos = eosda_service.obtener_datos_optimizado(
        parcela=parcela,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        indices=['NDVI', 'NDMI', 'SAVI'],
        usuario=usuario,
        max_nubosidad=100
    )
    
    if datos and 'resultados' in datos:
        escenas = datos.get('resultados', [])
        print(f"\n✅ Total de imágenes: {len(escenas)}")
        
        if escenas:
            from collections import defaultdict
            por_mes = defaultdict(list)
            
            for escena in escenas:
                fecha_str = escena.get('date', '')
                if fecha_str:
                    from datetime import datetime
                    fecha_obj = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    mes = fecha_obj.strftime('%Y-%m')
                    por_mes[mes].append(escena)
            
            print(f"\n📊 Distribución por mes:")
            for mes in sorted(por_mes.keys()):
                escenas_mes = por_mes[mes]
                nubosidades = [e.get('cloud', 0) for e in escenas_mes]
                nub_min = min(nubosidades)
                nub_prom = sum(nubosidades) / len(nubosidades)
                
                print(f"   {mes}: {len(escenas_mes)} imágenes (nubosidad: {nub_min:.1f}% - promedio: {nub_prom:.1f}%)")
        else:
            print("\n⚠️ No hay imágenes disponibles")
    else:
        print(f"\n❌ Error obteniendo datos")
        if 'error' in datos:
            print(f"   Error: {datos.get('error')}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
