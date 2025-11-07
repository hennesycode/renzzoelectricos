"""
Script para configurar la estructura inicial de caja y tesorería
con todos los tipos de movimiento y cuentas necesarios.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from caja.models import TipoMovimiento, Cuenta, DenominacionMoneda


class Command(BaseCommand):
    help = 'Configura la estructura inicial de caja y tesorería'

    def handle(self, *args, **options):
        self.stdout.write("Configurando sistema de caja y tesorería...")
        
        with transaction.atomic():
            self.crear_tipos_movimiento()
            self.crear_cuentas_base()
            self.crear_denominaciones()
        
        self.stdout.write(
            self.style.SUCCESS('✓ Configuración completada exitosamente')
        )
    
    def crear_tipos_movimiento(self):
        """Crear todos los tipos de movimiento necesarios."""
        tipos_movimiento = [
            # INGRESOS
            {
                'codigo': 'VENTA',
                'nombre': 'Venta',
                'descripcion': 'Ingresos por ventas de productos',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INGRESO,
            },
            {
                'codigo': 'COBRO_CXC',
                'nombre': 'Cobro de Cuentas por Cobrar',
                'descripcion': 'Cobros de deudas pendientes',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INGRESO,
            },
            {
                'codigo': 'DEV_PAGO',
                'nombre': 'Devolución de un Pago',
                'descripcion': 'Devoluciones de pagos realizados',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INGRESO,
            },
            {
                'codigo': 'REC_GASTOS',
                'nombre': 'Recuperación de Gastos',
                'descripcion': 'Recuperación de gastos previamente realizados',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INGRESO,
            },
            
            # GASTOS OPERATIVOS
            {
                'codigo': 'GASTO',
                'nombre': 'Gasto General',
                'descripcion': 'Gastos operativos generales',
                'tipo_base': TipoMovimiento.TipoBaseChoices.GASTO,
            },
            {
                'codigo': 'FLETES',
                'nombre': 'Fletes y Transporte',
                'descripcion': 'Gastos de transporte y fletes',
                'tipo_base': TipoMovimiento.TipoBaseChoices.GASTO,
            },
            {
                'codigo': 'DEV_VENTA',
                'nombre': 'Devolución de Venta',
                'descripcion': 'Devoluciones de ventas realizadas',
                'tipo_base': TipoMovimiento.TipoBaseChoices.GASTO,
            },
            {
                'codigo': 'SUELDOS',
                'nombre': 'Sueldos y Salarios',
                'descripcion': 'Pagos de nómina y salarios',
                'tipo_base': TipoMovimiento.TipoBaseChoices.GASTO,
            },
            {
                'codigo': 'SUMINISTROS',
                'nombre': 'Suministros',
                'descripcion': 'Compra de suministros de oficina y operación',
                'tipo_base': TipoMovimiento.TipoBaseChoices.GASTO,
            },
            {
                'codigo': 'ALQUILER',
                'nombre': 'Alquiler y Servicios',
                'descripcion': 'Pagos de alquiler y servicios públicos',
                'tipo_base': TipoMovimiento.TipoBaseChoices.GASTO,
            },
            {
                'codigo': 'MANTENIMIENTO',
                'nombre': 'Mantenimiento y Reparaciones',
                'descripcion': 'Gastos de mantenimiento y reparaciones',
                'tipo_base': TipoMovimiento.TipoBaseChoices.GASTO,
            },
            
            # INVERSIONES
            {
                'codigo': 'COMPRA',
                'nombre': 'Compra de Mercadería',
                'descripcion': 'Inversión en inventario y mercadería',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INVERSION,
            },
            
            # MOVIMIENTOS INTERNOS
            {
                'codigo': 'APERTURA',
                'nombre': 'Apertura de Caja',
                'descripcion': 'Dinero inicial al abrir la caja',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
            },
            {
                'codigo': 'CIERRE_CAJA',
                'nombre': 'Cierre de Caja - Dinero Guardado',
                'descripcion': 'Dinero retirado de caja y guardado al cierre',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
            },
            {
                'codigo': 'BALANCE',
                'nombre': 'Balance de Cuentas',
                'descripcion': 'Ajuste por diferencias de balance',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
            },
            {
                'codigo': 'TRANSFERENCIA',
                'nombre': 'Transferencia entre Cuentas',
                'descripcion': 'Movimiento de fondos entre cuentas',
                'tipo_base': TipoMovimiento.TipoBaseChoices.INTERNO,
            },
        ]
        
        creados = 0
        actualizados = 0
        
        for tipo_data in tipos_movimiento:
            tipo, created = TipoMovimiento.objects.get_or_create(
                codigo=tipo_data['codigo'],
                defaults={
                    'nombre': tipo_data['nombre'],
                    'descripcion': tipo_data['descripcion'],
                    'tipo_base': tipo_data['tipo_base'],
                    'activo': True
                }
            )
            
            if created:
                creados += 1
                self.stdout.write(f"  ✓ Creado tipo: {tipo.codigo} - {tipo.nombre}")
            else:
                # Actualizar campos si es necesario
                actualizado = False
                if tipo.nombre != tipo_data['nombre']:
                    tipo.nombre = tipo_data['nombre']
                    actualizado = True
                if tipo.descripcion != tipo_data['descripcion']:
                    tipo.descripcion = tipo_data['descripcion']
                    actualizado = True
                if tipo.tipo_base != tipo_data['tipo_base']:
                    tipo.tipo_base = tipo_data['tipo_base']
                    actualizado = True
                if not tipo.activo:
                    tipo.activo = True
                    actualizado = True
                
                if actualizado:
                    tipo.save()
                    actualizados += 1
                    self.stdout.write(f"  ↻ Actualizado tipo: {tipo.codigo} - {tipo.nombre}")
        
        self.stdout.write(f"Tipos de movimiento: {creados} creados, {actualizados} actualizados")
    
    def crear_cuentas_base(self):
        """Crear las cuentas base necesarias."""
        cuentas = [
            {
                'nombre': 'Banco Principal',
                'tipo': 'BANCO',
                'saldo_inicial': Decimal('0.00'),
                'activo': True
            },
            {
                'nombre': 'Dinero Guardado',
                'tipo': 'RESERVA',
                'saldo_inicial': Decimal('0.00'),
                'activo': True
            },
            {
                'nombre': 'Caja Virtual',
                'tipo': 'RESERVA',
                'saldo_inicial': Decimal('0.00'),
                'activo': False  # Cuenta interna para tracking
            },
        ]
        
        creadas = 0
        
        for cuenta_data in cuentas:
            # Verificar si ya existe una cuenta activa del mismo tipo
            if cuenta_data['activo']:
                cuenta_existente = Cuenta.objects.filter(
                    tipo=cuenta_data['tipo'],
                    activo=True
                ).first()
                
                if cuenta_existente:
                    self.stdout.write(f"  → Ya existe cuenta {cuenta_data['tipo']}: {cuenta_existente.nombre}")
                    continue
            
            cuenta, created = Cuenta.objects.get_or_create(
                nombre=cuenta_data['nombre'],
                defaults={
                    'tipo': cuenta_data['tipo'],
                    'saldo_actual': cuenta_data['saldo_inicial'],
                    'activo': cuenta_data['activo']
                }
            )
            
            if created:
                creadas += 1
                estado = "activa" if cuenta.activo else "interna"
                self.stdout.write(f"  ✓ Creada cuenta {estado}: {cuenta.nombre}")
        
        self.stdout.write(f"Cuentas: {creadas} creadas")
    
    def crear_denominaciones(self):
        """Crear las denominaciones de moneda colombiana."""
        denominaciones = [
            # Billetes
            {'valor': Decimal('100000'), 'tipo': 'BILLETE', 'orden': 1},
            {'valor': Decimal('50000'), 'tipo': 'BILLETE', 'orden': 2},
            {'valor': Decimal('20000'), 'tipo': 'BILLETE', 'orden': 3},
            {'valor': Decimal('10000'), 'tipo': 'BILLETE', 'orden': 4},
            {'valor': Decimal('5000'), 'tipo': 'BILLETE', 'orden': 5},
            {'valor': Decimal('2000'), 'tipo': 'BILLETE', 'orden': 6},
            {'valor': Decimal('1000'), 'tipo': 'BILLETE', 'orden': 7},
            
            # Monedas
            {'valor': Decimal('1000'), 'tipo': 'MONEDA', 'orden': 8},
            {'valor': Decimal('500'), 'tipo': 'MONEDA', 'orden': 9},
            {'valor': Decimal('200'), 'tipo': 'MONEDA', 'orden': 10},
            {'valor': Decimal('100'), 'tipo': 'MONEDA', 'orden': 11},
            {'valor': Decimal('50'), 'tipo': 'MONEDA', 'orden': 12},
        ]
        
        creadas = 0
        
        for denom_data in denominaciones:
            denom, created = DenominacionMoneda.objects.get_or_create(
                valor=denom_data['valor'],
                tipo=denom_data['tipo'],
                defaults={
                    'activo': True,
                    'orden': denom_data['orden']
                }
            )
            
            if created:
                creadas += 1
                self.stdout.write(f"  ✓ Creada denominación: ${denom.valor:,.0f} ({denom.tipo})")
        
        self.stdout.write(f"Denominaciones: {creadas} creadas")