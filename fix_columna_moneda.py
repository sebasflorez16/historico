"""
Script para agregar manualmente la columna 'moneda' que falta
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.db import connection

print("🔧 Agregando columna 'moneda' a la tabla informes_clienteinvitacion...")

try:
    with connection.cursor() as cursor:
        # Agregar la columna con un valor por defecto
        cursor.execute("""
            ALTER TABLE "informes_clienteinvitacion" 
            ADD COLUMN "moneda" varchar(3) DEFAULT 'COP' NOT NULL
        """)
        print("✅ Columna 'moneda' agregada exitosamente")
        
        # Verificar
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='informes_clienteinvitacion' AND column_name='moneda'
        """)
        
        if cursor.fetchone():
            print("✅ Verificación exitosa: la columna 'moneda' ahora existe")
        else:
            print("⚠️ Advertencia: no se pudo verificar la columna")
            
except Exception as e:
    if 'already exists' in str(e) or 'duplicate column' in str(e).lower():
        print("ℹ️ La columna 'moneda' ya existe (esto es normal si ya se ejecutó antes)")
    else:
        print(f"❌ Error: {e}")
        raise
