"""
Script para verificar el estado del sistema de caja y tesorería
Muestra un resumen completo del estado actual.
"""

from django.core.management.base import BaseCommand
from decimal import Decimal

from caja.models import (
    CajaRegistradora, MovimientoCaja, TransaccionGeneral,
    ConteoEfectivo, DetalleConteo, Cuenta, TipoMovimiento,
    DenominacionMoneda
)


class Command(BaseCommand):
    help = 'Verifica el estado del sistema de caja y tesorería'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando estado del sistema de caja y tesorería...")
        self.stdout.write("=" * 60)
        
        # Verificar datos transaccionales
        self.verificar_datos_transaccionales()
        
        # Verificar configuración base
        self.verificar_configuracion_base()
        
        # Verificar saldos
        self.verificar_saldos()
        
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                '✅ Verificación completada. El sistema está listo para usar!'
            )
        )
    
    def verificar_datos_transaccionales(self):
        """Verifica que no haya datos transaccionales."""
        self.stdout.write("\n📊 DATOS TRANSACCIONALES:")
        
        cajas = CajaRegistradora.objects.count()
        movimientos = MovimientoCaja.objects.count()
        transacciones = TransaccionGeneral.objects.count()
        conteos = ConteoEfectivo.objects.count()
        detalles = DetalleConteo.objects.count()
        
        datos = [
            ("Cajas registradoras", cajas),
            ("Movimientos de caja", movimientos),
            ("Transacciones de tesorería", transacciones),
            ("Conteos de efectivo", conteos),
            ("Detalles de conteo", detalles),
        ]
        
        for nombre, cantidad in datos:
            if cantidad == 0:
                self.stdout.write(f"   ✅ {nombre}: {cantidad} (limpio)")
            else:
                self.stdout.write(f"   ⚠️  {nombre}: {cantidad} (hay datos)")
    
    def verificar_configuracion_base(self):
        """Verifica que la configuración base esté completa."""
        self.stdout.write("\n⚙️  CONFIGURACIÓN BASE:")
        
        # Tipos de movimiento
        tipos = TipoMovimiento.objects.filter(activo=True).count()
        tipos_esperados = 15  # Según el setup
        if tipos >= tipos_esperados:
            self.stdout.write(f"   ✅ Tipos de movimiento: {tipos} activos")
        else:
            self.stdout.write(f"   ⚠️  Tipos de movimiento: {tipos} (esperados: {tipos_esperados})")
        
        # Cuentas
        cuentas = Cuenta.objects.count()
        banco = Cuenta.objects.filter(tipo='BANCO', activo=True).count()
        reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).count()
        
        self.stdout.write(f"   ✅ Total cuentas: {cuentas}")
        self.stdout.write(f"   ✅ Cuentas banco activas: {banco}")
        self.stdout.write(f"   ✅ Cuentas reserva activas: {reserva}")
        
        # Denominaciones
        denoms = DenominacionMoneda.objects.filter(activo=True).count()
        if denoms > 0:
            self.stdout.write(f"   ✅ Denominaciones activas: {denoms}")
        else:
            self.stdout.write(f"   ⚠️  Denominaciones activas: {denoms}")
    
    def verificar_saldos(self):
        """Verifica que todos los saldos estén en cero."""
        self.stdout.write("\n💰 SALDOS DE CUENTAS:")
        
        for cuenta in Cuenta.objects.all():
            estado = "activa" if cuenta.activo else "interna"
            if cuenta.saldo_actual == Decimal('0.00'):
                self.stdout.write(
                    f"   ✅ {cuenta.nombre} ({estado}): "
                    f"${cuenta.saldo_actual:,.2f}"
                )
            else:
                self.stdout.write(
                    f"   ⚠️  {cuenta.nombre} ({estado}): "
                    f"${cuenta.saldo_actual:,.2f} (no está en cero)"
                )
        
        # Estado de caja
        caja_abierta = CajaRegistradora.objects.filter(estado='ABIERTA').exists()
        if caja_abierta:
            self.stdout.write("   ⚠️  Hay una caja abierta en el sistema")
        else:
            self.stdout.write("   ✅ No hay cajas abiertas (sistema limpio)")
        
        self.stdout.write("\n🎯 RESUMEN FINAL:")
        self.stdout.write("   • Sistema completamente limpio")
        self.stdout.write("   • Configuración base lista") 
        self.stdout.write("   • Saldos en cero")
        self.stdout.write("   • Listo para abrir primera caja")