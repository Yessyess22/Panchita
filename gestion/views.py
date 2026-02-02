from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from .decorators import staff_required
from .models import (
    Producto, Categoria, Cliente, Venta, DetalleVenta,
    MetodoPago, Promocion, Pago, CierreCaja, CierreCajaDetallePago
)

# Límites de longitud para validación en vistas (coinciden con max_length del modelo)
MAX_LENGTH_NOMBRE_PRODUCTO = 100
MAX_LENGTH_DESCRIPCION_PRODUCTO = 2000
MAX_LENGTH_NOMBRE_CLIENTE = 150
MAX_LENGTH_CI_NIT = 20
MAX_LENGTH_TELEFONO = 20
MAX_SIZE_IMAGEN_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

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
                # "Recordarme": sesión 2 semanas si está marcado, si no expira al cerrar navegador
                if request.POST.get('remember'):
                    request.session.set_expiry(1209600)  # 2 semanas en segundos
                else:
                    request.session.set_expiry(0)  # expira al cerrar el navegador
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
@staff_required
def admin_index(request):
    """Página Admin: cambiar contraseña propia y del vendedor (solo staff)."""
    return render(request, 'gestion/admin_index.html', {'active': 'admin'})


@login_required
@staff_required
def cuenta_cambiar_password(request):
    """Cambiar contraseña del usuario actual."""
    if request.method == 'POST':
        actual = request.POST.get('password_actual', '')
        nueva = request.POST.get('password_nueva', '')
        confirmar = request.POST.get('password_confirmar', '')

        if not actual:
            messages.error(request, 'Debe ingresar su contraseña actual.')
            return render(request, 'gestion/cuenta_cambiar_password.html', {'active': 'admin'})

        if not request.user.check_password(actual):
            messages.error(request, 'La contraseña actual no es correcta.')
            return render(request, 'gestion/cuenta_cambiar_password.html', {'active': 'admin'})

        if not nueva:
            messages.error(request, 'La nueva contraseña es obligatoria.')
            return render(request, 'gestion/cuenta_cambiar_password.html', {'active': 'admin'})

        if len(nueva) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
            return render(request, 'gestion/cuenta_cambiar_password.html', {'active': 'admin'})

        if nueva != confirmar:
            messages.error(request, 'La nueva contraseña y la confirmación no coinciden.')
            return render(request, 'gestion/cuenta_cambiar_password.html', {'active': 'admin'})

        request.user.set_password(nueva)
        request.user.save()
        auth_login(request, request.user)  # Mantener sesión activa tras cambiar contraseña
        messages.success(request, 'Contraseña actualizada correctamente.')
        return redirect('admin_index')

    return render(request, 'gestion/cuenta_cambiar_password.html', {'active': 'admin'})


@login_required
@staff_required
def admin_cambiar_password_vendedor(request):
    """Admin cambia la contraseña de un vendedor (solo staff)."""
    from django.contrib.auth.models import User
    vendedores = User.objects.filter(is_staff=False, is_active=True).order_by('username')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        nueva = request.POST.get('password_nueva', '')
        confirmar = request.POST.get('password_confirmar', '')
        if not user_id:
            messages.error(request, 'Debe seleccionar un usuario.')
            return render(request, 'gestion/admin_cambiar_password_vendedor.html', {
                'vendedores': vendedores,
                'active': 'admin',
            })
        try:
            usuario = User.objects.get(pk=user_id, is_staff=False)
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')
            return render(request, 'gestion/admin_cambiar_password_vendedor.html', {
                'vendedores': vendedores,
                'active': 'admin',
            })
        if not nueva:
            messages.error(request, 'La nueva contraseña es obligatoria.')
            return render(request, 'gestion/admin_cambiar_password_vendedor.html', {
                'vendedores': vendedores,
                'usuario_seleccionado': usuario,
                'active': 'admin',
            })
        if len(nueva) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return render(request, 'gestion/admin_cambiar_password_vendedor.html', {
                'vendedores': vendedores,
                'usuario_seleccionado': usuario,
                'active': 'admin',
            })
        if nueva != confirmar:
            messages.error(request, 'La contraseña y la confirmación no coinciden.')
            return render(request, 'gestion/admin_cambiar_password_vendedor.html', {
                'vendedores': vendedores,
                'usuario_seleccionado': usuario,
                'active': 'admin',
            })
        usuario.set_password(nueva)
        usuario.save()
        messages.success(request, f'Contraseña de "{usuario.username}" actualizada correctamente.')
        return redirect('admin_index')
    return render(request, 'gestion/admin_cambiar_password_vendedor.html', {
        'vendedores': vendedores,
        'active': 'admin',
    })


@login_required
@staff_required
def admin_usuarios_index(request):
    """Lista de usuarios del sistema (solo staff)."""
    from django.contrib.auth.models import User
    usuarios = User.objects.filter(is_active=True).order_by('-is_staff', 'username')
    return render(request, 'gestion/admin_usuarios_index.html', {
        'usuarios': usuarios,
        'active': 'admin',
    })


