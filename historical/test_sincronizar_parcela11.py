#!/usr/bin/env python
"""
Script para probar la sincronización de la parcela 11 con EOSDA.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from informes.models import Parcela
from informes.services.eosda_api import eosda_service

def main():
    print("\n" + "="*80)
    print("  🧪 TEST DE SINCRONIZACIÓN - PARCELA 11")
    print("="*80)
    
    # Obtener parcela 11
    try:
        parcela = Parcela.objects.get(id=11)
        print(f"\n✅ Parcela encontrada:")
        print(f"   ID: {parcela.id}")
        print(f"   Nombre: {parcela.nombre}")
        print(f"   Cultivo: {parcela.tipo_cultivo}")
        print(f"   Área: {parcela.area_hectareas:.2f} ha")
        print(f"   Sincronizada: {'Sí' if parcela.eosda_sincronizada else 'No'}")
        if parcela.eosda_field_id:
            print(f"   Field ID actual: {parcela.eosda_field_id}")
    except Parcela.DoesNotExist:
        print("\n❌ Parcela 11 no encontrada")
        return
    
    # Resetear sincronización si existe
    if parcela.eosda_sincronizada:
        print(f"\n⚠️  Reseteando sincronización previa...")
        parcela.eosda_sincronizada = False
        parcela.eosda_field_id = None
        parcela.save()
        print(f"   ✅ Reset completado")
    
    # Intentar sincronizar
    print("\n" + "="*80)
    print("  🔄 INICIANDO SINCRONIZACIÓN")
    print("="*80)
    
    resultado = eosda_service.sincronizar_parcela_con_eosda(parcela)
    
    print("\n" + "="*80)
    print("  📊 RESULTADO")
    print("="*80)
    
    if resultado['exito']:
        print(f"\n✅ SINCRONIZACIÓN EXITOSA!")
        print(f"   Field ID: {resultado['field_id']}")
        print(f"   Mensaje: {resultado.get('mensaje', 'N/A')}")
        
        if resultado.get('field_compartido'):
            print(f"\n   ℹ️  NOTA: Se está usando un field existente porque el API key")
            print(f"       no tiene permisos para crear nuevos fields.")
        
        # Recargar parcela para ver cambios
        parcela.refresh_from_db()
        print(f"\n   Estado de la parcela:")
        print(f"   - Sincronizada: {parcela.eosda_sincronizada}")
        print(f"   - Field ID: {parcela.eosda_field_id}")
        print(f"   - Nombre campo EOSDA: {parcela.eosda_nombre_campo}")
        
    else:
        print(f"\n❌ ERROR EN SINCRONIZACIÓN")
        print(f"   Error: {resultado.get('error', 'Desconocido')}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
