from django.contrib import admin
from .models import (
    Categoria, Producto, Cliente, Venta, DetalleVenta,
    MetodoPago, Promocion, Pago, CierreCaja, CierreCajaDetallePago
)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'costo', 'precio_venta', 'descuento', 'precio_final', 'stock', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion',)
    
    def precio_final(self, obj):
        return f"Bs. {obj.precio_final():.2f}"
    precio_final.short_description = 'Precio Final'

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'ci_nit', 'telefono', 'email', 'activo', 'fecha_registro')
    list_filter = ('activo', 'fecha_registro')
    search_fields = ('nombre_completo', 'ci_nit', 'telefono', 'email')
    readonly_fields = ('fecha_registro',)

@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'activo', 'requiere_validacion')
    list_filter = ('tipo', 'activo', 'requiere_validacion')
    search_fields = ('nombre',)

@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descuento_porcentaje', 'fecha_inicio', 'fecha_fin', 'activo', 'esta_vigente')
    list_filter = ('activo', 'fecha_inicio', 'fecha_fin')
    search_fields = ('nombre', 'descripcion')
    filter_horizontal = ('productos',)

    def save_model(self, request, obj, form, change):
        obj.full_clean()  # Valida fecha_fin > fecha_inicio
        super().save_model(request, obj, form, change)

    def esta_vigente(self, obj):
        return obj.esta_vigente()
    esta_vigente.boolean = True
    esta_vigente.short_description = 'Vigente'

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    readonly_fields = ('subtotal', 'descuento_aplicado')

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ('fecha_pago', 'fecha_validacion', 'validado_por')

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'usuario', 'modo_consumo', 'fecha', 'subtotal', 'descuento_total', 'total', 'estado', 'tiene_pago_completo')
    list_filter = ('estado', 'modo_consumo', 'fecha')
    search_fields = ('cliente__nombre_completo', 'usuario__username')
    readonly_fields = ('fecha', 'subtotal', 'descuento_total', 'total')
    inlines = [DetalleVentaInline, PagoInline]
    
    def tiene_pago_completo(self, obj):
        return obj.tiene_pago_completo()
    tiene_pago_completo.boolean = True
    tiene_pago_completo.short_description = 'Pago Completo'

class CierreCajaDetallePagoInline(admin.TabularInline):
    model = CierreCajaDetallePago
    extra = 0
    readonly_fields = ('metodo_pago', 'monto')


@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_cierre', 'total_ventas', 'fondo_inicial', 'fondo_final')
    list_filter = ('usuario', 'fecha_cierre')
    search_fields = ('usuario__username', 'notas')
    readonly_fields = ('fecha_cierre',)
    inlines = [CierreCajaDetallePagoInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta', 'metodo_pago', 'monto', 'fecha_pago', 'validado', 'validado_por')
    list_filter = ('validado', 'metodo_pago', 'fecha_pago')
    search_fields = ('venta__id', 'referencia')
    readonly_fields = ('fecha_pago', 'fecha_validacion', 'validado_por')
    
    def save_model(self, request, obj, form, change):
        # Si se marca como validado y no tiene validado_por, asignar el usuario actual
        if obj.validado and not obj.validado_por:
            obj.validar_pago(request.user)
        else:
            # Si ya está validado o no se está validando, guardar normalmente
            super().save_model(request, obj, form, change)
