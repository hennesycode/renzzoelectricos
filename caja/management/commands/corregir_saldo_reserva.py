"""
Management command para corregir manualmente el saldo de la cuenta reserva.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from caja.models import Cuenta


class Command(BaseCommand):
    help = 'Corrige manualmente el saldo de la cuenta reserva'

    def add_arguments(self, parser):
        parser.add_argument(
            '--saldo',
            type=str,
            help='Nuevo saldo para la cuenta reserva'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== CORREGIR SALDO CUENTA RESERVA ===\n')
        )

        try:
            # Obtener cuenta reserva
            cuenta_reserva = Cuenta.objects.filter(
                tipo=Cuenta.TipoCuentaChoices.RESERVA,
                activo=True
            ).first()
            
            if not cuenta_reserva:
                self.stdout.write(
                    self.style.ERROR('No se encontró cuenta reserva activa.')
                )
                return
            
            self.stdout.write(f'Cuenta encontrada: {cuenta_reserva.nombre}')
            self.stdout.write(f'Saldo actual: ${cuenta_reserva.saldo_actual:,.2f}')
            
            # Obtener nuevo saldo
            nuevo_saldo_str = options.get('saldo')
            
            if nuevo_saldo_str:
                try:
                    nuevo_saldo = Decimal(nuevo_saldo_str.replace(',', ''))
                except:
                    self.stdout.write(self.style.ERROR('Saldo inválido.'))
                    return
            else:
                # Preguntar por el nuevo saldo
                while True:
                    saldo_input = input('Ingrese el nuevo saldo (sin $, use punto para decimales): ').strip()
                    try:
                        nuevo_saldo = Decimal(saldo_input.replace(',', ''))
                        break
                    except:
                        self.stdout.write(self.style.ERROR('Formato inválido. Ej: 100000'))
            
            # Mostrar cambio
            diferencia = nuevo_saldo - cuenta_reserva.saldo_actual
            self.stdout.write(f'\nNuevo saldo: ${nuevo_saldo:,.2f}')
            self.stdout.write(f'Diferencia: ${diferencia:+,.2f}')
            
            # Confirmar
            confirmacion = input('\n¿Confirmar el cambio? (s/n): ').strip().lower()
            
            if confirmacion in ['s', 'si', 'sí']:
                # Actualizar saldo
                cuenta_reserva.saldo_actual = nuevo_saldo
                cuenta_reserva.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✓ Saldo actualizado exitosamente!\n'
                        f'  Cuenta: {cuenta_reserva.nombre}\n'
                        f'  Nuevo saldo: ${nuevo_saldo:,.2f}'
                    )
                )
            else:
                self.stdout.write('Operación cancelada.')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )