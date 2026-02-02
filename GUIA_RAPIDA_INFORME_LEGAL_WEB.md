# 🚀 Guía Rápida: Generar Informe Legal desde la Web

**¿Qué hace?** Genera un PDF con verificación legal de restricciones ambientales para tu parcela.

---

## ⚡ Uso en 3 Pasos

### 1️⃣ Ir al Detalle de la Parcela

```
http://localhost:8000/parcelas/
```

Clic en "Ver Detalle" de la parcela deseada

---

### 2️⃣ Clic en "Informe Legal"

Buscar el botón verde:

```
⚖️ Informe Legal
```

---

### 3️⃣ ¡Listo! El PDF se descarga automáticamente

```
📥 informe_legal_Juan_Parcela2_20260202.pdf
```

---

## 📋 ¿Qué incluye el PDF?

### 🗺️ 3 Mapas Profesionales

✅ **Mapa 1:** Ubicación Departamental (con resguardos y áreas protegidas)  
✅ **Mapa 2:** Ubicación Municipal (con red hídrica y resguardos)  
✅ **Mapa 3:** Influencia Legal Directa (solo parcela + distancias a ríos)

### 📊 Análisis Legal

✅ Tabla de proximidad a elementos críticos  
✅ Distancias desde lindero (precisas según normativa)  
✅ Resumen ejecutivo con recomendaciones  
✅ Fuentes legales normativas (Ley 99/1993, etc.)

---

## 🔒 Requisitos

- ✅ Estar autenticado (login)
- ✅ Ser propietario de la parcela (o superusuario)
- ✅ Parcela debe tener geometría definida

---

## ⚠️ Si hay error

**"Parcela no tiene geometría"**  
→ Definir ubicación en el mapa primero

**"No tiene permisos"**  
→ Solo el propietario puede generar informes

**"Error generando PDF"**  
→ Contactar al administrador (revisar logs)

---

## 🎯 Ejemplo de Uso Real

```
1. Login: http://localhost:8000/accounts/login/
   Usuario: admin
   Password: ****

2. Parcelas: http://localhost:8000/parcelas/

3. Detalle: http://localhost:8000/parcelas/6/

4. Clic en: ⚖️ Informe Legal

5. Resultado: 📥 informe_legal_admin_Parcela_6_20260202.pdf
```

---

## 📞 Soporte

**Logs del sistema:**
```bash
tail -f agrotech.log | grep "informe legal"
```

**Verificar configuración:**
```bash
python manage.py check
```

**Test manual:**
```bash
python generar_pdf_legal_test.py
```

---

✅ **¡Eso es todo!** Simple, rápido y profesional.
