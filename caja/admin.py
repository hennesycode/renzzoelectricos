"""
Configuración del administrador para la app caja.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    DenominacionMoneda, ConteoEfectivo, DetalleConteo
)


@admin.register(CajaRegistradora)
class CajaRegistradoraAdmin(admin.ModelAdmin):
    """
    Administrador para CajaRegistradora.
    """
    list_display = ('cajero', 'fecha_apertura', 'fecha_cierre', 'estado', 'monto_inicial', 'monto_final_declarado', 'diferencia')
    list_filter = ('estado', 'fecha_apertura', 'cajero')
    search_fields = ('cajero__username', 'cajero__first_name', 'cajero__last_name')
    ordering = ('-fecha_apertura',)
    readonly_fields = ('fecha_apertura', 'monto_final_sistema', 'diferencia')
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('cajero', 'estado', 'fecha_apertura', 'fecha_cierre')
        }),
        (_('Montos'), {
            'fields': ('monto_inicial', 'monto_final_declarado', 'monto_final_sistema', 'diferencia')
        }),
        (_('Observaciones'), {
            'fields': ('observaciones_apertura', 'observaciones_cierre')
        }),
    )


class MovimientoCajaInline(admin.TabularInline):
    """
    Inline para mostrar movimientos en la caja.
    """
    model = MovimientoCaja
    extra = 0
    readonly_fields = ('fecha_movimiento',)


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    """
    Administrador para MovimientoCaja.
    """
    list_display = ('caja', 'tipo', 'tipo_movimiento', 'monto', 'usuario', 'fecha_movimiento')
    list_filter = ('tipo', 'tipo_movimiento', 'fecha_movimiento', 'usuario')
    search_fields = ('descripcion', 'referencia', 'usuario__username')
    ordering = ('-fecha_movimiento',)
    readonly_fields = ('fecha_movimiento',)
    
    fieldsets = (
        (_('Información del Movimiento'), {
            'fields': ('caja', 'tipo', 'tipo_movimiento', 'usuario')
        }),
        (_('Detalles'), {
            'fields': ('monto', 'descripcion', 'referencia', 'fecha_movimiento')
        }),
    )


@admin.register(TipoMovimiento)
class TipoMovimientoAdmin(admin.ModelAdmin):
    """
    Administrador para TipoMovimiento.
    """
    list_display = ('codigo', 'nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(DenominacionMoneda)
class DenominacionMonedaAdmin(admin.ModelAdmin):
    """
    Administrador para DenominacionMoneda.
    """
    list_display = ('valor', 'tipo', 'activo', 'orden')
    list_filter = ('tipo', 'activo')
    ordering = ('-valor',)


class DetalleConteoInline(admin.TabularInline):
    """
    Inline para detalles de conteo.
    """
    model = DetalleConteo
    extra = 0


@admin.register(ConteoEfectivo)
class ConteoEfectivoAdmin(admin.ModelAdmin):
    """
    Administrador para ConteoEfectivo.
    """
    list_display = ('caja', 'tipo_conteo', 'usuario', 'total', 'fecha_conteo')
    list_filter = ('tipo_conteo', 'fecha_conteo', 'usuario')
    ordering = ('-fecha_conteo',)
    readonly_fields = ('fecha_conteo',)
    inlines = [DetalleConteoInline]


@admin.register(DetalleConteo)
class DetalleConteoAdmin(admin.ModelAdmin):
    """
    Administrador para DetalleConteo.
    """
    list_display = ('conteo', 'denominacion', 'cantidad', 'subtotal')
    list_filter = ('denominacion__tipo',)
    ordering = ('-denominacion__valor',)
