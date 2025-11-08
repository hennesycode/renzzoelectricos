"""
Configuración simplificada del administrador para la app caja.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CajaRegistradora, MovimientoCaja, TipoMovimiento,
    DenominacionMoneda, ConteoEfectivo, DetalleConteo,
    Cuenta, TransaccionGeneral
)


@admin.register(CajaRegistradora)
class CajaRegistradoraAdmin(admin.ModelAdmin):
    """Administrador simplificado para CajaRegistradora."""
    
    list_display = (
        'id', 
        'cajero', 
        'fecha_apertura', 
        'fecha_cierre', 
        'estado',
        'monto_inicial',
        'monto_final_declarado',
        'diferencia'
    )
    list_filter = ('estado', 'fecha_apertura', 'cajero')
    search_fields = ('id', 'cajero__username')
    ordering = ('-fecha_apertura',)
    readonly_fields = ('fecha_apertura', 'monto_final_sistema', 'diferencia')
    
    fields = (
        'cajero', 'estado', 'fecha_apertura', 'fecha_cierre',
        'monto_inicial', 'monto_final_declarado', 'monto_final_sistema', 'diferencia',
        'dinero_en_caja', 'dinero_guardado',
        'observaciones_apertura', 'observaciones_cierre'
    )
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    """Administrador simplificado para MovimientoCaja."""
    
    list_display = ('id', 'caja', 'tipo', 'monto', 'fecha_movimiento', 'usuario')
    list_filter = ('tipo', 'fecha_movimiento', 'usuario')
    search_fields = ('descripcion', 'referencia')
    ordering = ('-fecha_movimiento',)
    readonly_fields = ('fecha_movimiento',)
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(TipoMovimiento)
class TipoMovimientoAdmin(admin.ModelAdmin):
    """Administrador para TipoMovimiento."""
    
    list_display = ('codigo', 'nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre')
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DenominacionMoneda)
class DenominacionMonedaAdmin(admin.ModelAdmin):
    """Administrador para DenominacionMoneda."""
    
    list_display = ('valor', 'tipo', 'activo', 'orden')
    list_filter = ('tipo', 'activo')
    ordering = ('-valor',)
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ConteoEfectivo)
class ConteoEfectivoAdmin(admin.ModelAdmin):
    """Administrador para ConteoEfectivo."""
    
    list_display = ('id', 'caja', 'tipo_conteo', 'total', 'fecha_conteo', 'usuario')
    list_filter = ('tipo_conteo', 'fecha_conteo')
    search_fields = ('caja__id',)
    ordering = ('-fecha_conteo',)
    readonly_fields = ('fecha_conteo',)
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DetalleConteo)
class DetalleConteoAdmin(admin.ModelAdmin):
    """Administrador para DetalleConteo."""
    
    list_display = ('id', 'conteo', 'denominacion', 'cantidad', 'subtotal')
    list_filter = ('denominacion__tipo',)
    ordering = ('-conteo__fecha_conteo', '-denominacion__valor')
    readonly_fields = ('subtotal',)
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    """Administrador para Cuenta."""
    
    list_display = ('nombre', 'tipo', 'saldo_actual', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre',)
    readonly_fields = ('fecha_creacion',)
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(TransaccionGeneral)
class TransaccionGeneralAdmin(admin.ModelAdmin):
    """Administrador para TransaccionGeneral."""
    
    list_display = ('id', 'fecha', 'tipo', 'monto', 'cuenta', 'usuario')
    list_filter = ('tipo', 'fecha', 'cuenta__tipo')
    search_fields = ('descripcion', 'referencia')
    ordering = ('-fecha',)
    readonly_fields = ('fecha',)
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser