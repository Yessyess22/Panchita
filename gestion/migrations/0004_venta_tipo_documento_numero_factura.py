# Generated manually for tipo_documento (Ticket/Factura) y numero_factura

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0003_venta_modo_consumo'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='tipo_documento',
            field=models.CharField(
                choices=[('ticket', 'Ticket'), ('factura', 'Factura')],
                default='ticket',
                max_length=10,
                verbose_name='Tipo de documento'
            ),
        ),
        migrations.AddField(
            model_name='venta',
            name='numero_factura',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Solo para ventas tipo factura',
                null=True,
                verbose_name='Número de factura'
            ),
        ),
    ]
