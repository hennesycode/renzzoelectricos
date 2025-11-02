"""
Fixture inicial para el sistema de caja registradora.
Tipos de movimientos y denominaciones de moneda colombiana.
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from caja.models import TipoMovimiento, DenominacionMoneda


class Command(BaseCommand):
    help = 'Crea datos iniciales para el sistema de caja registradora'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales para el sistema de caja...')
        
        # Crear tipos de movimientos
        tipos_movimiento = [
            {'codigo': 'VENTA', 'nombre': 'Venta de Productos', 'descripcion': 'Ingresos por venta de productos o servicios'},
            {'codigo': 'DEVOL', 'nombre': 'Devolución', 'descripcion': 'Devolución de dinero por productos devueltos'},
            {'codigo': 'GASTO', 'nombre': 'Gasto Operativo', 'descripcion': 'Gastos del negocio (servicios, suministros, etc.)'},
            {'codigo': 'CAMBIO', 'nombre': 'Cambio de Billetes', 'descripcion': 'Intercambio de denominaciones'},
            {'codigo': 'AJUSTE', 'nombre': 'Ajuste de Caja', 'descripcion': 'Correcciones y ajustes manuales'},
            {'codigo': 'PAGO', 'nombre': 'Pago a Proveedores', 'descripcion': 'Pagos a proveedores y servicios'},
            {'codigo': 'RETIRO', 'nombre': 'Retiro de Efectivo', 'descripcion': 'Retiros para banco o seguridad'},
            {'codigo': 'INGRESO', 'nombre': 'Ingreso Extra', 'descripcion': 'Ingresos adicionales no relacionados con ventas'},
        ]
        
        for tipo_data in tipos_movimiento:
            tipo, created = TipoMovimiento.objects.get_or_create(
                codigo=tipo_data['codigo'],
                defaults={
                    'nombre': tipo_data['nombre'],
                    'descripcion': tipo_data['descripcion'],
                    'activo': True
                }
            )
            if created:
                self.stdout.write(f'✅ Creado tipo de movimiento: {tipo.nombre}')
            else:
                self.stdout.write(f'ℹ️  Ya existe: {tipo.nombre}')
        
        # Crear denominaciones de moneda colombiana (2025)
        denominaciones = [
            # Billetes - Mayor a menor
            {'valor': 100000, 'tipo': 'BILLETE', 'orden': 1, 'activo': True},
            {'valor': 50000, 'tipo': 'BILLETE', 'orden': 2, 'activo': True},
            {'valor': 20000, 'tipo': 'BILLETE', 'orden': 3, 'activo': True},
            {'valor': 10000, 'tipo': 'BILLETE', 'orden': 4, 'activo': True},
            {'valor': 5000, 'tipo': 'BILLETE', 'orden': 5, 'activo': True},
            {'valor': 2000, 'tipo': 'BILLETE', 'orden': 6, 'activo': True},
            {'valor': 1000, 'tipo': 'BILLETE', 'orden': 7, 'activo': True},  # Activado
            
            # Monedas - Mayor a menor
            {'valor': 1000, 'tipo': 'MONEDA', 'orden': 8, 'activo': True},
            {'valor': 500, 'tipo': 'MONEDA', 'orden': 9, 'activo': True},
            {'valor': 200, 'tipo': 'MONEDA', 'orden': 10, 'activo': True},
            {'valor': 100, 'tipo': 'MONEDA', 'orden': 11, 'activo': True},
            {'valor': 50, 'tipo': 'MONEDA', 'orden': 12, 'activo': True},
            {'valor': 20, 'tipo': 'MONEDA', 'orden': 13, 'activo': False},   # Menos común
            {'valor': 10, 'tipo': 'MONEDA', 'orden': 14, 'activo': False},   # Menos común
        ]
        
        for denom_data in denominaciones:
            denom, created = DenominacionMoneda.objects.get_or_create(
                valor=Decimal(str(denom_data['valor'])),
                defaults={
                    'tipo': denom_data['tipo'],
                    'orden': denom_data['orden'],
                    'activo': denom_data['activo']
                }
            )
            if created:
                self.stdout.write(f'✅ Creada denominación: ${denom.valor:,.0f} ({denom.get_tipo_display()})')
            else:
                self.stdout.write(f'ℹ️  Ya existe: ${denom.valor:,.0f} ({denom.get_tipo_display()})')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Datos iniciales del sistema de caja creados exitosamente!')
        )