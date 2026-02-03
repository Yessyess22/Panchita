# Migración: Promocion.descripcion permite vacío (blank=True)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0006_cliente_email_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='promocion',
            name='descripcion',
            field=models.TextField(blank=True),
        ),
    ]