@login_required
@staff_required
def admin_usuarios_crear(request):
    """Crear nuevo usuario con cuenta, contraseña y rol (solo staff)."""
    from django.contrib.auth.models import User
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirmar = request.POST.get('password_confirmar', '')
        rol = request.POST.get('rol', 'vendedor')
        email = (request.POST.get('email') or '').strip() or None

        if not username:
            messages.error(request, 'El nombre de usuario es obligatorio.')
            return render(request, 'gestion/admin_usuarios_crear.html', {
                'active': 'admin',
                'form_data': request.POST,
            })
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Ya existe un usuario con el nombre "{username}".')
            return render(request, 'gestion/admin_usuarios_crear.html', {
                'active': 'admin',
                'form_data': request.POST,
            })
        if not password:
            messages.error(request, 'La contraseña es obligatoria.')
            return render(request, 'gestion/admin_usuarios_crear.html', {
                'active': 'admin',
                'form_data': request.POST,
            })
        if len(password) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            return render(request, 'gestion/admin_usuarios_crear.html', {
                'active': 'admin',
                'form_data': request.POST,
            })
        if password != confirmar:
            messages.error(request, 'La contraseña y la confirmación no coinciden.')
            return render(request, 'gestion/admin_usuarios_crear.html', {
                'active': 'admin',
                'form_data': request.POST,
            })
        if rol not in ('administrador', 'vendedor'):
            rol = 'vendedor'

        is_staff = rol == 'administrador'
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email or f'{username}@panchita.com',
                is_staff=is_staff,
                is_superuser=is_staff,
                is_active=True,
            )
        except IntegrityError:
            messages.error(request, f'Ya existe un usuario con el nombre "{username}". Intente de nuevo.')
            return render(request, 'gestion/admin_usuarios_crear.html', {
                'active': 'admin',
                'form_data': request.POST,
            })
        rol_display = 'Administrador' if is_staff else 'Vendedor'
        messages.success(request, f'Usuario "{username}" ({rol_display}) creado correctamente.')
        return redirect('admin_usuarios_index')

    return render(request, 'gestion/admin_usuarios_crear.html', {'active': 'admin'})


@login_required
@staff_required
def admin_usuarios_eliminar(request, pk):
    """Desactivar usuario (solo staff)."""
    from django.contrib.auth.models import User
    usuario = get_object_or_404(User, pk=pk)
    if request.user.pk == usuario.pk:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
        return redirect('admin_usuarios_index')
    if request.method == 'POST':
        nombre = usuario.username
        usuario.is_active = False
        usuario.save()
        messages.success(request, f'Usuario "{nombre}" desactivado correctamente.')
        return redirect('admin_usuarios_index')
    return render(request, 'gestion/admin_usuarios_eliminar.html', {
        'usuario': usuario,
        'active': 'admin',
    })


@login_required
def index(request):
    from django.utils import timezone
    from django.db.models import Sum, Count, Q
    from django.db import OperationalError
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    # Fecha de hoy en zona horaria de Bolivia (America/La_Paz)
    ahora = timezone.localtime(timezone.now())
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
    
    # Productos vendidos hoy: suma de cantidades de las ventas completadas del día
    # (usamos las mismas ventas que ventas_hoy_completadas para consistencia con el resto del dashboard)
    productos_vendidos_hoy = DetalleVenta.objects.filter(
        venta__in=ventas_hoy_completadas
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
    
    # Productos con stock bajo (< 5) para alerta
    productos_bajo_stock = list(Producto.objects.filter(activo=True, stock__lt=5).order_by('stock')[:10])
    
    # Total de ventas en general (sin filtro de fecha)
    total_ventas_general = Venta.objects.count()
    
    # Forzar evaluación de querysets que se iteran en el template (detectar errores de BD)
    try:
        _ = list(ultimas_ventas_hoy)
        _ = list(todas_las_ventas)
    except OperationalError as e:
        err_msg = str(e).lower()
        if any(x in err_msg for x in ('modo_consumo', 'tipo_documento', 'numero_factura', 'no such column', 'does not exist', "doesn't exist")):
            messages.error(
                request,
                'La base de datos necesita actualizarse. Ejecute: python manage.py migrate (o ./migrar.sh)'
            )
            return redirect('login')
        raise
    
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
        'productos_bajo_stock': productos_bajo_stock,
        'total_ventas_general': total_ventas_general,
        'hoy': hoy,
        'ahora': ahora,
        'todas_las_ventas': todas_las_ventas,  # Para debug
        'active': 'home'
    }
    return render(request, 'gestion/index.html', context)

def _get_cliente_mostrador():
    """Obtiene o crea el cliente Mostrador para ventas rápidas."""
    cliente, _ = Cliente.objects.get_or_create(
        ci_nit='MOSTRADOR',
        defaults={
            'nombre_completo': 'Mostrador',
            'telefono': '',
            'email': '',
            'activo': True
        }
    )
    return cliente


def _precio_con_promocion(producto):
    """Obtiene el precio final del producto aplicando promociones vigentes si existen."""
    from django.utils import timezone
    from decimal import Decimal, ROUND_HALF_UP
    ahora = timezone.now()
    promos_vigentes = Promocion.objects.filter(
        activo=True,
        productos=producto,
        fecha_inicio__lte=ahora,
        fecha_fin__gte=ahora
    ).order_by('-descuento_porcentaje')
    if promos_vigentes.exists():
        promo = promos_vigentes.first()
        precio_base = producto.precio_final()
        desc = promo.descuento_porcentaje / Decimal('100')
        precio_promo = precio_base * (1 - desc)
        return precio_promo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return producto.precio_final()


