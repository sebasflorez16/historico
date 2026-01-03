# Generated manually on 2026-01-03 14:20

from decimal import Decimal
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('informes', '0017_add_payment_fields'),
    ]

    operations = [
        # Agregar campos de información financiera
        migrations.AddField(
            model_name='informe',
            name='precio_base',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Precio del informe según tipo de análisis',
                max_digits=10,
                verbose_name='Precio Base'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='descuento_porcentaje',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Porcentaje de descuento aplicado',
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100)
                ],
                verbose_name='Descuento (%)'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='precio_final',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Precio después de descuentos',
                max_digits=10,
                verbose_name='Precio Final'
            ),
        ),
        
        # Agregar campos de estado de pago
        migrations.AddField(
            model_name='informe',
            name='estado_pago',
            field=models.CharField(
                choices=[
                    ('pagado', '💰 Pagado'),
                    ('pendiente', '⏳ Pendiente'),
                    ('vencido', '⚠️ Vencido'),
                    ('parcial', '📊 Pago Parcial'),
                    ('cortesia', '🎁 Cortesía'),
                ],
                db_index=True,
                default='pendiente',
                max_length=20,
                verbose_name='Estado de Pago'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='monto_pagado',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=10,
                verbose_name='Monto Pagado'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='saldo_pendiente',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                max_digits=10,
                verbose_name='Saldo Pendiente'
            ),
        ),
        
        # Agregar campos de detalles de pago
        migrations.AddField(
            model_name='informe',
            name='fecha_pago',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Fecha de Pago'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='fecha_vencimiento',
            field=models.DateField(
                blank=True,
                help_text='Fecha límite para pago',
                null=True,
                verbose_name='Fecha de Vencimiento'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='metodo_pago',
            field=models.CharField(
                blank=True,
                help_text='Ej: Transferencia, Efectivo, Tarjeta',
                max_length=100,
                verbose_name='Método de Pago'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='referencia_pago',
            field=models.CharField(
                blank=True,
                help_text='Número de transacción o comprobante',
                max_length=200,
                verbose_name='Referencia de Pago'
            ),
        ),
        migrations.AddField(
            model_name='informe',
            name='notas_pago',
            field=models.TextField(
                blank=True,
                help_text='Observaciones sobre el pago',
                verbose_name='Notas de Pago'
            ),
        ),
        
        # Agregar relación con cliente
        migrations.AddField(
            model_name='informe',
            name='cliente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='informes_generados',
                to='informes.clienteinvitacion',
                verbose_name='Cliente'
            ),
        ),
        
        # Agregar índices para mejorar rendimiento
        migrations.AddIndex(
            model_name='informe',
            index=models.Index(fields=['estado_pago', 'fecha_generacion'], name='informes_in_estado__6a1b45_idx'),
        ),
        migrations.AddIndex(
            model_name='informe',
            index=models.Index(fields=['fecha_vencimiento'], name='informes_in_fecha_v_4d2c81_idx'),
        ),
    ]
