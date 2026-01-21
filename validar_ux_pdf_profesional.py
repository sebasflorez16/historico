#!/usr/bin/env python
"""
Validador UX/UI para PDFs Profesionales de AgroTech
====================================================

Verifica que los PDFs generados cumplan con los estándares de diseño profesional:
- Terminología comercial (no técnica)
- Sin elementos visuales agresivos
- Layout compacto
- Narrativa en lenguaje de campo
"""

import sys
import os
import re
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("⚠️  PyPDF2 no instalado. Instalando...")
    os.system("pip install PyPDF2")
    import PyPDF2


class ValidadorUXPDF:
    """Validador de estándares UX para PDFs de AgroTech"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.issues = []
        self.warnings = []
        self.success = []
        
    def validar(self):
        """Ejecuta todas las validaciones"""
        if not self.pdf_path.exists():
            print(f"❌ Error: PDF no encontrado en {self.pdf_path}")
            return False
        
        print(f"📄 Validando PDF: {self.pdf_path.name}")
        print("=" * 70)
        
        # Extraer texto del PDF
        texto_completo = self._extraer_texto()
        
        # Ejecutar validaciones
        self._validar_terminologia(texto_completo)
        self._validar_elementos_visuales(texto_completo)
        self._validar_estructura(texto_completo)
        self._validar_compactacion()
        self._validar_narrativa(texto_completo)
        
        # Mostrar resultados
        self._mostrar_resultados()
        
        return len(self.issues) == 0
    
    def _extraer_texto(self) -> str:
        """Extrae todo el texto del PDF"""
        try:
            with open(self.pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                texto = ""
                for page in pdf.pages:
                    texto += page.extract_text()
                return texto
        except Exception as e:
            self.issues.append(f"Error leyendo PDF: {e}")
            return ""
    
    def _validar_terminologia(self, texto: str):
        """Valida que se use terminología comercial profesional"""
        print("\n🔤 Validando terminología...")
        
        # Checks negativos (terminología técnica agresiva)
        if re.search(r'\!\!', texto):
            self.issues.append("Encontrado '!!' - usar iconos suaves (✓, ⚠, ●)")
        else:
            self.success.append("Sin signos de exclamación dobles agresivos")
        
        if "CRÍTICO" in texto and "ESTADO:" not in texto:
            self.warnings.append("Palabra 'CRÍTICO' sin contexto - verificar si es apropiado")
        
        # Checks positivos (terminología profesional)
        if "REQUIERE ATENCIÓN" in texto or "Requiere Atención" in texto:
            self.success.append("Terminología profesional: 'REQUIERE ATENCIÓN'")
        
        if "Nivel de Prioridad" in texto or "Prioridad Alta" in texto:
            self.success.append("Terminología comercial en tabla de severidad")
        else:
            self.warnings.append("No se encontró 'Nivel de Prioridad' - verificar tabla")
        
        if "ESTADO DEL CULTIVO" in texto:
            self.success.append("Banner ejecutivo con terminología apropiada")
    
    def _validar_elementos_visuales(self, texto: str):
        """Valida elementos visuales (iconos, emojis, etc.)"""
        print("\n🎨 Validando elementos visuales...")
        
        # Contar emojis problemáticos
        emojis_problematicos = ['🔴', '🟠', '🟡', '⚠️', '❗']
        emojis_encontrados = sum(1 for emoji in emojis_problematicos if emoji in texto)
        
        if emojis_encontrados > 5:
            self.warnings.append(f"Muchos emojis ({emojis_encontrados}) - considerar iconos ● en su lugar")
        else:
            self.success.append("Uso moderado de emojis/iconos")
        
        # Verificar iconos profesionales
        if "●" in texto:
            self.success.append("Uso de iconos profesionales (●)")
        
        if "✓" in texto:
            self.success.append("Uso de checkmarks profesionales (✓)")
    
    def _validar_estructura(self, texto: str):
        """Valida estructura del documento"""
        print("\n📋 Validando estructura...")
        
        # Verificar secciones clave
        secciones_requeridas = [
            ("DIAGNÓSTICO DETALLADO", "Sección de diagnóstico detallado"),
            ("ANEXOS TÉCNICOS", "Anexos técnicos"),
            ("Eficiencia", "Métrica de eficiencia")
        ]
        
        for patron, nombre in secciones_requeridas:
            if patron in texto:
                self.success.append(f"Sección encontrada: {nombre}")
            else:
                self.warnings.append(f"Sección no encontrada: {nombre}")
        
        # Verificar que diagnóstico esté al final (no al inicio)
        idx_diagnostico = texto.find("DIAGNÓSTICO DETALLADO")
        idx_anexos = texto.find("ANEXOS TÉCNICOS")
        
        if idx_diagnostico > idx_anexos and idx_anexos > 0:
            self.success.append("Diagnóstico correctamente ubicado al final")
        else:
            self.warnings.append("Verificar ubicación del diagnóstico (debe estar al final)")
    
    def _validar_compactacion(self):
        """Valida que el documento sea compacto"""
        print("\n📏 Validando compactación...")
        
        try:
            with open(self.pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                num_paginas = len(pdf.pages)
                
                if num_paginas > 20:
                    self.issues.append(f"Documento muy extenso: {num_paginas} páginas (objetivo: <16)")
                elif num_paginas > 16:
                    self.warnings.append(f"Documento extenso: {num_paginas} páginas (ideal: 14-16)")
                else:
                    self.success.append(f"Documento compacto: {num_paginas} páginas ✓")
                
                # Estimación de tamaño de archivo
                tamanio_mb = self.pdf_path.stat().st_size / (1024 * 1024)
                if tamanio_mb > 10:
                    self.warnings.append(f"Archivo grande: {tamanio_mb:.1f}MB - considerar comprimir imágenes")
                else:
                    self.success.append(f"Tamaño de archivo apropiado: {tamanio_mb:.1f}MB")
                    
        except Exception as e:
            self.warnings.append(f"No se pudo validar compactación: {e}")
    
    def _validar_narrativa(self, texto: str):
        """Valida que se use lenguaje de campo (no técnico)"""
        print("\n📝 Validando narrativa...")
        
        # Frases de lenguaje de campo
        frases_campo = [
            "falta de agua",
            "riego no está llegando",
            "plantas presentan",
            "cobertura vegetal",
            "desarrollo de las plantas"
        ]
        
        frases_encontradas = sum(1 for frase in frases_campo if frase in texto.lower())
        
        if frases_encontradas >= 2:
            self.success.append(f"Narrativa en lenguaje de campo ({frases_encontradas} frases)")
        else:
            self.warnings.append("Poca narrativa en lenguaje de campo - verificar descripciones")
        
        # Verificar exceso de jerga técnica
        jerga_tecnica = ["matriz de covarianza", "algoritmo bayesiano", "tensor", "hiperplano"]
        jerga_encontrada = sum(1 for termino in jerga_tecnica if termino in texto.lower())
        
        if jerga_encontrada > 0:
            self.warnings.append(f"Jerga técnica excesiva ({jerga_encontrada} términos)")
        else:
            self.success.append("Sin jerga técnica innecesaria")
    
    def _mostrar_resultados(self):
        """Muestra resumen de validación"""
        print("\n" + "=" * 70)
        print("📊 RESULTADOS DE VALIDACIÓN")
        print("=" * 70)
        
        print(f"\n✅ Checks exitosos: {len(self.success)}")
        for item in self.success:
            print(f"   ✓ {item}")
        
        if self.warnings:
            print(f"\n⚠️  Advertencias: {len(self.warnings)}")
            for item in self.warnings:
                print(f"   ⚠ {item}")
        
        if self.issues:
            print(f"\n❌ Problemas críticos: {len(self.issues)}")
            for item in self.issues:
                print(f"   ✗ {item}")
        
        print("\n" + "=" * 70)
        
        if len(self.issues) == 0:
            if len(self.warnings) == 0:
                print("🎉 ¡PERFECTO! El PDF cumple con todos los estándares UX")
                return True
            else:
                print("✓ PDF ACEPTABLE con advertencias menores")
                return True
        else:
            print("❌ PDF NECESITA CORRECCIONES")
            return False


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python validar_ux_pdf_profesional.py <ruta_al_pdf>")
        print("\nEjemplo:")
        print("  python validar_ux_pdf_profesional.py media/informes/informe_parcela_3.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    validador = ValidadorUXPDF(pdf_path)
    
    resultado = validador.validar()
    
    sys.exit(0 if resultado else 1)


if __name__ == "__main__":
    main()
