from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from caja.models import Cuenta, TransaccionGeneral


class Command(BaseCommand):
    help = 'Corrige los saldos de las cuentas banco y reserva basándose en las transacciones'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Iniciando corrección de saldos de cuentas...")
        
        # Corregir cuenta BANCO
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        if cuenta_banco:
            self.corregir_cuenta(cuenta_banco, 'BANCO')
        else:
            self.stdout.write(self.style.WARNING("⚠️  No se encontró cuenta BANCO activa"))
        
        # Corregir cuenta RESERVA
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        if cuenta_reserva:
            self.corregir_cuenta(cuenta_reserva, 'RESERVA')
        else:
            self.stdout.write(self.style.WARNING("⚠️  No se encontró cuenta RESERVA activa"))
        
        self.stdout.write(self.style.SUCCESS("✅ Corrección de saldos completada"))

    def corregir_cuenta(self, cuenta, tipo_nombre):
        """Corrige el saldo de una cuenta específica"""
        transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta)
        
        total_ingresos = transacciones.filter(tipo='INGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        total_egresos = transacciones.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        saldo_calculado = total_ingresos - total_egresos
        saldo_anterior = cuenta.saldo_actual
        
        self.stdout.write(f"\n📊 {tipo_nombre} - {cuenta.nombre}:")
        self.stdout.write(f"   Transacciones: {transacciones.count()}")
        self.stdout.write(f"   Ingresos: ${total_ingresos:,.2f}")
        self.stdout.write(f"   Egresos: ${total_egresos:,.2f}")
        self.stdout.write(f"   Saldo anterior: ${saldo_anterior:,.2f}")
        self.stdout.write(f"   Saldo calculado: ${saldo_calculado:,.2f}")
        
        if saldo_anterior != saldo_calculado:
            cuenta.saldo_actual = saldo_calculado
            cuenta.save()
            diferencia = saldo_calculado - saldo_anterior
            if diferencia > 0:
                self.stdout.write(self.style.SUCCESS(f"   ✅ Saldo corregido (+${diferencia:,.2f})"))
            else:
                self.stdout.write(self.style.SUCCESS(f"   ✅ Saldo corregido (${diferencia:,.2f})"))
        else:
            self.stdout.write(self.style.SUCCESS("   ✅ Saldo ya estaba correcto"))