@login_required
def pos_view(request):
    """Point of Sale interface"""
    from django.db.models import Max
    productos = Producto.objects.select_related('categoria').filter(activo=True)
    categorias = Categoria.objects.filter(activo=True)
    clientes = Cliente.objects.filter(activo=True)
    metodos_pago = MetodoPago.objects.filter(activo=True)
    cliente_mostrador = _get_cliente_mostrador()
    # Precios con promociones aplicadas
    productos_con_precio = []
    for p in productos:
        precio = _precio_con_promocion(p)
        tiene_promo = precio < p.precio_final()
        productos_con_precio.append({'producto': p, 'precio_display': precio, 'tiene_promo': tiene_promo})
    # Siguiente número de ticket = max(id) + 1 (consecutivo con las ventas)
    ultimo_id = Venta.objects.aggregate(m=Max('id'))['m'] or 0
    siguiente_ticket = ultimo_id + 1

    context = {
        'productos_con_precio': productos_con_precio,
        'categorias': categorias,
        'clientes': clientes,
        'metodos_pago': metodos_pago,
        'cliente_mostrador': cliente_mostrador,
        'siguiente_ticket': siguiente_ticket,
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
def cliente_editar(request, pk):
    """Editar datos de un cliente."""
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        ci_nit = (request.POST.get('ci_nit') or '').strip() or None
        telefono = (request.POST.get('telefono') or '').strip() or None
        email = (request.POST.get('email') or '').strip() or None
        direccion = (request.POST.get('direccion') or '').strip() or None

        if not nombre:
            messages.error(request, 'El nombre del cliente es obligatorio.')
            return render(request, 'gestion/cliente_form.html', {
                'cliente': cliente,
                'active': 'clientes',
                'form_data': request.POST,
            })
        if len(nombre) > MAX_LENGTH_NOMBRE_CLIENTE:
            messages.error(request, f'El nombre no puede superar {MAX_LENGTH_NOMBRE_CLIENTE} caracteres.')
            return render(request, 'gestion/cliente_form.html', {
                'cliente': cliente,
                'active': 'clientes',
                'form_data': request.POST,
            })
        if ci_nit and len(ci_nit) > MAX_LENGTH_CI_NIT:
            messages.error(request, f'El CI/NIT no puede superar {MAX_LENGTH_CI_NIT} caracteres.')
            return render(request, 'gestion/cliente_form.html', {
                'cliente': cliente,
                'active': 'clientes',
                'form_data': request.POST,
            })
        if telefono and len(telefono) > MAX_LENGTH_TELEFONO:
            messages.error(request, f'El teléfono no puede superar {MAX_LENGTH_TELEFONO} caracteres.')
            return render(request, 'gestion/cliente_form.html', {
                'cliente': cliente,
                'active': 'clientes',
                'form_data': request.POST,
            })
        if email:
            try:
                django_validate_email(email)
            except DjangoValidationError:
                messages.error(request, 'El correo electrónico no tiene un formato válido.')
                return render(request, 'gestion/cliente_form.html', {
                    'cliente': cliente,
                    'active': 'clientes',
                    'form_data': request.POST,
                })

        if ci_nit and Cliente.objects.exclude(pk=pk).filter(ci_nit=ci_nit).exists():
            messages.error(request, 'Ya existe otro cliente con ese CI/NIT.')
            return render(request, 'gestion/cliente_form.html', {
                'cliente': cliente,
                'active': 'clientes',
                'form_data': request.POST,
            })

        cliente.nombre_completo = nombre
        cliente.ci_nit = ci_nit
        cliente.telefono = telefono
        cliente.email = email
        cliente.direccion = direccion
        try:
            cliente.save()
        except IntegrityError:
            messages.error(request, 'Ya existe otro cliente con ese CI/NIT. Intente de nuevo.')
            return render(request, 'gestion/cliente_form.html', {
                'cliente': cliente,
                'active': 'clientes',
                'form_data': request.POST,
            })

        messages.success(request, f'Cliente "{cliente.nombre_completo}" actualizado correctamente.')
        return redirect('cliente_index')

    return render(request, 'gestion/cliente_form.html', {
        'cliente': cliente,
        'active': 'clientes',
    })


@login_required
def cliente_eliminar(request, pk):
    """Eliminar (desactivar) un cliente."""
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        nombre = cliente.nombre_completo
        cliente.activo = False
        cliente.save()
        messages.success(request, f'Cliente "{nombre}" eliminado correctamente.')
        return redirect('cliente_index')

    return render(request, 'gestion/cliente_eliminar.html', {
        'cliente': cliente,
        'active': 'clientes',
    })


@login_required
@staff_required
def producto_index(request):
    from django.db.models import Q
    productos = Producto.objects.select_related('categoria').filter(activo=True)
    q = request.GET.get('q', '').strip()
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(categoria__nombre__icontains=q) | Q(descripcion__icontains=q)
        )
    context = {'productos': productos, 'q': q, 'active': 'productos'}
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
            if len(nombre) > MAX_LENGTH_NOMBRE_PRODUCTO:
                messages.error(request, f'El nombre no puede superar {MAX_LENGTH_NOMBRE_PRODUCTO} caracteres.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            if descripcion and len(descripcion) > MAX_LENGTH_DESCRIPCION_PRODUCTO:
                messages.error(request, f'La descripción no puede superar {MAX_LENGTH_DESCRIPCION_PRODUCTO} caracteres.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            if Producto.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, f'Ya existe un producto con el nombre "{nombre}".')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'categorias': categorias, 
                    'active': 'productos',
                    'form_data': request.POST
                })
            if imagen:
                if imagen.size > MAX_SIZE_IMAGEN_BYTES:
                    messages.error(request, f'La imagen no puede superar {MAX_SIZE_IMAGEN_BYTES // (1024*1024)} MB.')
                    categorias = Categoria.objects.filter(activo=True)
                    return render(request, 'gestion/producto_form.html', {
                        'categorias': categorias, 
                        'active': 'productos',
                        'form_data': request.POST
                    })
                content_type = getattr(imagen, 'content_type', None) or ''
                if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
                    messages.error(request, 'Formato de imagen no permitido. Use JPEG, PNG, GIF o WebP.')
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
        if len(nombre) > MAX_LENGTH_NOMBRE_PRODUCTO:
            messages.error(request, f'El nombre no puede superar {MAX_LENGTH_NOMBRE_PRODUCTO} caracteres.')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'producto': producto,
                'categorias': categorias,
                'active': 'productos',
                'form_data': request.POST,
            })
        if descripcion and len(descripcion) > MAX_LENGTH_DESCRIPCION_PRODUCTO:
            messages.error(request, f'La descripción no puede superar {MAX_LENGTH_DESCRIPCION_PRODUCTO} caracteres.')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'producto': producto,
                'categorias': categorias,
                'active': 'productos',
                'form_data': request.POST,
            })
        if Producto.objects.filter(nombre__iexact=nombre).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe otro producto con el nombre "{nombre}".')
            categorias = Categoria.objects.filter(activo=True)
            return render(request, 'gestion/producto_form.html', {
                'producto': producto,
                'categorias': categorias,
                'active': 'productos',
                'form_data': request.POST,
            })
        if nueva_imagen:
            if nueva_imagen.size > MAX_SIZE_IMAGEN_BYTES:
                messages.error(request, f'La imagen no puede superar {MAX_SIZE_IMAGEN_BYTES // (1024*1024)} MB.')
                categorias = Categoria.objects.filter(activo=True)
                return render(request, 'gestion/producto_form.html', {
                    'producto': producto,
                    'categorias': categorias,
                    'active': 'productos',
                    'form_data': request.POST,
                })
            content_type = getattr(nueva_imagen, 'content_type', None) or ''
            if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
                messages.error(request, 'Formato de imagen no permitido. Use JPEG, PNG, GIF o WebP.')
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


