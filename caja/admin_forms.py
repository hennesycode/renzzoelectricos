"""
Formularios administrativos para gestión avanzada de cajas.
Solo accesible por superusuarios.
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime
from .models import TipoMovimiento, DenominacionMoneda
from django.contrib.auth import get_user_model

User = get_user_model()


class MovimientoAdminForm(forms.Form):
    """Formulario para agregar un movimiento individual en admin."""
    
    tipo_movimiento = forms.ModelChoiceField(
        queryset=TipoMovimiento.objects.filter(activo=True),
        label='Tipo de Movimiento',
        help_text='Selecciona el tipo de movimiento'
    )
    
    tipo = forms.ChoiceField(
        choices=[('INGRESO', 'Ingreso'), ('EGRESO', 'Egreso')],
        label='Tipo',
        help_text='Indica si es entrada o salida de dinero'
    )
    
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Monto',
        help_text='Cantidad de dinero del movimiento'
    )
    
    descripcion = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Descripción',
        help_text='Detalles del movimiento (opcional). Agrega [BANCO] si es entrada al banco'
    )
    
    referencia = forms.CharField(
        max_length=100,
        required=False,
        label='Referencia',
        help_text='Número de factura, recibo, etc. (opcional)'
    )
    
    es_entrada_banco = forms.BooleanField(
        required=False,
        label='¿Es entrada al banco?',
        help_text='Marca si este movimiento va directamente al banco'
    )


class CajaAdminCompleteForm(forms.Form):
    """
    Formulario completo para crear una caja con fecha personalizada
    y todos sus movimientos desde el admin.
    """
    
    # === DATOS BÁSICOS DE LA CAJA ===
    cajero = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label='Cajero',
        help_text='Usuario responsable de la caja'
    )
    
    fecha_apertura = forms.DateTimeField(
        label='Fecha de Apertura',
        help_text='Fecha y hora de apertura de la caja',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    monto_inicial = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        label='Monto Inicial',
        help_text='Dinero inicial al abrir la caja'
    )
    
    observaciones_apertura = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Observaciones de Apertura',
        help_text='Notas sobre la apertura (opcional)'
    )
    
    # === MOVIMIENTOS (INGRESOS) ===
    # Ventas
    ventas_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Total Ventas',
        help_text='Monto total de ventas en efectivo'
    )
    
    cobros_cxc_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Cobros de Cuentas por Cobrar',
        help_text='Dinero cobrado de cuentas pendientes'
    )
    
    otros_ingresos_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Otros Ingresos',
        help_text='Otros ingresos en efectivo'
    )
    
    otros_ingresos_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Descripción Otros Ingresos',
        help_text='Detalle de otros ingresos'
    )
    
    # === ENTRADAS AL BANCO ===
    entradas_banco_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Entradas al Banco',
        help_text='Dinero que se depositó directamente al banco'
    )
    
    entradas_banco_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Descripción Entrada Banco',
        help_text='Detalle de las entradas al banco'
    )
    
    # === MOVIMIENTOS (EGRESOS) ===
    gastos_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Gastos Operativos',
        help_text='Gastos del día (servicios, suministros, etc.)'
    )
    
    gastos_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Descripción Gastos',
        help_text='Detalle de los gastos'
    )
    
    compras_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Compras/Inversiones',
        help_text='Dinero usado para comprar mercancía o inversiones'
    )
    
    compras_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Descripción Compras',
        help_text='Detalle de las compras'
    )
    
    otros_egresos_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Otros Egresos',
        help_text='Otros gastos o salidas de dinero'
    )
    
    otros_egresos_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Descripción Otros Egresos',
        help_text='Detalle de otros egresos'
    )
    
    # === CIERRE DE CAJA ===
    cerrar_caja = forms.BooleanField(
        required=False,
        initial=True,
        label='¿Cerrar la caja automáticamente?',
        help_text='Si está marcado, la caja se cierra automáticamente después de crear los movimientos'
    )
    
    fecha_cierre = forms.DateTimeField(
        required=False,
        label='Fecha de Cierre',
        help_text='Fecha y hora de cierre (opcional, se puede dejar abierta)',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    monto_final_declarado = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        label='Monto Final Declarado',
        help_text='Dinero contado al cerrar (requerido si se cierra)'
    )
    
    dinero_en_caja = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Dinero que queda en Caja',
        help_text='Dinero físico que permanece en la caja'
    )
    
    dinero_guardado = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Dinero Guardado (fuera de caja)',
        help_text='Dinero guardado en otro lugar seguro'
    )
    
    observaciones_cierre = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label='Observaciones de Cierre',
        help_text='Notas sobre el cierre (opcional)'
    )
    
    def clean(self):
        """Validaciones personalizadas del formulario."""
        cleaned_data = super().clean()
        
        # Validar fechas
        fecha_apertura = cleaned_data.get('fecha_apertura')
        fecha_cierre = cleaned_data.get('fecha_cierre')
        cerrar_caja = cleaned_data.get('cerrar_caja')
        
        if cerrar_caja and fecha_cierre and fecha_apertura:
            if fecha_cierre <= fecha_apertura:
                raise ValidationError('La fecha de cierre debe ser posterior a la de apertura')
        
        # Si se va a cerrar, validar campos requeridos
        if cerrar_caja:
            monto_final_declarado = cleaned_data.get('monto_final_declarado')
            dinero_en_caja = cleaned_data.get('dinero_en_caja', Decimal('0'))
            dinero_guardado = cleaned_data.get('dinero_guardado', Decimal('0'))
            
            if monto_final_declarado is None:
                raise ValidationError('El monto final declarado es requerido si se va a cerrar la caja')
            
            # Validar que la distribución del dinero coincida con el declarado
            suma_distribucion = dinero_en_caja + dinero_guardado
            if abs(suma_distribucion - monto_final_declarado) > Decimal('0.01'):
                raise ValidationError(
                    f'La suma de dinero en caja (${dinero_en_caja}) + dinero guardado (${dinero_guardado}) '
                    f'debe ser igual al monto final declarado (${monto_final_declarado})'
                )
        
        # Validar que si hay descripción, haya monto correspondiente
        campos_monto_descripcion = [
            ('otros_ingresos_monto', 'otros_ingresos_descripcion'),
            ('entradas_banco_monto', 'entradas_banco_descripcion'),
            ('gastos_monto', 'gastos_descripcion'),
            ('compras_monto', 'compras_descripcion'),
            ('otros_egresos_monto', 'otros_egresos_descripcion'),
        ]
        
        for campo_monto, campo_descripcion in campos_monto_descripcion:
            monto = cleaned_data.get(campo_monto, Decimal('0'))
            descripcion = cleaned_data.get(campo_descripcion, '')
            
            if monto > 0 and not descripcion.strip():
                raise ValidationError(f'Si especificas un monto para {campo_monto}, debes agregar una descripción')
        
        return cleaned_data
    
    def get_movimientos_data(self):
        """
        Convierte los datos del formulario en una lista de movimientos
        que se pueden crear usando las funciones existentes.
        """
        if not self.is_valid():
            return None
        
        movimientos = []
        cleaned_data = self.cleaned_data
        
        # Helper para agregar movimientos
        def agregar_movimiento(tipo_codigo, tipo_nombre, tipo_tipo, monto, descripcion='', referencia='', es_banco=False):
            if monto > 0:
                desc_final = descripcion
                if es_banco:
                    desc_final = f"[BANCO] {descripcion}" if descripcion else "[BANCO]"
                
                movimientos.append({
                    'tipo_codigo': tipo_codigo,
                    'tipo_nombre': tipo_nombre,
                    'tipo': tipo_tipo,
                    'monto': monto,
                    'descripcion': desc_final,
                    'referencia': referencia
                })
        
        # INGRESOS
        agregar_movimiento('VENTA', 'Venta', 'INGRESO', 
                          cleaned_data.get('ventas_monto', Decimal('0')), 'Ventas del día')
        
        agregar_movimiento('COBRO_CXC', 'Cobro de Cuentas por Cobrar', 'INGRESO',
                          cleaned_data.get('cobros_cxc_monto', Decimal('0')), 'Cobros de cuentas pendientes')
        
        agregar_movimiento('REC_GASTOS', 'Recuperación de Gastos', 'INGRESO',
                          cleaned_data.get('otros_ingresos_monto', Decimal('0')),
                          cleaned_data.get('otros_ingresos_descripcion', ''))
        
        # ENTRADAS AL BANCO
        agregar_movimiento('VENTA', 'Venta', 'INGRESO',
                          cleaned_data.get('entradas_banco_monto', Decimal('0')),
                          cleaned_data.get('entradas_banco_descripcion', 'Depósito al banco'),
                          '', True)
        
        # EGRESOS
        agregar_movimiento('GASTO', 'Gasto Operativo', 'EGRESO',
                          cleaned_data.get('gastos_monto', Decimal('0')),
                          cleaned_data.get('gastos_descripcion', ''))
        
        agregar_movimiento('COMPRA', 'Compra/Inversión', 'EGRESO',
                          cleaned_data.get('compras_monto', Decimal('0')),
                          cleaned_data.get('compras_descripcion', ''))
        
        agregar_movimiento('GASTO', 'Gasto Operativo', 'EGRESO',
                          cleaned_data.get('otros_egresos_monto', Decimal('0')),
                          cleaned_data.get('otros_egresos_descripcion', ''))
        
        return movimientos