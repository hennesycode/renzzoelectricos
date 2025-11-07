"""
Management command para verificar el estado de la cuenta reserva
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from caja.models import Cuenta, TransaccionGeneral, CajaRegistradora


class Command(BaseCommand):
    help = 'Verifica el estado actual de la cuenta reserva'

    def handle(self, *args, **options):
        self.stdout.write('=== ANÁLISIS DE CUENTA RESERVA ===\n')

        # Verificar cuenta reserva
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        if cuenta_reserva:
            self.stdout.write(f'Cuenta Reserva: {cuenta_reserva.nombre}')
            self.stdout.write(f'Saldo actual en BD: ${cuenta_reserva.saldo_actual:,.2f}')
            self.stdout.write(f'ID de cuenta: {cuenta_reserva.id}')
        else:
            self.stdout.write(self.style.ERROR('❌ No hay cuenta reserva activa'))
            return

        self.stdout.write('')

        # Verificar transacciones de balance recientes
        transacciones_balance = TransaccionGeneral.objects.filter(
            descripcion__icontains='Balance:'
        ).order_by('-fecha')[:3]

        self.stdout.write(f'Últimas {len(transacciones_balance)} transacciones de balance:')
        for t in transacciones_balance:
            fecha_str = t.fecha.strftime('%d/%m/%Y %H:%M')
            self.stdout.write(f'- {fecha_str} | {t.tipo} | ${t.monto:,.0f}')

        self.stdout.write('')

        # Verificar si el saldo está correcto después del balance
        saldo_esperado = Decimal('100000.00')  # El valor que se puso en el balance
        
        if cuenta_reserva.saldo_actual == saldo_esperado:
            self.stdout.write(self.style.SUCCESS('✅ El saldo está correcto'))
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ El saldo debe ser ${saldo_esperado:,.2f} '
                    f'pero está en ${cuenta_reserva.saldo_actual:,.2f}'
                )
            )
            
            # Preguntar si corregir
            respuesta = input('¿Corregir el saldo ahora? (s/n): ').strip().lower()
            if respuesta in ['s', 'si', 'sí']:
                cuenta_reserva.saldo_actual = saldo_esperado
                cuenta_reserva.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Saldo corregido a ${saldo_esperado:,.2f}'
                    )
                )
            else:
                self.stdout.write('Operación cancelada.')