"""
Comando para sincronizar automáticamente los saldos de las cuentas bancarias
basándose en sus transacciones reales.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from caja.models import Cuenta, TransaccionGeneral


class Command(BaseCommand):
    help = 'Sincroniza los saldos de las cuentas bancarias con sus transacciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cuenta',
            type=str,
            choices=['BANCO', 'RESERVA', 'ALL'],
            default='ALL',
            help='Tipo de cuenta a sincronizar (BANCO, RESERVA, o ALL)'
        )

    def handle(self, *args, **options):
        cuenta_tipo = options['cuenta']
        
        self.stdout.write(self.style.SUCCESS("🔄 SINCRONIZACIÓN DE SALDOS"))
        self.stdout.write("=" * 50)
        
        if cuenta_tipo == 'ALL' or cuenta_tipo == 'BANCO':
            self.sincronizar_banco()
        
        if cuenta_tipo == 'ALL' or cuenta_tipo == 'RESERVA':
            self.sincronizar_reserva()
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("✅ SINCRONIZACIÓN COMPLETADA"))

    def sincronizar_banco(self):
        """Sincroniza la cuenta BANCO usando el método correcto"""
        self.stdout.write("\n🏦 SINCRONIZANDO BANCO PRINCIPAL:")
        
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        
        if not cuenta_banco:
            self.stdout.write(self.style.ERROR("   ❌ No hay cuenta BANCO activa"))
            return
        
        # Importar aquí para evitar dependencias circulares
        from caja.models import MovimientoCaja
        
        # Calcular saldo dinámico usando el método correcto
        # Entradas del banco = ingresos de MovimientoCaja con [BANCO]
        entradas_banco = MovimientoCaja.objects.filter(
            tipo='INGRESO',
            descripcion__icontains='[BANCO]'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        # Egresos del banco = transacciones EGRESO del banco
        egresos_banco = TransaccionGeneral.objects.filter(
            cuenta=cuenta_banco,
            tipo='EGRESO'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        saldo_calculado = entradas_banco - egresos_banco
        saldo_actual = cuenta_banco.saldo_actual
        
        # Contar todas las transacciones del banco para mostrar
        total_transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta_banco).count()
        
        self.stdout.write(f"   Cuenta: {cuenta_banco.nombre}")
        self.stdout.write(f"   Transacciones totales: {total_transacciones}")
        self.stdout.write(f"   Entradas desde caja: ${entradas_banco:,.2f}")
        self.stdout.write(f"   Egresos (gastos): ${egresos_banco:,.2f}")
        self.stdout.write(f"   Saldo actual: ${saldo_actual:,.2f}")
        self.stdout.write(f"   Saldo calculado: ${saldo_calculado:,.2f}")
        
        if saldo_actual != saldo_calculado:
            diferencia = saldo_calculado - saldo_actual
            cuenta_banco.saldo_actual = saldo_calculado
            cuenta_banco.save()
            
            if diferencia > 0:
                self.stdout.write(self.style.SUCCESS(f"   ✅ CORREGIDO: +${diferencia:,.2f}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"   ✅ CORREGIDO: ${diferencia:,.2f}"))
        else:
            self.stdout.write(self.style.SUCCESS("   ✅ Ya estaba sincronizado"))

    def sincronizar_reserva(self):
        """Sincroniza la cuenta RESERVA (no cambia saldo_actual, solo reporta)"""
        self.stdout.write("\n💰 VERIFICANDO DINERO GUARDADO:")
        
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        
        if not cuenta_reserva:
            self.stdout.write(self.style.WARNING("   ⚠️  No hay cuenta RESERVA activa"))
            return
        
        # El dinero guardado se calcula dinámicamente, no se sincroniza
        # Solo reportamos el estado actual
        
        from caja.models import CajaRegistradora
        
        # Dinero de cajas cerradas
        cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
        total_cajas_cerradas = sum(
            caja.dinero_en_caja or Decimal('0.00') 
            for caja in cajas_cerradas
        )
        
        # Transacciones en cuenta RESERVA
        transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta_reserva)
        ingresos = transacciones.filter(tipo='INGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        egresos = transacciones.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        ajustes_reserva = ingresos - egresos
        dinero_guardado_total = total_cajas_cerradas + ajustes_reserva
        
        self.stdout.write(f"   Cuenta: {cuenta_reserva.nombre}")
        self.stdout.write(f"   Cajas cerradas: {cajas_cerradas.count()}")
        self.stdout.write(f"   Dinero de cajas: ${total_cajas_cerradas:,.2f}")
        self.stdout.write(f"   Transacciones RESERVA: {transacciones.count()}")
        self.stdout.write(f"   Ajustes (+/-): ${ajustes_reserva:,.2f}")
        self.stdout.write(f"   DINERO GUARDADO TOTAL: ${dinero_guardado_total:,.2f}")
        self.stdout.write(f"   Saldo cuenta (ignorado): ${cuenta_reserva.saldo_actual:,.2f}")
        
        # Nota informativa
        self.stdout.write(self.style.WARNING("   ℹ️  El dinero guardado se calcula dinámicamente"))
        self.stdout.write(self.style.WARNING("   ℹ️  No se modifica saldo_actual de la cuenta RESERVA"))