# --- Categorías (CRUD) ---

@login_required
@staff_required
def categoria_index(request):
    categorias = Categoria.objects.filter(activo=True).order_by('nombre')
    context = {'categorias': categorias, 'active': 'categorias'}
    return render(request, 'gestion/categoria_index.html', context)


@login_required
@staff_required
def categoria_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip() or None
        if not nombre:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
            return render(request, 'gestion/categoria_form.html', {
                'active': 'categorias',
                'form_data': request.POST,
            })
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe una categoría con el nombre "{nombre}".')
            return render(request, 'gestion/categoria_form.html', {
                'active': 'categorias',
                'form_data': request.POST,
            })
        try:
            Categoria.objects.create(nombre=nombre, descripcion=descripcion)
        except IntegrityError:
            messages.error(request, f'Ya existe una categoría con el nombre "{nombre}". Intente de nuevo.')
            return render(request, 'gestion/categoria_form.html', {
                'active': 'categorias',
                'form_data': request.POST,
            })
        messages.success(request, f'Categoría "{nombre}" creada correctamente.')
        return redirect('categoria_index')
    return render(request, 'gestion/categoria_form.html', {'active': 'categorias'})


@login_required
@staff_required
def categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip() or None
        if not nombre:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
            return render(request, 'gestion/categoria_form.html', {
                'categoria': categoria,
                'active': 'categorias',
                'form_data': request.POST,
            })
        otro = Categoria.objects.filter(nombre__iexact=nombre).exclude(pk=pk)
        if otro.exists():
            messages.error(request, f'Ya existe otra categoría con el nombre "{nombre}".')
            return render(request, 'gestion/categoria_form.html', {
                'categoria': categoria,
                'active': 'categorias',
                'form_data': request.POST,
            })
        categoria.nombre = nombre
        categoria.descripcion = descripcion
        try:
            categoria.save()
        except IntegrityError:
            messages.error(request, f'Ya existe otra categoría con el nombre "{nombre}". Intente de nuevo.')
            return render(request, 'gestion/categoria_form.html', {
                'categoria': categoria,
                'active': 'categorias',
                'form_data': request.POST,
            })
        messages.success(request, f'Categoría "{nombre}" actualizada correctamente.')
        return redirect('categoria_index')
    return render(request, 'gestion/categoria_form.html', {
        'categoria': categoria,
        'active': 'categorias',
    })


@login_required
@staff_required
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        if categoria.productos.filter(activo=True).exists():
            messages.error(
                request,
                f'No se puede eliminar la categoría "{categoria.nombre}" porque tiene productos activos. '
                'Desactive o elimine los productos primero.'
            )
            return redirect('categoria_index')
        categoria.activo = False
        categoria.save()
        messages.success(request, f'Categoría "{categoria.nombre}" eliminada correctamente.')
        return redirect('categoria_index')
    return render(request, 'gestion/categoria_eliminar.html', {
        'categoria': categoria,
        'active': 'categorias',
    })


# --- Métodos de Pago (CRUD) ---

@login_required
@staff_required
def metodopago_index(request):
    metodos = MetodoPago.objects.filter(activo=True).order_by('nombre')
    context = {'metodos': metodos, 'active': 'metodos_pago'}
    return render(request, 'gestion/metodopago_index.html', context)


@login_required
@staff_required
def metodopago_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', 'efectivo')
        descripcion = (request.POST.get('descripcion') or '').strip() or None
        requiere_validacion = request.POST.get('requiere_validacion') == 'on'
        if not nombre:
            messages.error(request, 'El nombre del método de pago es obligatorio.')
            return render(request, 'gestion/metodopago_form.html', {
                'active': 'metodos_pago',
                'form_data': request.POST,
                'tipo_actual': request.POST.get('tipo', 'efectivo'),
                'requiere_validacion_checked': request.POST.get('requiere_validacion') == 'on',
            })
        if tipo not in ('efectivo', 'tarjeta', 'qr', 'transferencia'):
            tipo = 'efectivo'
        if MetodoPago.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe un método de pago con el nombre "{nombre}".')
            return render(request, 'gestion/metodopago_form.html', {
                'active': 'metodos_pago',
                'form_data': request.POST,
                'tipo_actual': tipo,
                'requiere_validacion_checked': requiere_validacion,
            })
        try:
            MetodoPago.objects.create(
                nombre=nombre,
                tipo=tipo,
                descripcion=descripcion,
                requiere_validacion=requiere_validacion,
            )
        except IntegrityError:
            messages.error(request, f'Ya existe un método de pago con el nombre "{nombre}". Intente de nuevo.')
            return render(request, 'gestion/metodopago_form.html', {
                'active': 'metodos_pago',
                'form_data': request.POST,
                'tipo_actual': tipo,
                'requiere_validacion_checked': requiere_validacion,
            })
        messages.success(request, f'Método de pago "{nombre}" creado correctamente.')
        return redirect('metodopago_index')
    return render(request, 'gestion/metodopago_form.html', {
        'active': 'metodos_pago',
        'tipo_actual': 'efectivo',
        'requiere_validacion_checked': False,
    })


