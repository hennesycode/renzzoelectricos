"""
Script para limpiar completamente el sistema de caja y tesorería
Elimina todas las transacciones, cajas, movimientos y conteos existentes.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from caja.models import (
    CajaRegistradora, MovimientoCaja, TransaccionGeneral,
    ConteoEfectivo, DetalleConteo, Cuenta
)


class Command(BaseCommand):
    help = 'Limpia completamente el sistema de caja y tesorería'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar que desea eliminar todos los datos',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Este comando eliminará TODOS los datos de caja y tesorería.\n'
                    'Para confirmar, ejecute:\n'
                    'python manage.py limpiar_sistema_caja --confirm'
                )
            )
            return

        self.stdout.write("🧹 Limpiando sistema de caja y tesorería...")
        
        with transaction.atomic():
            # Contar registros antes de eliminar
            cajas_count = CajaRegistradora.objects.count()
            movimientos_count = MovimientoCaja.objects.count()
            transacciones_count = TransaccionGeneral.objects.count()
            conteos_count = ConteoEfectivo.objects.count()
            detalles_count = DetalleConteo.objects.count()
            
            self.stdout.write(f"📊 Registros encontrados:")
            self.stdout.write(f"   - Cajas: {cajas_count}")
            self.stdout.write(f"   - Movimientos: {movimientos_count}")
            self.stdout.write(f"   - Transacciones: {transacciones_count}")
            self.stdout.write(f"   - Conteos: {conteos_count}")
            self.stdout.write(f"   - Detalles conteo: {detalles_count}")
            
            # Eliminar en orden para evitar problemas de foreign keys
            self.stdout.write("🗑️  Eliminando datos...")
            
            # 1. Detalles de conteo (dependen de conteos)
            DetalleConteo.objects.all().delete()
            self.stdout.write("   ✓ Detalles de conteo eliminados")
            
            # 2. Conteos de efectivo (dependen de cajas)
            ConteoEfectivo.objects.all().delete()
            self.stdout.write("   ✓ Conteos de efectivo eliminados")
            
            # 3. Transacciones generales
            TransaccionGeneral.objects.all().delete()
            self.stdout.write("   ✓ Transacciones de tesorería eliminadas")
            
            # 4. Movimientos de caja (dependen de cajas)
            MovimientoCaja.objects.all().delete()
            self.stdout.write("   ✓ Movimientos de caja eliminados")
            
            # 5. Cajas registradoras
            CajaRegistradora.objects.all().delete()
            self.stdout.write("   ✓ Cajas registradoras eliminadas")
            
            # 6. Resetear saldos de cuentas a cero
            self.resetear_saldos_cuentas()
            
            total_eliminados = (cajas_count + movimientos_count + 
                              transacciones_count + conteos_count + detalles_count)
            
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Sistema limpiado exitosamente!\n'
                f'📈 Total de registros eliminados: {total_eliminados}\n'
                f'🎯 El sistema está listo para usar desde cero.'
            )
        )
    
    def resetear_saldos_cuentas(self):
        """Resetea los saldos de todas las cuentas a cero."""
        cuentas_actualizadas = 0
        
        for cuenta in Cuenta.objects.all():
            if cuenta.saldo_actual != Decimal('0.00'):
                cuenta.saldo_actual = Decimal('0.00')
                cuenta.save()
                cuentas_actualizadas += 1
                self.stdout.write(f"   ↻ Saldo de '{cuenta.nombre}' reseteado a $0")
        
        if cuentas_actualizadas == 0:
            self.stdout.write("   → Saldos de cuentas ya estaban en $0")
        else:
            self.stdout.write(f"   ✓ {cuentas_actualizadas} cuentas reseteadas a $0")