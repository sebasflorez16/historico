# 🚀 Instrucciones de Despliegue a Producción Railway

**Fecha:** 22 de enero de 2026  
**Sistema:** AgroTech Histórico v2.0  
**Motor:** Análisis Temporal con Data Cubes 3D

---

## ⚠️ ESTADO ACTUAL DEL DESPLIEGUE

### ✅ COMPLETADO

1. **Test de Honestidad Creado** ([tests/test_honestidad_sistema.py](../tests/test_honestidad_sistema.py))
   - Valida detección de crisis históricas
   - Verifica cálculo de IEA
   - Comprueba cicatrices permanentes
   - Asegura penalización de eficiencia

2. **Entry Points Refactorizados**
   - CLI ([buscar_parcela_y_generar_informe.py](../buscar_parcela_y_generar_informe.py))
     - Dinamismo total (sin hardcoded paths)
     - Mismo motor que la web
     - Limpieza automática de archivos
   - Web ([informes/views.py](../informes/views.py#L2027))
     - Construcción de Data Cubes 3D
     - Detección de memoria de crisis

3. **Documentación Actualizada**
   - README.md con nueva arquitectura
   - RESUMEN_TECNICO_ARQUITECTURA_DIAGNOSTICO.md completo
   - Instrucciones de despliegue

4. **Optimizaciones Implementadas**
   - Uso de `np.float32` en Data Cubes (50% menos RAM)
   - Limpieza automática de archivos temporales (>7 días)
   - Operaciones vectorizadas NumPy

### 🔴 PENDIENTE (BLOQUEADOR)

**El sistema NO pasa el test de honestidad.**

**Razón:** La función `calcular_eficiencia_lote()` en `cerebro_diagnostico.py` y `generador_pdf.py` debe implementar la penalización por crisis históricas.

**Ubicaciones a modificar:**

1. `/informes/motor_analisis/cerebro_diagnostico.py` líneas 617-653
   - Implementar penalización: `(meses_crisis / total_meses) * 15`
   - Validar que eficiencia < 100% si hubo crisis

2. `/informes/generador_pdf.py` líneas 2180-2250
   - Pasar `crisis_historicas` al cerebro
   - Integrar data_cubes_temporales

---

## 📋 CHECKLIST DE DESPLIEGUE

### Fase 1: Validación Local

- [x] Test de honestidad creado
- [x] Entry points refactorizados (CLI + Web)
- [x] Limpieza automática implementada
- [x] README.md actualizado
- [ ] **Test de honestidad pasa (BLOQUEADOR)**
- [ ] Generar PDF de prueba local
- [ ] Validar tamaño de PDF < 1MB

### Fase 2: Implementación Pendiente

**CRÍTICO:** Estas modificaciones son OBLIGATORIAS para producción.

```python
# 1. Modificar cerebro_diagnostico.py (línea ~617)

def _calcular_eficiencia_lote(self, ndvi, savi, area_afectada, crisis_historicas=None):
    """
    Calcula eficiencia con penalización histórica
    
    Args:
        crisis_historicas: List de meses con crisis detectadas
    """
    # Eficiencia base
    if area_afectada <= 0.0:
        eficiencia_base = 100.0
    else:
        porcentaje_afectado = (area_afectada / self.area_parcela_ha) * 100.0
        eficiencia_base = max(0.0, 100.0 - porcentaje_afectado)
    
    # Penalización por crisis históricas
    penalizacion = 0.0
    if crisis_historicas and len(crisis_historicas) > 0:
        total_meses = 15  # Período típico de análisis
        meses_crisis = len(crisis_historicas)
        penalizacion = (meses_crisis / total_meses) * 15.0
        logger.info(f"⚠️ Penalización histórica: {penalizacion:.1f}% "
                   f"({meses_crisis} meses con crisis)")
    
    # Eficiencia final
    eficiencia_final = max(0.0, eficiencia_base - penalizacion)
    
    # VALIDACIÓN: Si hubo crisis, NO puede ser 100%
    if crisis_historicas and len(crisis_historicas) > 0:
        if eficiencia_final >= 100.0:
            eficiencia_final = min(eficiencia_final, 92.0)
            logger.warning("⚠️ Eficiencia ajustada a 92% por crisis históricas")
    
    return eficiencia_final
```

```python
# 2. Modificar generador_pdf.py (_ejecutar_diagnostico_cerebro)

# Pasar crisis_historicas al cerebro
diagnostico = ejecutar_diagnostico_unificado(
    datos_indices={'ndvi': array_2d, 'ndmi': array_2d, 'savi': array_2d},
    geo_transform=geo_transform,
    area_parcela_ha=parcela.area_hectareas,
    output_dir=output_dir,
    mascara_cultivo=mascara,
    geometria_parcela=parcela.geometria,
    crisis_historicas=crisis_detectadas,  # ✅ NUEVO
    data_cubes_temporales=data_cubes       # ✅ NUEVO
)
```

### Fase 3: Despliegue Railway

- [ ] Variables de entorno configuradas
- [ ] PostgreSQL + PostGIS activo
- [ ] Test de honestidad pasa
- [ ] Commit con mensaje claro
- [ ] Push a Railway
- [ ] Verificar logs de despliegue
- [ ] Prueba end-to-end en producción

---

## 🔑 Variables de Entorno Railway

```env
# Database (auto-provisto por Railway)
DATABASE_URL=postgresql://...

# Django
SECRET_KEY=your_production_secret_key
DEBUG=False
ALLOWED_HOSTS=your-app.up.railway.app,agrotechdigital.com
DJANGO_SETTINGS_MODULE=agrotech_historico.settings_production

# EOSDA API
EOSDA_API_KEY=your_eosda_token_here
EOSDA_BASE_URL=https://api.eosda.com

# Email (opcional)
EMAIL_HOST_USER=agrotechdigitalcolombia@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Optimizaciones
NUMPY_DTYPE=float32
MAX_DATA_CUBE_SIZE_MB=50
AUTO_CLEANUP_DAYS=7
```

---

## 📝 Mensaje de Commit Sugerido

```bash
git add .
git commit -m "feat: Motor de Análisis Temporal con Data Cubes 3D e IEA

IMPLEMENTADO:
- Sistema de Memoria de Crisis Históricas (detecta meses con problemas)
- Data Cubes 3D [Meses, Lat, Lon] con np.float32 (50% menos RAM)
- Índice de Estrés Acumulado (IEA) con operaciones vectorizadas
- Detección de Cicatrices Permanentes (NDMI < -0.1)
- Entry points unificados (CLI + Web usan mismo motor)
- Limpieza automática de archivos temporales (>7 días)
- Test de honestidad como gate de despliegue
- Documentación técnica completa

PENDIENTE (Siguiente PR):
- Integración completa de penalización histórica en cerebro
- Eficiencia ajustada por crisis pasadas (< 100% siempre)
- Data cubes temporales en ejecutar_diagnostico_unificado

BREAKING CHANGES:
- Sistema requiere análisis temporal completo
- Eficiencia 100% solo si NO hubo crisis históricas

Docs: docs/RESUMEN_TECNICO_ARQUITECTURA_DIAGNOSTICO.md
Test: python tests/test_honestidad_sistema.py
"
```

---

## 🧪 Comandos de Validación

```bash
# 1. Test de honestidad (DEBE PASAR)
python tests/test_honestidad_sistema.py

# 2. Generar PDF de prueba
python buscar_parcela_y_generar_informe.py

# 3. Verificar tamaño del PDF
ls -lh media/informes/*.pdf | tail -1

# 4. Revisar logs
tail -f logs/django.log

# 5. Verificar memoria (Railway)
railway run python -c "import numpy as np; cube = np.zeros((15,256,256), dtype=np.float32); print(f'{cube.nbytes / 1024 / 1024:.2f} MB')"
```

---

## 📊 Métricas de Producción Esperadas

| Métrica | Objetivo | Validación |
|---------|----------|------------|
| **Data Cube RAM** | < 5 MB por parcela | np.float32 × 3 índices |
| **PDF Size** | 500-1000 KB | Compresión PNG |
| **Generación PDF** | < 5 segundos | Railway 512MB RAM |
| **Limpieza automática** | Cada 7 días | Cron job / Signal |
| **Test honestidad** | 100% pass | Gate pre-deploy |

---

## ⚠️ ADVERTENCIAS IMPORTANTES

1. **NO DESPLEGAR** sin que el test de honestidad pase
2. **VALIDAR** que el PDF se genera correctamente en local
3. **VERIFICAR** que Railway tiene PostGIS habilitado
4. **CONFIRMAR** que EOSDA API key es válida
5. **PROBAR** limpieza automática en staging primero

---

## 🆘 Rollback Plan

Si algo falla en producción:

```bash
# 1. Revertir al commit anterior
git revert HEAD
git push railway main

# 2. O forzar versión anterior
railway rollback

# 3. Verificar logs
railway logs --tail 100

# 4. Validar BD
railway run python manage.py check
```

---

## 📞 Contacto de Emergencia

**Desarrollador:** AgroTech Engineering Team  
**Documentación:** [docs/](../docs/)  
**Issues:** GitHub Issues  
**Status:** Railway Dashboard

---

**Última actualización:** 22 de enero de 2026  
**Estado:** ⚠️ PENDIENTE - Test de honestidad debe pasar antes de deploy
