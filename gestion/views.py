from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .decorators import staff_required
from .models import (
    Producto, Categoria, Cliente, Venta, DetalleVenta,
    MetodoPago, Promocion, Pago
)

def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
            else:
                auth_login(request, user)
                rol = 'Administrador' if user.is_staff else 'Cajero / Vendedor'
                messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}. Sesión: {rol}.')
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Verifica que el usuario exista y la contraseña sea correcta.')
    
    return render(request, 'gestion/login.html')

def logout_view(request):
    """Logout view"""
    auth_logout(request)
    messages.success(request, 'Sesión cerrada exitosamente.')
    return redirect('login')

@login_required
def index(request):
    from django.utils import timezone
    from django.db.models import Sum, Count, Q
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    # Fecha de hoy en la zona horaria del servidor
    ahora = timezone.now()
    hoy = ahora.date()
    
    # Estadísticas del día - TODAS las ventas del día (completadas y pendientes)
    # Usamos fecha__date para comparar solo la fecha, ignorando la hora
    # Esto evita problemas de zona horaria
    ventas_hoy_todas = Venta.objects.filter(fecha__date=hoy)
    
    # Si no hay ventas con fecha__date, intentamos con las últimas 24 horas como respaldo
    if ventas_hoy_todas.count() == 0:
        hace_24_horas = ahora - timedelta(hours=24)
        ventas_hoy_todas = Venta.objects.filter(fecha__gte=hace_24_horas)
    
    ventas_hoy_completadas = ventas_hoy_todas.filter(estado='completado')
    ventas_hoy_pendientes = ventas_hoy_todas.filter(estado='pendiente')
    
    # Totales
    total_ventas_hoy = ventas_hoy_todas.count()
    total_ventas_completadas = ventas_hoy_completadas.count()
    total_ventas_pendientes = ventas_hoy_pendientes.count()
    
    # Total recaudado (solo completadas)
    total_recaudado_hoy = ventas_hoy_completadas.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    
    # Total pendiente (ventas pendientes)
    total_pendiente_hoy = ventas_hoy_pendientes.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    
    # Productos vendidos hoy (suma de cantidades - solo completadas)
    productos_vendidos_hoy = DetalleVenta.objects.filter(
        venta__fecha__date=hoy,
        venta__estado='completado'
    ).aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Promedio por venta (solo completadas)
    promedio_venta = total_recaudado_hoy / total_ventas_completadas if total_ventas_completadas > 0 else Decimal('0.00')
    
    # Últimas ventas del día (máximo 5) - TODAS incluyendo pendientes
    ultimas_ventas_hoy = ventas_hoy_todas.order_by('-fecha')[:5]
    
    # Para debug: verificar todas las ventas (últimas 10)
    todas_las_ventas = Venta.objects.all().order_by('-fecha')[:10]
    
    # Estadísticas generales (para referencia)
    total_productos = Producto.objects.filter(activo=True).count()
    total_clientes = Cliente.objects.filter(activo=True).count()
    
    # Total de ventas en general (sin filtro de fecha)
    total_ventas_general = Venta.objects.count()
    
    context = {
        # Estadísticas del día
        'total_ventas_hoy': total_ventas_hoy,
        'total_ventas_completadas': total_ventas_completadas,
        'total_ventas_pendientes': total_ventas_pendientes,
        'total_recaudado_hoy': total_recaudado_hoy,
        'total_pendiente_hoy': total_pendiente_hoy,
        'productos_vendidos_hoy': productos_vendidos_hoy,
        'promedio_venta': promedio_venta,
        'ultimas_ventas_hoy': ultimas_ventas_hoy,
        # Estadísticas generales
        'total_productos': total_productos,
        'total_clientes': total_clientes,
        'total_ventas_general': total_ventas_general,
        'hoy': hoy,
        'ahora': ahora,
        'todas_las_ventas': todas_las_ventas,  # Para debug
        'active': 'home'
    }
    return render(request, 'gestion/index.html', context)

@login_required
def pos_view(request):
    """Point of Sale interface"""
    productos = Producto.objects.select_related('categoria').filter(activo=True)
    categorias = Categoria.objects.filter(activo=True)
    clientes = Cliente.objects.filter(activo=True)
    metodos_pago = MetodoPago.objects.filter(activo=True)
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'clientes': clientes,
        'metodos_pago': metodos_pago,
        'active': 'pos'
    }
    return render(request, 'gestion/pos.html', context)

@login_required
@staff_required
def producto_index(request):
    productos = Producto.objects.select_related('categoria').filter(activo=True)
    context = {'productos': productos, 'active': 'productos'}
    return render(request, 'gestion/producto_index.html', context)

