"""
Command simple para verificar saldo
"""
from django.core.management.base import BaseCommand
from caja.models import Cuenta


class Command(BaseCommand):
    help = 'Verifica saldos actuales'

    def handle(self, *args, **options):
        # Dinero Guardado
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        if cuenta_reserva:
            self.stdout.write(f'Dinero Guardado: ${cuenta_reserva.saldo_actual:,.0f}')
        
        # Banco
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        if cuenta_banco:
            self.stdout.write(f'Banco Principal: ${cuenta_banco.saldo_actual:,.0f}')
            
        self.stdout.write('✅ Saldos verificados')