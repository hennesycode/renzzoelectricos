"""
Configuración del administrador para la app caja.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from decimal import Decimal
from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    DenominacionMoneda, ConteoEfectivo, DetalleConteo,
    Cuenta, TransaccionGeneral
)


def safe_decimal_to_float(value):
    """
    Convierte de forma segura cualquier valor a float para formateo.
    Maneja Decimal, int, float, str, SafeString, None.
    """
    if value is None:
        return 0.0
    
    # Si ya es float, devolver
    if isinstance(value, float):
        return value
    
    # Si es int, convertir directamente
    if isinstance(value, int):
        return float(value)
    
    # Si es Decimal, convertir
    if isinstance(value, Decimal):
        return float(value)
    
    # Si es string (incluyendo SafeString), intentar convertir
    if isinstance(value, str):
        # Eliminar caracteres de formato
        cleaned = str(value).replace(',', '').replace('$', '').strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    # Intentar conversión directa como último recurso
    try:
        return float(value)
    except (ValueError, TypeError, AttributeError):
        return 0.0


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
        'dinero_en_caja_fmt',
        'dinero_guardado_fmt',
        'duracion'
    )
    list_filter = ('estado', 'fecha_apertura', 'fecha_cierre', 'cajero')
    search_fields = ('id', 'cajero__username', 'cajero__first_name', 'cajero__last_name', 'observaciones_apertura', 'observaciones_cierre')
    ordering = ('-fecha_apertura',)
    inlines = [MovimientoCajaInline, ConteoEfectivoInline]
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO.
        Staff y otros usuarios tienen campos readonly.
        """
        if request.user.is_superuser:
            # Superusuarios pueden editar TODO, solo mostrar campos calculados como readonly
            return ('total_ingresos', 'total_egresos', 'duracion_formateada')
        # Para staff y otros, mantener campos readonly
        return (
            'fecha_apertura', 
            'monto_final_sistema', 
            'diferencia',
            'total_ingresos',
            'total_egresos',
            'duracion_formateada'
        )
    
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
        (_('Distribución del Dinero'), {
            'fields': ('dinero_en_caja', 'dinero_guardado'),
        }),
        (_('Resumen de Movimientos'), {
            'fields': ('total_ingresos', 'total_egresos'),
        }),
        (_('Observaciones'), {
            'fields': ('observaciones_apertura', 'observaciones_cierre')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar cajas.
        """
        return request.user.is_superuser
    
    def cajero_info(self, obj):
        """Muestra información completa del cajero."""
        try:
            full_name = obj.cajero.get_full_name() or obj.cajero.username
            email = obj.cajero.email or 'Sin email'
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                full_name,
                email
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    cajero_info.short_description = 'Cajero'
    
    def estado_badge(self, obj):
        """Muestra el estado con color."""
        try:
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
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    estado_badge.short_description = 'Estado'
    
    def monto_inicial_fmt(self, obj):
        """Formatea el monto inicial."""
        try:
            monto = safe_decimal_to_float(obj.monto_inicial)
            return format_html('${:,.0f}', monto)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    monto_inicial_fmt.short_description = 'Monto Inicial'
    monto_inicial_fmt.admin_order_field = 'monto_inicial'
    
    def monto_final_declarado_fmt(self, obj):
        """Formatea el monto final declarado."""
        try:
            if obj.monto_final_declarado:
                monto = safe_decimal_to_float(obj.monto_final_declarado)
                return format_html('${:,.0f}', monto)
            return '-'
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    monto_final_declarado_fmt.short_description = 'Final Declarado'
    monto_final_declarado_fmt.admin_order_field = 'monto_final_declarado'
    
    def monto_final_sistema_fmt(self, obj):
        """Formatea el monto final del sistema."""
        try:
            if obj.monto_final_sistema:
                monto = safe_decimal_to_float(obj.monto_final_sistema)
                return format_html('${:,.0f}', monto)
            return '-'
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    monto_final_sistema_fmt.short_description = 'Final Sistema'
    monto_final_sistema_fmt.admin_order_field = 'monto_final_sistema'
    
    def diferencia_fmt(self, obj):
        """Formatea la diferencia con color."""
        try:
            if obj.diferencia is not None:
                diferencia = safe_decimal_to_float(obj.diferencia)
                color = 'red' if diferencia < 0 else ('green' if diferencia > 0 else 'gray')
                return format_html(
                    '<span style="color: {}; font-weight: bold;">${:,.0f}</span>',
                    color,
                    diferencia
                )
            return '-'
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    diferencia_fmt.short_description = 'Diferencia'
    diferencia_fmt.admin_order_field = 'diferencia'
    
    def dinero_en_caja_fmt(self, obj):
        """Formatea el dinero en caja."""
        try:
            if obj.dinero_en_caja is not None:
                monto = safe_decimal_to_float(obj.dinero_en_caja)
                return format_html('<span style="color: #2196F3; font-weight: 600;">${:,.0f}</span>', monto)
            return '-'
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    dinero_en_caja_fmt.short_description = '💵 En Caja'
    dinero_en_caja_fmt.admin_order_field = 'dinero_en_caja'
    
    def dinero_guardado_fmt(self, obj):
        """Formatea el dinero guardado."""
        try:
            if obj.dinero_guardado is not None:
                monto = safe_decimal_to_float(obj.dinero_guardado)
                return format_html('<span style="color: #4CAF50; font-weight: 600;">${:,.0f}</span>', monto)
            return '-'
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    dinero_guardado_fmt.short_description = '🔒 Guardado'
    dinero_guardado_fmt.admin_order_field = 'dinero_guardado'
    
    def duracion(self, obj):
        """Muestra la duración de la caja."""
        try:
            duracion = obj.duracion_abierta
            horas = duracion.total_seconds() / 3600
            return format_html('{:.1f}h', horas)
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    duracion.short_description = 'Duración'
    
    def duracion_formateada(self, obj):
        """Muestra la duración formateada para el detalle."""
        try:
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
        except Exception as e:
            return f'Error: {str(e)}'
    duracion_formateada.short_description = 'Duración'
    
    def total_ingresos(self, obj):
        """Calcula y muestra el total de ingresos."""
        try:
            from django.db.models import Sum
            total = obj.movimientos.filter(tipo='INGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            total_float = safe_decimal_to_float(total)
            return format_html('${:,.0f}', total_float)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    total_ingresos.short_description = 'Total Ingresos'
    
    def total_egresos(self, obj):
        """Calcula y muestra el total de egresos."""
        try:
            from django.db.models import Sum
            total = obj.movimientos.filter(tipo='EGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            total_float = safe_decimal_to_float(total)
            return format_html('${:,.0f}', total_float)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
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
    date_hierarchy = 'fecha_movimiento'
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO, incluidas fechas.
        """
        if request.user.is_superuser:
            return ()  # Pueden editar todo
        return ('fecha_movimiento',)  # Staff solo lectura en fecha
    
    fieldsets = (
        (_('Información del Movimiento'), {
            'fields': ('caja', 'tipo', 'tipo_movimiento', 'usuario', 'fecha_movimiento')
        }),
        (_('Detalles Financieros'), {
            'fields': ('monto', 'descripcion', 'referencia')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar movimientos.
        """
        return request.user.is_superuser
    
    def caja_info(self, obj):
        """Muestra información de la caja."""
        try:
            return format_html(
                'Caja #{} - {}<br><small>{}</small>',
                obj.caja.id,
                obj.caja.cajero.username,
                obj.caja.fecha_apertura.strftime('%d/%m/%Y %H:%M')
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    caja_info.short_description = 'Caja'
    
    def tipo_badge(self, obj):
        """Muestra el tipo con color."""
        try:
            if obj.tipo == 'INGRESO':
                color = 'green'
                icon = '↑'
                tipo_display = 'Ingreso'
            elif obj.tipo == 'EGRESO':
                color = 'red'
                icon = '↓'
                tipo_display = 'Egreso'
            else:
                color = 'gray'
                icon = '?'
                tipo_display = obj.tipo
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {}</span>',
                color,
                icon,
                tipo_display
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    tipo_badge.short_description = 'Tipo'
    tipo_badge.admin_order_field = 'tipo'
    
    def monto_fmt(self, obj):
        """Formatea el monto con color."""
        try:
            color = 'green' if obj.tipo == 'INGRESO' else 'red'
            signo = '+' if obj.tipo == 'INGRESO' else '-'
            monto = safe_decimal_to_float(obj.monto)
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ${:,.0f}</span>',
                color,
                signo,
                monto
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    monto_fmt.short_description = 'Monto'
    monto_fmt.admin_order_field = 'monto'
    
    def usuario_info(self, obj):
        """Muestra información del usuario."""
        try:
            full_name = obj.usuario.get_full_name() or obj.usuario.username
            return format_html('<strong>{}</strong>', full_name)
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
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
            'fields': ('codigo', 'nombre', 'tipo_base', 'activo')
        }),
        (_('Descripción'), {
            'fields': ('descripcion',)
        }),
    )

    def has_add_permission(self, request):
        """
        Solo superusuarios pueden crear tipos de movimiento.
        """
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar tipos de movimiento.
        """
        return request.user.is_superuser
    
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
    
    def descripcion_short(self, obj):
        """Muestra descripción truncada."""
        try:
            if obj.descripcion:
                return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
            return '-'
        except Exception as e:
            return f'Error: {str(e)}'
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
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar denominaciones.
        """
        return request.user.is_superuser
    
    def valor_fmt(self, obj):
        """Formatea el valor."""
        try:
            valor = safe_decimal_to_float(obj.valor)
            return format_html('${:,.0f}', valor)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
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
        try:
            subtotal = safe_decimal_to_float(obj.subtotal)
            return format_html('${:,.0f}', subtotal)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
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
    date_hierarchy = 'fecha_conteo'
    inlines = [DetalleConteoInline]
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO, incluidas fechas y totales.
        """
        if request.user.is_superuser:
            return ()  # Pueden editar todo
        return ('fecha_conteo', 'total_calculado')  # Staff solo lectura
    
    fieldsets = (
        (_('Información del Conteo'), {
            'fields': ('caja', 'tipo_conteo', 'usuario', 'fecha_conteo')
        }),
        (_('Total'), {
            'fields': ('total', 'total_calculado')
        }),
        (_('Observaciones'), {
            'fields': ('observaciones',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar conteos.
        """
        return request.user.is_superuser
    
    def caja_info(self, obj):
        """Muestra información de la caja."""
        try:
            return format_html(
                'Caja #{} - {}<br><small>{}</small>',
                obj.caja.id,
                obj.caja.cajero.username,
                obj.caja.fecha_apertura.strftime('%d/%m/%Y %H:%M')
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    caja_info.short_description = 'Caja'
    
    def tipo_conteo_badge(self, obj):
        """Muestra el tipo de conteo con icono."""
        try:
            if obj.tipo_conteo == 'APERTURA':
                icon = '🟢'
                color = 'green'
                tipo_display = 'Apertura'
            elif obj.tipo_conteo == 'CIERRE':
                icon = '🔴'
                color = 'red'
                tipo_display = 'Cierre'
            else:
                icon = '❓'
                color = 'gray'
                tipo_display = obj.tipo_conteo
            return format_html(
                '<span style="color: {};">{} {}</span>',
                color,
                icon,
                tipo_display
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    tipo_conteo_badge.short_description = 'Tipo'
    tipo_conteo_badge.admin_order_field = 'tipo_conteo'
    
    def usuario_info(self, obj):
        """Muestra información del usuario."""
        try:
            if obj.usuario:
                full_name = obj.usuario.get_full_name() or obj.usuario.username
                return format_html('<strong>{}</strong>', full_name)
            return '-'
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    usuario_info.short_description = 'Usuario'
    
    def total_fmt(self, obj):
        """Formatea el total."""
        try:
            total = safe_decimal_to_float(obj.total)
            return format_html('<strong>${:,.0f}</strong>', total)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    total_fmt.short_description = 'Total Contado'
    total_fmt.admin_order_field = 'total'
    
    def total_calculado(self, obj):
        """Calcula el total desde los detalles."""
        try:
            from django.db.models import Sum
            total = obj.detalles.aggregate(
                total=Sum('subtotal')
            )['total'] or Decimal('0.00')
            total_float = safe_decimal_to_float(total)
            return format_html('${:,.0f}', total_float)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
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
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO.
        """
        if request.user.is_superuser:
            return ()  # Pueden editar todo, incluido subtotal
        return ('subtotal',)  # Staff solo lectura en subtotal
    
    fieldsets = (
        (_('Información del Detalle'), {
            'fields': ('conteo', 'denominacion', 'cantidad', 'subtotal')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar detalles de conteo.
        """
        return request.user.is_superuser
    
    def conteo_info(self, obj):
        """Muestra información del conteo."""
        try:
            # Usar comparación directa en lugar de get_tipo_conteo_display()
            if obj.conteo.tipo_conteo == 'APERTURA':
                tipo_display = 'Apertura'
            elif obj.conteo.tipo_conteo == 'CIERRE':
                tipo_display = 'Cierre'
            else:
                tipo_display = str(obj.conteo.tipo_conteo)
                
            return format_html(
                'Conteo #{} - {}<br><small>Caja #{}</small>',
                int(obj.conteo.id),
                str(tipo_display),
                int(obj.conteo.caja.id)
            )
        except (AttributeError, ValueError, TypeError) as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    conteo_info.short_description = 'Conteo'
    
    def denominacion_fmt(self, obj):
        """Formatea la denominación."""
        try:
            icon = '💵' if obj.denominacion.tipo == 'BILLETE' else '🪙'
            valor = safe_decimal_to_float(obj.denominacion.valor)
            return format_html(
                '{} ${:,.0f}',
                icon,
                valor
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    denominacion_fmt.short_description = 'Denominación'
    denominacion_fmt.admin_order_field = 'denominacion__valor'
    
    def subtotal_fmt(self, obj):
        """Formatea el subtotal."""
        try:
            subtotal = safe_decimal_to_float(obj.subtotal)
            return format_html('<strong>${:,.0f}</strong>', subtotal)
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    subtotal_fmt.short_description = 'Subtotal'
    subtotal_fmt.admin_order_field = 'subtotal'


# ============================================================================
# ADMINISTRADORES DE TESORERÍA
# ============================================================================

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    """
    Administrador para Cuenta (Banco, Reserva).
    IMPORTANTE: El sistema está diseñado para tener SOLO 1 cuenta BANCO y 1 cuenta RESERVA.
    """
    list_display = (
        'id',
        'nombre',
        'tipo_badge',
        'saldo_actual_fmt',
        'activo_badge',
        'fecha_creacion'
    )
    list_filter = ('tipo', 'activo', 'fecha_creacion')
    search_fields = ('nombre',)
    ordering = ('tipo', 'nombre')
    
    def get_queryset(self, request):
        """
        Sobrescribir para evitar errores con datos corruptos.
        """
        try:
            return super().get_queryset(request)
        except Exception as e:
            # Si hay error, devolver queryset vacío
            from django.contrib import messages
            messages.error(request, f'Error al cargar cuentas: {str(e)}')
            return Cuenta.objects.none()
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODOS los campos, incluido saldo_actual.
        """
        if request.user.is_superuser:
            return ('fecha_creacion',)  # Solo fecha_creacion readonly
        return ('fecha_creacion', 'saldo_actual')  # Staff no puede editar saldo manualmente
    
    fieldsets = (
        (_('⚠️ IMPORTANTE - Lee esto primero'), {
            'fields': (),
            'description': (
                '<div style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 10px;">'
                '<h3 style="margin-top: 0; color: #856404;">📚 ¿Cómo funcionan las Cuentas?</h3>'
                '<p><strong>El sistema maneja 2 tipos de cuentas:</strong></p>'
                '<ul>'
                '<li><strong>🏦 BANCO:</strong> Dinero en cuenta bancaria (transferencias, pagos electrónicos)</li>'
                '<li><strong>🔒 RESERVA:</strong> Dinero guardado físicamente (caja fuerte, efectivo resguardado)</li>'
                '</ul>'
                '<p><strong style="color: #d9534f;">⚠️ LIMITACIÓN:</strong> Solo puedes tener <u>1 cuenta activa de cada tipo</u>.</p>'
                '<p><strong>🔄 Para cambiar de cuenta:</strong> Desactiva la existente (activo=False) antes de crear una nueva.</p>'
                '<p><strong>💡 Uso en Tesorería:</strong> Estas cuentas aparecen en las opciones de transferencia/gastos/ingresos.</p>'
                '</div>'
            )
        }),
        (_('Información Básica'), {
            'fields': ('nombre', 'tipo', 'activo')
        }),
        (_('Saldo'), {
            'fields': ('saldo_actual',),
            'description': '⚠️ Superusuarios pueden editar el saldo manualmente. Usar con precaución.'
        }),
        (_('Metadata'), {
            'fields': ('fecha_creacion',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar cuentas.
        """
        return request.user.is_superuser
    
    def tipo_badge(self, obj):
        """Muestra el tipo con icono."""
        try:
            if obj.tipo == 'BANCO':
                icon = '🏦'
                color = '#2196F3'
                display = 'Banco'
            elif obj.tipo == 'RESERVA':
                icon = '🔒'
                color = '#4CAF50'
                display = 'Reserva / Dinero Guardado'
            else:
                icon = '❓'
                color = 'gray'
                display = str(obj.tipo)
            return format_html(
                '<span style="color: {};">{} {}</span>',
                color,
                icon,
                display
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    tipo_badge.short_description = 'Tipo'
    tipo_badge.admin_order_field = 'tipo'
    
    def saldo_actual_fmt(self, obj):
        """Formatea el saldo actual."""
        try:
            saldo = safe_decimal_to_float(obj.saldo_actual)
            color = 'red' if saldo < 0 else 'green'
            return format_html(
                '<strong style="color: {};">${:,.0f}</strong>',
                color,
                saldo
            )
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    saldo_actual_fmt.short_description = 'Saldo Actual'
    saldo_actual_fmt.admin_order_field = 'saldo_actual'
    
    def activo_badge(self, obj):
        """Muestra el estado activo con color."""
        try:
            if obj.activo:
                return format_html('<span style="color: green;">✓ Activo</span>')
            return format_html('<span style="color: red;">✗ Inactivo</span>')
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    activo_badge.short_description = 'Estado'
    activo_badge.admin_order_field = 'activo'


@admin.register(TransaccionGeneral)
class TransaccionGeneralAdmin(admin.ModelAdmin):
    """
    Administrador para TransaccionGeneral.
    """
    list_display = (
        'id',
        'fecha',
        'tipo_badge',
        'tipo_movimiento',
        'monto_fmt',
        'cuenta_info',
        'usuario_info',
        'referencia'
    )
    list_filter = ('tipo', 'tipo_movimiento', 'cuenta__tipo', 'fecha', 'usuario')
    search_fields = (
        'id',
        'descripcion',
        'referencia',
        'usuario__username',
        'cuenta__nombre',
        'tipo_movimiento__nombre'
    )
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO, incluidas fechas.
        """
        if request.user.is_superuser:
            return ()  # Pueden editar todo
        return ('fecha',)  # Staff solo lectura en fecha
    
    fieldsets = (
        (_('Información de la Transacción'), {
            'fields': ('tipo', 'tipo_movimiento', 'usuario', 'fecha')
        }),
        (_('Cuentas'), {
            'fields': ('cuenta', 'cuenta_destino')
        }),
        (_('Detalles Financieros'), {
            'fields': ('monto', 'descripcion', 'referencia')
        }),
        (_('Relaciones'), {
            'fields': ('movimiento_caja_asociado',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar transacciones.
        """
        return request.user.is_superuser
    
    def tipo_badge(self, obj):
        """Muestra el tipo con color."""
        if obj.tipo == 'INGRESO':
            color = 'green'
            icon = '↑'
        elif obj.tipo == 'EGRESO':
            color = 'red'
            icon = '↓'
        elif obj.tipo == 'TRANSFERENCIA':
            color = 'blue'
            icon = '↔'
        else:
            color = 'gray'
            icon = '?'
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
        if obj.tipo == 'INGRESO':
            color = 'green'
            signo = '+'
        elif obj.tipo == 'EGRESO':
            color = 'red'
            signo = '-'
        else:
            color = 'blue'
            signo = ''
        monto = safe_decimal_to_float(obj.monto)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ${:,.0f}</span>',
            color,
            signo,
            monto
        )
    monto_fmt.short_description = 'Monto'
    monto_fmt.admin_order_field = 'monto'
    
    def cuenta_info(self, obj):
        """Muestra información de la cuenta."""
        info = f'{obj.cuenta.nombre}'
        if obj.cuenta_destino:
            info += f' → {obj.cuenta_destino.nombre}'
        return format_html('<strong>{}</strong>', info)
    cuenta_info.short_description = 'Cuenta(s)'
    
    def usuario_info(self, obj):
        """Muestra información del usuario."""
        full_name = obj.usuario.get_full_name() or obj.usuario.username
        return format_html('<strong>{}</strong>', full_name)
    usuario_info.short_description = 'Usuario'
    usuario_info.admin_order_field = 'usuario__username'

