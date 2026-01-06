#!/usr/bin/env python3
"""
Listar modelos disponibles de Gemini
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar .env
load_dotenv()

# Configurar API
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("🔍 Modelos de Gemini disponibles:")
print("=" * 80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n✅ {model.name}")
        print(f"   - Display name: {model.display_name}")
        print(f"   - Description: {model.description}")
        print(f"   - Input token limit: {model.input_token_limit}")
        print(f"   - Output token limit: {model.output_token_limit}")
        print(f"   - Supported methods: {model.supported_generation_methods}")
