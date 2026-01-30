# Generated manually for modo_consumo (En el local / Para llevar)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0002_cierrecaja_cierre_caja'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='modo_consumo',
            field=models.CharField(
                choices=[('local', 'En el local'), ('llevar', 'Para llevar')],
                default='local',
                max_length=10,
                verbose_name='Modo de consumo'
            ),
        ),
    ]
