"""
Comando para restablecer contraseñas de admin y vendedor.
Útil si no puedes ingresar o olvidaste la contraseña.

Uso: python manage.py reset_usuarios
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Restablece contraseñas de admin y vendedor (admin123 y vendedor123) y asegura que estén activos.'

    def handle(self, *args, **options):
        # Admin
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@panchita.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()
        self.stdout.write(self.style.SUCCESS('✓ Admin: usuario listo. Usuario: admin  Contraseña: admin123'))

        # Vendedor / Cajero
        vendedor_user, created = User.objects.get_or_create(
            username='vendedor',
            defaults={
                'email': 'vendedor@panchita.com',
                'is_staff': False,
                'is_active': True,
            }
        )
        vendedor_user.set_password('vendedor123')
        vendedor_user.is_staff = False
        vendedor_user.is_superuser = False
        vendedor_user.is_active = True
        vendedor_user.save()
        self.stdout.write(self.style.SUCCESS('✓ Vendedor: usuario listo. Usuario: vendedor  Contraseña: vendedor123'))

        self.stdout.write(self.style.SUCCESS('\n✅ Ya puedes ingresar con admin o vendedor.'))
