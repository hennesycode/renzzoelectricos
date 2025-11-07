"""
Comando para eliminar transacciones de balance incorrectas que están causando problemas.
Solo elimina transacciones de tipo 'Balance:' que fueron ajustes manuales erróneos.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from caja.models import TransaccionGeneral


class Command(BaseCommand):
    help = 'Elimina transacciones de balance incorrectas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Aplicar realmente los cambios'
        )
        parser.add_argument(
            '--patron',
            type=str,
            default='Balance:',
            help='Patrón en la descripción para identificar transacciones a eliminar'
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']
        patron = options['patron']
        
        self.stdout.write(self.style.SUCCESS("🗑️ LIMPIEZA DE TRANSACCIONES INCORRECTAS"))
        self.stdout.write("=" * 60)
        
        if not aplicar:
            self.stdout.write(self.style.WARNING("⚠️  MODO SIMULACIÓN - Para aplicar usa --aplicar"))
        
        # Buscar transacciones con el patrón en la descripción
        transacciones_incorrectas = TransaccionGeneral.objects.filter(
            descripcion__icontains=patron
        ).order_by('-fecha')
        
        self.stdout.write(f"🔍 Buscando transacciones con patrón: '{patron}'")
        self.stdout.write(f"📊 Encontradas: {transacciones_incorrectas.count()} transacciones")
        
        if transacciones_incorrectas.count() == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay transacciones para eliminar"))
            return
        
        total_eliminadas = 0
        total_monto_banco = 0
        total_monto_reserva = 0
        
        self.stdout.write("\n📋 TRANSACCIONES A ELIMINAR:")
        
        for trans in transacciones_incorrectas:
            signo = '+' if trans.tipo == 'INGRESO' else '-'
            fecha_str = trans.fecha.strftime('%d/%m %H:%M')
            cuenta_tipo = trans.cuenta.tipo if trans.cuenta else 'N/A'
            
            self.stdout.write(f"   {fecha_str} | {signo}${trans.monto:,.0f} | {cuenta_tipo} | {trans.descripcion[:50]}")
            
            if trans.cuenta and trans.cuenta.tipo == 'BANCO':
                if trans.tipo == 'INGRESO':
                    total_monto_banco += trans.monto
                else:
                    total_monto_banco -= trans.monto
            elif trans.cuenta and trans.cuenta.tipo == 'RESERVA':
                if trans.tipo == 'INGRESO':
                    total_monto_reserva += trans.monto
                else:
                    total_monto_reserva -= trans.monto
        
        self.stdout.write(f"\n💰 IMPACTO EN SALDOS:")
        self.stdout.write(f"   Banco: {total_monto_banco:+,.0f}")
        self.stdout.write(f"   Reserva: {total_monto_reserva:+,.0f}")
        
        if aplicar:
            # Eliminar las transacciones
            with transaction.atomic():
                eliminadas = transacciones_incorrectas.delete()
                total_eliminadas = eliminadas[0]
            
            self.stdout.write(f"\n✅ ELIMINADAS: {total_eliminadas} transacciones")
            
            # Recalcular saldos de banco (RESERVA se calcula dinámicamente)
            from caja.models import Cuenta
            from django.db.models import Sum
            from decimal import Decimal
            
            cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
            if cuenta_banco:
                transacciones_banco = TransaccionGeneral.objects.filter(cuenta=cuenta_banco)
                ingresos = transacciones_banco.filter(tipo='INGRESO').aggregate(
                    total=Sum('monto'))['total'] or Decimal('0.00')
                egresos = transacciones_banco.filter(tipo='EGRESO').aggregate(
                    total=Sum('monto'))['total'] or Decimal('0.00')
                
                saldo_anterior = cuenta_banco.saldo_actual
                cuenta_banco.saldo_actual = ingresos - egresos
                cuenta_banco.save()
                
                diferencia = cuenta_banco.saldo_actual - saldo_anterior
                self.stdout.write(f"🏦 BANCO RECALCULADO: ${saldo_anterior:,.0f} → ${cuenta_banco.saldo_actual:,.0f} ({diferencia:+,.0f})")
        else:
            self.stdout.write(f"\n💡 Para aplicar: python manage.py limpiar_balances_incorrectos --aplicar")
        
        self.stdout.write("\n" + "=" * 60)
        if aplicar:
            self.stdout.write(self.style.SUCCESS("✅ LIMPIEZA COMPLETADA"))
        else:
            self.stdout.write(self.style.WARNING(f"💡 Se eliminarían {transacciones_incorrectas.count()} transacciones"))