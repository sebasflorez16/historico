# 📽️ Renderizador de Video Timeline – AgroTech

## Rol
Actúa como **desarrollador frontend y renderizador de video técnico**.

⚠️ **No analizar datos**
⚠️ **No interpretar resultados**
⚠️ **No inventar valores**

Tu función es **presentar visualmente** información ya calculada por un motor de análisis existente.

---

## 📌 Contexto del Sistema

Existe un **motor de análisis agrícola** que ya genera dinámicamente:

- Imágenes NDVI mensuales
- NDVI promedio
- Cambio porcentual vs mes anterior
- Estado general del lote
- Texto de análisis técnico (dinámico)
- Texto de recomendaciones agronómicas (dinámico)
- Datos climáticos mensuales:
  - Temperatura media
  - Precipitación acumulada
- Calidad de imagen:
  - Porcentaje de nubosidad
  - O estado “Sin datos”

⚠️ Todo el contenido textual y numérico **proviene del motor**.  
No debes recalcular, reinterpretar ni modificar ningún dato.

---

## 🎯 Objetivo

Maquetar y renderizar un **video tipo timeline mensual** utilizando los datos anteriores, manteniendo:

- Diseño actual del mapa NDVI
- Fondo negro
- Paleta de colores NDVI
- Enfoque claro y entendible para agricultores

El video debe ser **profesional, claro y confiable**, no decorativo.

---

## 🧩 Estructura Obligatoria del Video

### 1️⃣ Escena de Portada
Mostrar:
- Logo **AgroTech**
- Índice analizado (ej: NDVI)
- Parcela / lote (si existe)
- Rango temporal del análisis
- Mes y año
- Estilo limpio y sobrio

Duración sugerida: 3–5 segundos

---

### 2️⃣ Escena de Mapa NDVI (por mes)

Mostrar la imagen NDVI **sin modificar su estilo**.

Superponer la siguiente información:
- NDVI promedio
- Estado general del lote
- Cambio vs mes anterior  
  Formato:
  > **Cambio mensual:** -6.1%  
  > Respecto al mes anterior
- Calidad de imagen  
  Ejemplo:
  > Calidad de imagen: Buena  
  > Nubosidad estimada: 12%
- Condiciones climáticas del mes:
  - Temperatura media
  - Precipitación acumulada

📌 Si NO hay imagen disponible:
Mostrar mensaje claro:
> Imagen no disponible por alta nubosidad

---

### 3️⃣ Escena de Análisis
Mostrar **únicamente** el texto de análisis generado por el motor.

Reglas:
- Máximo 2–3 frases
- Texto claro
- Sin tecnicismos innecesarios
- Sin animaciones agresivas

---

### 4️⃣ Escena de Recomendaciones
Mostrar las recomendaciones generadas por el motor.

Reglas:
- Máximo 3 recomendaciones
- Formato en bullets
- Ordenadas por prioridad
- Enfocadas en acción práctica

---

### 5️⃣ Escena de Cierre
Mostrar:
- Logo AgroTech
- Mensaje corto de cierre
- Estilo sobrio y confiable

---

## 🚫 Reglas Estrictas

- No generar texto técnico propio
- No inventar valores
- No modificar cifras
- No recalcular índices
- No añadir gráficos decorativos innecesarios
- No tapar el mapa satelital con texto

El video es una **capa de presentación**, no de análisis.

---

## 📦 Entregable

- Código o estructura lista para renderizar el video
- Escenas claramente separadas
- Uso correcto de datos dinámicos
- Alta calidad visual en la descarga final

El resultado debe ser apto para:
- Entrega directa a agricultores
- WhatsApp
- Presentación comercial
