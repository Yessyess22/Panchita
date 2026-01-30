"""Template tags para gestion app."""
from django import template

register = template.Library()


@register.filter
def modo_consumo_safe(venta):
    """Retorna modo_consumo de la venta o 'local' si no existe (compatibilidad)."""
    return getattr(venta, 'modo_consumo', 'local')
