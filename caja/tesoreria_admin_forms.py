"""
Formularios administrativos para gestión avanzada de tesorería.
Permite crear transacciones con fechas personalizadas.
Solo accesible por superusuarios.
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime
from .models import TipoMovimiento, Cuenta
from django.contrib.auth import get_user_model

User = get_user_model()


class TransaccionTesoreriaAdminForm(forms.Form):
    """
    Formulario para crear transacciones de tesorería individuales
    con fecha personalizada.
    """
    
    # === DATOS BÁSICOS ===
    fecha = forms.DateTimeField(
        label='Fecha de Transacción',
        help_text='Fecha y hora de la transacción',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    usuario = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label='Usuario Responsable',
        help_text='Usuario que registra la transacción'
    )
    
    # === TIPO DE TRANSACCIÓN ===
    tipo = forms.ChoiceField(
        choices=[
            ('INGRESO', 'Ingreso'),
            ('EGRESO', 'Egreso'),
            ('TRANSFERENCIA', 'Transferencia entre Cuentas')
        ],
        label='Tipo de Transacción',
        help_text='Selecciona el tipo de movimiento'
    )
    
    tipo_movimiento = forms.ModelChoiceField(
        queryset=TipoMovimiento.objects.filter(activo=True),
        label='Categoría del Movimiento',
        help_text='Tipo específico de movimiento'
    )
    
    # === CUENTAS ===
    cuenta = forms.ModelChoiceField(
        queryset=Cuenta.objects.filter(activo=True),
        label='Cuenta Principal',
        help_text='Cuenta de origen (egresos) o destino (ingresos)'
    )
    
    cuenta_destino = forms.ModelChoiceField(
        queryset=Cuenta.objects.filter(activo=True),
        required=False,
        label='Cuenta Destino',
        help_text='Solo para transferencias: cuenta que recibe el dinero'
    )
    
    # === DETALLES ===
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Monto',
        help_text='Cantidad de dinero de la transacción'
    )
    
    descripcion = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Descripción',
        help_text='Detalle de la transacción'
    )
    
    referencia = forms.CharField(
        max_length=100,
        required=False,
        label='Referencia',
        help_text='Número de comprobante, factura, etc. (opcional)'
    )
    
    def clean(self):
        """Validaciones personalizadas del formulario."""
        cleaned_data = super().clean()
        
        tipo = cleaned_data.get('tipo')
        cuenta = cleaned_data.get('cuenta')
        cuenta_destino = cleaned_data.get('cuenta_destino')
        monto = cleaned_data.get('monto')
        
        # Validar transferencias
        if tipo == 'TRANSFERENCIA':
            if not cuenta_destino:
                raise ValidationError('Para transferencias debes seleccionar la cuenta destino')
            
            if cuenta == cuenta_destino:
                raise ValidationError('La cuenta origen y destino no pueden ser la misma')
        
        # Validar fondos suficientes para egresos y transferencias
        if tipo in ['EGRESO', 'TRANSFERENCIA'] and cuenta and monto:
            if not cuenta.tiene_fondos_suficientes(monto):
                raise ValidationError(
                    f'La cuenta "{cuenta.nombre}" no tiene fondos suficientes. '
                    f'Saldo actual: ${cuenta.saldo_actual:,.2f}, Requerido: ${monto:,.2f}'
                )
        
        return cleaned_data


class GestorTesoreriaAdminForm(forms.Form):
    """
    Formulario completo para gestionar múltiples operaciones de tesorería
    con fecha personalizada.
    """
    
    # === DATOS GENERALES ===
    fecha_base = forms.DateTimeField(
        label='Fecha Base',
        help_text='Fecha base para todas las transacciones',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    
    usuario = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label='Usuario Responsable',
        help_text='Usuario que registra las transacciones'
    )
    
    # === GASTOS OPERATIVOS ===
    gastos_servicios_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Servicios Públicos',
        help_text='Luz, agua, internet, teléfono'
    )
    
    gastos_servicios_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Detalle Servicios',
        help_text='Especifica qué servicios se pagaron'
    )
    
    gastos_suministros_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Suministros y Materiales',
        help_text='Papelería, limpieza, etc.'
    )
    
    gastos_suministros_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Detalle Suministros',
        help_text='Especifica qué suministros se compraron'
    )
    
    gastos_mantenimiento_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Mantenimiento y Reparaciones',
        help_text='Reparaciones, mantenimiento de equipos'
    )
    
    gastos_mantenimiento_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Detalle Mantenimiento',
        help_text='Especifica qué mantenimiento se realizó'
    )
    
    gastos_otros_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Otros Gastos',
        help_text='Otros gastos operativos no categorizados'
    )
    
    gastos_otros_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Detalle Otros Gastos',
        help_text='Especifica otros gastos'
    )
    
    # === COMPRAS E INVERSIONES ===
    compras_mercancia_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Compra de Mercancía',
        help_text='Productos para reventa'
    )
    
    compras_mercancia_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Detalle Mercancía',
        help_text='Especifica qué mercancía se compró'
    )
    
    compras_equipos_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Compra de Equipos',
        help_text='Equipos, herramientas, activos fijos'
    )
    
    compras_equipos_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Detalle Equipos',
        help_text='Especifica qué equipos se compraron'
    )
    
    # === SUELDOS Y PERSONAL ===
    sueldos_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Sueldos y Salarios',
        help_text='Pagos a empleados'
    )
    
    sueldos_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Detalle Sueldos',
        help_text='Período y empleados pagados'
    )
    
    # === TRANSFERENCIAS ===
    transferencia_banco_reserva_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Transferir de Banco a Reserva',
        help_text='Retirar dinero del banco para guardarlo'
    )
    
    transferencia_reserva_banco_monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        required=False,
        label='Transferir de Reserva a Banco',
        help_text='Depositar dinero guardado al banco'
    )
    
    transferencia_descripcion = forms.CharField(
        max_length=300,
        required=False,
        label='Motivo de Transferencias',
        help_text='Razón de las transferencias'
    )
    
    # === CONFIGURACIÓN ===
    cuenta_origen_gastos = forms.ModelChoiceField(
        queryset=Cuenta.objects.filter(activo=True),
        label='Cuenta para Gastos',
        help_text='Cuenta de donde salen los gastos (generalmente Banco o Reserva)',
        empty_label='Seleccionar cuenta...'
    )
    
    def clean(self):
        """Validaciones personalizadas del formulario."""
        cleaned_data = super().clean()
        
        # Validar que si hay descripción, haya monto correspondiente
        campos_monto_descripcion = [
            ('gastos_servicios_monto', 'gastos_servicios_descripcion'),
            ('gastos_suministros_monto', 'gastos_suministros_descripcion'),
            ('gastos_mantenimiento_monto', 'gastos_mantenimiento_descripcion'),
            ('gastos_otros_monto', 'gastos_otros_descripcion'),
            ('compras_mercancia_monto', 'compras_mercancia_descripcion'),
            ('compras_equipos_monto', 'compras_equipos_descripcion'),
            ('sueldos_monto', 'sueldos_descripcion'),
        ]
        
        for campo_monto, campo_descripcion in campos_monto_descripcion:
            monto = cleaned_data.get(campo_monto, Decimal('0'))
            descripcion = cleaned_data.get(campo_descripcion, '')
            
            if monto > 0 and not descripcion.strip():
                raise ValidationError(f'Si especificas un monto para {campo_monto}, debes agregar una descripción')
        
        # Validar transferencias
        transfer_br = cleaned_data.get('transferencia_banco_reserva_monto', Decimal('0'))
        transfer_rb = cleaned_data.get('transferencia_reserva_banco_monto', Decimal('0'))
        
        if transfer_br > 0 and transfer_rb > 0:
            raise ValidationError('No puedes transferir en ambas direcciones al mismo tiempo')
        
        # Validar fondos suficientes en cuenta origen
        cuenta_origen = cleaned_data.get('cuenta_origen_gastos')
        if cuenta_origen:
            # Calcular total de gastos que salen de esta cuenta
            total_gastos = sum([
                cleaned_data.get('gastos_servicios_monto', Decimal('0')),
                cleaned_data.get('gastos_suministros_monto', Decimal('0')),
                cleaned_data.get('gastos_mantenimiento_monto', Decimal('0')),
                cleaned_data.get('gastos_otros_monto', Decimal('0')),
                cleaned_data.get('compras_mercancia_monto', Decimal('0')),
                cleaned_data.get('compras_equipos_monto', Decimal('0')),
                cleaned_data.get('sueldos_monto', Decimal('0')),
            ])
            
            # Agregar transferencias que salen de esta cuenta
            if cuenta_origen.tipo == 'BANCO':
                total_gastos += transfer_br
            elif cuenta_origen.tipo == 'RESERVA':
                total_gastos += transfer_rb
            
            if total_gastos > 0 and not cuenta_origen.tiene_fondos_suficientes(total_gastos):
                raise ValidationError(
                    f'La cuenta "{cuenta_origen.nombre}" no tiene fondos suficientes. '
                    f'Saldo actual: ${cuenta_origen.saldo_actual:,.2f}, '
                    f'Total requerido: ${total_gastos:,.2f}'
                )
        
        return cleaned_data
    
    def get_transacciones_data(self):
        """
        Convierte los datos del formulario en una lista de transacciones
        que se pueden crear usando las funciones existentes.
        """
        if not self.is_valid():
            return None
        
        transacciones = []
        cleaned_data = self.cleaned_data
        
        # Helper para agregar transacciones
        def agregar_transaccion(tipo_codigo, tipo_nombre, tipo_tipo, monto, descripcion, cuenta_origen, cuenta_destino=None):
            if monto > 0:
                transacciones.append({
                    'tipo_codigo': tipo_codigo,
                    'tipo_nombre': tipo_nombre,
                    'tipo': tipo_tipo,
                    'monto': monto,
                    'descripcion': descripcion,
                    'cuenta': cuenta_origen,
                    'cuenta_destino': cuenta_destino
                })
        
        cuenta_origen = cleaned_data.get('cuenta_origen_gastos')
        
        # GASTOS OPERATIVOS
        agregar_transaccion('GASTO', 'Gasto Operativo', 'EGRESO',
                          cleaned_data.get('gastos_servicios_monto', Decimal('0')),
                          f"Servicios públicos: {cleaned_data.get('gastos_servicios_descripcion', '')}",
                          cuenta_origen)
        
        agregar_transaccion('SUMINISTROS', 'Suministros', 'EGRESO',
                          cleaned_data.get('gastos_suministros_monto', Decimal('0')),
                          f"Suministros: {cleaned_data.get('gastos_suministros_descripcion', '')}",
                          cuenta_origen)
        
        agregar_transaccion('MANTENIMIENTO', 'Mantenimiento', 'EGRESO',
                          cleaned_data.get('gastos_mantenimiento_monto', Decimal('0')),
                          f"Mantenimiento: {cleaned_data.get('gastos_mantenimiento_descripcion', '')}",
                          cuenta_origen)
        
        agregar_transaccion('GASTO', 'Gasto Operativo', 'EGRESO',
                          cleaned_data.get('gastos_otros_monto', Decimal('0')),
                          f"Otros gastos: {cleaned_data.get('gastos_otros_descripcion', '')}",
                          cuenta_origen)
        
        # COMPRAS E INVERSIONES
        agregar_transaccion('COMPRA', 'Compra/Inversión', 'EGRESO',
                          cleaned_data.get('compras_mercancia_monto', Decimal('0')),
                          f"Mercancía: {cleaned_data.get('compras_mercancia_descripcion', '')}",
                          cuenta_origen)
        
        agregar_transaccion('COMPRA', 'Compra/Inversión', 'EGRESO',
                          cleaned_data.get('compras_equipos_monto', Decimal('0')),
                          f"Equipos: {cleaned_data.get('compras_equipos_descripcion', '')}",
                          cuenta_origen)
        
        # SUELDOS
        agregar_transaccion('SUELDOS', 'Sueldos y Salarios', 'EGRESO',
                          cleaned_data.get('sueldos_monto', Decimal('0')),
                          f"Sueldos: {cleaned_data.get('sueldos_descripcion', '')}",
                          cuenta_origen)
        
        # TRANSFERENCIAS
        banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        
        if banco and reserva:
            # Banco a Reserva
            transfer_br = cleaned_data.get('transferencia_banco_reserva_monto', Decimal('0'))
            if transfer_br > 0:
                transacciones.append({
                    'tipo_codigo': 'TRANSFERENCIA',
                    'tipo_nombre': 'Transferencia',
                    'tipo': 'TRANSFERENCIA',
                    'monto': transfer_br,
                    'descripcion': f"Transferencia Banco → Reserva: {cleaned_data.get('transferencia_descripcion', '')}",
                    'cuenta': banco,
                    'cuenta_destino': reserva
                })
            
            # Reserva a Banco
            transfer_rb = cleaned_data.get('transferencia_reserva_banco_monto', Decimal('0'))
            if transfer_rb > 0:
                transacciones.append({
                    'tipo_codigo': 'TRANSFERENCIA',
                    'tipo_nombre': 'Transferencia',
                    'tipo': 'TRANSFERENCIA',
                    'monto': transfer_rb,
                    'descripcion': f"Transferencia Reserva → Banco: {cleaned_data.get('transferencia_descripcion', '')}",
                    'cuenta': reserva,
                    'cuenta_destino': banco
                })
        
        return transacciones