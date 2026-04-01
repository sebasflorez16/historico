import json
from pathlib import Path

BASE = Path("datos_geograficos")

# Resguardos vacío
resguardos_dir = BASE / "resguardos_indigenas"
resguardos_dir.mkdir(parents=True, exist_ok=True)

resguardos_geojson = {
    "type": "FeatureCollection",
    "features": []
}

with open(resguardos_dir / "resguardos_casanare.geojson", 'w') as f:
    json.dump(resguardos_geojson, f, indent=2)

print("✅ Resguardos: archivo vacío creado")

# Páramos vacío
paramos_dir = BASE / "paramos"
paramos_dir.mkdir(parents=True, exist_ok=True)

paramos_geojson = {
    "type": "FeatureCollection",
    "features": []
}

with open(paramos_dir / "paramos_casanare.geojson", 'w') as f:
    json.dump(paramos_geojson, f, indent=2)

print("✅ Páramos: archivo vacío creado")
print("\n📊 Capas para Casanare:")
print("   • RUNAP: ✅ 174 áreas protegidas")
print("   • Resguardos: ⚠️ 0 (pendiente descarga)")
print("   • Páramos: ✅ 0 (Casanare no tiene páramos)")
