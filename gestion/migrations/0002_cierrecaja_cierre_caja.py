# Generated manually for CierreCaja

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CierreCaja',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_cierre', models.DateTimeField(default=django.utils.timezone.now)),
                ('total_ventas', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('fondo_inicial', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('fondo_final', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('notas', models.TextField(blank=True, null=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cierres_caja', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cierre de Caja',
                'verbose_name_plural': 'Cierres de Caja',
                'ordering': ['-fecha_cierre'],
            },
        ),
        migrations.CreateModel(
            name='CierreCajaDetallePago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monto', models.DecimalField(decimal_places=2, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0'))])),
                ('cierre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles_pago', to='gestion.cierrecaja')),
                ('metodo_pago', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gestion.metodopago')),
            ],
            options={
                'verbose_name': 'Detalle de pago (cierre)',
                'verbose_name_plural': 'Detalles de pago (cierre)',
                'unique_together': {('cierre', 'metodo_pago')},
            },
        ),
    ]
