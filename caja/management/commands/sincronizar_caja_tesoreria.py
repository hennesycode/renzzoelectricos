"""
Comando para sincronizar TODOS los movimientos de caja con tesorería.
Crea TransaccionGeneral para cada MovimientoCaja que no tenga registro en tesorería.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from caja.models import (
    CajaRegistradora, MovimientoCaja, TransaccionGeneral, 
    Cuenta, TipoMovimiento
)


class Command(BaseCommand):
    help = 'Sincroniza todos los movimientos de caja con tesorería'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Aplicar realmente los cambios (por defecto solo simula)'
        )
        parser.add_argument(
            '--caja',
            type=int,
            help='ID de caja específica a sincronizar (opcional)'
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']
        caja_id = options.get('caja')
        
        self.stdout.write(self.style.SUCCESS("🔄 SINCRONIZACIÓN CAJA ↔ TESORERÍA"))
        self.stdout.write("=" * 60)
        
        if not aplicar:
            self.stdout.write(self.style.WARNING("⚠️  MODO SIMULACIÓN - Para aplicar usa --aplicar"))
        
        # Obtener cuentas necesarias
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        
        if not cuenta_banco:
            self.stdout.write(self.style.ERROR("❌ No hay cuenta BANCO activa"))
            return
        
        if not cuenta_reserva:
            self.stdout.write(self.style.ERROR("❌ No hay cuenta RESERVA activa"))
            return
        
        # Filtrar cajas
        if caja_id:
            cajas = CajaRegistradora.objects.filter(id=caja_id)
            if not cajas.exists():
                self.stdout.write(self.style.ERROR(f"❌ No existe caja con ID {caja_id}"))
                return
        else:
            cajas = CajaRegistradora.objects.all()
        
        transacciones_creadas = 0
        
        for caja in cajas:
            self.stdout.write(f"\n📦 PROCESANDO CAJA {caja.id} ({caja.get_estado_display()})")
            
            # Obtener movimientos de esta caja que NO tengan transacción asociada
            movimientos = MovimientoCaja.objects.filter(
                caja=caja,
                transaccion_asociada__isnull=True
            ).exclude(
                tipo_movimiento__codigo='APERTURA'  # Excluir aperturas
            )
            
            self.stdout.write(f"   Movimientos sin sincronizar: {movimientos.count()}")
            
            for movimiento in movimientos:
                # Determinar si es entrada al banco
                es_entrada_banco = '[BANCO]' in (movimiento.descripcion or '')
                
                if es_entrada_banco:
                    # Crear transacción en BANCO
                    cuenta_destino = cuenta_banco
                    descripcion = f"[CAJA {caja.id}] {movimiento.descripcion}"
                else:
                    # Movimiento normal de caja - registrar en RESERVA para tracking
                    cuenta_destino = cuenta_reserva
                    descripcion = f"[CAJA {caja.id}] {movimiento.descripcion or 'Movimiento de caja'}"
                
                # Determinar tipo de transacción
                if movimiento.tipo == 'INGRESO':
                    tipo_transaccion = TransaccionGeneral.TipoTransaccionChoices.INGRESO
                    simbolo = "+"
                else:
                    tipo_transaccion = TransaccionGeneral.TipoTransaccionChoices.EGRESO
                    simbolo = "-"
                
                self.stdout.write(f"   {simbolo}${movimiento.monto:,.0f} - {movimiento.tipo_movimiento.nombre}")
                self.stdout.write(f"     → {'BANCO' if es_entrada_banco else 'TRACKING'}")
                
                if aplicar:
                    with transaction.atomic():
                        # Crear la transacción en tesorería
                        transaccion = TransaccionGeneral.objects.create(
                            fecha=movimiento.fecha_movimiento,
                            tipo=tipo_transaccion,
                            monto=movimiento.monto,
                            descripcion=descripcion,
                            referencia=movimiento.referencia or '',
                            tipo_movimiento=movimiento.tipo_movimiento,
                            cuenta=cuenta_destino,
                            usuario=movimiento.usuario,
                            movimiento_caja_asociado=movimiento
                        )
                        
                        # Actualizar el movimiento para marcar que ya tiene transacción
                        movimiento.transaccion_asociada = transaccion
                        movimiento.save()
                        
                        transacciones_creadas += 1
                else:
                    # En modo simulación, también contar
                    transacciones_creadas += 1
        
        self.stdout.write(f"\n" + "=" * 60)
        if aplicar:
            self.stdout.write(self.style.SUCCESS(f"✅ SINCRONIZACIÓN COMPLETADA: {transacciones_creadas} transacciones creadas"))
        else:
            self.stdout.write(self.style.WARNING(f"💡 SIMULACIÓN: Se crearían {transacciones_creadas} transacciones"))
            self.stdout.write("   Para aplicar: python manage.py sincronizar_caja_tesoreria --aplicar")
        
        # Recalcular saldos después de sincronizar
        if aplicar and transacciones_creadas > 0:
            self.stdout.write("\n🔧 Recalculando saldos...")
            self.recalcular_saldos(cuenta_banco, cuenta_reserva)
    
    def recalcular_saldos(self, cuenta_banco, cuenta_reserva):
        """Recalcula los saldos de las cuentas después de la sincronización"""
        
        # Recalcular BANCO
        from django.db.models import Sum
        transacciones_banco = TransaccionGeneral.objects.filter(cuenta=cuenta_banco)
        ingresos_banco = transacciones_banco.filter(tipo='INGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        egresos_banco = transacciones_banco.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        saldo_banco_calculado = ingresos_banco - egresos_banco
        saldo_banco_anterior = cuenta_banco.saldo_actual
        
        cuenta_banco.saldo_actual = saldo_banco_calculado
        cuenta_banco.save()
        
        diferencia_banco = saldo_banco_calculado - saldo_banco_anterior
        
        self.stdout.write(f"🏦 BANCO: ${saldo_banco_anterior:,.0f} → ${saldo_banco_calculado:,.0f} ({diferencia_banco:+,.0f})")
        
        # Para RESERVA no actualizamos saldo_actual (se calcula dinámicamente)
        self.stdout.write("💰 RESERVA: Se calcula dinámicamente (sin cambios en saldo_actual)")