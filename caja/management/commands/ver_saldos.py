"""
Command simple para verificar saldo
"""
from django.core.management.base import BaseCommand
from caja.models import Cuenta, CajaRegistradora
from decimal import Decimal


class Command(BaseCommand):
    help = 'Verifica saldos actuales'

    def handle(self, *args, **options):
        # Dinero Guardado (suma de cajas cerradas)
        cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
        saldo_guardado = sum(
            caja.dinero_en_caja or Decimal('0.00') 
            for caja in cajas_cerradas
        )
        self.stdout.write(f'Dinero Guardado: ${saldo_guardado:,.0f}')
        
        # Banco
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        if cuenta_banco:
            self.stdout.write(f'Banco Principal: ${cuenta_banco.saldo_actual:,.0f}')
            
        self.stdout.write('✅ Saldos verificados')