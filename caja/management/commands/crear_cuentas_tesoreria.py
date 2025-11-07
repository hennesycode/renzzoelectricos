"""
Comando para crear las cuentas iniciales de Tesorería.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from caja.models import Cuenta


class Command(BaseCommand):
    help = 'Crea las cuentas iniciales de Tesorería (Banco y Reserva)'

    def handle(self, *args, **options):
        self.stdout.write('🏦 Creando cuentas de Tesorería...\n')
        
        with transaction.atomic():
            # Crear cuenta de Banco
            banco, created_banco = Cuenta.objects.get_or_create(
                tipo='BANCO',
                defaults={
                    'nombre': 'Banco Principal',
                    'saldo_actual': 0,
                    'activo': True
                }
            )
            
            if created_banco:
                self.stdout.write(self.style.SUCCESS(f'✅ Creada: {banco.nombre} (Banco)'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Ya existe: {banco.nombre}'))
            
            # Crear cuenta de Reserva
            reserva, created_reserva = Cuenta.objects.get_or_create(
                tipo='RESERVA',
                defaults={
                    'nombre': 'Dinero Guardado',
                    'saldo_actual': 0,
                    'activo': True
                }
            )
            
            if created_reserva:
                self.stdout.write(self.style.SUCCESS(f'✅ Creada: {reserva.nombre} (Reserva)'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Ya existe: {reserva.nombre}'))
        
        self.stdout.write('\n' + self.style.SUCCESS('✨ Proceso completado!'))
        self.stdout.write('\n📊 Resumen de cuentas:')
        
        for cuenta in Cuenta.objects.all():
            estado = '✓ Activa' if cuenta.activo else '✗ Inactiva'
            self.stdout.write(f'  - {cuenta.nombre} ({cuenta.get_tipo_display()}) - Saldo: ${cuenta.saldo_actual:,.0f} - {estado}')
