# Generated for unique numero_factura when tipo_documento='factura'

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0004_venta_tipo_documento_numero_factura'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='venta',
            constraint=models.UniqueConstraint(
                condition=models.Q(tipo_documento='factura'),
                fields=('numero_factura',),
                name='unique_numero_factura_factura',
            ),
        ),
    ]
