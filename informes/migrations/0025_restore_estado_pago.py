# Generated manually on 2026-01-10 to restore estado_pago column

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('informes', '0024_parcela_ultima_calidad_datos_and_more'),
    ]

    operations = [
        # La columna ya fue creada manualmente en la base de datos
        # Esta migración solo registra el cambio para mantener sincronización
        migrations.RunSQL(
            sql=migrations.RunSQL.noop,  # No ejecutar nada, ya existe
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
