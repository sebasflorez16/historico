"""
Script para verificar si la columna 'moneda' existe en la tabla
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='informes_clienteinvitacion'
    ORDER BY ordinal_position
""")

columnas = [row[0] for row in cursor.fetchall()]
print("🔍 Columnas en informes_clienteinvitacion:")
for col in columnas:
    print(f"  - {col}")

if 'moneda' in columnas:
    print("\n✅ La columna 'moneda' EXISTE en la base de datos")
else:
    print("\n❌ La columna 'moneda' NO EXISTE - necesitamos aplicar la migración manualmente")
