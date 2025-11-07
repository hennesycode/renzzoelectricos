"""
Administración de Django para el sistema de facturación.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Factura, DetalleFactura


class DetalleFacturaInline(admin.TabularInline):
    """
    Inline para mostrar los detalles de la factura dentro del admin de Factura.
    """
    model = DetalleFactura
    extra = 0
    readonly_fields = ('valor_unitario', 'total')
    fields = ('orden', 'descripcion', 'cantidad', 'precio_unitario', 'descuento', 'valor_unitario', 'total')
    ordering = ('orden',)


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    """
    Administración de facturas con todos los detalles.
    """
    list_display = (
        'codigo_factura',
        'fecha_emision',
        'cliente_nombre',
        'total_pagar_formatted',
        'metodo_pago',
        'condicion_pago',
        'activa_badge',
    )
    
    list_filter = (
        'activa',
        'metodo_pago',
        'condicion_pago',
        'fecha_emision',
    )
    
    search_fields = (
        'codigo_factura',
        'cliente__username',
        'cliente__first_name',
        'cliente__last_name',
        'cliente__email',
    )
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO, incluidas fechas y totales calculados.
        """
        if request.user.is_superuser:
            return ()  # Pueden editar todo, incluso subtotal, totales, etc.
        # Staff solo lectura en campos calculados y código
        return (
            'codigo_factura',
            'fecha_creacion',
            'fecha_modificacion',
            'subtotal',
            'total_descuentos',
            'subtotal_neto',
            'total_iva',
            'total_pagar',
        )
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'codigo_factura',
                'fecha_emision',
                'cliente',
                'usuario_emisor',
                'activa',
            )
        }),
        ('Totales', {
            'fields': (
                'subtotal',
                'total_descuentos',
                'subtotal_neto',
                'total_iva',
                'total_pagar',
            ),
            'description': '⚠️ Superusuarios pueden editar estos valores manualmente.'
        }),
        ('Condiciones de Pago', {
            'fields': (
                'metodo_pago',
                'condicion_pago',
                'notas',
            )
        }),
        ('Metadatos', {
            'fields': (
                'fecha_creacion',
                'fecha_modificacion',
            )
        }),
    )
    
    inlines = [DetalleFacturaInline]
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar facturas.
        Staff solo puede desactivarlas (activa=False).
        """
        return request.user.is_superuser
    
    def cliente_nombre(self, obj):
        """Muestra el nombre completo del cliente"""
        return obj.cliente.get_full_name() or obj.cliente.username
    cliente_nombre.short_description = 'Cliente'
    
    def total_pagar_formatted(self, obj):
        """Formatea el total con símbolo de pesos"""
        return f"${obj.total_pagar:,.2f}"
    total_pagar_formatted.short_description = 'Total'
    total_pagar_formatted.admin_order_field = 'total_pagar'
    
    def activa_badge(self, obj):
        """Muestra un badge de color según el estado"""
        if obj.activa:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Activa</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Anulada</span>'
            )
    activa_badge.short_description = 'Estado'


@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    """
    Administración de detalles de factura (líneas de productos).
    """
    list_display = (
        'factura',
        'orden',
        'descripcion',
        'cantidad',
        'precio_unitario',
        'descuento',
        'total_formatted',
    )
    
    list_filter = (
        'factura__fecha_emision',
    )
    
    search_fields = (
        'factura__codigo_factura',
        'descripcion',
    )
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO, incluidos valores calculados.
        """
        if request.user.is_superuser:
            return ()  # Pueden editar todo
        return ('valor_unitario', 'total')  # Staff solo lectura en calculados
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar detalles de factura.
        """
        return request.user.is_superuser
    
    def total_formatted(self, obj):
        """Formatea el total con símbolo de pesos"""
        return f"${obj.total:,.2f}"
    total_formatted.short_description = 'Total'
    total_formatted.admin_order_field = 'total'
