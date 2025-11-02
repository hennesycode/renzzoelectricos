"""
Modelos para el sistema de caja registradora.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


User = get_user_model()


class CajaRegistradora(models.Model):
    """
    Representa una sesión de caja registradora (apertura y cierre).
    """
    class EstadoChoices(models.TextChoices):
        ABIERTA = 'ABIERTA', _('Abierta')
        CERRADA = 'CERRADA', _('Cerrada')
    
    # Usuario que maneja la caja
    cajero = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cajas_manejadas',
        verbose_name=_('Cajero')
    )
    
    # Fechas y tiempos
    fecha_apertura = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de apertura')
    )
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de cierre')
    )
    
    # Estado de la caja
    estado = models.CharField(
        max_length=10,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ABIERTA,
        verbose_name=_('Estado')
    )
    
    # Montos de apertura
    monto_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Monto inicial'),
        help_text=_('Dinero en efectivo al abrir la caja')
    )
    
    # Montos de cierre
    monto_final_declarado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Monto final declarado'),
        help_text=_('Dinero contado al cerrar la caja')
    )
    
    monto_final_sistema = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Monto final sistema'),
        help_text=_('Monto calculado por el sistema')
    )
    
    diferencia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Diferencia'),
        help_text=_('Diferencia entre declarado y sistema')
    )
    
    # Observaciones
    observaciones_apertura = models.TextField(
        blank=True,
        verbose_name=_('Observaciones de apertura')
    )
    
    observaciones_cierre = models.TextField(
        blank=True,
        verbose_name=_('Observaciones de cierre')
    )
    
    class Meta:
        verbose_name = _('Caja Registradora')
        verbose_name_plural = _('Cajas Registradoras')
        ordering = ['-fecha_apertura']
    
    def __str__(self):
        fecha_str = self.fecha_apertura.strftime('%d/%m/%Y %H:%M')
        return f"Caja {self.cajero.username} - {fecha_str} ({self.get_estado_display()})"
    
    @property
    def duracion_abierta(self):
        """Calcula cuánto tiempo ha estado abierta la caja."""
        if self.fecha_cierre:
            return self.fecha_cierre - self.fecha_apertura
        else:
            from django.utils import timezone
            return timezone.now() - self.fecha_apertura
    
    def calcular_monto_sistema(self):
        """Calcula el monto que debería haber según los movimientos."""
        total_ingresos = self.movimientos.filter(
            tipo='INGRESO'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
        
        total_egresos = self.movimientos.filter(
            tipo='EGRESO'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
        
        return self.monto_inicial + total_ingresos - total_egresos
    
    def cerrar_caja(self, monto_final_declarado, observaciones_cierre=''):
        """Cierra la caja calculando diferencias."""
        from django.utils import timezone
        
        self.monto_final_declarado = monto_final_declarado
        self.monto_final_sistema = self.calcular_monto_sistema()
        self.diferencia = self.monto_final_declarado - self.monto_final_sistema
        self.observaciones_cierre = observaciones_cierre
        self.estado = self.EstadoChoices.CERRADA
        self.fecha_cierre = timezone.now()
        self.save()
        
        return self.diferencia


class TipoMovimiento(models.Model):
    """
    Tipos de movimientos de caja (Venta, Gasto, Cambio, etc.).
    """
    nombre = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Nombre')
    )
    
    codigo = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_('Código')
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    class Meta:
        verbose_name = _('Tipo de Movimiento')
        verbose_name_plural = _('Tipos de Movimientos')
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class MovimientoCaja(models.Model):
    """
    Movimientos individuales de dinero en la caja.
    """
    class TipoChoices(models.TextChoices):
        INGRESO = 'INGRESO', _('Ingreso')
        EGRESO = 'EGRESO', _('Egreso')
    
    # Relaciones
    caja = models.ForeignKey(
        CajaRegistradora,
        on_delete=models.CASCADE,
        related_name='movimientos',
        verbose_name=_('Caja')
    )
    
    tipo_movimiento = models.ForeignKey(
        TipoMovimiento,
        on_delete=models.CASCADE,
        verbose_name=_('Tipo de movimiento')
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Usuario')
    )
    
    # Datos del movimiento
    tipo = models.CharField(
        max_length=10,
        choices=TipoChoices.choices,
        verbose_name=_('Tipo')
    )
    
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Monto')
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
        help_text=_('Detalle del movimiento (opcional)')
    )
    
    referencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Referencia'),
        help_text=_('Número de factura, recibo, etc. (opcional)')
    )
    
    fecha_movimiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha del movimiento')
    )
    
    class Meta:
        verbose_name = _('Movimiento de Caja')
        verbose_name_plural = _('Movimientos de Caja')
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        signo = '+' if self.tipo == 'INGRESO' else '-'
        return f"{signo}${self.monto:,.2f} - {self.tipo_movimiento.nombre}"


class DenominacionMoneda(models.Model):
    """
    Denominaciones de monedas y billetes colombianos.
    """
    class TipoChoices(models.TextChoices):
        BILLETE = 'BILLETE', _('Billete')
        MONEDA = 'MONEDA', _('Moneda')
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        unique=True,
        verbose_name=_('Valor')
    )
    
    tipo = models.CharField(
        max_length=10,
        choices=TipoChoices.choices,
        verbose_name=_('Tipo')
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Orden'),
        help_text=_('Orden de aparición (menor número aparece primero)')
    )
    
    class Meta:
        verbose_name = _('Denominación de Moneda')
        verbose_name_plural = _('Denominaciones de Monedas')
        ordering = ['-valor']
    
    def __str__(self):
        return f"${self.valor:,.0f} ({self.get_tipo_display()})"


class ConteoEfectivo(models.Model):
    """
    Conteo detallado de efectivo (puede ser de apertura o cierre).
    """
    class TipoConteoChoices(models.TextChoices):
        APERTURA = 'APERTURA', _('Apertura')
        CIERRE = 'CIERRE', _('Cierre')
    
    caja = models.ForeignKey(
        CajaRegistradora,
        on_delete=models.CASCADE,
        related_name='conteos',
        verbose_name=_('Caja')
    )
    
    tipo_conteo = models.CharField(
        max_length=10,
        choices=TipoConteoChoices.choices,
        default=TipoConteoChoices.CIERRE,
        verbose_name=_('Tipo de conteo')
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,  # Temporal para migración
        blank=True,
        verbose_name=_('Usuario que realizó el conteo')
    )
    
    fecha_conteo = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de conteo')
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Total contado')
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name=_('Observaciones')
    )
    
    class Meta:
        verbose_name = _('Conteo de Efectivo')
        verbose_name_plural = _('Conteos de Efectivo')
        ordering = ['-fecha_conteo']
    
    def __str__(self):
        return f"Conteo {self.get_tipo_conteo_display()} ${self.total:,.2f} - {self.caja}"


class DetalleConteo(models.Model):
    """
    Detalle de cada denominación contada.
    """
    conteo = models.ForeignKey(
        ConteoEfectivo,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name=_('Conteo')
    )
    
    denominacion = models.ForeignKey(
        DenominacionMoneda,
        on_delete=models.CASCADE,
        verbose_name=_('Denominación')
    )
    
    cantidad = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Cantidad')
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Subtotal')
    )
    
    class Meta:
        verbose_name = _('Detalle de Conteo')
        verbose_name_plural = _('Detalles de Conteo')
        unique_together = ['conteo', 'denominacion']
    
    def __str__(self):
        return f"{self.cantidad}x ${self.denominacion.valor:,.0f} = ${self.subtotal:,.2f}"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el subtotal."""
        self.subtotal = self.cantidad * self.denominacion.valor
        super().save(*args, **kwargs)
