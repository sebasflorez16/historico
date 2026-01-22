# AgroTech Histórico 🌾

Sistema Django avanzado para análisis satelital agrícola con **Memoria Histórica** y **Análisis Temporal Pixel-por-Píxel**.

## 🚀 NUEVO (Enero 2026): Motor de Análisis Temporal

El sistema implementa tecnología de **Data Cubes 3D** para análisis temporal persistente:

- **📦 Data Cubes 3D**: Arrays temporales `[Meses, Latitud, Longitud]` optimizados con `np.float32`
- **🧠 Índice de Estrés Acumulado (IEA)**: Suma vectorizada de crisis por píxel
- **🏥 Memoria de Crisis**: Detección de meses históricos con problemas críticos
- **🎯 Cicatrices Permanentes**: Marcado de píxeles con estrés extremo (NDMI < -0.1)
- **📊 Penalización Histórica**: Eficiencia ajustada por crisis pasadas
- **⚡ Operaciones Vectorizadas**: Procesamiento instantáneo de millones de píxeles

### REGLA DE ORO
> **Si hubo crisis históricas, la eficiencia NUNCA puede ser 100%, aunque el lote esté verde hoy.**

Ver documentación completa: [docs/RESUMEN_TECNICO_ARQUITECTURA_DIAGNOSTICO.md](docs/RESUMEN_TECNICO_ARQUITECTURA_DIAGNOSTICO.md)

## ⚠️ IMPORTANTE: Generación de Informes PDF

**ÚNICO generador oficial:**
- **Archivo:** `informes/generador_pdf.py`
- **Clase:** `GeneradorPDFProfesional`
- **Motor:** `informes/motor_analisis/cerebro_diagnostico.py`
- **Documentación:** Ver `docs/FLUJO_GENERACION_INFORMES_PDF.md`

❌ **NO USAR:** `informes/services/generador_pdf_OBSOLETO_NO_USAR.py`

## 🌱 Características Principales

- **🛰️ Integración EOSDA**: Obtención automática de datos satelitales (NDVI, NDMI, SAVI)
- **🗺️ PostGIS Nativo**: Campos geoespaciales optimizados para consultas ultra-rápidas
- **📊 Análisis Temporal 3D**: Procesamiento píxel-por-píxel con Data Cubes
- **🧠 Motor de Diagnóstico**: Triangulación multi-índice con OpenCV
- **🏥 Memoria de Crisis**: Sistema que recuerda problemas históricos
- **📄 Informes PDF**: Generación automática con análisis IA local
- **🗺️ Mapas Georeferenciados**: Coordenadas GPS + zonas de intervención
- **🤖 IA Local**: Recomendaciones agronómicas basadas en umbrales científicos
- **📱 Interfaz Responsiva**: Dashboard moderno con Bootstrap 5
- **⚡ Optimizado para Railway**: float32, limpieza automática de archivos

## 📁 Estructura del Proyecto

```
historico/
├── informes/                           # Aplicación principal Django
│   ├── models.py                       # Modelos con PostGIS
│   ├── views.py                        # Vistas y lógica de negocio
│   ├── generador_pdf.py                # ✅ Generador oficial de PDFs
│   ├── motor_analisis/                 # 🧠 Motor de diagnóstico
│   │   ├── cerebro_diagnostico.py      # Análisis multi-índice + Data Cubes
│   │   ├── kpis_unificados.py          # KPIs con formateo estándar
│   │   └── mascara_cultivo.py          # Generación de máscaras PostGIS
│   ├── services/                       # Servicios externos
│   │   ├── eosda_api.py                # Integración EOSDA
│   │   ├── openmeteo_weather.py        # Datos climáticos
│   │   └── email_service.py            # Envío de emails
│   ├── analizadores/                   # Analizadores de índices
│   └── templates/                      # Templates HTML
├── tests/                              # 🧪 Pruebas de integración
│   ├── test_honestidad_sistema.py      # ✅ Test crítico pre-deploy
│   └── ...
├── docs/                               # 📚 Documentación completa
│   ├── RESUMEN_TECNICO_ARQUITECTURA_DIAGNOSTICO.md  # 📖 Arquitectura
│   ├── FLUJO_GENERACION_INFORMES_PDF.md
│   └── ...
├── media/                              # Archivos generados (auto-limpieza)
├── static/                             # Archivos estáticos
├── buscar_parcela_y_generar_informe.py # 🖥️  Entry point CLI
└── manage.py                           # Django management
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

### 🖥️ Interfaz Web
Acceda a `http://localhost:8000` para:
- **Dashboard**: Estadísticas y estado del sistema
- **Parcelas**: Crear con polígonos PostGIS dinámicos
- **Datos Históricos**: Obtener desde EOSDA (automático)
- **Informes PDF**: Generación con análisis temporal

