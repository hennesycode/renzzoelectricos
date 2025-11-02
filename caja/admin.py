"""
Configuración del administrador para la app caja.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    DenominacionMoneda, ConteoEfectivo, DetalleConteo
)


class MovimientoCajaInline(admin.TabularInline):
    """
    Inline para mostrar movimientos en la caja.
    """
    model = MovimientoCaja
    extra = 0
    readonly_fields = ('fecha_movimiento', 'usuario', 'tipo', 'tipo_movimiento', 'monto', 'descripcion', 'referencia')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """No permitir agregar movimientos desde el admin de caja."""
        return False


class ConteoEfectivoInline(admin.TabularInline):
    """
    Inline para mostrar conteos de efectivo.
    """
    model = ConteoEfectivo
    extra = 0
    readonly_fields = ('tipo_conteo', 'usuario', 'fecha_conteo', 'total', 'observaciones')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        """No permitir agregar conteos desde el admin."""
        return False


@admin.register(CajaRegistradora)
class CajaRegistradoraAdmin(admin.ModelAdmin):
    """
    Administrador completo para CajaRegistradora con todos los datos visibles.
    """
    list_display = (
        'id', 
        'cajero_info', 
        'fecha_apertura', 
        'fecha_cierre', 
        'estado_badge',
        'monto_inicial_fmt',
        'monto_final_declarado_fmt',
        'monto_final_sistema_fmt',
        'diferencia_fmt',
        'duracion'
    )
    list_filter = ('estado', 'fecha_apertura', 'fecha_cierre', 'cajero')
    search_fields = ('id', 'cajero__username', 'cajero__first_name', 'cajero__last_name', 'observaciones_apertura', 'observaciones_cierre')
    ordering = ('-fecha_apertura',)
    readonly_fields = (
        'fecha_apertura', 
        'monto_final_sistema', 
        'diferencia',
        'total_ingresos',
        'total_egresos',
        'duracion_formateada'
    )
    inlines = [MovimientoCajaInline, ConteoEfectivoInline]
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('cajero', 'estado', 'fecha_apertura', 'fecha_cierre', 'duracion_formateada')
        }),
        (_('Montos de Apertura'), {
            'fields': ('monto_inicial',)
        }),
        (_('Montos de Cierre'), {
            'fields': ('monto_final_declarado', 'monto_final_sistema', 'diferencia')
        }),
        (_('Resumen de Movimientos'), {
            'fields': ('total_ingresos', 'total_egresos'),
            'classes': ('collapse',)
        }),
        (_('Observaciones'), {
            'fields': ('observaciones_apertura', 'observaciones_cierre')
        }),
    )
    
    def cajero_info(self, obj):
        """Muestra información completa del cajero."""
        full_name = obj.cajero.get_full_name() or obj.cajero.username
        email = obj.cajero.email or 'Sin email'
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            full_name,
            email
        )
    cajero_info.short_description = 'Cajero'
    
    def estado_badge(self, obj):
        """Muestra el estado con color."""
        if obj.estado == 'ABIERTA':
            color = 'green'
            icon = '🟢'
        else:
            color = 'gray'
            icon = '⚫'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def monto_inicial_fmt(self, obj):
        """Formatea el monto inicial."""
        return format_html('${:,.0f}', obj.monto_inicial)
    monto_inicial_fmt.short_description = 'Monto Inicial'
    monto_inicial_fmt.admin_order_field = 'monto_inicial'
    
    def monto_final_declarado_fmt(self, obj):
        """Formatea el monto final declarado."""
        if obj.monto_final_declarado:
            return format_html('${:,.0f}', obj.monto_final_declarado)
        return '-'
    monto_final_declarado_fmt.short_description = 'Final Declarado'
    monto_final_declarado_fmt.admin_order_field = 'monto_final_declarado'
    
    def monto_final_sistema_fmt(self, obj):
        """Formatea el monto final del sistema."""
        if obj.monto_final_sistema:
            return format_html('${:,.0f}', obj.monto_final_sistema)
        return '-'
    monto_final_sistema_fmt.short_description = 'Final Sistema'
    monto_final_sistema_fmt.admin_order_field = 'monto_final_sistema'
    
    def diferencia_fmt(self, obj):
        """Formatea la diferencia con color."""
        if obj.diferencia is not None:
            color = 'red' if obj.diferencia < 0 else ('green' if obj.diferencia > 0 else 'gray')
            return format_html(
                '<span style="color: {}; font-weight: bold;">${:,.0f}</span>',
                color,
                obj.diferencia
            )
        return '-'
    diferencia_fmt.short_description = 'Diferencia'
    diferencia_fmt.admin_order_field = 'diferencia'
    
    def duracion(self, obj):
        """Muestra la duración de la caja."""
        duracion = obj.duracion_abierta
        horas = duracion.total_seconds() / 3600
        return format_html('{:.1f}h', horas)
    duracion.short_description = 'Duración'
    
    def duracion_formateada(self, obj):
        """Muestra la duración formateada para el detalle."""
        duracion = obj.duracion_abierta
        dias = duracion.days
        segundos = duracion.seconds
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        
        if dias > 0:
            return f'{dias}d {horas}h {minutos}m'
        elif horas > 0:
            return f'{horas}h {minutos}m'
        else:
            return f'{minutos}m'
    duracion_formateada.short_description = 'Duración'
    
    def total_ingresos(self, obj):
        """Calcula y muestra el total de ingresos."""
        from decimal import Decimal
        from django.db.models import Sum
        total = obj.movimientos.filter(tipo='INGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        return format_html('${:,.0f}', total)
    total_ingresos.short_description = 'Total Ingresos'
    
    def total_egresos(self, obj):
        """Calcula y muestra el total de egresos."""
        from decimal import Decimal
        from django.db.models import Sum
        total = obj.movimientos.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        return format_html('${:,.0f}', total)
    total_egresos.short_description = 'Total Egresos'


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    """
    Administrador completo para MovimientoCaja con todos los datos visibles.
    """
    list_display = (
        'id',
        'caja_info',
        'tipo_badge',
        'tipo_movimiento',
        'monto_fmt',
        'usuario_info',
        'fecha_movimiento',
        'referencia'
    )
    list_filter = ('tipo', 'tipo_movimiento', 'fecha_movimiento', 'usuario', 'caja__cajero')
    search_fields = (
        'id',
        'descripcion', 
        'referencia', 
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'caja__id'
    )
    ordering = ('-fecha_movimiento',)
    readonly_fields = ('fecha_movimiento',)
    date_hierarchy = 'fecha_movimiento'
    
    fieldsets = (
        (_('Información del Movimiento'), {
            'fields': ('caja', 'tipo', 'tipo_movimiento', 'usuario', 'fecha_movimiento')
        }),
        (_('Detalles Financieros'), {
            'fields': ('monto', 'descripcion', 'referencia')
        }),
    )
    
    def caja_info(self, obj):
        """Muestra información de la caja."""
        return format_html(
            'Caja #{} - {}<br><small>{}</small>',
            obj.caja.id,
            obj.caja.cajero.username,
            obj.caja.fecha_apertura.strftime('%d/%m/%Y %H:%M')
        )
    caja_info.short_description = 'Caja'
    
    def tipo_badge(self, obj):
        """Muestra el tipo con color."""
        if obj.tipo == 'INGRESO':
            color = 'green'
            icon = '↑'
        else:
            color = 'red'
            icon = '↓'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    tipo_badge.admin_order_field = 'tipo'
    
    def monto_fmt(self, obj):
        """Formatea el monto con color."""
        color = 'green' if obj.tipo == 'INGRESO' else 'red'
        signo = '+' if obj.tipo == 'INGRESO' else '-'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ${:,.0f}</span>',
            color,
            signo,
            obj.monto
        )
    monto_fmt.short_description = 'Monto'
    monto_fmt.admin_order_field = 'monto'
    
    def usuario_info(self, obj):
        """Muestra información del usuario."""
        full_name = obj.usuario.get_full_name() or obj.usuario.username
        return format_html('<strong>{}</strong>', full_name)
    usuario_info.short_description = 'Usuario'
    usuario_info.admin_order_field = 'usuario__username'


@admin.register(TipoMovimiento)
class TipoMovimientoAdmin(admin.ModelAdmin):
    """
    Administrador completo para TipoMovimiento.
    """
    list_display = ('id', 'codigo', 'nombre', 'activo_badge', 'descripcion_short')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('nombre',)
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('codigo', 'nombre', 'activo')
        }),
        (_('Descripción'), {
            'fields': ('descripcion',)
        }),
    )
    
    def activo_badge(self, obj):
        """Muestra el estado activo con color."""
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'
    
    def descripcion_short(self, obj):
        """Muestra descripción truncada."""
        if obj.descripcion:
            return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
        return '-'
    descripcion_short.short_description = 'Descripción'


@admin.register(DenominacionMoneda)
class DenominacionMonedaAdmin(admin.ModelAdmin):
    """
    Administrador completo para DenominacionMoneda.
    """
    list_display = ('id', 'valor_fmt', 'tipo_badge', 'activo_badge', 'orden')
    list_filter = ('tipo', 'activo')
    ordering = ('-valor', 'tipo')
    
    fieldsets = (
        (_('Información de la Denominación'), {
            'fields': ('valor', 'tipo', 'activo', 'orden')
        }),
    )
    
    def valor_fmt(self, obj):
        """Formatea el valor."""
        try:
            return format_html('${:,.0f}', float(obj.valor))
        except (ValueError, TypeError):
            return format_html('<span style="color: red;">Error: {}</span>', obj.valor)
    valor_fmt.short_description = 'Valor'
    valor_fmt.admin_order_field = 'valor'
    
    def tipo_badge(self, obj):
        """Muestra el tipo con icono."""
        try:
            if obj.tipo == 'BILLETE':
                icon = '💵'
                tipo_display = 'Billete'
            elif obj.tipo == 'MONEDA':
                icon = '🪙'
                tipo_display = 'Moneda'
            else:
                icon = '❓'
                tipo_display = obj.tipo
            return format_html('{} {}', icon, tipo_display)
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    tipo_badge.short_description = 'Tipo'
    tipo_badge.admin_order_field = 'tipo'
    
    def activo_badge(self, obj):
        """Muestra el estado activo con color."""
        try:
            if obj.activo:
                return format_html('<span style="color: green;">✓ Activo</span>')
            return format_html('<span style="color: red;">✗ Inactivo</span>')
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'


class DetalleConteoInline(admin.TabularInline):
    """
    Inline para detalles de conteo con cálculos automáticos.
    """
    model = DetalleConteo
    extra = 0
    readonly_fields = ('subtotal_fmt',)
    fields = ('denominacion', 'cantidad', 'subtotal_fmt')
    
    def subtotal_fmt(self, obj):
        """Muestra el subtotal formateado."""
        return format_html('${:,.0f}', obj.subtotal)
    subtotal_fmt.short_description = 'Subtotal'


@admin.register(ConteoEfectivo)
class ConteoEfectivoAdmin(admin.ModelAdmin):
    """
    Administrador completo para ConteoEfectivo.
    """
    list_display = (
        'id',
        'caja_info',
        'tipo_conteo_badge',
        'usuario_info',
        'total_fmt',
        'fecha_conteo'
    )
    list_filter = ('tipo_conteo', 'fecha_conteo', 'usuario', 'caja__cajero')
    search_fields = (
        'id',
        'caja__id',
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'observaciones'
    )
    ordering = ('-fecha_conteo',)
    readonly_fields = ('fecha_conteo', 'total_calculado')
    date_hierarchy = 'fecha_conteo'
    inlines = [DetalleConteoInline]
    
    fieldsets = (
        (_('Información del Conteo'), {
            'fields': ('caja', 'tipo_conteo', 'usuario', 'fecha_conteo')
        }),
        (_('Total'), {
            'fields': ('total', 'total_calculado')
        }),
        (_('Observaciones'), {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def caja_info(self, obj):
        """Muestra información de la caja."""
        return format_html(
            'Caja #{} - {}<br><small>{}</small>',
            obj.caja.id,
            obj.caja.cajero.username,
            obj.caja.fecha_apertura.strftime('%d/%m/%Y %H:%M')
        )
    caja_info.short_description = 'Caja'
    
    def tipo_conteo_badge(self, obj):
        """Muestra el tipo de conteo con icono."""
        if obj.tipo_conteo == 'APERTURA':
            icon = '🟢'
            color = 'green'
        else:
            icon = '🔴'
            color = 'red'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.get_tipo_conteo_display()
        )
    tipo_conteo_badge.short_description = 'Tipo'
    tipo_conteo_badge.admin_order_field = 'tipo_conteo'
    
    def usuario_info(self, obj):
        """Muestra información del usuario."""
        if obj.usuario:
            full_name = obj.usuario.get_full_name() or obj.usuario.username
            return format_html('<strong>{}</strong>', full_name)
        return '-'
    usuario_info.short_description = 'Usuario'
    
    def total_fmt(self, obj):
        """Formatea el total."""
        return format_html('<strong>${:,.0f}</strong>', obj.total)
    total_fmt.short_description = 'Total Contado'
    total_fmt.admin_order_field = 'total'
    
    def total_calculado(self, obj):
        """Calcula el total desde los detalles."""
        from decimal import Decimal
        from django.db.models import Sum
        total = obj.detalles.aggregate(
            total=Sum('subtotal')
        )['total'] or Decimal('0.00')
        return format_html('${:,.0f}', total)
    total_calculado.short_description = 'Total Calculado (desde detalles)'


@admin.register(DetalleConteo)
class DetalleConteoAdmin(admin.ModelAdmin):
    """
    Administrador completo para DetalleConteo.
    """
    list_display = (
        'id',
        'conteo_info',
        'denominacion_fmt',
        'cantidad',
        'subtotal_fmt'
    )
    list_filter = ('denominacion__tipo', 'conteo__tipo_conteo')
    search_fields = (
        'conteo__id',
        'conteo__caja__id',
        'denominacion__valor'
    )
    ordering = ('-conteo__fecha_conteo', '-denominacion__valor')
    readonly_fields = ('subtotal',)
    
    fieldsets = (
        (_('Información del Detalle'), {
            'fields': ('conteo', 'denominacion', 'cantidad', 'subtotal')
        }),
    )
    
    def conteo_info(self, obj):
        """Muestra información del conteo."""
        return format_html(
            'Conteo #{} - {}<br><small>Caja #{}</small>',
            obj.conteo.id,
            obj.conteo.get_tipo_conteo_display(),
            obj.conteo.caja.id
        )
    conteo_info.short_description = 'Conteo'
    
    def denominacion_fmt(self, obj):
        """Formatea la denominación."""
        icon = '💵' if obj.denominacion.tipo == 'BILLETE' else '🪙'
        return format_html(
            '{} ${:,.0f}',
            icon,
            obj.denominacion.valor
        )
    denominacion_fmt.short_description = 'Denominación'
    denominacion_fmt.admin_order_field = 'denominacion__valor'
    
    def subtotal_fmt(self, obj):
        """Formatea el subtotal."""
        return format_html('<strong>${:,.0f}</strong>', obj.subtotal)
    subtotal_fmt.short_description = 'Subtotal'
    subtotal_fmt.admin_order_field = 'subtotal'

