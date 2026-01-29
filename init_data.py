"""
Script para inicializar datos básicos en la base de datos
Ejecutar con: Get-Content init_data.py | python manage.py shell
"""

from gestion.models import Categoria, Producto, Cliente, MetodoPago
from django.contrib.auth.models import User

print("Inicializando datos básicos...")

# Crear categorías
categorias_data = [
    {'nombre': 'Pollos', 'descripcion': 'Combos de pollo'},
    {'nombre': 'Bebidas', 'descripcion': 'Bebidas y refrescos'},
    {'nombre': 'Extras', 'descripcion': 'Complementos y extras'},
]

for cat_data in categorias_data:
    cat, created = Categoria.objects.get_or_create(
        nombre=cat_data['nombre'],
        defaults={'descripcion': cat_data['descripcion']}
    )
    if created:
        print(f"✓ Categoría creada: {cat.nombre}")

# Obtener categoría de pollos
cat_pollos = Categoria.objects.get(nombre='Pollos')

# Crear productos iniciales
productos_data = [
    {
        'nombre': 'Chiquitin (1 presa)',
        'descripcion': 'Combo con 1 presa de pollo',
        'costo': 12.00,
        'precio_venta': 18.00,
        'stock': 50,
        'categoria': cat_pollos
    },
    {
        'nombre': 'Chipollo (2 presas)',
        'descripcion': 'Combo con 2 presas de pollo',
        'costo': 16.00,
        'precio_venta': 24.00,
        'stock': 40,
        'categoria': cat_pollos
    },
    {
        'nombre': 'Escolar (3 presas)',
        'descripcion': 'Combo con 3 presas de pollo',
        'costo': 20.00,
        'precio_venta': 29.00,
        'stock': 30,
        'categoria': cat_pollos
    },
    {
        'nombre': 'Panchita (4 presas)',
        'descripcion': 'Combo con 4 presas de pollo',
        'costo': 24.00,
        'precio_venta': 35.00,
        'stock': 20,
        'categoria': cat_pollos
    },
]

for prod_data in productos_data:
    prod, created = Producto.objects.get_or_create(
        nombre=prod_data['nombre'],
        defaults=prod_data
    )
    if created:
        print(f"✓ Producto creado: {prod.nombre} - Bs. {prod.precio_venta}")

# Crear métodos de pago
metodos_pago_data = [
    {
        'nombre': 'Efectivo',
        'tipo': 'efectivo',
        'descripcion': 'Pago en efectivo',
        'requiere_validacion': False
    },
    {
        'nombre': 'Tarjeta',
        'tipo': 'tarjeta',
        'descripcion': 'Tarjeta de crédito o débito',
        'requiere_validacion': True
    },
    {
        'nombre': 'QR Bancario',
        'tipo': 'qr',
        'descripcion': 'Pago mediante código QR',
        'requiere_validacion': True
    },
    {
        'nombre': 'Transferencia',
        'tipo': 'transferencia',
        'descripcion': 'Transferencia bancaria',
        'requiere_validacion': True
    },
]

for metodo_data in metodos_pago_data:
    metodo, created = MetodoPago.objects.get_or_create(
        nombre=metodo_data['nombre'],
        defaults=metodo_data
    )
    if created:
        print(f"✓ Método de pago creado: {metodo.nombre}")

# Crear o actualizar usuario administrador (siempre con contraseña correcta)
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
admin_user.email = 'admin@panchita.com'
admin_user.save()
print(f"✓ Usuario admin listo (password: admin123)" if created else "✓ Usuario admin actualizado (password: admin123)")

# Crear o actualizar usuario vendedor/cajero (siempre con contraseña correcta)
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
vendedor_user.email = 'vendedor@panchita.com'
vendedor_user.save()
print(f"✓ Usuario vendedor listo (password: vendedor123)" if created else "✓ Usuario vendedor actualizado (password: vendedor123)")

# Crear cliente de ejemplo
cliente, created = Cliente.objects.get_or_create(
    ci_nit='1234567',
    defaults={
        'nombre_completo': 'Cliente General',
        'telefono': '70000000',
        'email': 'cliente@example.com'
    }
)
if created:
    print(f"✓ Cliente creado: {cliente.nombre_completo}")

print("\n✅ Datos iniciales creados exitosamente!")