@login_required
@staff_required
def producto_crear(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            costo_str = request.POST.get('costo', '0')
            precio_venta_str = request.POST.get('precio_venta', '0')
            descuento_str = request.POST.get('descuento', '0') or '0'
            stock_str = request.POST.get('stock', '0') or '0'
            categoria_id = request.POST.get('categoria_id')
            imagen = request.FILES.get('imagen')
            
            # Validar campos requeridos
            if not nombre:
                messages.error(request, 'El nombre del producto es requerido.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            if not categoria_id:
                messages.error(request, 'Debe seleccionar una categoría.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            # Validar que la categoría exista
            try:
                categoria = Categoria.objects.get(id=categoria_id, activo=True)
            except Categoria.DoesNotExist:
                messages.error(request, 'La categoría seleccionada no existe o está inactiva.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            # Convertir valores numéricos
            from decimal import Decimal, InvalidOperation
            try:
                costo = Decimal(costo_str)
                precio_venta = Decimal(precio_venta_str)
                descuento = Decimal(descuento_str)
                stock = int(stock_str)
            except (ValueError, InvalidOperation) as e:
                messages.error(request, f'Error en los valores numéricos: {str(e)}')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            # Validar valores mínimos
            if costo < 0:
                messages.error(request, 'El costo no puede ser negativo.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            if precio_venta <= 0:
                messages.error(request, 'El precio de venta debe ser mayor a 0.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            if descuento < 0 or descuento > 100:
                messages.error(request, 'El descuento debe estar entre 0 y 100.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            if stock < 0:
                messages.error(request, 'El stock no puede ser negativo.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            
            # Crear el producto
            Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion if descripcion else None,
                costo=costo,
                precio_venta=precio_venta,
                descuento=descuento,
                stock=stock,
                categoria_id=categoria_id,
                imagen=imagen
            )
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('producto_index')
            
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'categorias': categorias, 
                'active': 'productos',
                'form_data': request.POST
            })
        
    categorias = Categoria.objects.filter(activo=True)
    return render(request, 'gestion/producto_form.html', {'categorias': categorias, 'active': 'productos'})

@login_required
@staff_required
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre')
        producto.descripcion = request.POST.get('descripcion')
        producto.costo = request.POST.get('costo')
        producto.precio_venta = request.POST.get('precio_venta')
        producto.descuento = request.POST.get('descuento') or 0
        producto.stock = request.POST.get('stock') or 0
        producto.categoria_id = request.POST.get('categoria_id')
        
        if request.FILES.get('imagen'):
            producto.imagen = request.FILES.get('imagen')
            
        producto.save()
        
        messages.success(request, 'Producto actualizado exitosamente.')
        return redirect('producto_index')
    
    categorias = Categoria.objects.filter(activo=True)
    context = {
        'producto': producto,
        'categorias': categorias,
        'active': 'productos'
    }
    return render(request, 'gestion/producto_form.html', context)

@login_required
@staff_required
def producto_eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        producto.activo = False
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" eliminado exitosamente.')
        return redirect('producto_index')
    
    context = {
        'producto': producto,
        'active': 'productos'
    }
    return render(request, 'gestion/producto_eliminar.html', context)


@login_required
@staff_required
def venta_crear(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        items_ids = request.POST.getlist('productos[]')
        items_cantidades = request.POST.getlist('cantidades[]')
        metodo_pago_id = request.POST.get('metodo_pago_id')
        
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Get or create a default user for sales if not logged in
        from django.contrib.auth.models import User
        if request.user.is_authenticated:
            usuario = request.user
        else:
            usuario, created = User.objects.get_or_create(username='vendedor', defaults={'email': 'vendedor@panchita.com'})
            if created:
                usuario.set_password('vendedor123')
                usuario.save()
        
        # Create sale with explicit timezone-aware datetime
        from django.utils import timezone
        venta = Venta.objects.create(cliente=cliente, usuario=usuario)
        # Asegurar que la fecha se guarde correctamente
        if not venta.fecha:
            venta.fecha = timezone.now()
            venta.save()
        
        # Add sale details
        for prod_id, cant in zip(items_ids, items_cantidades):
            if prod_id and cant:
                try:
                    producto = Producto.objects.get(id=prod_id, activo=True)
                except Producto.DoesNotExist:
                    messages.error(request, f'Producto con ID {prod_id} no encontrado o inactivo.')
                    venta.delete()
                    return redirect('pos')
                
                try:
                    cantidad = int(cant)
                    if cantidad <= 0:
                        raise ValueError('Cantidad debe ser mayor a 0')
                except (ValueError, TypeError):
                    messages.error(request, 'Cantidad inválida.')
                    venta.delete()
                    return redirect('pos')
                
                # Check stock
                if not producto.tiene_stock(cantidad):
                    messages.error(request, f'Stock insuficiente para {producto.nombre}.')
                    venta.delete()
                    return redirect('pos')
                
                precio_unitario = producto.precio_final()
                descuento_porcentaje = producto.descuento
                
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    descuento_porcentaje=descuento_porcentaje
                )
                
                # Update stock
                producto.stock -= cantidad
                producto.save()
        
        # Calculate totals
        venta.calcular_totales()
        
        # Create payment if method provided
        if metodo_pago_id:
            metodo_pago = get_object_or_404(MetodoPago, id=metodo_pago_id)
            pago = Pago.objects.create(
                venta=venta,
                metodo_pago=metodo_pago,
                monto=venta.total
            )
            
            # Auto-validate if method doesn't require validation
            if not metodo_pago.requiere_validacion:
                pago.validar_pago(usuario)
        
        messages.success(request, 'Venta registrada exitosamente.')
        return redirect('index')

    clientes = Cliente.objects.filter(activo=True)
    productos = Producto.objects.filter(activo=True)
    metodos_pago = MetodoPago.objects.filter(activo=True)
    
    return render(request, 'gestion/venta_form.html', {
        'clientes': clientes, 
        'productos': productos,
        'metodos_pago': metodos_pago,
        'active': 'ventas'
    })

@login_required
def pos_procesar_pago(request):
    """Process payment from POS"""
    from django.http import JsonResponse
    import json
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cliente_id = data.get('cliente_id')
            metodo_pago_id = data.get('metodo_pago_id')
            items = data.get('items', [])
            
            if not cliente_id or not metodo_pago_id or not items:
                return JsonResponse({'success': False, 'error': 'Datos incompletos'}, status=400)
            
            cliente = get_object_or_404(Cliente, id=cliente_id)
            metodo_pago = get_object_or_404(MetodoPago, id=metodo_pago_id)
            
            # Create sale with explicit timezone-aware datetime
            from django.utils import timezone
            venta = Venta.objects.create(cliente=cliente, usuario=request.user)
            # Asegurar que la fecha se guarde correctamente
            if not venta.fecha:
                venta.fecha = timezone.now()
                venta.save()
            
            # Add sale details
            for item in items:
                try:
                    producto = Producto.objects.get(id=item['id'], activo=True)
                except Producto.DoesNotExist:
                    venta.delete()
                    return JsonResponse({
                        'success': False, 
                        'error': f'Producto con ID {item["id"]} no encontrado o inactivo'
                    }, status=400)
                
                try:
                    cantidad = int(item['quantity'])
                    if cantidad <= 0:
                        raise ValueError('Cantidad debe ser mayor a 0')
                except (ValueError, KeyError):
                    venta.delete()
                    return JsonResponse({
                        'success': False, 
                        'error': 'Cantidad inválida'
                    }, status=400)
                
                # Check stock
                if not producto.tiene_stock(cantidad):
                    venta.delete()
                    return JsonResponse({
                        'success': False, 
                        'error': f'Stock insuficiente para {producto.nombre}'
                    }, status=400)
                
                precio_unitario = producto.precio_final()
                descuento_porcentaje = producto.descuento
                
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    descuento_porcentaje=descuento_porcentaje
                )
                
                # Update stock
                producto.stock -= cantidad
                producto.save()
            
            # Calculate totals
            venta.calcular_totales()
            
            # Create payment
            pago = Pago.objects.create(
                venta=venta,
                metodo_pago=metodo_pago,
                monto=venta.total
            )
            
            # Auto-validate if method doesn't require validation
            if not metodo_pago.requiere_validacion:
                pago.validar_pago(request.user)
            
            return JsonResponse({
                'success': True,
                'venta_id': venta.id,
                'total': str(venta.total),
                'message': 'Venta procesada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def venta_index(request):
    """Lista todas las ventas"""
    from django.db.models import Sum
    from datetime import datetime
    
    # Filtros opcionales
    estado_filter = request.GET.get('estado', '')
    fecha_filter = request.GET.get('fecha', '')
    
    # Query base
    ventas = Venta.objects.select_related('cliente', 'usuario').prefetch_related('detalles', 'pagos').order_by('-fecha')
    
    # Aplicar filtros
    if estado_filter:
        ventas = ventas.filter(estado=estado_filter)
    
    if fecha_filter:
        try:
            fecha = datetime.strptime(fecha_filter, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__date=fecha)
        except ValueError:
            pass
    
    # Estadísticas
    total_ventas = ventas.count()
    total_general = ventas.aggregate(total=Sum('total'))['total'] or 0
    
    # Paginación simple (últimas 50 ventas por defecto)
    ventas = ventas[:50]
    
    context = {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_general': total_general,
        'estado_filter': estado_filter,
        'fecha_filter': fecha_filter,
        'active': 'ventas'
    }
    return render(request, 'gestion/venta_index.html', context)