### 💻 Línea de Comandos (CLI)

```bash
# Generar informe para la parcela con más datos
python buscar_parcela_y_generar_informe.py

# Generar informe para parcela específica
python buscar_parcela_y_generar_informe.py 5

# Listar parcelas disponibles
python buscar_parcela_y_generar_informe.py --list
```

**Características CLI:**
- ✅ Usa el mismo motor que la web (Data Cubes 3D)
- ✅ Totalmente dinámico (sin hardcoded paths)
- ✅ Limpieza automática de archivos temporales
- ✅ Optimizado para Railway (np.float32)

### 🧪 Test de Integridad (Pre-Deploy)

```bash
# Ejecutar test de honestidad del sistema
python tests/test_honestidad_sistema.py
```

**Este test debe pasar antes de cada despliegue.**

Valida:
- ✅ Detección de crisis históricas
- ✅ Cálculo de IEA (Índice de Estrés Acumulado)
- ✅ Marcado de cicatrices permanentes
- ✅ Penalización correcta de eficiencia

**Si el test falla, el despliegue debe detenerse.**

## 🚀 Despliegue a Railway

### Pre-requisitos
1. Cuenta en [Railway.app](https://railway.app)
2. PostgreSQL con PostGIS habilitado
3. Test de honestidad aprobado

### Pasos

```bash
# 1. Ejecutar test de integridad
python tests/test_honestidad_sistema.py

# 2. Si pasa, hacer commit
git add .
git commit -m "feat: Motor de Análisis Temporal con Data Cubes 3D e IEA

- Implementado sistema de Memoria de Crisis Históricas
- Análisis píxel-por-píxel con operaciones vectorizadas NumPy
- Índice de Estrés Acumulado (IEA) con detección de cicatrices
- Penalización de eficiencia por crisis pasadas (REGLA: < 100%)
- Optimización RAM: np.float32 en Data Cubes
- Limpieza automática de archivos temporales
- Entry points unificados (CLI + Web)
- Test de honestidad como gate de despliegue

BREAKING: Sistema ahora requiere análisis temporal completo.
Eficiencia 100% solo si NO hubo crisis históricas."

# 3. Push a Railway
git push railway main

# 4. Verificar logs
railway logs
```

### Variables de Entorno (Railway)

```env
# Base de datos
DATABASE_URL=postgresql://...  # Railway auto-provee

# EOSDA API
EOSDA_API_KEY=your_token_here

# Django
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=your-app.up.railway.app

# Optimizaciones
DJANGO_SETTINGS_MODULE=agrotech_historico.settings_production
```

## 🔧 Optimizaciones para Producción

### Memoria RAM
- **Data Cubes**: `np.float32` (50% menos RAM que float64)
- **Limpieza automática**: Archivos > 7 días eliminados
- **Compresión**: Mapas PNG optimizados

### Rendimiento
- **Operaciones vectorizadas**: NumPy sin bucles Python
- **PostGIS**: Consultas espaciales nativas
- **Caché**: Índices mensuales pre-calculados

### Seguridad
- **Test pre-deploy**: Gate automático
- **Validación matemática**: Coherencia eficiencia/área
- **Logs**: Registro completo de operaciones

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