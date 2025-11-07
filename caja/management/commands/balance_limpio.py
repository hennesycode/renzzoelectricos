"""
Comando para hacer un balance completo y limpio del sistema.
Resetea los saldos y los recalcula desde las transacciones reales.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from caja.models import (
    CajaRegistradora, MovimientoCaja, TransaccionGeneral, 
    Cuenta, TipoMovimiento
)


class Command(BaseCommand):
    help = 'Hace un balance completo y limpio del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aplicar',
            action='store_true',
            help='Aplicar realmente los cambios'
        )
        parser.add_argument(
            '--saldo-inicial-banco',
            type=float,
            default=0,
            help='Saldo inicial real del banco (default: 0)'
        )

    def handle(self, *args, **options):
        aplicar = options['aplicar']
        saldo_inicial_banco = Decimal(str(options['saldo_inicial_banco']))
        
        self.stdout.write(self.style.SUCCESS("🧹 BALANCE COMPLETO Y LIMPIO"))
        self.stdout.write("=" * 60)
        
        if not aplicar:
            self.stdout.write(self.style.WARNING("⚠️  MODO SIMULACIÓN - Para aplicar usa --aplicar"))
        
        # Obtener cuentas
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
        
        if not cuenta_banco or not cuenta_reserva:
            self.stdout.write(self.style.ERROR("❌ Faltan cuentas BANCO o RESERVA"))
            return
        
        self.stdout.write("\\n📊 ANÁLISIS DE MOVIMIENTOS REALES:")
        
        # 1. ANALIZAR ENTRADAS REALES AL BANCO (desde caja)
        entradas_banco_caja = MovimientoCaja.objects.filter(
            tipo='INGRESO',
            descripcion__icontains='[BANCO]'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
        
        self.stdout.write(f"💰 Entradas al banco desde caja: ${entradas_banco_caja:,.0f}")
        
        # 2. ANALIZAR TRANSACCIONES DIRECTAS DE BANCO
        transacciones_banco = TransaccionGeneral.objects.filter(cuenta=cuenta_banco)
        
        # Separar por origen
        desde_caja = transacciones_banco.filter(
            descripcion__icontains='[CAJA'
        )
        directas = transacciones_banco.exclude(
            descripcion__icontains='[CAJA'
        ).exclude(
            descripcion__icontains='Balance:'
        )
        balances = transacciones_banco.filter(
            descripcion__icontains='Balance:'
        )
        
        # Calcular totales
        ingresos_caja = desde_caja.filter(tipo='INGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        egresos_caja = desde_caja.filter(tipo='EGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        
        ingresos_directos = directas.filter(tipo='INGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        egresos_directos = directas.filter(tipo='EGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        
        ingresos_balance = balances.filter(tipo='INGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        egresos_balance = balances.filter(tipo='EGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        
        self.stdout.write(f"\n🏦 TRANSACCIONES EN BANCO:")
        self.stdout.write(f"   Desde caja: +${ingresos_caja:,.0f} -${egresos_caja:,.0f}")
        self.stdout.write(f"   Directas: +${ingresos_directos:,.0f} -${egresos_directos:,.0f}")
        self.stdout.write(f"   Balances: +${ingresos_balance:,.0f} -${egresos_balance:,.0f}")
        
        # 3. CALCULAR SALDO REAL DEL BANCO
        saldo_banco_real = (saldo_inicial_banco + 
                           ingresos_caja - egresos_caja +
                           ingresos_directos - egresos_directos)
        # NO incluir los balances porque esos fueron ajustes manuales posiblemente incorrectos
        
        self.stdout.write(f"\n💵 CÁLCULO SALDO BANCO:")
        self.stdout.write(f"   Saldo inicial: ${saldo_inicial_banco:,.0f}")
        self.stdout.write(f"   + Entradas caja: ${ingresos_caja:,.0f}")
        self.stdout.write(f"   - Gastos caja: ${egresos_caja:,.0f}")
        self.stdout.write(f"   + Ingresos directos: ${ingresos_directos:,.0f}")
        self.stdout.write(f"   - Gastos directos: ${egresos_directos:,.0f}")
        self.stdout.write(f"   = SALDO REAL: ${saldo_banco_real:,.0f}")
        
        # 4. ANALIZAR DINERO GUARDADO
        cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
        dinero_cajas = sum(c.dinero_en_caja or Decimal('0.00') for c in cajas_cerradas)
        
        # Transacciones directas en reserva (excluyendo balances y tracking de caja)
        transacciones_reserva = TransaccionGeneral.objects.filter(cuenta=cuenta_reserva)
        
        directas_reserva = transacciones_reserva.exclude(
            descripcion__icontains='[CAJA'
        ).exclude(
            descripcion__icontains='Balance:'
        )
        
        ingresos_reserva_directos = directas_reserva.filter(tipo='INGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        egresos_reserva_directos = directas_reserva.filter(tipo='EGRESO').aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
        
        dinero_guardado_real = dinero_cajas + ingresos_reserva_directos - egresos_reserva_directos
        
        self.stdout.write(f"\n💰 CÁLCULO DINERO GUARDADO:")
        self.stdout.write(f"   Dinero en cajas cerradas: ${dinero_cajas:,.0f}")
        self.stdout.write(f"   + Ingresos directos a reserva: ${ingresos_reserva_directos:,.0f}")
        self.stdout.write(f"   - Gastos directos de reserva: ${egresos_reserva_directos:,.0f}")
        self.stdout.write(f"   = DINERO GUARDADO REAL: ${dinero_guardado_real:,.0f}")
        
        # 5. PROPONER CORRECCIÓN
        saldo_banco_actual = cuenta_banco.saldo_actual
        diferencia_banco = saldo_banco_real - saldo_banco_actual
        
        self.stdout.write(f"\n🔧 CORRECCIONES NECESARIAS:")
        self.stdout.write(f"   Banco actual: ${saldo_banco_actual:,.0f}")
        self.stdout.write(f"   Banco correcto: ${saldo_banco_real:,.0f}")
        self.stdout.write(f"   Diferencia: {diferencia_banco:+,.0f}")
        
        if aplicar and diferencia_banco != 0:
            # Aplicar corrección
            cuenta_banco.saldo_actual = saldo_banco_real
            cuenta_banco.save()
            
            # Crear transacción de ajuste
            tipo_balance, _ = TipoMovimiento.objects.get_or_create(
                codigo='BALANCE_LIMPIO',
                defaults={
                    'nombre': 'Balance Limpio Sistema',
                    'descripcion': 'Ajuste por balance completo',
                    'tipo_base': 'INTERNO',
                    'activo': True
                }
            )
            
            if diferencia_banco > 0:
                tipo_trans = 'INGRESO'
                desc = f"Balance limpio: Ajuste positivo (${saldo_banco_actual:,.0f} → ${saldo_banco_real:,.0f})"
            else:
                tipo_trans = 'EGRESO'
                desc = f"Balance limpio: Ajuste negativo (${saldo_banco_actual:,.0f} → ${saldo_banco_real:,.0f})"
            
            TransaccionGeneral.objects.create(
                tipo=tipo_trans,
                monto=abs(diferencia_banco),
                descripcion=desc,
                referencia=f"Balance-Limpio-{timezone.now().strftime('%Y%m%d')}",
                tipo_movimiento=tipo_balance,
                cuenta=cuenta_banco,
                usuario_id=1  # Asumiendo admin
            )
            
            if diferencia_banco > 0:
                self.stdout.write(self.style.SUCCESS(f"   ✅ BANCO CORREGIDO: +${diferencia_banco:,.0f}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"   ✅ BANCO CORREGIDO: ${diferencia_banco:,.0f}"))
        
        # 6. MOSTRAR TOTALES FINALES
        if aplicar:
            total_final = saldo_banco_real + dinero_guardado_real
        else:
            total_final = saldo_banco_real + dinero_guardado_real
        
        # Agregar dinero en caja abierta
        caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').first()
        if caja_abierta:
            dinero_caja_abierta = caja_abierta.calcular_monto_sistema()
            total_final += dinero_caja_abierta
        else:
            dinero_caja_abierta = Decimal('0.00')
        
        self.stdout.write(f"\n💎 TOTALES FINALES:")
        self.stdout.write(f"   Dinero en Caja: ${dinero_caja_abierta:,.0f}")
        self.stdout.write(f"   Banco Principal: ${saldo_banco_real:,.0f}")
        self.stdout.write(f"   Dinero Guardado: ${dinero_guardado_real:,.0f}")
        self.stdout.write(f"   TOTAL DISPONIBLE: ${total_final:,.0f}")
        
        self.stdout.write("\n" + "=" * 60)
        if aplicar:
            self.stdout.write(self.style.SUCCESS("✅ BALANCE LIMPIO COMPLETADO"))
        else:
            self.stdout.write(self.style.WARNING("💡 Para aplicar: --aplicar --saldo-inicial-banco=MONTO_REAL"))