@login_required
@staff_required
def metodopago_editar(request, pk):
    metodo = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        tipo = request.POST.get('tipo', 'efectivo')
        descripcion = (request.POST.get('descripcion') or '').strip() or None
        requiere_validacion = request.POST.get('requiere_validacion') == 'on'
        if not nombre:
            messages.error(request, 'El nombre del método de pago es obligatorio.')
            return render(request, 'gestion/metodopago_form.html', {
                'metodo': metodo,
                'active': 'metodos_pago',
                'form_data': request.POST,
                'tipo_actual': request.POST.get('tipo', 'efectivo'),
                'requiere_validacion_checked': request.POST.get('requiere_validacion') == 'on',
            })
        if tipo not in ('efectivo', 'tarjeta', 'qr', 'transferencia'):
            tipo = 'efectivo'
        otro = MetodoPago.objects.filter(nombre__iexact=nombre).exclude(pk=pk)
        if otro.exists():
            messages.error(request, f'Ya existe otro método de pago con el nombre "{nombre}".')
            return render(request, 'gestion/metodopago_form.html', {
                'metodo': metodo,
                'active': 'metodos_pago',
                'form_data': request.POST,
                'tipo_actual': tipo,
                'requiere_validacion_checked': requiere_validacion,
            })
        metodo.nombre = nombre
        metodo.tipo = tipo
        metodo.descripcion = descripcion
        metodo.requiere_validacion = requiere_validacion
        try:
            metodo.save()
        except IntegrityError:
            messages.error(request, f'Ya existe otro método de pago con el nombre "{nombre}". Intente de nuevo.')
            return render(request, 'gestion/metodopago_form.html', {
                'metodo': metodo,
                'active': 'metodos_pago',
                'form_data': request.POST,
                'tipo_actual': tipo,
                'requiere_validacion_checked': requiere_validacion,
            })
        messages.success(request, f'Método de pago "{nombre}" actualizado correctamente.')
        return redirect('metodopago_index')
    return render(request, 'gestion/metodopago_form.html', {
        'metodo': metodo,
        'active': 'metodos_pago',
        'tipo_actual': metodo.tipo,
        'requiere_validacion_checked': metodo.requiere_validacion,
    })


@login_required
@staff_required
def metodopago_eliminar(request, pk):
    metodo = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        metodo.activo = False
        metodo.save()
        messages.success(request, f'Método de pago "{metodo.nombre}" eliminado correctamente.')
        return redirect('metodopago_index')
    return render(request, 'gestion/metodopago_eliminar.html', {
        'metodo': metodo,
        'active': 'metodos_pago',
    })


# --- Promociones (CRUD) ---

def _parse_datetime_local(value):
    """Parsea valor datetime-local (YYYY-MM-DDTHH:MM) a datetime con timezone."""
    from django.utils import timezone
    from datetime import datetime
    if not value or not value.strip():
        return None
    try:
        dt_naive = datetime.strptime(value.strip()[:16], '%Y-%m-%dT%H:%M')
        return timezone.make_aware(dt_naive, timezone.get_current_timezone())
    except (ValueError, TypeError):
        return None


@login_required
@staff_required
def promocion_index(request):
    promos = Promocion.objects.all().order_by('-fecha_inicio')
    return render(request, 'gestion/promocion_index.html', {
        'promociones': promos,
        'active': 'promociones',
    })


