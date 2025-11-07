"""
Management command para establecer el saldo correcto de cualquier cuenta después de un balance
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from caja.models import Cuenta


class Command(BaseCommand):
    help = 'Establece el saldo correcto de una cuenta'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cuenta',
            type=str,
            choices=['caja', 'banco', 'reserva'],
            help='Tipo de cuenta a actualizar'
        )
        parser.add_argument(
            '--saldo',
            type=str,
            help='Nuevo saldo para la cuenta'
        )

    def handle(self, *args, **options):
        cuenta_tipo = options.get('cuenta')
        nuevo_saldo_str = options.get('saldo')
        
        if not cuenta_tipo:
            self.stdout.write(self.style.ERROR('Debe especificar --cuenta (caja, banco, reserva)'))
            return
            
        if not nuevo_saldo_str:
            self.stdout.write(self.style.ERROR('Debe especificar --saldo'))
            return

        try:
            nuevo_saldo = Decimal(nuevo_saldo_str.replace(',', ''))
        except:
            self.stdout.write(self.style.ERROR('Saldo inválido'))
            return

        # Obtener cuenta según tipo
        if cuenta_tipo == 'banco':
            cuenta = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        elif cuenta_tipo == 'reserva':
            cuenta = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        else:
            self.stdout.write(self.style.ERROR('Tipo de cuenta no soportado para esta operación'))
            return

        if not cuenta:
            self.stdout.write(self.style.ERROR(f'No se encontró cuenta {cuenta_tipo} activa'))
            return

        # Mostrar cambio
        saldo_anterior = cuenta.saldo_actual
        diferencia = nuevo_saldo - saldo_anterior
        
        self.stdout.write(f'Cuenta: {cuenta.nombre}')
        self.stdout.write(f'Saldo anterior: ${saldo_anterior:,.2f}')
        self.stdout.write(f'Nuevo saldo: ${nuevo_saldo:,.2f}')
        self.stdout.write(f'Diferencia: ${diferencia:+,.2f}')

        # Actualizar
        cuenta.saldo_actual = nuevo_saldo
        cuenta.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Saldo de {cuenta.nombre} actualizado a ${nuevo_saldo:,.2f}'
            )
        )