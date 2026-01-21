# AgroTech Histórico 🌾

Sistema Django completo para análisis satelital agrícola con integración EOSDA API, generación automática de informes PDF y mapas interactivos.

## ⚠️ IMPORTANTE: Generación de Informes PDF

**ÚNICO generador oficial:**
- **Archivo:** `informes/generador_pdf.py`
- **Clase:** `GeneradorPDFProfesional`
- **Documentación:** Ver `REGLAS_GENERADOR_PDF.md` y `docs/FLUJO_GENERACION_INFORMES_PDF.md`

❌ **NO USAR:** `informes/services/generador_pdf_OBSOLETO_NO_USAR.py`

## 🌱 Características Principales

- **🛰️ Integración EOSDA**: Obtención automática de datos satelitales (NDVI, NDMI, SAVI)
- **🗺️ PostGIS Nativo**: Campos geoespaciales optimizados para consultas ultra-rápidas
- **📊 Análisis Histórico**: Procesamiento de tendencias y patrones temporales
- **📄 Informes PDF**: Generación automática con gráficos y análisis IA local
- **🗺️ Mapas Interactivos**: Visualización geoespacial con Leaflet y folium
- **🤖 IA Local**: Análisis automático de salud vegetal y recomendaciones
- **📱 Interfaz Responsiva**: Dashboard moderno con Bootstrap 5
- **⚡ Rendimiento GIS**: PostgreSQL + PostGIS para datos geoespaciales masivos

## � Estructura del Proyecto

```
historical/
├── informes/              # Aplicación principal Django
│   ├── models.py          # Modelos con PostGIS
│   ├── views.py           # Vistas y lógica de negocio
│   ├── generador_pdf.py   # Generador de informes PDF
│   ├── services/          # Servicios (EOSDA, Weather, Email)
│   ├── analizadores/      # Analizadores de índices satelitales
│   └── templates/         # Templates HTML
├── tests/                 # 🧪 Scripts de prueba
├── scripts/               # 🔧 Scripts de utilidad y mantenimiento
├── docs/                  # 📚 Documentación completa
│   ├── sprints/          # Documentación de sprints
│   ├── sistema/          # Arquitectura del sistema
│   ├── frontend/         # Guías de diseño UI/UX
│   ├── correcciones/     # Guías de correcciones
│   └── instalacion/      # Guías de instalación
├── media/                 # Archivos generados (PDFs, imágenes)
├── static/                # Archivos estáticos
└── manage.py              # Django management

```

## 🚀 Instalación Rápida

### Requisitos Previos
- Python 3.11+
- PostgreSQL 15+ con PostGIS
- Git

### Instalación

```bash
# 1. Clonar y configurar
git clone <url-del-repo>
cd historical
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 4. Configurar base de datos
python scripts/configurar_db.py

# 5. Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Ejecutar servidor
python manage.py runserver
```

## 📚 Documentación

La documentación está organizada por categorías en la carpeta `docs/`:

- **📖 [Guía de Documentación](docs/README.md)** - Índice completo
- **🏗️ [Arquitectura del Sistema](docs/sistema/)** - Flujos y diseño técnico
- **🎨 [Guías de Frontend](docs/frontend/)** - Estilos y UI/UX
- **🔧 [Correcciones y Fixes](docs/correcciones/)** - Solución de problemas
- **📦 [Guías de Instalación](docs/instalacion/)** - PostgreSQL/PostGIS

### Documentos Destacados

- [FLUJO_IMAGENES_SATELITALES.md](docs/sistema/FLUJO_IMAGENES_SATELITALES.md) - Flujo completo de imágenes
- [SISTEMA_INFORMES_IMPLEMENTADO.md](docs/sistema/SISTEMA_INFORMES_IMPLEMENTADO.md) - Sistema de informes
- [INSTALACION_POSTGRESQL.md](docs/instalacion/INSTALACION_POSTGRESQL.md) - Setup de base de datos

## 🧪 Testing

Los tests están organizados en la carpeta `tests/`:

```bash
# Test de generación de informes
python tests/test_informe_simple.py

# Test de API EOSDA
python tests/test_eosda_febrero_2025.py

# Test de clima Open-Meteo
python tests/test_openmeteo.py
```

Ver [tests/README.md](tests/README.md) para más información.

## 🔧 Scripts de Utilidad

Scripts de mantenimiento y desarrollo en la carpeta `scripts/`:

```bash
# Actualizar datos climáticos
python scripts/actualizar_datos_clima_todas_parcelas.py

# Diagnóstico de datos
python scripts/diagnostico_datos_mensuales.py

# Limpiar datos
python scripts/limpiar_datos.py
```

Ver [scripts/README.md](scripts/README.md) para lista completa.

# Ubuntu  
sudo apt install postgresql postgresql-contrib postgis

# 2. Crear base de datos
psql postgres
CREATE USER agrotech_user WITH PASSWORD 'agrotech_password';
CREATE DATABASE agrotech_historico OWNER agrotech_user;
\c agrotech_historico
CREATE EXTENSION postgis;

# 3. Configurar proyecto
cd agrotech_historico
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Configurar .env para PostgreSQL
DATABASE_ENGINE=postgresql
DATABASE_NAME=agrotech_historico
DATABASE_USER=agrotech_user
DATABASE_PASSWORD=agrotech_password

# 5. Migrar y ejecutar
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

📖 **Guía completa PostGIS:** Ver `INSTALACION_POSTGRESQL.md`

## 🎯 Uso del Sistema

