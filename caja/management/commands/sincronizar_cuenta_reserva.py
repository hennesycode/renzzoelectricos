"""
Management command para sincronizar el saldo de la cuenta reserva con las cajas cerradas.
Renzzo Eléctricos - Villavicencio, Meta
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from caja.models import Cuenta, CajaRegistradora, TransaccionGeneral


class Command(BaseCommand):
    help = 'Sincroniza el saldo de la cuenta reserva con el dinero guardado de las cajas'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== SINCRONIZAR CUENTA RESERVA ===\n')
        )

        try:
            # Obtener o crear cuenta reserva
            cuenta_reserva, created = Cuenta.objects.get_or_create(
                tipo=Cuenta.TipoCuentaChoices.RESERVA,
                defaults={
                    'nombre': 'Dinero Guardado',
                    'saldo_actual': Decimal('0.00'),
                    'activo': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('✓ Cuenta reserva creada.')
                )
            else:
                self.stdout.write(
                    f'Cuenta reserva existente: {cuenta_reserva.nombre}'
                )
            
            # Mostrar saldo actual
            self.stdout.write(f'Saldo actual de la cuenta: ${cuenta_reserva.saldo_actual:,.2f}')
            
            # Calcular dinero guardado de todas las cajas cerradas
            total_guardado_cajas = CajaRegistradora.objects.filter(
                estado='CERRADA',
                dinero_guardado__gt=0
            ).aggregate(total=Sum('dinero_guardado'))['total'] or Decimal('0.00')
            
            self.stdout.write(f'Total dinero guardado en cajas: ${total_guardado_cajas:,.2f}')
            
            # Calcular transacciones de la cuenta reserva
            egresos_reserva = TransaccionGeneral.objects.filter(
                cuenta=cuenta_reserva,
                tipo='EGRESO'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            ingresos_reserva = TransaccionGeneral.objects.filter(
                cuenta=cuenta_reserva,
                tipo='INGRESO'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            self.stdout.write(f'Ingresos en transacciones: ${ingresos_reserva:,.2f}')
            self.stdout.write(f'Egresos en transacciones: ${egresos_reserva:,.2f}')
            
            # Calcular saldo correcto
            saldo_correcto = total_guardado_cajas + ingresos_reserva - egresos_reserva
            
            self.stdout.write(f'\nSaldo correcto calculado: ${saldo_correcto:,.2f}')
            
            # Actualizar saldo si es diferente
            if cuenta_reserva.saldo_actual != saldo_correcto:
                diferencia = saldo_correcto - cuenta_reserva.saldo_actual
                
                self.stdout.write(
                    self.style.WARNING(
                        f'Diferencia encontrada: ${diferencia:+,.2f}'
                    )
                )
                
                confirmacion = input('¿Actualizar el saldo de la cuenta reserva? (s/n): ').strip().lower()
                
                if confirmacion in ['s', 'si', 'sí']:
                    cuenta_reserva.saldo_actual = saldo_correcto
                    cuenta_reserva.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Saldo actualizado a ${saldo_correcto:,.2f}'
                        )
                    )
                else:
                    self.stdout.write('Operación cancelada.')
            else:
                self.stdout.write(
                    self.style.SUCCESS('✓ El saldo ya está correcto.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )