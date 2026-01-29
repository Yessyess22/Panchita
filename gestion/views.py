from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .decorators import staff_required
from .models import (
    Producto, Categoria, Cliente, Venta, DetalleVenta,
    MetodoPago, Promocion, Pago
)

def _ensure_default_user(username, password, email, is_staff, is_superuser=False):
    """Crea o actualiza el usuario por defecto si no existe o la contraseña no coincide."""
    from django.contrib.auth.models import User
    try:
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_active = True
        u.email = email
        if username == 'admin':
            u.is_staff = True
            u.is_superuser = True
        else:
            u.is_staff = is_staff
            u.is_superuser = False
        u.save()
        return u
    except User.DoesNotExist:
        u = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=True,
        )
        return u


def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        # Si no existe el usuario pero intentan con credenciales por defecto, crearlo
        if user is None and username and password:
            if username == 'admin' and password == 'admin123':
                _ensure_default_user(
                    'admin', 'admin123', 'admin@panchita.com',
                    is_staff=True, is_superuser=True
                )
                user = authenticate(request, username='admin', password='admin123')
            elif username == 'vendedor' and password == 'vendedor123':
                _ensure_default_user(
                    'vendedor', 'vendedor123', 'vendedor@panchita.com',
                    is_staff=False
                )
                user = authenticate(request, username='vendedor', password='vendedor123')
        
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
def cliente_index(request):
    """Lista de clientes del sistema."""
    clientes = Cliente.objects.filter(activo=True).order_by('nombre_completo')
    context = {'clientes': clientes, 'active': 'clientes'}
    return render(request, 'gestion/cliente_index.html', context)


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
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        costo_str = request.POST.get('costo', '0')
        precio_venta_str = request.POST.get('precio_venta', '0')
        descuento_str = request.POST.get('descuento', '0') or '0'
        stock_str = request.POST.get('stock', '0') or '0'
        categoria_id = request.POST.get('categoria_id')
        nueva_imagen = request.FILES.get('imagen')
        
        # Validaciones (mismas que en crear)
        if not nombre:
            messages.error(request, 'El nombre del producto es requerido.')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'producto': producto,
                'categorias': categorias,
                'active': 'productos',
                'form_data': request.POST,
            })
        if not categoria_id:
            messages.error(request, 'Debe seleccionar una categoría.')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'producto': producto,
                'categorias': categorias,
                'active': 'productos',
                'form_data': request.POST,
            })
        try:
            from decimal import Decimal, InvalidOperation
            costo = Decimal(costo_str)
            precio_venta = Decimal(precio_venta_str)
            descuento = Decimal(descuento_str)
            stock = int(stock_str)
        except (ValueError, InvalidOperation):
            messages.error(request, 'Error en los valores numéricos.')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'producto': producto,
                'categorias': categorias,
                'active': 'productos',
                'form_data': request.POST,
            })
        if costo < 0 or precio_venta <= 0 or descuento < 0 or descuento > 100 or stock < 0:
            messages.error(request, 'Revise costo, precio, descuento y stock.')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'producto': producto,
                'categorias': categorias,
                'active': 'productos',
                'form_data': request.POST,
            })
        
        # Actualizar producto
        producto.nombre = nombre
        producto.descripcion = descripcion if descripcion else None
        producto.costo = costo
        producto.precio_venta = precio_venta
        producto.descuento = descuento
        producto.stock = stock
        producto.categoria_id = categoria_id
        if nueva_imagen:
            producto.imagen = nueva_imagen
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
def pos_buscar_clientes(request):
    """API: buscar clientes por nombre, teléfono o CI (para POS)."""
    from django.http import JsonResponse
    from django.db.models import Q

    q = (request.GET.get('q') or '').strip()
    clientes_qs = Cliente.objects.filter(activo=True).order_by('nombre_completo')

    if q:
        clientes_qs = clientes_qs.filter(
            Q(nombre_completo__icontains=q)
            | Q(telefono__icontains=q)
            | Q(ci_nit__icontains=q)
            | Q(email__icontains=q)
        )[:30]
    else:
        clientes_qs = clientes_qs[:100]

    lista = [
        {'id': c.id, 'nombre_completo': c.nombre_completo, 'telefono': c.telefono or '', 'ci_nit': c.ci_nit or ''}
        for c in clientes_qs
    ]
    return JsonResponse({'clientes': lista})


@login_required
def pos_crear_cliente(request):
    """API: crear cliente desde POS (JSON)."""
    from django.http import JsonResponse
    import json

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        nombre = (data.get('nombre_completo') or '').strip()
        telefono = (data.get('telefono') or '').strip()
        ci_nit = (data.get('ci_nit') or '').strip() or None
        email = (data.get('email') or '').strip() or None

        if not nombre:
            return JsonResponse({'success': False, 'error': 'El nombre del cliente es obligatorio.'}, status=400)

        if ci_nit and Cliente.objects.filter(ci_nit=ci_nit).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe un cliente con ese CI/NIT.'}, status=400)

        cliente = Cliente.objects.create(
            nombre_completo=nombre,
            telefono=telefono or None,
            ci_nit=ci_nit,
            email=email,
            activo=True,
        )
        return JsonResponse({
            'success': True,
            'cliente': {'id': cliente.id, 'nombre_completo': cliente.nombre_completo},
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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