#!/usr/bin/env python
"""Agrega campos Y métodos de pago al modelo Informe"""

with open('informes/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar donde termina el método save() original
# Vamos a insertar los métodos después del método save() actual

metodos_pago = '''
    def marcar_como_pagado(self, monto=None, metodo='', referencia='', notas=''):
        """Marca el informe como pagado"""
        self.monto_pagado = monto if monto else self.precio_final
        self.estado_pago = 'pagado'
        self.saldo_pendiente = Decimal('0.00')
        self.fecha_pago = timezone.now()
        if metodo:
            self.metodo_pago = metodo
        if referencia:
            self.referencia_pago = referencia
        if notas:
            self.notas_pago = notas
        self.save()
    
    def registrar_pago_parcial(self, monto, metodo='', referencia='', notas=''):
        """Registra un pago parcial"""
        self.monto_pagado += Decimal(str(monto))
        self.metodo_pago = metodo
        self.referencia_pago = referencia
        if notas:
            self.notas_pago = f"{self.notas_pago}\\n{notas}" if self.notas_pago else notas
        self.save()
    
    def aplicar_descuento(self, porcentaje, notas=''):
        """Aplica un descuento al informe"""
        if porcentaje < 0 or porcentaje > 100:
            raise ValueError("El descuento debe estar entre 0 y 100%")
        self.descuento_porcentaje = Decimal(str(porcentaje))
        if notas:
            self.notas_pago = f"{self.notas_pago}\\n{notas}" if self.notas_pago else notas
        self.save()
    
    def anular_pago(self, notas=''):
        """Anula el pago y vuelve a estado pendiente"""
        self.monto_pagado = Decimal('0.00')
        self.saldo_pendiente = self.precio_final
        self.estado_pago = 'pendiente'
        self.fecha_pago = None
        if notas:
            self.notas_pago = f"{self.notas_pago}\\n{notas}" if self.notas_pago else notas
        self.save()
    
    @property
    def esta_vencido(self):
        """Verifica si el pago está vencido"""
        if self.estado_pago in ['pagado', 'cortesia']:
            return False
        if self.fecha_vencimiento:
            return timezone.now().date() > self.fecha_vencimiento
        return False
    
    @property
    def dias_vencido(self):
        """Calcula los días de vencimiento"""
        if not self.esta_vencido:
            return 0
        return (timezone.now().date() - self.fecha_vencimiento).days
    
    @property
    def porcentaje_pagado(self):
        """Calcula el porcentaje pagado"""
        if self.precio_final == 0:
            return 100
        return float((self.monto_pagado / self.precio_final) * 100)
    
    @property
    def descuento_monto(self):
        """Calcula el monto del descuento"""
        return self.precio_base * (self.descuento_porcentaje / 100)
    
    @classmethod
    def obtener_pendientes_pago(cls):
        """Retorna informes con pago pendiente"""
        return cls.objects.filter(estado_pago__in=['pendiente', 'parcial'])
    
    @classmethod
    def obtener_vencidos(cls):
        """Retorna informes vencidos"""
        return cls.objects.filter(
            estado_pago__in=['pendiente', 'parcial', 'vencido'],
            fecha_vencimiento__lt=timezone.now().date()
        )
    
    @classmethod
    def calcular_ingresos_periodo(cls, fecha_inicio, fecha_fin):
        """Calcula ingresos en un período"""
        informes = cls.objects.filter(
            estado_pago='pagado',
            fecha_pago__range=[fecha_inicio, fecha_fin]
        )
        return informes.aggregate(total=models.Sum('monto_pagado'))['total'] or Decimal('0.00')
'''

# Buscar el final del método save() (antes del método estado_salud_general)
import re
pattern = r'(def save\(self.*?super\(\)\.save\(\*args, \*\*kwargs\))\s*(@property\s+def estado_salud_general)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Insertar métodos después del save()
    new_content = content[:match.end(1)] + '\n' + metodos_pago + '\n    ' + match.group(2) + content[match.end():]
    
    with open('informes/models.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Métodos de pago agregados correctamente")
else:
    print("❌ No se encontró el método save() para insertar los métodos de pago")
    print("Contenido del archivo tiene", len(content), "caracteres")
