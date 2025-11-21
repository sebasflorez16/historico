#!/usr/bin/env python
"""
Script de configuración para seleccionar base de datos
Permite elegir entre SQLite (desarrollo rápido) y PostgreSQL + PostGIS (producción)
"""

import os
import sys
import shutil
from pathlib import Path

def configurar_sqlite():
    """
    Configura el proyecto para usar SQLite (desarrollo rápido)
    """
    print("🗃️  Configurando SQLite...")
    
    # Asegurar que el archivo .env esté configurado para SQLite
    env_content = """# Configuración AgroTech Histórico - SQLite
EOSDA_API_KEY=demo_token_reemplazar_con_real
DATABASE_ENGINE=sqlite
DEBUG=True
SECRET_KEY=django-insecure-5u89m&zufi#-gy57+2_pe(m(srq@6s-*#$$vwq0((v8hw&-pjc
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Usar modelos estándar
    models_src = "informes/models.py"
    if os.path.exists(models_src):
        print("   ✅ Usando modelos estándar para SQLite")
    else:
        print("   ❌ Error: archivo models.py no encontrado")
        return False
    
    print("   ✅ SQLite configurado")
    print("   📝 Limitaciones: Sin optimizaciones geoespaciales avanzadas")
    print("   🚀 Ventajas: Setup inmediato, sin dependencias externas")
    return True

def configurar_postgresql():
    """
    Configura el proyecto para usar PostgreSQL + PostGIS
    """
    print("🐘 Configurando PostgreSQL + PostGIS...")
    
    # Verificar si PostgreSQL está disponible
    try:
        import psycopg2
        print("   ✅ Driver PostgreSQL disponible")
    except ImportError:
        print("   ❌ Driver PostgreSQL no encontrado")
        print("   📦 Instale con: pip install psycopg2-binary")
        return False
    
    # Configurar .env para PostgreSQL
    env_content = """# Configuración AgroTech Histórico - PostgreSQL + PostGIS
EOSDA_API_KEY=demo_token_reemplazar_con_real
DATABASE_ENGINE=postgresql
DATABASE_NAME=agrotech_historico
DATABASE_USER=agrotech_user
DATABASE_PASSWORD=agrotech_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
DEBUG=True
SECRET_KEY=django-insecure-5u89m&zufi#-gy57+2_pe(m(srq@6s-*#$$vwq0((v8hw&-pjc
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Reemplazar modelos con versión PostGIS
    if os.path.exists("informes/models_postgis.py"):
        if os.path.exists("informes/models_backup.py"):
            os.remove("informes/models_backup.py")
        
        # Backup del modelo actual
        shutil.copy2("informes/models.py", "informes/models_backup.py")
        
        # Reemplazar con versión PostGIS
        shutil.copy2("informes/models_postgis.py", "informes/models.py")
        
        print("   ✅ Modelos PostGIS activados")
        print("   💾 Backup guardado como models_backup.py")
    else:
        print("   ❌ Error: archivo models_postgis.py no encontrado")
        return False
    
    print("   ✅ PostgreSQL + PostGIS configurado")
    print("   🚀 Ventajas: Rendimiento geoespacial profesional")
    print("   📋 Siguiente: Crear base de datos (ver INSTALACION_POSTGRESQL.md)")
    return True

def verificar_conexion_postgresql():
    """
    Verifica si se puede conectar a PostgreSQL
    """
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv('DATABASE_HOST', 'localhost'),
            port=os.getenv('DATABASE_PORT', '5432'),
            user=os.getenv('DATABASE_USER', 'agrotech_user'),
            password=os.getenv('DATABASE_PASSWORD', 'agrotech_password'),
            database=os.getenv('DATABASE_NAME', 'agrotech_historico')
        )
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Error conectando a PostgreSQL: {e}")
        return False

def mostrar_estado_actual():
    """
    Muestra la configuración actual de la base de datos
    """
    print("\n📊 ESTADO ACTUAL")
    print("=" * 50)
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            if 'DATABASE_ENGINE=postgresql' in content:
                print("🐘 Base de datos: PostgreSQL + PostGIS")
                if verificar_conexion_postgresql():
                    print("✅ Conexión: Exitosa")
                else:
                    print("❌ Conexión: Error (verificar configuración)")
            else:
                print("🗃️  Base de datos: SQLite")
                if os.path.exists('db.sqlite3'):
                    print("✅ Archivo: db.sqlite3 existe")
                else:
                    print("⚠️  Archivo: db.sqlite3 no existe (ejecutar migrate)")
    else:
        print("❌ Archivo .env no encontrado")
    
    # Verificar modelos activos
    if os.path.exists('informes/models.py'):
        with open('informes/models.py', 'r') as f:
            content = f.read()
            if 'gis_models' in content:
                print("📐 Modelos: PostGIS (geoespaciales optimizados)")
            else:
                print("📝 Modelos: Estándar (compatibilidad básica)")

def menu_principal():
    """
    Menú principal para configuración de base de datos
    """
    while True:
        print("\n" + "="*60)
        print("🌱 AGROTECH HISTÓRICO - CONFIGURACIÓN DE BASE DE DATOS")
        print("="*60)
        
        mostrar_estado_actual()
        
        print("\nOpciones:")
        print("1. 🗃️  Configurar SQLite (desarrollo rápido)")
        print("2. 🐘 Configurar PostgreSQL + PostGIS (recomendado)")
        print("3. 📋 Ver guía de instalación PostgreSQL")
        print("4. 🔍 Verificar estado actual")
        print("5. 🚀 Ejecutar migraciones")
        print("0. ❌ Salir")
        print("-" * 60)
        
        try:
            opcion = input("Seleccione una opción: ").strip()
            
            if opcion == '0':
                print("👋 ¡Configuración finalizada!")
                break
            elif opcion == '1':
                if configurar_sqlite():
                    print("\n🎉 SQLite configurado exitosamente!")
                    print("💡 Ejecute: python manage.py migrate")
            elif opcion == '2':
                if configurar_postgresql():
                    print("\n🎉 PostgreSQL configurado!")
                    print("📖 Ver: INSTALACION_POSTGRESQL.md para crear la base de datos")
            elif opcion == '3':
                print("\n📖 Guía de instalación:")
                print("   Archivo: INSTALACION_POSTGRESQL.md")
                if os.path.exists("INSTALACION_POSTGRESQL.md"):
                    print("   📄 Guía disponible en el proyecto")
                else:
                    print("   ❌ Guía no encontrada")
            elif opcion == '4':
                # El estado se muestra al inicio del loop
                pass
            elif opcion == '5':
                print("\n🔄 Ejecutando migraciones...")
                os.system("python manage.py makemigrations")
                os.system("python manage.py migrate")
                print("✅ Migraciones completadas")
            else:
                print("❌ Opción no válida")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def main():
    """
    Función principal del script de configuración
    """
    print("🌱 Configurador de Base de Datos - AgroTech Histórico")
    print("🎯 Objetivo: Optimizar para datos geoespaciales")
    print()
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ Error: Ejecute este script desde el directorio del proyecto Django")
        sys.exit(1)
    
    # Si se pasa argumento, configurar automáticamente
    if len(sys.argv) > 1:
        if sys.argv[1] == '--sqlite':
            configurar_sqlite()
            return
        elif sys.argv[1] == '--postgresql':
            configurar_postgresql()
            return
        elif sys.argv[1] == '--estado':
            mostrar_estado_actual()
            return
    
    # Mostrar menú interactivo
    menu_principal()

if __name__ == '__main__':
    main()