"""
Modelos para el sistema de facturación.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Factura(models.Model):
    """
    Modelo principal de Factura.
    Almacena la información general de cada factura emitida.
    """
    
    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia Bancaria'
        TARJETA = 'TARJETA', 'Tarjeta de Crédito/Débito'
        CHEQUE = 'CHEQUE', 'Cheque'
        OTRO = 'OTRO', 'Otro'
    
    class CondicionPago(models.TextChoices):
        CONTADO = 'CONTADO', 'Contado (Pago Inmediato)'
        CREDITO_15 = 'CREDITO_15', 'Crédito 15 Días'
        CREDITO_30 = 'CREDITO_30', 'Crédito 30 Días'
        CREDITO_60 = 'CREDITO_60', 'Crédito 60 Días'
        CREDITO_90 = 'CREDITO_90', 'Crédito 90 Días'
    
    # Información básica
    codigo_factura = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Código de Factura',
        help_text='Formato: FACT-000001'
    )
    
    fecha_emision = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Emisión'
    )
    
    # Cliente
    cliente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='facturas',
        verbose_name='Cliente',
        limit_choices_to={'rol': 'CLIENTE'}
    )
    
    # Usuario que emite la factura
    usuario_emisor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='facturas_emitidas',
        verbose_name='Usuario Emisor'
    )
    
    # Totales
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Subtotal'
    )
    
    total_descuentos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total Descuentos'
    )
    
    subtotal_neto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Subtotal Neto'
    )
    
    total_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total IVA (19%)'
    )
    
    total_pagar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Total a Pagar'
    )
    
    # Condiciones de pago
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
        verbose_name='Método de Pago'
    )
    
    condicion_pago = models.CharField(
        max_length=20,
        choices=CondicionPago.choices,
        default=CondicionPago.CONTADO,
        verbose_name='Condición de Pago'
    )
    
    # Notas
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas',
        help_text='Condiciones, garantías, agradecimientos, etc.'
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Modificación'
    )
    
    activa = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text='Indica si la factura está activa o fue anulada'
    )
    
    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['-fecha_emision']),
            models.Index(fields=['codigo_factura']),
            models.Index(fields=['cliente']),
        ]
    
    def __str__(self):
        return f"{self.codigo_factura} - {self.cliente.get_full_name()} - ${self.total_pagar}"
    
    def generar_codigo_factura(self):
        """
        Genera el código único de factura en formato FACT-000001
        """
        ultima_factura = Factura.objects.all().order_by('-id').first()
        if ultima_factura:
            ultimo_numero = int(ultima_factura.codigo_factura.split('-')[1])
            nuevo_numero = ultimo_numero + 1
        else:
            nuevo_numero = 1
        
        return f"FACT-{nuevo_numero:06d}"
    
    def save(self, *args, **kwargs):
        """
        Genera el código de factura automáticamente si no existe
        """
        if not self.codigo_factura:
            self.codigo_factura = self.generar_codigo_factura()
        super().save(*args, **kwargs)


class DetalleFactura(models.Model):
    """
    Modelo para los ítems/productos de cada factura.
    Cada fila representa un producto en la factura.
    """
    
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Factura'
    )
    
    # Información del producto
    descripcion = models.CharField(
        max_length=500,
        verbose_name='Descripción',
        help_text='Nombre o descripción del producto/servicio'
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name='Cantidad'
    )
    
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Precio Unitario',
        help_text='Precio sin impuestos'
    )
    
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Descuento',
        help_text='Descuento en pesos'
    )
    
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor Unitario',
        help_text='Precio unitario después del descuento'
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Total',
        help_text='Valor unitario × Cantidad'
    )
    
    # Referencia opcional al producto de Oscar (si existe)
    producto_oscar_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Producto Oscar',
        help_text='ID del producto en el catálogo Oscar'
    )
    
    # Orden en la factura
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden'
    )
    
    class Meta:
        verbose_name = 'Detalle de Factura'
        verbose_name_plural = 'Detalles de Factura'
        ordering = ['orden', 'id']
    
    def __str__(self):
        return f"{self.descripcion} - Cant: {self.cantidad} - Total: ${self.total}"
    
    def calcular_valores(self):
        """
        Calcula valor_unitario y total basándose en precio, descuento y cantidad
        """
        self.valor_unitario = self.precio_unitario - self.descuento
        self.total = self.valor_unitario * self.cantidad
    
    def save(self, *args, **kwargs):
        """
        Calcula valores automáticamente antes de guardar
        """
        self.calcular_valores()
        super().save(*args, **kwargs)
