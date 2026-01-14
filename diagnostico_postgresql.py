"""
Script para verificar la configuración completa de PostgreSQL y la tabla
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings')
django.setup()

from django.db import connection
from informes.models_clientes import ClienteInvitacion

print("=" * 60)
print("🔍 DIAGNÓSTICO COMPLETO DE BASE DE DATOS POSTGRESQL")
print("=" * 60)

# 1. Verificar conexión
print("\n1️⃣ Conexión a PostgreSQL:")
with connection.cursor() as cursor:
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"   ✅ PostgreSQL conectado: {version.split(',')[0]}")
    
    cursor.execute("SELECT current_database();")
    db_name = cursor.fetchone()[0]
    print(f"   ✅ Base de datos: {db_name}")

# 2. Verificar estructura de tabla
print("\n2️⃣ Estructura de tabla 'informes_clienteinvitacion':")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name='informes_clienteinvitacion'
        AND column_name IN ('moneda', 'costo_servicio', 'pagado')
        ORDER BY ordinal_position
    """)
    
    for row in cursor.fetchall():
        col_name, data_type, nullable, default = row
        print(f"   ✅ {col_name:20s} | Tipo: {data_type:15s} | Nullable: {nullable} | Default: {default or 'N/A'}")

# 3. Verificar modelo Django
print("\n3️⃣ Modelo Django ClienteInvitacion:")
try:
    # Verificar que podemos acceder al campo
    fields = [f.name for f in ClienteInvitacion._meta.get_fields()]
    if 'moneda' in fields:
        print(f"   ✅ Campo 'moneda' existe en el modelo Django")
    
    # Intentar hacer una query
    count = ClienteInvitacion.objects.all().count()
    print(f"   ✅ Query exitosa: {count} invitaciones en la BD")
    
    # Intentar crear un objeto (sin guardarlo)
    test_obj = ClienteInvitacion(
        token="TEST123",
        nombre_cliente="Test",
        moneda="COP"
    )
    print(f"   ✅ Instancia de prueba creada: moneda={test_obj.moneda}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Verificar índices y constraints
print("\n4️⃣ Constraints y defaults de PostgreSQL:")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT 
            conname as constraint_name,
            contype as constraint_type
        FROM pg_constraint
        WHERE conrelid = 'informes_clienteinvitacion'::regclass
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"   ✅ {row[0]}")

print("\n" + "=" * 60)
print("✅ DIAGNÓSTICO COMPLETADO")
print("=" * 60)
