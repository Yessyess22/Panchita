from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    # Estructura de precios mejorada
    costo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Costo de producción/compra"
    )
    precio_venta = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Precio de venta al público"
    )
    descuento = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text="Porcentaje de descuento (0-100)"
    )
    
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def precio_final(self):
        """Calcula el precio final con descuento aplicado"""
        if self.descuento > 0:
            descuento_monto = self.precio_venta * (self.descuento / Decimal('100'))
            precio_final = self.precio_venta - descuento_monto
            # Redondear a 2 decimales
            return precio_final.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return self.precio_venta
    
    def margen_ganancia(self):
        """Calcula el margen de ganancia en porcentaje"""
        if self.costo > 0:
            ganancia = self.precio_final() - self.costo
            return (ganancia / self.costo) * 100
        return 0
    
    def tiene_stock(self, cantidad=1):
        """Verifica si hay stock suficiente"""
        return self.stock >= cantidad

class Cliente(models.Model):
    nombre_completo = models.CharField(max_length=150)
    ci_nit = models.CharField(max_length=20, blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre_completo']
    
    def __str__(self):
        return self.nombre_completo

class MetodoPago(models.Model):
    TIPO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('qr', 'Código QR'),
        ('transferencia', 'Transferencia Bancaria'),
    ]
    
    nombre = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    requiere_validacion = models.BooleanField(
        default=False,
        help_text="Si requiere validación manual del pago"
    )
    
    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Promocion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    descuento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100'))]
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activo = models.BooleanField(default=True)
    productos = models.ManyToManyField(Producto, related_name='promociones', blank=True)
    
    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.nombre} ({self.descuento_porcentaje}%)"
    
    def esta_vigente(self):
        """Verifica si la promoción está vigente"""
        ahora = timezone.now()
        return self.activo and self.fecha_inicio <= ahora <= self.fecha_fin
    
    def aplicar_a_producto(self, producto):
        """Aplica la promoción a un producto si está vigente"""
        if self.esta_vigente() and producto in self.productos.all():
            return True
        return False

class Venta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    MODO_CONSUMO_CHOICES = [
        ('local', 'En el local'),
        ('llevar', 'Para llevar'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('ticket', 'Ticket'),
        ('factura', 'Factura'),
    ]
    
    fecha = models.DateTimeField(auto_now_add=True)
    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='ticket',
        verbose_name='Tipo de documento'
    )
    numero_factura = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Número de factura',
        help_text='Solo para ventas tipo factura'
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Vendedor")
    modo_consumo = models.CharField(
        max_length=10,
        choices=MODO_CONSUMO_CHOICES,
        default='local',
        verbose_name='Modo de consumo'
    )
    
    # Estructura de totales mejorada
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Venta #{self.id} - {self.cliente}"
    
    def calcular_totales(self):
        """Calcula subtotal, descuentos y total de la venta"""
        detalles = self.detalles.all()
        self.subtotal = sum(detalle.subtotal for detalle in detalles)
        self.descuento_total = sum(detalle.descuento_aplicado for detalle in detalles)
        self.total = self.subtotal - self.descuento_total
        self.save()
    
    def tiene_pago_completo(self):
        """Verifica si la venta tiene el pago completo"""
        total_pagado = sum(pago.monto for pago in self.pagos.filter(validado=True))
        return total_pagado >= self.total

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_porcentaje = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
    )
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Calcular subtotal base
        subtotal_base = self.cantidad * self.precio_unitario
        
        # Calcular descuento
        if self.descuento_porcentaje > 0:
            self.descuento_aplicado = subtotal_base * (self.descuento_porcentaje / 100)
        else:
            self.descuento_aplicado = 0
        
        # Calcular subtotal final
        self.subtotal = subtotal_base - self.descuento_aplicado
        
        super().save(*args, **kwargs)

class Pago(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Número de referencia o transacción"
    )
    validado = models.BooleanField(default=False)
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    validado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_validados'
    )
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago {self.metodo_pago} - Bs. {self.monto} (Venta #{self.venta.id})"
    
    def validar_pago(self, usuario):
        """Valida el pago"""
        if not self.validado:
            self.validado = True
            self.fecha_validacion = timezone.now()
            self.validado_por = usuario
            self.save()
            
            # Verificar si la venta está completamente pagada
            if self.venta.tiene_pago_completo() and self.venta.estado == 'pendiente':
                self.venta.estado = 'completado'
                self.venta.save()
            
            return True
        return False
    
    def clean(self):
        """Validaciones del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que el monto no exceda el total de la venta
        if self.venta:
            total_pagado = sum(
                pago.monto for pago in self.venta.pagos.exclude(id=self.id)
            )
            if total_pagado + self.monto > self.venta.total:
                raise ValidationError(
                    f'El monto total de pagos ({total_pagado + self.monto}) '
                    f'excede el total de la venta ({self.venta.total})'
                )


class CierreCaja(models.Model):
    """Registro de cierre de caja al final del turno."""
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cierres_caja')
    fecha_cierre = models.DateTimeField(default=timezone.now)
    total_ventas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )
    fondo_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    fondo_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    notas = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Cierre de Caja"
        verbose_name_plural = "Cierres de Caja"
        ordering = ['-fecha_cierre']

    def __str__(self):
        return f"Cierre {self.usuario.username} - {self.fecha_cierre.strftime('%d/%m/%Y %H:%M')}"


class CierreCajaDetallePago(models.Model):
    """Total por método de pago en un cierre de caja."""
    cierre = models.ForeignKey(CierreCaja, on_delete=models.CASCADE, related_name='detalles_pago')
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))]
    )

    class Meta:
        verbose_name = "Detalle de pago (cierre)"
        verbose_name_plural = "Detalles de pago (cierre)"
        unique_together = [['cierre', 'metodo_pago']]
