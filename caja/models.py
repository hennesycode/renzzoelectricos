"""
Modelos para el sistema de caja registradora.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
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
    
    # Distribución del dinero al cierre
    dinero_en_caja = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Dinero en caja'),
        help_text=_('Dinero que quedó en la caja al cerrar')
    )
    
    dinero_guardado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Dinero guardado'),
        help_text=_('Dinero guardado fuera de la caja al cerrar')
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
        """
        Calcula el monto que debería haber EN EFECTIVO según los movimientos.
        INCLUYE:
        - Movimiento de apertura (dinero inicial en caja)
        - Ingresos en efectivo (excluir banco)
        EXCLUYE:
        - Entradas al banco (tienen [BANCO] en descripción)
        """
        # Ingresos en efectivo (incluir apertura, excluir banco)
        total_ingresos = self.movimientos.filter(
            tipo='INGRESO'
        ).exclude(
            descripcion__icontains='[BANCO]'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Todos los egresos (siempre salen de caja)
        total_egresos = self.movimientos.filter(
            tipo='EGRESO'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Ahora el cálculo es: total_ingresos - total_egresos
        # (porque total_ingresos ya incluye la apertura)
        return total_ingresos - total_egresos
    
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
    class TipoBaseChoices(models.TextChoices):
        INGRESO = 'INGRESO', _('Ingreso')
        GASTO = 'GASTO', _('Gasto Operativo')
        INVERSION = 'INVERSION', _('Compra / Inversión')
        INTERNO = 'INTERNO', _('Movimiento Interno')
    
    nombre = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Nombre')
    )
    
    codigo = models.CharField(
        max_length=20,
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
    
    tipo_base = models.CharField(
        max_length=20,
        choices=TipoBaseChoices.choices,
        default=TipoBaseChoices.GASTO,
        verbose_name=_('Tipo Base'),
        help_text=_('Categoría base para filtrado en tesorería')
    )
    
    class Meta:
        verbose_name = _('Tipo de Movimiento')
        verbose_name_plural = _('Tipos de Movimientos')
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    # Códigos fijos que deben existir por defecto y no pueden eliminarse
    DEFAULT_CODES = {
        'VENTA', 'COBRO_CXC', 'DEV_PAGO', 'REC_GASTOS',
        'GASTO', 'COMPRA', 'FLETES', 'DEV_VENTA', 'SUELDOS', 'SUMINISTROS', 
        'ALQUILER', 'MANTENIMIENTO', 'APERTURA'
    }

    def delete(self, *args, **kwargs):
        """Impedir la eliminación de tipos de movimiento por defecto."""
        try:
            if self.codigo in self.DEFAULT_CODES:
                raise Exception('No se permite eliminar tipos de movimiento por defecto')
        except Exception:
            # Re-raise as a ValueError para que Django lo maneje en admin/flows
            raise
        return super().delete(*args, **kwargs)


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
    
    # Relación con tesorería (para sincronización)
    transaccion_asociada = models.OneToOneField(
        'TransaccionGeneral',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimiento_caja_origen',
        verbose_name=_('Transacción asociada'),
        help_text=_('Transacción de tesorería generada por este movimiento')
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
        unique_together = ['valor', 'tipo']  # Permite mismo valor si son tipos diferentes
    
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


# ============================================================================
# MODELOS DE TESORERÍA
# ============================================================================

class Cuenta(models.Model):
    """
    Representa cuentas financieras del negocio (Banco, Reserva).
    La 'Caja' no es una cuenta porque su saldo es volátil y 
    lo gestiona CajaRegistradora.
    """
    class TipoCuentaChoices(models.TextChoices):
        BANCO = 'BANCO', _('Banco')
        RESERVA = 'RESERVA', _('Reserva / Dinero Guardado')
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Nombre de la cuenta')
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TipoCuentaChoices.choices,
        verbose_name=_('Tipo de cuenta')
    )
    
    saldo_actual = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Saldo actual'),
        help_text=_('Saldo disponible en esta cuenta')
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    class Meta:
        verbose_name = _('Cuenta')
        verbose_name_plural = _('Cuentas')
        ordering = ['tipo', 'nombre']
    
    def __str__(self):
        """
        Representación en string de la cuenta.
        Maneja errores para evitar crashes en el admin.
        """
        try:
            tipo_display = self.get_tipo_display() if hasattr(self, 'get_tipo_display') else self.tipo
            return f"{self.nombre} ({tipo_display}) - ${self.saldo_actual:,.2f}"
        except Exception:
            # Fallback si hay algún error
            return f"{self.nombre} ({self.tipo})"
    
    def clean(self):
        """
        Validación personalizada: solo puede haber 1 cuenta activa de cada tipo.
        """
        from django.core.exceptions import ValidationError
        
        # Verificar si ya existe una cuenta activa del mismo tipo
        if self.activo:
            cuentas_mismo_tipo = Cuenta.objects.filter(
                tipo=self.tipo,
                activo=True
            ).exclude(pk=self.pk)
            
            if cuentas_mismo_tipo.exists():
                cuenta_existente = cuentas_mismo_tipo.first()
                tipo_nombre = 'BANCO' if self.tipo == 'BANCO' else 'RESERVA/Dinero Guardado'
                raise ValidationError({
                    'tipo': f'⚠️ Ya existe una cuenta {tipo_nombre} activa: "{cuenta_existente.nombre}". '
                            f'El sistema solo permite 1 cuenta activa de cada tipo. '
                            f'Desactiva la cuenta existente primero si quieres crear una nueva.'
                })
    
    def save(self, *args, **kwargs):
        """
        Sobrescribir save para ejecutar validación.
        """
        self.full_clean()  # Ejecuta clean()
        super().save(*args, **kwargs)
    
    def tiene_fondos_suficientes(self, monto):
        """Verifica si la cuenta tiene fondos suficientes."""
        return self.saldo_actual >= monto
    
    def agregar_fondos(self, monto):
        """Agrega fondos a la cuenta."""
        self.saldo_actual += Decimal(str(monto))
        self.save()
    
    def retirar_fondos(self, monto):
        """Retira fondos de la cuenta (con validación)."""
        monto_decimal = Decimal(str(monto))
        if not self.tiene_fondos_suficientes(monto_decimal):
            raise ValueError(f'Fondos insuficientes en {self.nombre}')
        self.saldo_actual -= monto_decimal
        self.save()
    
    @classmethod
    def get_cuenta_caja_virtual(cls):
        """Obtiene o crea la cuenta virtual para tracking de caja."""
        cuenta, created = cls.objects.get_or_create(
            nombre='Caja Virtual',
            defaults={
                'tipo': 'RESERVA',
                'saldo_actual': Decimal('0.00'),
                'activo': False
            }
        )
        return cuenta


class TransaccionGeneral(models.Model):
    """
    Log de todos los movimientos de Tesorería (Banco y Reserva).
    Los movimientos de Caja se quedan en MovimientoCaja.
    """
    class TipoTransaccionChoices(models.TextChoices):
        INGRESO = 'INGRESO', _('Ingreso')
        EGRESO = 'EGRESO', _('Egreso')
        TRANSFERENCIA = 'TRANSFERENCIA', _('Transferencia')
    
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de transacción')
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TipoTransaccionChoices.choices,
        verbose_name=_('Tipo de transacción')
    )
    
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Monto')
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    
    referencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Referencia'),
        help_text=_('Número de comprobante, recibo, etc.')
    )
    
    # Relaciones
    tipo_movimiento = models.ForeignKey(
        TipoMovimiento,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo de movimiento')
    )
    
    cuenta = models.ForeignKey(
        Cuenta,
        on_delete=models.PROTECT,
        related_name='transacciones',
        verbose_name=_('Cuenta'),
        help_text=_('Cuenta de origen (para egresos) o destino (para ingresos)')
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name=_('Usuario')
    )
    
    # Relación opcional con MovimientoCaja (para tracking unificado)
    movimiento_caja_asociado = models.OneToOneField(
        'MovimientoCaja',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Movimiento de caja asociado')
    )
    
    # Para transferencias entre cuentas
    cuenta_destino = models.ForeignKey(
        Cuenta,
        on_delete=models.PROTECT,
        related_name='transferencias_recibidas',
        null=True,
        blank=True,
        verbose_name=_('Cuenta destino')
    )
    
    class Meta:
        verbose_name = _('Transacción General')
        verbose_name_plural = _('Transacciones Generales')
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.tipo_movimiento.nombre} - ${self.monto:,.2f}"


# ============================================================================
# SEÑALES PARA SINCRONIZACIÓN AUTOMÁTICA
# ============================================================================

@receiver(post_save, sender='caja.CajaRegistradora')
def crear_transaccion_apertura_caja(sender, instance, created, **kwargs):
    """
    Cuando se abre una caja, crear:
    1. Movimiento de apertura en la caja 
    2. Transacción en tesorería (Origen: caja, Tipo: apertura caja)
    """
    if created and instance.estado == 'ABIERTA':
        # 1. Crear movimiento de apertura en la caja
        tipo_apertura, _ = TipoMovimiento.objects.get_or_create(
            codigo='APERTURA',
            defaults={
                'nombre': 'Apertura de Caja',
                'descripcion': 'Dinero inicial al abrir la caja',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
                'activo': True
            }
        )
        
        movimiento_apertura = MovimientoCaja.objects.create(
            caja=instance,
            tipo_movimiento=tipo_apertura,
            tipo='INGRESO',
            monto=instance.monto_inicial,
            descripcion=f'Apertura de caja - Monto inicial: ${instance.monto_inicial:,.2f}',
            usuario=instance.cajero
        )
        
        # 2. Crear transacción en tesorería
        # Primero obtener o crear cuenta "Caja" virtual para tracking
        cuenta_caja_virtual, _ = Cuenta.objects.get_or_create(
            nombre='Caja Virtual',
            defaults={
                'tipo': 'RESERVA',  # Usar RESERVA como tipo base
                'saldo_actual': Decimal('0.00'),
                'activo': False  # No mostrar en listados normales
            }
        )
        
        transaccion = TransaccionGeneral.objects.create(
            tipo='INGRESO',
            monto=instance.monto_inicial,
            descripcion=f'Apertura caja - Cajero: {instance.cajero.username}',
            referencia=f'APERTURA-CAJA-{instance.id}',
            tipo_movimiento=tipo_apertura,
            cuenta=cuenta_caja_virtual,
            usuario=instance.cajero
        )
        
        # Vincular movimiento y transacción
        movimiento_apertura.transaccion_asociada = transaccion
        movimiento_apertura.save()


@receiver(post_save, sender='caja.MovimientoCaja')
def crear_transaccion_tesoreria_desde_movimiento(sender, instance, created, **kwargs):
    """
    Cuando se crea un movimiento en caja (que no sea apertura), crear la transacción
    correspondiente en tesorería con origen caja y tipo entrada:categoría o salida:categoría
    """
    if created and instance.tipo_movimiento.codigo != 'APERTURA':
        # Obtener cuenta destino según el tipo de movimiento
        if '[BANCO]' in instance.descripcion:
            # Es una entrada al banco
            cuenta_destino = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
            tipo_origen = 'banco'
            descripcion_base = f'Entrada:{instance.tipo_movimiento.nombre}'
        else:
            # Es un movimiento de caja normal
            cuenta_caja_virtual, _ = Cuenta.objects.get_or_create(
                nombre='Caja Virtual',
                defaults={
                    'tipo': 'RESERVA',
                    'saldo_actual': Decimal('0.00'),
                    'activo': False
                }
            )
            cuenta_destino = cuenta_caja_virtual
            tipo_origen = 'caja'
            
            if instance.tipo == 'INGRESO':
                descripcion_base = f'Entrada:{instance.tipo_movimiento.nombre}'
            else:
                descripcion_base = f'Salida:{instance.tipo_movimiento.nombre}'
        
        if cuenta_destino:
            # Crear transacción en tesorería
            transaccion = TransaccionGeneral.objects.create(
                tipo=instance.tipo,  # INGRESO o EGRESO
                monto=instance.monto,
                descripcion=f'Origen {tipo_origen} - {descripcion_base} - {instance.descripcion}',
                referencia=instance.referencia or f'MOV-{instance.id}',
                tipo_movimiento=instance.tipo_movimiento,
                cuenta=cuenta_destino,
                usuario=instance.usuario
            )
            
            # Vincular movimiento y transacción
            instance.transaccion_asociada = transaccion
            instance.save(update_fields=['transaccion_asociada'])
            
            # Actualizar saldo de cuenta si es banco
            if cuenta_destino.tipo == 'BANCO':
                if instance.tipo == 'INGRESO':
                    cuenta_destino.saldo_actual += instance.monto
                else:
                    cuenta_destino.saldo_actual -= instance.monto
                cuenta_destino.save(update_fields=['saldo_actual'])


@receiver(post_delete, sender='caja.MovimientoCaja')
def eliminar_transaccion_tesoreria_asociada(sender, instance, **kwargs):
    """
    Cuando se elimina un movimiento de caja, eliminar también su transacción asociada
    y ajustar el saldo de la cuenta si es necesario
    """
    if instance.transaccion_asociada:
        # Si hay cuenta banco asociada, ajustar saldo
        if (instance.transaccion_asociada.cuenta and 
            instance.transaccion_asociada.cuenta.tipo == 'BANCO'):
            
            cuenta = instance.transaccion_asociada.cuenta
            if instance.tipo == 'INGRESO':
                cuenta.saldo_actual -= instance.monto
            else:
                cuenta.saldo_actual += instance.monto
            cuenta.save(update_fields=['saldo_actual'])
        
        # Eliminar transacción asociada
        instance.transaccion_asociada.delete()
