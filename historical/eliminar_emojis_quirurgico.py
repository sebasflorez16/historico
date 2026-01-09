#!/usr/bin/env python3
"""
Script quirúrgico para eliminar SOLO emojis visuales, preservando toda la lógica
"""
import re

def eliminar_emojis_preservando_logica(texto):
    """Elimina emojis pero preserva toda la estructura del código"""
    
    # Patrón para emojis comunes en strings
    emojis_pattern = re.compile(
        "["
        "\U0001F300-\U0001F9FF"  # Emojis varios
        "\U0001F600-\U0001F64F"  # Emoticones
        "\U0001F680-\U0001F6FF"  # Transporte y símbolos
        "\U0001F1E0-\U0001F1FF"  # Banderas
        "\U00002600-\U000027BF"  # Símbolos varios
        "\U0000FE00-\U0000FE0F"  # Selectores de variación
        "\U00002700-\U000027BF"  # Dingbats
        "\U0000231A-\U0000231B"  # Relojes
        "\U000023E9-\U000023FA"  # Símbolos AV
        "\U000025AA-\U000025AB"  # Cuadrados
        "\U000025B6-\U000025C0"  # Triángulos
        "\U000025FB-\U000025FE"  # Cuadrados blancos/negros
        "\U00002B50"              # Estrella
        "\U0001F004"              # Mahjong
        "\U0001F0CF"              # Joker
        "\U0001F170-\U0001F251"  # Símbolos encerrados
        "]+", flags=re.UNICODE
    )
    
    # Solo eliminar en strings, no en comentarios técnicos
    lineas = texto.split('\n')
    resultado = []
    
    for linea in lineas:
        # Si es un string (contiene comillas), eliminar emojis
        if '"' in linea or "'" in linea:
            linea = emojis_pattern.sub('', linea)
        resultado.append(linea)
    
    return '\n'.join(resultado)

# Leer archivo
with open('informes/generador_pdf.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Aplicar limpieza quirúrgica
contenido_limpio = eliminar_emojis_preservando_logica(contenido)

# Guardar
with open('informes/generador_pdf.py', 'w', encoding='utf-8') as f:
    f.write(contenido_limpio)

print("Emojis eliminados de forma quirúrgica")
