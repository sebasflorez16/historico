#!/usr/bin/env python3
"""
Verificar capas disponibles en servicio REST IGAC
"""
import requests
import json

URL_BASE = "https://mapas2.igac.gov.co/server/rest/services/carto/carto100000colombia2019/MapServer"

def listar_capas():
    """Listar todas las capas del servicio"""
    print("🔍 Consultando servicio REST IGAC...")
    print(f"   URL: {URL_BASE}")
    
    try:
        # Consultar info del servicio
        response = requests.get(f"{URL_BASE}?f=json", timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n✅ Servicio disponible: {data.get('serviceDescription', 'N/A')}")
        print(f"   Versión: {data.get('currentVersion', 'N/A')}")
        print(f"   Máx escala: {data.get('maxScale', 'N/A')}")
        print(f"   Min escala: {data.get('minScale', 'N/A')}")
        
        # Listar capas
        capas = data.get('layers', [])
        print(f"\n📂 Capas disponibles: {len(capas)}")
        print("=" * 80)
        
        # Buscar capas de hidrografía
        capas_hidro = []
        
        for capa in capas:
            id_capa = capa.get('id')
            nombre = capa.get('name', '')
            tipo_geom = capa.get('geometryType', '')
            
            # Marcar capas de hidrografía
            es_hidro = any(term in nombre.lower() for term in [
                'drenaje', 'hidro', 'rio', 'quebrada', 'corriente', 'agua'
            ])
            
            marcador = "🌊" if es_hidro else "  "
            tipo_corto = tipo_geom.replace('esriGeometry', '')
            
            print(f"{marcador} [{id_capa:3d}] {nombre:50s} ({tipo_corto})")
            
            if es_hidro:
                capas_hidro.append({
                    'id': id_capa,
                    'nombre': nombre,
                    'tipo': tipo_geom
                })
        
        # Resumen de capas de hidrografía
        if capas_hidro:
            print("\n" + "=" * 80)
            print("🎯 CAPAS DE HIDROGRAFÍA ENCONTRADAS:")
            print("=" * 80)
            
            for capa in capas_hidro:
                print(f"\n📍 ID: {capa['id']}")
                print(f"   Nombre: {capa['nombre']}")
                print(f"   Geometría: {capa['tipo']}")
                
                # Verificar si es LineString
                if 'Polyline' in capa['tipo']:
                    print(f"   ✅ CORRECTO - Es LineString (Polyline)")
                elif 'Polygon' in capa['tipo']:
                    print(f"   ⚠️  Es Polygon - NO es lo que necesitamos")
                
                # URL para descargar
                url_descarga = f"{URL_BASE}/{capa['id']}/query?where=1%3D1&outFields=*&f=geojson"
                print(f"   🔗 URL descarga: {url_descarga}")
        else:
            print("\n⚠️ No se encontraron capas de hidrografía con nombres obvios")
            print("   Revisa la lista completa arriba")
        
        return capas_hidro
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error de conexión: {e}")
        return []
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return []

def verificar_capa_especifica(id_capa):
    """Verificar detalles de una capa específica"""
    print(f"\n🔍 Verificando capa {id_capa}...")
    
    try:
        url = f"{URL_BASE}/{id_capa}?f=json"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n   Nombre: {data.get('name')}")
        print(f"   Tipo: {data.get('geometryType')}")
        print(f"   Descripción: {data.get('description', 'N/A')}")
        
        # Campos
        campos = data.get('fields', [])
        print(f"\n   Campos ({len(campos)}):")
        for campo in campos[:10]:  # Primeros 10
            print(f"   - {campo.get('name')}: {campo.get('type')}")
        
        # Contar features
        url_count = f"{URL_BASE}/{id_capa}/query?where=1%3D1&returnCountOnly=true&f=json"
        resp_count = requests.get(url_count, timeout=30)
        count_data = resp_count.json()
        print(f"\n   Total features: {count_data.get('count', 'N/A'):,}")
        
        return data
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("🗺️  VERIFICADOR DE SERVICIO REST IGAC")
    print("=" * 80)
    
    capas_hidro = listar_capas()
    
    print("\n" + "=" * 80)
    print("💡 SIGUIENTE PASO:")
    print("=" * 80)
    
    if capas_hidro:
        # Buscar la mejor capa
        mejor_capa = None
        for capa in capas_hidro:
            if 'Polyline' in capa['tipo'] and 'sencillo' in capa['nombre'].lower():
                mejor_capa = capa
                break
        
        if not mejor_capa:
            for capa in capas_hidro:
                if 'Polyline' in capa['tipo']:
                    mejor_capa = capa
                    break
        
        if mejor_capa:
            print(f"\n✅ Usar capa ID {mejor_capa['id']}: {mejor_capa['nombre']}")
            print(f"\n📥 Para descargar esta capa, ejecuta:")
            print(f"   python descargar_capa_rest.py {mejor_capa['id']}")
        else:
            print("\n⚠️ Ninguna capa tiene geometría LineString/Polyline")
            print("   Revisa la lista y elige la capa correcta")
    else:
        print("\n💡 Revisa la lista completa de capas arriba")
        print("   Busca capas con 'Polyline' que contengan información de ríos/drenajes")
