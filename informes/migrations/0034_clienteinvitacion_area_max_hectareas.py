"""
Migración: Agregar campo area_max_hectareas a ClienteInvitacion
Permite limitar el área que el cliente puede dibujar al registrar su parcela.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('informes', '0033_demo_url_fields_to_charfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='clienteinvitacion',
            name='area_max_hectareas',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Área máxima acordada en hectáreas. 0 = sin límite.',
                max_digits=10,
            ),
        ),
    ]
