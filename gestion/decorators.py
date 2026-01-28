"""
Decoradores para control de roles: Administrador vs Cajero/Vendedor.

- Administrador: user.is_staff == True (acceso a productos, categorías, admin, etc.)
- Cajero/Vendedor: user.is_staff == False (solo Inicio, POS, ver Ventas)
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def staff_required(view_func):
    """
    Decorador que restringe la vista solo a usuarios con is_staff=True (Administrador).
    Los cajeros son redirigidos al inicio con un mensaje de acceso denegado.
    Debe usarse junto con @login_required (login_required primero).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.warning(
                request,
                'No tienes permiso para acceder a esta sección. Solo el administrador puede gestionarla.'
            )
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
