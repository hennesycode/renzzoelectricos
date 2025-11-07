"""
Comando para validar y corregir la integridad completa del sistema de caja y tesorería.
Detecta y reporta inconsistencias entre los diferentes métodos de cálculo.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from caja.models import CajaRegistradora, MovimientoCaja, Cuenta, TransaccionGeneral
from django.utils import timezone


class Command(BaseCommand):
    help = 'Valida la integridad completa del sistema de caja y tesorería'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix', 
            action='store_true',
            help='Corregir automáticamente las inconsistencias encontradas'
        )

    def handle(self, *args, **options):
        self.fix_mode = options['fix']
        
        self.stdout.write(self.style.SUCCESS("🔍 VALIDACIÓN COMPLETA DEL SISTEMA"))
        self.stdout.write("=" * 60)
        
        # 1. Validar Dinero en Caja
        self.validar_dinero_caja()
        
        # 2. Validar Banco Principal  
        self.validar_banco_principal()
        
        # 3. Validar Dinero Guardado
        self.validar_dinero_guardado()
        
        # 4. Validar Coherencia Total
        self.validar_coherencia_total()
        
        self.stdout.write("\n" + "=" * 60)
        if self.fix_mode:
            self.stdout.write(self.style.SUCCESS("✅ VALIDACIÓN Y CORRECCIÓN COMPLETADA"))
        else:
            self.stdout.write(self.style.WARNING("ℹ️  VALIDACIÓN COMPLETADA (sin correcciones)"))
            self.stdout.write("💡 Ejecuta con --fix para aplicar correcciones automáticas")

    def validar_dinero_caja(self):
        """Valida el cálculo de dinero en caja"""
        self.stdout.write("\n📦 DINERO EN CAJA:")
        
        caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
        
        if caja_abierta:
            # Calcular saldo según el método del dashboard
            movimientos = MovimientoCaja.objects.filter(caja=caja_abierta)
            
            total_ingresos = movimientos.filter(
                tipo='INGRESO'
            ).exclude(
                tipo_movimiento__codigo='APERTURA'
            ).exclude(
                descripcion__icontains='[BANCO]'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            
            total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            
            saldo_calculado = caja_abierta.monto_inicial + total_ingresos - total_egresos
            saldo_sistema = caja_abierta.calcular_monto_sistema()
            
            self.stdout.write(f"   Caja abierta: ID {caja_abierta.id}")
            self.stdout.write(f"   Monto inicial: ${caja_abierta.monto_inicial:,.2f}")
            self.stdout.write(f"   Ingresos efectivo: ${total_ingresos:,.2f}")
            self.stdout.write(f"   Egresos: ${total_egresos:,.2f}")
            self.stdout.write(f"   Saldo dashboard: ${saldo_calculado:,.2f}")
            self.stdout.write(f"   Saldo método modelo: ${saldo_sistema:,.2f}")
            
            if saldo_calculado != saldo_sistema:
                self.stdout.write(self.style.ERROR(f"   ❌ INCONSISTENCIA: ${saldo_calculado - saldo_sistema:,.2f}"))
            else:
                self.stdout.write(self.style.SUCCESS("   ✅ Cálculo consistente"))
        else:
            # Caja cerrada - mostrar último dinero_en_caja
            ultima_caja = CajaRegistradora.objects.filter(
                estado='CERRADA'
            ).order_by('-fecha_cierre').first()
            
            if ultima_caja:
                self.stdout.write(f"   No hay caja abierta")
                self.stdout.write(f"   Última caja cerrada: ${ultima_caja.dinero_en_caja or 0:,.2f}")
            else:
                self.stdout.write("   No hay cajas registradas")

    def validar_banco_principal(self):
        """Valida el cálculo del banco principal"""
        self.stdout.write("\n🏦 BANCO PRINCIPAL:")
        
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        
        if not cuenta_banco:
            self.stdout.write(self.style.ERROR("   ❌ No hay cuenta BANCO activa"))
            return
        
        # Método 1: saldo_actual de la cuenta
        saldo_cuenta = cuenta_banco.saldo_actual
        
        # Método 2: Transacciones en la cuenta
        transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta_banco)
        ingresos_trans = transacciones.filter(tipo='INGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        egresos_trans = transacciones.filter(tipo='EGRESO').aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        saldo_transacciones = ingresos_trans - egresos_trans
        
        # Método 3: Entradas desde caja (solo para referencia)
        entradas_banco = MovimientoCaja.objects.filter(
            tipo='INGRESO',
            descripcion__icontains='[BANCO]'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        self.stdout.write(f"   Cuenta: {cuenta_banco.nombre}")
        self.stdout.write(f"   Saldo en cuenta: ${saldo_cuenta:,.2f}")
        self.stdout.write(f"   Saldo por transacciones: ${saldo_transacciones:,.2f}")
        self.stdout.write(f"   Entradas desde caja: ${entradas_banco:,.2f}")
        
        if saldo_cuenta != saldo_transacciones:
            diferencia = saldo_cuenta - saldo_transacciones
            self.stdout.write(self.style.ERROR(f"   ❌ INCONSISTENCIA: ${diferencia:,.2f}"))
            
            if self.fix_mode:
                cuenta_banco.saldo_actual = saldo_transacciones
                cuenta_banco.save()
                self.stdout.write(self.style.SUCCESS(f"   🔧 CORREGIDO: saldo actualizado a ${saldo_transacciones:,.2f}"))
        else:
            self.stdout.write(self.style.SUCCESS("   ✅ Saldo consistente"))

    def validar_dinero_guardado(self):
        """Valida el cálculo del dinero guardado"""
        self.stdout.write("\n💰 DINERO GUARDADO:")
        
        # Método 1: Suma de dinero_en_caja de cajas cerradas (CORRECTO)
        cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
        total_cajas_cerradas = sum(
            caja.dinero_en_caja or Decimal('0.00') 
            for caja in cajas_cerradas
        )
        
        # Método 2: Cuenta RESERVA (PROBLEMÁTICO)
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        saldo_cuenta_reserva = cuenta_reserva.saldo_actual if cuenta_reserva else Decimal('0.00')
        
        # Método 3: Transacciones en cuenta RESERVA
        if cuenta_reserva:
            transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta_reserva)
            ingresos_reserva = transacciones.filter(tipo='INGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            egresos_reserva = transacciones.filter(tipo='EGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            saldo_transacciones_reserva = ingresos_reserva - egresos_reserva
        else:
            saldo_transacciones_reserva = Decimal('0.00')
            ingresos_reserva = Decimal('0.00')
            egresos_reserva = Decimal('0.00')
        
        self.stdout.write(f"   Cajas cerradas: {cajas_cerradas.count()}")
        self.stdout.write(f"   Total en cajas cerradas: ${total_cajas_cerradas:,.2f}")
        self.stdout.write(f"   Saldo cuenta RESERVA: ${saldo_cuenta_reserva:,.2f}")
        self.stdout.write(f"   Transacciones RESERVA: Ing=${ingresos_reserva:,.2f}, Egr=${egresos_reserva:,.2f}")
        self.stdout.write(f"   Saldo por transacciones: ${saldo_transacciones_reserva:,.2f}")
        
        # El dinero guardado real debe ser: cajas cerradas + transacciones reserva
        saldo_real_guardado = total_cajas_cerradas + saldo_transacciones_reserva
        
        self.stdout.write(f"   DINERO GUARDADO REAL: ${saldo_real_guardado:,.2f}")
        
        if cuenta_reserva and saldo_cuenta_reserva != saldo_transacciones_reserva:
            diferencia = saldo_cuenta_reserva - saldo_transacciones_reserva
            self.stdout.write(self.style.ERROR(f"   ❌ INCONSISTENCIA EN CUENTA RESERVA: ${diferencia:,.2f}"))
            
            if self.fix_mode:
                cuenta_reserva.saldo_actual = saldo_transacciones_reserva
                cuenta_reserva.save()
                self.stdout.write(self.style.SUCCESS(f"   🔧 CUENTA RESERVA CORREGIDA"))
        
        if not cuenta_reserva:
            self.stdout.write(self.style.WARNING("   ⚠️  No hay cuenta RESERVA activa"))

    def validar_coherencia_total(self):
        """Valida la coherencia total del sistema"""
        self.stdout.write("\n🎯 COHERENCIA TOTAL:")
        
        # Simular los cálculos del dashboard
        caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
        if caja_abierta:
            movimientos = MovimientoCaja.objects.filter(caja=caja_abierta)
            total_ingresos = movimientos.filter(
                tipo='INGRESO'
            ).exclude(
                tipo_movimiento__codigo='APERTURA'
            ).exclude(
                descripcion__icontains='[BANCO]'
            ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
            total_egresos = movimientos.filter(tipo='EGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            saldo_caja = caja_abierta.monto_inicial + total_ingresos - total_egresos
        else:
            ultima_caja = CajaRegistradora.objects.filter(
                estado='CERRADA'
            ).order_by('-fecha_cierre').first()
            saldo_caja = ultima_caja.dinero_en_caja if ultima_caja else Decimal('0.00')
        
        # Banco
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        saldo_banco = cuenta_banco.saldo_actual if cuenta_banco else Decimal('0.00')
        
        # Dinero guardado (método correcto)
        cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
        total_cajas_cerradas = sum(
            caja.dinero_en_caja or Decimal('0.00') 
            for caja in cajas_cerradas
        )
        
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        if cuenta_reserva:
            transacciones = TransaccionGeneral.objects.filter(cuenta=cuenta_reserva)
            ingresos_reserva = transacciones.filter(tipo='INGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            egresos_reserva = transacciones.filter(tipo='EGRESO').aggregate(
                total=Sum('monto')
            )['total'] or Decimal('0.00')
            ajustes_reserva = ingresos_reserva - egresos_reserva
        else:
            ajustes_reserva = Decimal('0.00')
        
        saldo_guardado = total_cajas_cerradas + ajustes_reserva
        saldo_total = saldo_caja + saldo_banco + saldo_guardado
        
        self.stdout.write(f"   Dinero en Caja: ${saldo_caja:,.2f}")
        self.stdout.write(f"   Banco Principal: ${saldo_banco:,.2f}")
        self.stdout.write(f"   Dinero Guardado: ${saldo_guardado:,.2f}")
        self.stdout.write(f"     - De cajas cerradas: ${total_cajas_cerradas:,.2f}")
        self.stdout.write(f"     - Ajustes RESERVA: ${ajustes_reserva:,.2f}")
        self.stdout.write(f"   TOTAL DISPONIBLE: ${saldo_total:,.2f}")
        
        # Verificar que los comandos devuelvan lo mismo
        from io import StringIO
        import sys
        from django.core.management import call_command
        
        try:
            out = StringIO()
            call_command('ver_saldos', stdout=out)
            output = out.getvalue()
            self.stdout.write(f"\n   Salida comando ver_saldos:")
            for line in output.strip().split('\n'):
                self.stdout.write(f"     {line}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error ejecutando ver_saldos: {e}"))