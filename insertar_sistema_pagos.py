import shutil
from decimal import Decimal

# Restaurar backup
shutil.copy('informes/models.py.backup', 'informes/models.py')

with open('informes/models.py', 'r') as f:
    lines = f.readlines()

# Encontrar class Meta en Informe
meta_idx = None
for i, line in enumerate(lines):
    if i > 500 and 'class Meta:' in line:
        # Verificar que es Informe
        for j in range(max(0, i-15), i):
            if 'tiempo_procesamiento' in lines[j]:
                meta_idx = i
                break
        if meta_idx:
            break

print(f"✅ Meta en índice {meta_idx}")

# Campos de pago
campos = '''    
    # === SISTEMA DE PAGOS ===
    ESTADO_PAGO_CHOICES = [('pagado', '💰 Pagado'), ('pendiente', '⏳ Pendiente'), ('vencido', '⚠️ Vencido'), ('parcial', '📊 Pago Parcial'), ('cortesia', '🎁 Cortesía')]
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Precio Base")
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Descuento %")
    precio_final = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Precio Final")
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='pendiente', verbose_name="Estado Pago", db_index=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Pagado")
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Saldo Pendiente")
    fecha_pago = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Pago")
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name="Vencimiento", db_index=True)
    metodo_pago = models.CharField(max_length=100, blank=True, verbose_name="Método Pago")
    referencia_pago = models.CharField(max_length=200, blank=True, verbose_name="Referencia")
    notas_pago = models.TextField(blank=True, verbose_name="Notas")
    cliente = models.ForeignKey('ClienteInvitacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='informes_generados', verbose_name="Cliente")

'''
lines.insert(meta_idx, campos)

# Actualizar Meta con indexes
for i in range(meta_idx, min(meta_idx+20, len(lines))):
    if "ordering = ['-fecha_generacion']" in lines[i]:
        lines[i] = lines[i].rstrip() + '\n        indexes = [models.Index(fields=[\'estado_pago\', \'fecha_generacion\']), models.Index(fields=[\'fecha_vencimiento\'])]\n'
        break

# Actualizar __str__
for i in range(meta_idx, min(meta_idx+25, len(lines))):
    if 'def __str__(self):' in lines[i]:
        lines[i+1] = '        estado = dict(self.ESTADO_PAGO_CHOICES).get(self.estado_pago, "")\n        return f"Informe {self.parcela.nombre} - {self.fecha_generacion.strftime(\'%d/%m/%Y\')} {estado}"\n'
        break

# Agregar métodos
metodos = '''
    def save(self, *args, **kwargs):
        if not self.titulo:
            self.titulo = f"Análisis Satelital - {self.parcela.nombre} ({self.periodo_analisis_meses} meses)"
        if self.descuento_porcentaje > 0:
            self.precio_final = self.precio_base - (self.precio_base * self.descuento_porcentaje / 100)
        else:
            self.precio_final = self.precio_base
        self.saldo_pendiente = self.precio_final - self.monto_pagado
        if self.precio_base == 0:
            self.estado_pago = 'cortesia'
        elif self.monto_pagado >= self.precio_final:
            self.estado_pago = 'pagado'
        elif self.monto_pagado > 0:
            self.estado_pago = 'parcial'
        super().save(*args, **kwargs)
    
    def aplicar_descuento(self, porcentaje, notas=''):
        self.descuento_porcentaje = Decimal(str(porcentaje))
        if notas:
            self.notas_pago = notas
        self.save()
    
    def marcar_como_pagado(self, monto=None, metodo='', referencia='', notas=''):
        self.monto_pagado = monto if monto else self.precio_final
        if metodo:
            self.metodo_pago = metodo
        if referencia:
            self.referencia_pago = referencia
        if notas:
            self.notas_pago = notas
        self.save()
    
    def registrar_pago_parcial(self, monto, metodo='', referencia='', notas=''):
        self.monto_pagado += Decimal(str(monto))
        if metodo:
            self.metodo_pago = metodo
        if referencia:
            self.referencia_pago = referencia
        if notas:
            self.notas_pago = f"{self.notas_pago}\\n{notas}" if self.notas_pago else notas
        self.save()
    
    @property
    def esta_vencido(self):
        return bool(self.fecha_vencimiento and timezone.now().date() > self.fecha_vencimiento)
    
    @property
    def porcentaje_pagado(self):
        return 100 if self.precio_final == 0 else float((self.monto_pagado / self.precio_final) * 100)
'''

# Insertar métodos después de __str__
for i in range(meta_idx, min(meta_idx+30, len(lines))):
    if 'def __str__(self):' in lines[i]:
        j = i + 1
        while j < len(lines) and (lines[j].startswith('        ') or not lines[j].strip()):
            j += 1
        lines.insert(j, metodos + '\n')
        break

with open('informes/models.py', 'w') as f:
    f.writelines(lines)

print(f"✅ Sistema completo agregado - {len(lines)} líneas")