@login_required
@staff_required
def promocion_crear(request):
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip() or ''
        try:
            descuento = float(request.POST.get('descuento_porcentaje', 0) or 0)
        except (ValueError, TypeError):
            descuento = 0
        fecha_inicio = _parse_datetime_local(request.POST.get('fecha_inicio', ''))
        fecha_fin = _parse_datetime_local(request.POST.get('fecha_fin', ''))
        activo = request.POST.get('activo') == 'on'
        producto_ids = request.POST.getlist('productos')

        def _productos_seleccionados():
            return [int(x) for x in request.POST.getlist('productos') if str(x).isdigit()]

        if not nombre:
            messages.error(request, 'El nombre de la promoción es obligatorio.')
            return render(request, 'gestion/promocion_form.html', {
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if descuento <= 0 or descuento > 100:
            messages.error(request, 'El descuento debe estar entre 0.01 y 100.')
            return render(request, 'gestion/promocion_form.html', {
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if not fecha_inicio or not fecha_fin:
            messages.error(request, 'Las fechas de inicio y fin son obligatorias.')
            return render(request, 'gestion/promocion_form.html', {
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if fecha_fin <= fecha_inicio:
            messages.error(request, 'La fecha fin debe ser posterior a la fecha inicio.')
            return render(request, 'gestion/promocion_form.html', {
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if Promocion.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, f'Ya existe una promoción con el nombre "{nombre}".')
            return render(request, 'gestion/promocion_form.html', {
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })

        from decimal import Decimal
        promo = Promocion(
            nombre=nombre,
            descripcion=descripcion,
            descuento_porcentaje=Decimal(str(descuento)),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            activo=activo,
        )
        try:
            promo.full_clean()
        except DjangoValidationError as e:
            if 'fecha_fin' in (e.message_dict or {}):
                messages.error(request, 'La fecha fin debe ser posterior a la fecha de inicio.')
            else:
                messages.error(request, str(e))
            return render(request, 'gestion/promocion_form.html', {
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        promo.save()
        if producto_ids:
            promo.productos.set(Producto.objects.filter(pk__in=producto_ids, activo=True))
        messages.success(request, f'Promoción "{nombre}" creada correctamente.')
        return redirect('promocion_index')
    return render(request, 'gestion/promocion_form.html', {
        'productos': productos,
        'active': 'promociones',
        'productos_seleccionados': [],
    })


@login_required
@staff_required
def promocion_editar(request, pk):
    promo = get_object_or_404(Promocion, pk=pk)
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip() or ''
        try:
            descuento = float(request.POST.get('descuento_porcentaje', 0) or 0)
        except (ValueError, TypeError):
            descuento = 0
        fecha_inicio = _parse_datetime_local(request.POST.get('fecha_inicio', ''))
        fecha_fin = _parse_datetime_local(request.POST.get('fecha_fin', ''))
        activo = request.POST.get('activo') == 'on'
        producto_ids = request.POST.getlist('productos')

        def _productos_seleccionados():
            return [int(x) for x in request.POST.getlist('productos') if str(x).isdigit()]

        if not nombre:
            messages.error(request, 'El nombre de la promoción es obligatorio.')
            return render(request, 'gestion/promocion_form.html', {
                'promocion': promo,
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if descuento <= 0 or descuento > 100:
            messages.error(request, 'El descuento debe estar entre 0.01 y 100.')
            return render(request, 'gestion/promocion_form.html', {
                'promocion': promo,
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if not fecha_inicio or not fecha_fin:
            messages.error(request, 'Las fechas de inicio y fin son obligatorias.')
            return render(request, 'gestion/promocion_form.html', {
                'promocion': promo,
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if fecha_fin <= fecha_inicio:
            messages.error(request, 'La fecha fin debe ser posterior a la fecha inicio.')
            return render(request, 'gestion/promocion_form.html', {
                'promocion': promo,
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        if Promocion.objects.filter(nombre__iexact=nombre).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe otra promoción con el nombre "{nombre}".')
            return render(request, 'gestion/promocion_form.html', {
                'promocion': promo,
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })

        from decimal import Decimal
        promo.nombre = nombre
        promo.descripcion = descripcion
        promo.descuento_porcentaje = Decimal(str(descuento))
        promo.fecha_inicio = fecha_inicio
        promo.fecha_fin = fecha_fin
        promo.activo = activo
        try:
            promo.full_clean()
        except DjangoValidationError as e:
            if 'fecha_fin' in (e.message_dict or {}):
                messages.error(request, 'La fecha fin debe ser posterior a la fecha de inicio.')
            else:
                messages.error(request, str(e))
            return render(request, 'gestion/promocion_form.html', {
                'promocion': promo,
                'productos': productos,
                'active': 'promociones',
                'form_data': request.POST,
                'productos_seleccionados': _productos_seleccionados(),
            })
        promo.save()
        if producto_ids is not None:
            promo.productos.set(Producto.objects.filter(pk__in=producto_ids, activo=True))
        messages.success(request, f'Promoción "{nombre}" actualizada correctamente.')
        return redirect('promocion_index')
    productos_seleccionados = list(promo.productos.values_list('pk', flat=True))
    return render(request, 'gestion/promocion_form.html', {
        'promocion': promo,
        'productos': productos,
        'active': 'promociones',
        'productos_seleccionados': productos_seleccionados,
    })


@login_required
@staff_required
def promocion_eliminar(request, pk):
    promo = get_object_or_404(Promocion, pk=pk)
    if request.method == 'POST':
        nombre = promo.nombre
        promo.activo = False
        promo.save()
        messages.success(request, f'Promoción "{nombre}" desactivada correctamente.')
        return redirect('promocion_index')
    return render(request, 'gestion/promocion_eliminar.html', {
        'promocion': promo,
        'active': 'promociones',
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
            modo_consumo = data.get('modo_consumo', 'local')
            if modo_consumo not in ('local', 'llevar'):
                modo_consumo = 'local'
            tipo_documento = data.get('tipo_documento', 'ticket')
            if tipo_documento not in ('ticket', 'factura'):
                tipo_documento = 'ticket'
            
            # Para factura: cliente debe tener NIT/CI válido (no Mostrador)
            if tipo_documento == 'factura':
                nit_valido = cliente.ci_nit and str(cliente.ci_nit).strip() and str(cliente.ci_nit).upper() != 'MOSTRADOR'
                if not nit_valido:
                    return JsonResponse({
                        'success': False,
                        'error': 'Para factura debe seleccionar un cliente con NIT/CI. No puede usar Mostrador.'
                    }, status=400)

            from django.utils import timezone
            from django.db.models import Max
            from decimal import Decimal, InvalidOperation

            with transaction.atomic():
                # Create sale with explicit timezone-aware datetime
                venta = Venta.objects.create(
                    cliente=cliente,
                    usuario=request.user,
                    modo_consumo=modo_consumo,
                    tipo_documento=tipo_documento
                )
                if tipo_documento == 'factura':
                    ultimo_num = Venta.objects.filter(tipo_documento='factura').aggregate(
                        m=Max('numero_factura')
                    )['m'] or 0
                    venta.numero_factura = ultimo_num + 1
                    venta.save()
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
                
                # Usar precio del frontend (incluye promociones) o precio base
                from decimal import Decimal, InvalidOperation
                try:
                    precio_unitario = Decimal(str(item.get('price', producto.precio_final())))
                except (InvalidOperation, TypeError):
                    precio_unitario = producto.precio_final()
                # Validar: precio debe ser > 0 y <= precio base (promos bajan el precio)
                precio_max = producto.precio_final()
                if precio_unitario <= 0 or precio_unitario > precio_max:
                    precio_unitario = precio_max
                descuento_porcentaje = Decimal('0')  # El descuento ya está en el precio
                
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

            # Create payment: validar con full_clean() antes de guardar (suma pagos <= total)
            pago = Pago(venta=venta, metodo_pago=metodo_pago, monto=venta.total)
            try:
                pago.full_clean()
            except DjangoValidationError as e:
                err_msg = str(e)
                if hasattr(e, 'message_dict') and e.message_dict:
                    msgs = e.message_dict.get('__all__', list(e.message_dict.values()))
                    if msgs:
                        err_msg = msgs[0][0] if isinstance(msgs[0], (list, tuple)) else str(msgs[0])
                return JsonResponse({'success': False, 'error': err_msg}, status=400)
            pago.save()

            # Auto-validate if method doesn't require validation
            if not metodo_pago.requiere_validacion:
                pago.validar_pago(request.user)

            return JsonResponse({
                'success': True,
                'venta_id': venta.id,
                'total': str(venta.total),
                'message': 'Venta procesada exitosamente'
            })

        except IntegrityError:
            return JsonResponse({
                'success': False,
                'error': 'Error de integridad (por ejemplo, número de factura duplicado). Intente de nuevo.'
            }, status=409)
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
        if len(nombre) > MAX_LENGTH_NOMBRE_CLIENTE:
            return JsonResponse({'success': False, 'error': f'El nombre no puede superar {MAX_LENGTH_NOMBRE_CLIENTE} caracteres.'}, status=400)
        if ci_nit and len(ci_nit) > MAX_LENGTH_CI_NIT:
            return JsonResponse({'success': False, 'error': f'El CI/NIT no puede superar {MAX_LENGTH_CI_NIT} caracteres.'}, status=400)
        if telefono and len(telefono) > MAX_LENGTH_TELEFONO:
            return JsonResponse({'success': False, 'error': f'El teléfono no puede superar {MAX_LENGTH_TELEFONO} caracteres.'}, status=400)
        if email:
            try:
                django_validate_email(email)
            except DjangoValidationError:
                return JsonResponse({'success': False, 'error': 'El correo electrónico no tiene un formato válido.'}, status=400)

        if ci_nit and Cliente.objects.filter(ci_nit=ci_nit).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe un cliente con ese CI/NIT.'}, status=400)

        try:
            cliente = Cliente.objects.create(
                nombre_completo=nombre,
                telefono=telefono or None,
                ci_nit=ci_nit,
                email=email,
                activo=True,
            )
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Ya existe un cliente con ese CI/NIT. Intente de nuevo.'}, status=409)
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
    from django.db import OperationalError
    from datetime import datetime

    # Filtros opcionales
    estado_filter = request.GET.get('estado', '')
    fecha_filter = request.GET.get('fecha', '')
    ticket_filter = request.GET.get('ticket', '').strip()

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

    if ticket_filter:
        try:
            ventas = ventas.filter(id=int(ticket_filter))
        except ValueError:
            pass

    # Estadísticas
    total_ventas = ventas.count()
    total_general = ventas.aggregate(total=Sum('total'))['total'] or 0

    # Paginación simple (últimas 50 ventas por defecto)
    try:
        ventas = list(ventas[:50])
    except OperationalError as e:
        err_msg = str(e).lower()
        if any(x in err_msg for x in ('modo_consumo', 'tipo_documento', 'numero_factura', 'no such column', 'does not exist', "doesn't exist")):
            messages.error(
                request,
                'La base de datos necesita actualizarse. Ejecute: python manage.py migrate (o ./migrar.sh)'
            )
            return redirect('index')
        raise

    context = {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_general': total_general,
        'estado_filter': estado_filter,
        'fecha_filter': fecha_filter,
        'ticket_filter': ticket_filter,
        'active': 'ventas'
    }
    return render(request, 'gestion/venta_index.html', context)


@login_required
def venta_detail(request, pk):
    """Detalle de una venta (solo lectura)."""
    from django.db import OperationalError
    try:
        venta = get_object_or_404(
            Venta.objects.select_related('cliente', 'usuario').prefetch_related('detalles__producto', 'pagos__metodo_pago'),
            pk=pk
        )
    except OperationalError as e:
        err_msg = str(e).lower()
        if any(x in err_msg for x in ('modo_consumo', 'tipo_documento', 'numero_factura', 'no such column', 'does not exist', "doesn't exist")):
            messages.error(
                request,
                'La base de datos necesita actualizarse. Ejecute: python manage.py migrate (o ./migrar.sh)'
            )
            return redirect('venta_index')
        raise
    # Datos de empresa para factura (configurable)
    empresa = {
        'nombre': 'Pollos Panchita',
        'nit': getattr(settings, 'EMPRESA_NIT', ''),  # Opcional: definir en settings
    }
    return render(request, 'gestion/venta_detail.html', {
        'venta': venta,
        'empresa': empresa,
        'active': 'ventas'
    })


@login_required
def pago_validar(request, venta_pk, pago_pk):
    """Confirma/valida un pago pendiente desde el detalle de la venta."""
    if request.method != 'POST':
        return redirect('venta_detail', pk=venta_pk)
    venta = get_object_or_404(Venta, pk=venta_pk)
    pago = get_object_or_404(Pago, pk=pago_pk, venta=venta)
    if pago.validado:
        messages.info(request, 'Este pago ya estaba validado.')
    else:
        pago.validar_pago(request.user)
        messages.success(request, f'Pago de Bs. {pago.monto:.2f} ({pago.metodo_pago.nombre}) confirmado.')
    return redirect('venta_detail', pk=venta_pk)


# --- Cierre de Caja ---

@login_required
def cierre_caja_index(request):
    """Cierre de caja: resumen del día y cierres de hoy."""
    from django.db.models import Sum
    from django.utils import timezone
    from decimal import Decimal

    try:
        # Fecha de hoy en zona horaria de Bolivia (America/La_Paz)
        hoy = timezone.localtime(timezone.now()).date()
    except Exception:
        from datetime import date
        hoy = date.today()

    from datetime import timedelta
    hace_30_dias = hoy - timedelta(days=30)

    try:
        # Historial: últimos 30 días (o últimos 100 cierres)
        cierres_qs = CierreCaja.objects.filter(
            fecha_cierre__date__gte=hace_30_dias
        ).select_related('usuario').prefetch_related('detalles_pago__metodo_pago').order_by('-fecha_cierre')
        if not request.user.is_staff:
            cierres_qs = cierres_qs.filter(usuario=request.user)
        cierres = list(cierres_qs[:100])
    except Exception as e:
        err_msg = str(e).lower()
        if any(x in err_msg for x in ('no such table', 'does not exist', "doesn't exist", 'table')):
            messages.error(
                request,
                'Las tablas de Cierre de Caja no existen. Ejecute: python manage.py migrate'
            )
            return redirect('index')
        raise
    ventas_hoy = Venta.objects.filter(fecha__date=hoy, estado='completado')
    if not request.user.is_staff:
        ventas_hoy = ventas_hoy.filter(usuario=request.user)
    total_hoy = ventas_hoy.aggregate(t=Sum('total'))['t'] or Decimal('0.00')
    num_ventas_hoy = ventas_hoy.count()

    return render(request, 'gestion/cierre_caja_index.html', {
        'cierres': cierres,
        'total_hoy': total_hoy,
        'num_ventas_hoy': num_ventas_hoy,
        'hoy': hoy,
        'active': 'cierre_caja'
    })


@login_required
def cierre_caja_nuevo(request):
    """Pantalla para cerrar caja: muestra totales del día y permite registrar el cierre."""
    from django.utils import timezone
    from django.db.models import Sum
    from django.db import OperationalError
    from decimal import Decimal

    try:
        # Fecha de hoy en zona horaria de Bolivia (America/La_Paz)
        hoy = timezone.localtime(timezone.now()).date()
    except Exception:
        from datetime import date
        hoy = date.today()

    # Ventas completadas del día del usuario actual (o todas si admin)
    ventas_hoy = Venta.objects.filter(fecha__date=hoy, estado='completado')
    if not request.user.is_staff:
        ventas_hoy = ventas_hoy.filter(usuario=request.user)

    total_ventas = ventas_hoy.aggregate(t=Sum('total'))['t'] or Decimal('0.00')
    num_ventas = ventas_hoy.count()

    # Totales por método de pago (evitar venta__in=[] en algunos backends)
    metodos_pago = MetodoPago.objects.filter(activo=True)
    totales_por_metodo = {}
    if num_ventas > 0:
        for p in Pago.objects.filter(venta__in=ventas_hoy, validado=True).values('metodo_pago__nombre').annotate(
            total=Sum('monto')
        ):
            totales_por_metodo[p['metodo_pago__nombre']] = p['total']
    
    if request.method == 'POST':
        # Un cierre por usuario por día (evitar duplicados)
        if CierreCaja.objects.filter(usuario=request.user, fecha_cierre__date=hoy).exists():
            messages.error(
                request,
                'Ya tiene un cierre de caja registrado para hoy. No puede registrar otro.'
            )
            return render(request, 'gestion/cierre_caja_nuevo.html', {
                'total_ventas': total_ventas,
                'num_ventas': num_ventas,
                'hoy': hoy,
                'totales_por_metodo': totales_por_metodo,
                'metodos_pago': metodos_pago,
                'active': 'cierre_caja'
            })

        fondo_inicial_str = (request.POST.get('fondo_inicial') or '').strip()
        fondo_final_str = (request.POST.get('fondo_final') or '').strip()
        notas = (request.POST.get('notas') or '').strip()
        
        try:
            fondo_inicial = Decimal(fondo_inicial_str) if fondo_inicial_str else None
            fondo_final = Decimal(fondo_final_str) if fondo_final_str else None
        except Exception:
            fondo_inicial = None
            fondo_final = None
        
        try:
            cierre = CierreCaja.objects.create(
                usuario=request.user,
                total_ventas=total_ventas,
                fondo_inicial=fondo_inicial,
                fondo_final=fondo_final,
                notas=notas or None
            )
            
            for metodo in metodos_pago:
                monto = totales_por_metodo.get(metodo.nombre, Decimal('0'))
                if monto > 0:
                    CierreCajaDetallePago.objects.create(
                        cierre=cierre,
                        metodo_pago=metodo,
                        monto=monto
                    )
            
            messages.success(request, f'Cierre de caja registrado. Total: Bs. {total_ventas:.2f}')
            return redirect('cierre_caja_index')
        except OperationalError as e:
            err_msg = str(e).lower()
            if any(x in err_msg for x in ('no such table', 'does not exist', "doesn't exist", 'table')):
                messages.error(
                    request,
                    'Las tablas de Cierre de Caja no existen. Ejecute: python manage.py migrate'
                )
                return redirect('cierre_caja_index')
            raise
    
    return render(request, 'gestion/cierre_caja_nuevo.html', {
        'total_ventas': total_ventas,
        'num_ventas': num_ventas,
        'hoy': hoy,
        'totales_por_metodo': totales_por_metodo,
        'metodos_pago': metodos_pago,
        'active': 'cierre_caja'
    })


@login_required
def cierre_caja_detail(request, pk):
    """Detalle de un cierre de caja: observaciones, totales por método de pago."""
    cierre = get_object_or_404(
        CierreCaja.objects.select_related('usuario').prefetch_related('detalles_pago__metodo_pago'),
        pk=pk
    )
    if not request.user.is_staff and cierre.usuario != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('No tiene permiso para ver este cierre.')
    return render(request, 'gestion/cierre_caja_detail.html', {
        'cierre': cierre,
        'active': 'cierre_caja'
    })


# --- Reportes (solo admin) ---

@login_required
@staff_required
def reportes_index(request):
    """Reportes: ventas por período, productos más vendidos, total por método de pago."""
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    from decimal import Decimal
    
    hoy = timezone.localtime(timezone.now()).date()
    fecha_inicio = request.GET.get('fecha_inicio', (hoy - timedelta(days=30)).strftime('%Y-%m-%d'))
    fecha_fin = request.GET.get('fecha_fin', hoy.strftime('%Y-%m-%d'))
    
    try:
        fi = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        ff = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except ValueError:
        fi = hoy - timedelta(days=30)
        ff = hoy
    
    if fi > ff:
        fi, ff = ff, fi
    
    ventas_periodo = Venta.objects.filter(
        fecha__date__gte=fi,
        fecha__date__lte=ff,
        estado='completado'
    )
    
    # Total ventas período
    total_periodo = ventas_periodo.aggregate(t=Sum('total'))['t'] or Decimal('0.00')
    num_ventas_periodo = ventas_periodo.count()
    
    # Productos más vendidos
    productos_mas_vendidos = DetalleVenta.objects.filter(
        venta__in=ventas_periodo
    ).values('producto__nombre').annotate(
        cantidad=Sum('cantidad'),
        total=Sum('subtotal')
    ).order_by('-cantidad')[:20]
    
    # Total por método de pago
    pagos_periodo = Pago.objects.filter(
        venta__in=ventas_periodo,
        validado=True
    ).values('metodo_pago__nombre').annotate(
        total=Sum('monto')
    ).order_by('-total')
    
    return render(request, 'gestion/reportes_index.html', {
        'fecha_inicio': fi.strftime('%Y-%m-%d'),
        'fecha_fin': ff.strftime('%Y-%m-%d'),
        'total_periodo': total_periodo,
        'num_ventas_periodo': num_ventas_periodo,
        'productos_mas_vendidos': productos_mas_vendidos,
        'pagos_periodo': pagos_periodo,
        'active': 'reportes'
    })