### Panel Principal
Acceda a `http://localhost:8000` para ver el dashboard principal con:
- Estadísticas generales del sistema
- Parcelas activas en monitoreo
- Estado de conectividad con EOSDA
- Acceso a todas las funcionalidades

### Gestión de Parcelas
1. **Crear Parcela**: Dibujar polígono en mapa interactivo
2. **Monitoreo**: Procesamiento automático de datos satelitales
3. **Análisis**: Visualización de tendencias NDVI, NDMI, SAVI

### Generación de Informes
- Informes automáticos PDF con análisis de 6, 12 o 24 meses
- Gráficos de tendencias temporales
- Mapas de salud vegetal
- Recomendaciones agronómicas IA

## 🔧 Configuración API EOSDA

### Obtener Token
1. Registrarse en [EOS Data Analytics](https://eos.com/eos-data-analytics/)
2. Obtener API token
3. Configurar en `.env`:
```env
EOSDA_API_KEY=su_token_aqui
```

### Modo Simulación
Si no tiene token EOSDA, el sistema genera datos simulados realistas para demostración.

## 📁 Estructura del Proyecto

```
agrotech_historico/
├── agrotech_historico/          # Configuración principal Django
│   ├── settings.py             # Configuración del proyecto
│   └── urls.py                 # URLs principales
├── informes/                   # Aplicación principal
│   ├── models.py               # Modelos de datos
│   ├── views.py                # Lógica de vistas
│   ├── urls.py                 # URLs de la app
│   ├── admin.py                # Configuración admin
│   └── services/               # Servicios del sistema
│       ├── eosda_api.py       # Integración EOSDA
│       ├── analisis_datos.py  # Procesamiento de datos
│       └── generador_pdf.py   # Generación de informes
├── templates/informes/         # Plantillas HTML
│   ├── base.html              # Plantilla base
│   ├── dashboard.html         # Panel principal
│   └── ...                    # Otras plantillas
├── static/                     # Archivos estáticos
├── media/                      # Archivos subidos
├── demo.py                     # Script de demostración
├── .env.example               # Ejemplo de configuración
└── requirements.txt           # Dependencias
```

## 🎮 Script de Demostración

El script `demo.py` incluye:

### Modo Interactivo
```bash
python demo.py
```
Menú con opciones para:
- Crear parcela de demo
- Procesar datos satelitales
- Generar informes PDF
- Ver estadísticas del sistema

### Modo Automático
```bash
python demo.py --auto
```
Ejecuta demostración completa automáticamente.

## 🛠️ Tecnologías Utilizadas

### **Base de Datos y Geoespacial**
- **PostgreSQL + PostGIS**: Campos geoespaciales nativos (RECOMENDADO)
- **SQLite**: Modo desarrollo rápido con limitaciones GIS
- **Django GIS**: Framework geoespacial integrado
- **GDAL/GEOS**: Bibliotecas de procesamiento geoespacial

### Frontend
- **Bootstrap 5**: Framework CSS responsivo
- **Leaflet**: Mapas interactivos
- **Chart.js**: Gráficos dinámicos
- **Font Awesome**: Iconografía

### Integración y Análisis
- **EOSDA API**: Datos satelitales reales
- **Matplotlib**: Generación de gráficos
- **Folium**: Mapas geoespaciales
- **ReportLab**: Generación de PDF

## 🌟 Características Técnicas

### Modelos de Datos
- **Parcela**: Gestión de terrenos con GeoJSON
- **IndiceMensual**: Almacenamiento de datos satelitales
- **Informe**: Análisis generados automáticamente
- **ConfiguracionAPI**: Gestión de APIs externas

### Servicios Principales
- **EosdaAPIService**: Comunicación con API de EOSDA
- **AnalisisSatelitalService**: Procesamiento de datos
- **GeneradorInformePDF**: Creación de informes

### Funcionalidades IA
- Análisis automático de tendencias
- Evaluación de salud vegetal
- Generación de recomendaciones agronómicas
- Resúmenes ejecutivos automatizados

## 🔒 Seguridad y Configuración

### Variables de Entorno
- `EOSDA_API_KEY`: Token de acceso a EOSDA
- `DEBUG`: Modo de desarrollo
- `SECRET_KEY`: Clave secreta de Django

### Configuración de Producción
Para despliegue en producción:
1. Configurar `DEBUG=False`
2. Usar base de datos PostgreSQL
3. Configurar servidor web (Nginx/Apache)
4. Implementar HTTPS
5. Configurar almacenamiento en la nube

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto es de código abierto. Consulte el archivo LICENSE para más detalles.

## 🆘 Soporte

### Problemas Comunes

**Error de base de datos**
```bash
python manage.py migrate
```

**Dependencias faltantes**
```bash
pip install -r requirements.txt
```

**Token EOSDA inválido**
- Verificar configuración en `.env`
- El sistema funciona en modo simulación sin token

### Contacto
- 📧 Email: soporte@agrotech.com
- 📞 Teléfono: +57 1 234 5678
- 🌐 Website: www.agrotech.com

## 🔄 Roadmap

### Versión 2.0
- [ ] API REST completa
- [ ] Aplicación móvil React Native
- [ ] Machine Learning avanzado
- [ ] Integración con drones
- [ ] Alertas automáticas por SMS/Email

### Mejoras Futuras
- [ ] Soporte multi-idioma
- [ ] Análisis de múltiples cultivos
- [ ] Integración con sensores IoT
- [ ] Dashboard de análisis predictivo
- [ ] Exportación a múltiples formatos

---

**AgroTech Histórico** - Sistema profesional de análisis satelital agrícola 🌱🛰️