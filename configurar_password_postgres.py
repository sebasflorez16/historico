#!/usr/bin/env python
"""
Script interactivo para probar y configurar la conexión a PostgreSQL.
"""

import psycopg2
from psycopg2 import OperationalError
import os
import sys

def test_connection_with_password(password):
    """Prueba la conexión con una contraseña específica."""
    try:
        conn = psycopg2.connect(
            dbname='historical',
            user='postgres',
            password=password,
            host='localhost',
            port='5432'
        )
        cursor = conn.cursor()
        
        # Verificar parcela 6
        cursor.execute("""
            SELECT id, nombre, area_hectareas, tipo_cultivo 
            FROM informes_parcela 
            WHERE id = 6;
        """)
        parcela = cursor.fetchone()
        
        # Contar índices con imágenes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM informes_indicemensual 
            WHERE parcela_id = 6 
            AND imagen_ndvi IS NOT NULL;
        """)
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return True, parcela, count
    except OperationalError as e:
        return False, None, str(e)

def update_env_file(password):
    """Actualiza el archivo .env con la contraseña correcta."""
    env_path = '/Users/sebasflorez16/Documents/AgroTech Historico/.env'
    
    # Leer contenido existente o crear nuevo
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Actualizar o agregar DATABASE_PASSWORD
    password_found = False
    for i, line in enumerate(lines):
        if line.startswith('DATABASE_PASSWORD='):
            lines[i] = f'DATABASE_PASSWORD={password}\n'
            password_found = True
            break
    
    if not password_found:
        lines.append(f'DATABASE_PASSWORD={password}\n')
    
    # Escribir archivo
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Archivo .env actualizado en: {env_path}")

def main():
    print("🔐 Configuración de Contraseña PostgreSQL")
    print("=" * 60)
    
    # Solicitar contraseña
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(f"🔑 Usando contraseña del argumento: {'*' * len(password)}")
    else:
        print("\n💡 Por favor, ingresa la contraseña que usas en pgAdmin:")
        password = input("Contraseña: ").strip()
    
    print(f"\n🔍 Probando conexión a PostgreSQL...")
    success, parcela_data, count = test_connection_with_password(password)
    
    if success:
        print(f"\n{'='*60}")
        print(f"✅ ¡CONEXIÓN EXITOSA!")
        print(f"{'='*60}")
        
        if parcela_data:
            print(f"\n📍 Parcela 6 encontrada:")
            print(f"   • ID: {parcela_data[0]}")
            print(f"   • Nombre: {parcela_data[1]}")
            print(f"   • Área: {parcela_data[2]} ha")
            print(f"   • Cultivo: {parcela_data[3]}")
            print(f"\n📊 Índices con imágenes NDVI: {count}")
        else:
            print(f"\n⚠️  Parcela 6 no encontrada en la base de datos")
        
        # Actualizar .env
        print(f"\n🔧 ¿Actualizar archivo .env con esta contraseña? (s/n): ", end='')
        response = input().strip().lower()
        
        if response == 's':
            update_env_file(password)
            print(f"\n✅ Configuración completada")
            print(f"\n🚀 Ahora puedes ejecutar:")
            print(f"   python manage.py runserver")
        else:
            print(f"\n💡 Para actualizar manualmente, agrega a .env:")
            print(f"   DATABASE_PASSWORD={password}")
        
        return True
    else:
        print(f"\n{'='*60}")
        print(f"❌ Falló la conexión")
        print(f"{'='*60}")
        print(f"\nError: {count}")
        print(f"\n💡 Verifica:")
        print(f"   1. La contraseña en pgAdmin")
        print(f"   2. Que PostgreSQL esté ejecutándose")
        print(f"   3. Que la base de datos 'historical' exista")
        
        return False

if __name__ == "__main__":
    main()
