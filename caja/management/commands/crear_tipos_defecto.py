from django.core.management.base import BaseCommand
from caja.models import TipoMovimiento

class Command(BaseCommand):
    help = 'Crea los tipos de movimiento por defecto solicitados (no se ejecuta automáticamente)'

    def handle(self, *args, **options):
        tipos_ingreso = [
            ('VENTA', 'Venta'),
            ('COBRO_CXC', 'Cobro de Cuentas por Cobrar'),
            ('DEV_PAGO', 'Devolución de un Pago'),
            ('REC_GASTOS', 'Recuperación de Gastos'),
        ]
        tipos_egreso = [
            ('GASTO', 'Gasto general'),
            ('COMPRA', 'Compra de Mercadería'),
            ('FLETES', 'Fletes y Transporte'),
            ('DEV_VENTA', 'Devolución de Venta'),
            ('SUELDOS', 'Sueldos y Salarios'),
            ('SUMINISTROS', 'Suministros'),
            ('ALQUILER', 'Alquiler y Servicios'),
            ('MANTENIMIENTO', 'Mantenimiento y Reparaciones'),
        ]

        created = 0
        for codigo, nombre in (tipos_ingreso + tipos_egreso):
            tipo, was_created = TipoMovimiento.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'descripcion': '',
                    'activo': True
                }
            )
            if was_created:
                self.stdout.write(self.style.SUCCESS(f'Creado: {codigo} - {nombre}'))
                created += 1
            else:
                # actualizar nombre si difiere
                if tipo.nombre != nombre:
                    tipo.nombre = nombre
                    tipo.save()
                    self.stdout.write(f'Actualizado nombre: {codigo} -> {nombre}')
                else:
                    self.stdout.write(f'Ya existe: {codigo} - {nombre}')

        self.stdout.write(self.style.SUCCESS(f'Proceso completado. Nuevos creados: {created}'))
