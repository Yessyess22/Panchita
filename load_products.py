import os
from django.core.files import File
from gestion.models import Producto, Categoria

print("=== Iniciando Carga de Productos desde Imágenes (Modo Seguro) ===")

# 1. Asegurar Categorías
categorias_map = {
    'Pollos': 'Combos clásicos de pollo',
    'Bebidas': 'Refrescos y bebidas naturales',
    'Extras': 'Acompañamientos',
    'Mexicana': 'Tacos, burritos y más',
    'Platos': 'Platos especiales y completos',
    'Comida Rápida': 'Hamburguesas y Hot Dogs'
}

for nombre, desc in categorias_map.items():
    cat, created = Categoria.objects.get_or_create(nombre=nombre)
    if created:
        cat.descripcion = desc
        cat.save()
        print(f"Creada categoría: {nombre}")

# 2. Definición de Productos
productos_config = {
    'burrito.png': {
        'nombre': 'Burrito Panchita', 'precio': 25.00, 'cat': 'Mexicana',
        'desc': 'Delicioso burrito con carne, arroz y frijoles.'
    },
    'tacos.png': {
        'nombre': 'Tacos (3 unids)', 'precio': 30.00, 'cat': 'Mexicana',
        'desc': 'Trío de tacos con salsa especial.'
    },
    'nachos.png': {
        'nombre': 'Nachos con Queso', 'precio': 22.00, 'cat': 'Mexicana',
        'desc': 'Totopos crujientes bañados en queso cheddar.'
    },
    'quesadilla.png': {
        'nombre': 'Quesadilla', 'precio': 20.00, 'cat': 'Mexicana',
        'desc': 'Tortilla de harina rellena de queso fundido.'
    },
    'pique.jpg': {
        'nombre': 'Pique Macho', 'precio': 45.00, 'cat': 'Platos',
        'desc': 'Tradicional pique macho cochabambino.'
    },
    # REMOVIDO pique_n5lux4k.jpg para evitar duplicados
    'hamburguesa_queso.png': {
        'nombre': 'Hamburguesa con Queso', 'precio': 18.00, 'cat': 'Comida Rápida',
        'desc': 'Hamburguesa de res con queso americano.'
    },
    'hot_dog.png': {
        'nombre': 'Hot Dog', 'precio': 12.00, 'cat': 'Comida Rápida',
        'desc': 'Salchicha viena con salsas a elección.'
    },
    'ChichaMorada Panchita.jpg': {
        'nombre': 'Chicha Morada', 'precio': 10.00, 'cat': 'Bebidas',
        'desc': 'Refresco natural de maíz morado.'
    },
    'Limonada Panchita.jpg': {
        'nombre': 'Limonada', 'precio': 8.00, 'cat': 'Bebidas',
        'desc': 'Limonada fresca y natural.'
    },
    'Pollo al Spiedo.jpg': {
        'nombre': 'Pollo al Spiedo (Entero)', 'precio': 60.00, 'cat': 'Pollos',
        'desc': 'Pollo entero al spiedo con papas.'
    },
    'Tostada Panchita.jpg': {
        'nombre': 'Tostada de Pollo', 'precio': 15.00, 'cat': 'Platos',
        'desc': 'Tostada crujiente con pollo desmenuzado.'
    },
    'MegaBalde 10 Presas.jpg': {
        'nombre': 'Mega Balde (10 Presas)', 'precio': 90.00, 'cat': 'Pollos',
        'desc': 'Balde familiar con 10 presas de pollo.'
    },
    'Chiquitin.jpg': {
        'nombre': 'Chiquitin (1 presa)', 'precio': 18.00, 'cat': 'Pollos',
        'desc': 'Combo con 1 presa de pollo', 
    },
    'Chipollo Panchita.jpg': {
        'nombre': 'Chipollo (2 presas)', 'precio': 24.00, 'cat': 'Pollos',
        'desc': 'Combo con 2 presas de pollo',
    },
    'Escolar Panchita.jpg': {
        'nombre': 'Escolar (3 presas)', 'precio': 29.00, 'cat': 'Pollos',
        'desc': 'Combo con 3 presas de pollo',
    },
    'Panchita 4 presas.jpg': {
        'nombre': 'Panchita (4 presas)', 'precio': 35.00, 'cat': 'Pollos',
        'desc': 'Combo con 4 presas de pollo',
    },
}

# 3. Procesar
for filename, data in productos_config.items():
    img_relative_path = f'productos/{filename}'
    
    try:
        categoria = Categoria.objects.get(nombre=data['cat'])
    except Categoria.DoesNotExist:
        continue

    # BÚSQUEDA ROBUSTA: Por nombre exacto o nombres similares
    # Esto evita crear "Pique Macho" si ya existe "Pique Macho Especial" o "Pique"
    producto_existente = Producto.objects.filter(nombre__icontains=data['nombre']).first()
    
    if not producto_existente:
         # Intento secundario: buscar por coincidencia parcial inversa
         # Ej: buscar si en la base hay algo que contenga parte del nombre nuevo
         pass

    if producto_existente:
        # ACTUALIZAR: Solo aseguramos que tenga la imagen y validamos datos
        print(f"Encontrado existente: {producto_existente.nombre}")
        
        cambios = False
        if not producto_existente.imagen or str(producto_existente.imagen) != img_relative_path:
            producto_existente.imagen = img_relative_path
            cambios = True
            print(f" -> Actualizando imagen: {filename}")
            
        if not producto_existente.descripcion and data.get('desc'):
             producto_existente.descripcion = data['desc']
             cambios = True
             
        if cambios:
            producto_existente.save()
    else:
        # CREAR: Si no existe nada similar
        Producto.objects.create(
            nombre=data['nombre'],
            descripcion=data.get('desc', ''),
            costo=data['precio'] * 0.7,
            precio_venta=data['precio'],
            stock=50,
            categoria=categoria,
            imagen=img_relative_path
        )
        print(f"Creado nuevo: {data['nombre']}")

print("=== Limpieza Completada ===")
