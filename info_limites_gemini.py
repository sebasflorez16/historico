#!/usr/bin/env python3
"""
Verificar límites de modelos Gemini - Free Tier
Según la documentación:
- gemini-2.5-flash: 20 req/día (free tier)
- gemini-2.0-flash: potencialmente más cuota
- gemini-flash-latest: alias al último
"""

print("""
🔍 LÍMITES DE MODELOS GEMINI - FREE TIER
========================================

Según documentación oficial de Google AI:
https://ai.google.dev/gemini-api/docs/models/gemini#model-variations

TIER GRATUITO (FREE):
- gemini-2.5-flash: 20 solicitudes/día ❌
- gemini-2.5-flash-lite: 20 solicitudes/día ❌  
- gemini-2.0-flash: 1,500 solicitudes/día ✅
- gemini-flash-latest: Depende de la versión actual

RECOMENDACIÓN:
===============
Usar gemini-2.0-flash para FREE TIER
- 1,500 solicitudes/día
- 15 solicitudes/minuto
- 1M input tokens
- 8K output tokens

ALTERNATIVA:
============
Si necesitas más tokens de salida:
- Considerar upgrade a plan de pago
- O usar múltiples llamadas para análisis largos

ACCIÓN REQUERIDA:
=================
Cambiar el modelo en gemini_service.py:
    self.model = genai.GenerativeModel('gemini-2.0-flash')
""")
