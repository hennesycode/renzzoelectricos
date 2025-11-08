#!/usr/bin/env python
"""
Script para limpiar completamente el sistema de cajas y movimientos.
CUIDADO: Este script eliminará TODOS los datos de cajas registradoras y movimientos.
Solo usar cuando se necesite resetear completamente el sistema.

Renzzo Eléctricos - Villavicencio, Meta
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.db import transaction
from caja.models import (
    CajaRegistradora, 
    MovimientoCaja, 
    TransaccionGeneral,
    TipoMovimiento,
    DenominacionMoneda,
    Cuenta
)

def confirmar_limpieza():
    """Solicita confirmación antes de proceder con la limpieza."""
    print("🚨 ADVERTENCIA: LIMPIEZA COMPLETA DEL SISTEMA 🚨")
    print("=" * 60)
    print("Este script eliminará PERMANENTEMENTE:")
    print("• Todas las cajas registradoras")
    print("• Todos los movimientos de caja")
    print("• Todas las transacciones generales")
    print("• Mantendrá tipos de movimiento y denominaciones")
    print("• Mantendrá cuentas de tesorería (solo reseteará saldos)")
    print("=" * 60)
    
    respuesta = input("¿Estás SEGURO de continuar? Escribe 'ELIMINAR TODO' para confirmar: ")
    return respuesta == 'ELIMINAR TODO'

def obtener_estadisticas_antes():
    """Obtiene estadísticas antes de la limpieza."""
    stats = {
        'cajas': CajaRegistradora.objects.count(),
        'movimientos': MovimientoCaja.objects.count(),
        'transacciones': TransaccionGeneral.objects.count(),
        'tipos_movimiento': TipoMovimiento.objects.count(),
        'denominaciones': DenominacionMoneda.objects.count(),
        'cuentas': Cuenta.objects.count()
    }
    return stats

def mostrar_estadisticas(titulo, stats):
    """Muestra estadísticas formateadas."""
    print(f"\n{titulo}")
    print("-" * 40)
    print(f"📦 Cajas Registradoras: {stats['cajas']}")
    print(f"💰 Movimientos de Caja: {stats['movimientos']}")
    print(f"📊 Transacciones Generales: {stats['transacciones']}")
    print(f"🏷️ Tipos de Movimiento: {stats['tipos_movimiento']}")
    print(f"💵 Denominaciones: {stats['denominaciones']}")
    print(f"🏦 Cuentas de Tesorería: {stats['cuentas']}")

def limpiar_sistema():
    """Limpia completamente el sistema de cajas y movimientos."""
    try:
        with transaction.atomic():
            print("\n🧹 Iniciando limpieza del sistema...")
            
            # 1. Eliminar todas las transacciones generales
            print("1. Eliminando transacciones generales...")
            transacciones_eliminadas = TransaccionGeneral.objects.count()
            TransaccionGeneral.objects.all().delete()
            print(f"   ✅ {transacciones_eliminadas} transacciones eliminadas")
            
            # 2. Eliminar todos los movimientos de caja
            print("2. Eliminando movimientos de caja...")
            movimientos_eliminados = MovimientoCaja.objects.count()
            MovimientoCaja.objects.all().delete()
            print(f"   ✅ {movimientos_eliminados} movimientos eliminados")
            
            # 3. Eliminar todas las cajas registradoras
            print("3. Eliminando cajas registradoras...")
            cajas_eliminadas = CajaRegistradora.objects.count()
            CajaRegistradora.objects.all().delete()
            print(f"   ✅ {cajas_eliminadas} cajas eliminadas")
            
            # 4. Resetear saldos de cuentas de tesorería a cero
            print("4. Reseteando saldos de cuentas de tesorería...")
            cuentas_actualizadas = 0
            for cuenta in Cuenta.objects.all():
                saldo_anterior = cuenta.saldo_actual or Decimal('0.00')
                cuenta.saldo_actual = Decimal('0.00')
                cuenta.save()
                if saldo_anterior != Decimal('0.00'):
                    print(f"   📊 {cuenta.nombre}: ${saldo_anterior:,.2f} → $0.00")
                    cuentas_actualizadas += 1
            print(f"   ✅ {cuentas_actualizadas} cuentas reseteadas")
            
            print("\n🎉 LIMPIEZA COMPLETADA EXITOSAMENTE")
            print("Sistema completamente limpio y listo para usar")
            
    except Exception as e:
        print(f"\n❌ ERROR durante la limpieza: {str(e)}")
        raise

def verificar_limpieza():
    """Verifica que la limpieza se realizó correctamente."""
    print("\n🔍 Verificando limpieza...")
    
    # Verificar que no hay datos
    cajas_restantes = CajaRegistradora.objects.count()
    movimientos_restantes = MovimientoCaja.objects.count()
    transacciones_restantes = TransaccionGeneral.objects.count()
    
    if cajas_restantes == 0 and movimientos_restantes == 0 and transacciones_restantes == 0:
        print("✅ Verificación exitosa: Sistema completamente limpio")
        
        # Mostrar cuentas con saldo cero
        print("\n🏦 Estado de cuentas de tesorería:")
        for cuenta in Cuenta.objects.all():
            print(f"   {cuenta.nombre}: ${cuenta.saldo_actual or Decimal('0.00'):,.2f}")
        
        return True
    else:
        print("❌ Verificación falló: Aún hay datos en el sistema")
        print(f"   Cajas restantes: {cajas_restantes}")
        print(f"   Movimientos restantes: {movimientos_restantes}")
        print(f"   Transacciones restantes: {transacciones_restantes}")
        return False

def main():
    """Función principal del script."""
    print("🧹 SCRIPT DE LIMPIEZA COMPLETA DEL SISTEMA")
    print("Renzzo Eléctricos - Sistema de Caja Registradora")
    print("=" * 60)
    
    # Mostrar estadísticas antes
    stats_antes = obtener_estadisticas_antes()
    mostrar_estadisticas("📊 ESTADÍSTICAS ANTES DE LA LIMPIEZA", stats_antes)
    
    # Confirmar limpieza
    if not confirmar_limpieza():
        print("\n❌ Operación cancelada por el usuario")
        return
    
    print("\n⏳ Procediendo con la limpieza...")
    
    try:
        # Realizar limpieza
        limpiar_sistema()
        
        # Mostrar estadísticas después
        stats_despues = obtener_estadisticas_antes()
        mostrar_estadisticas("📊 ESTADÍSTICAS DESPUÉS DE LA LIMPIEZA", stats_despues)
        
        # Verificar limpieza
        if verificar_limpieza():
            print("\n🎯 MISIÓN CUMPLIDA")
            print("El sistema está completamente limpio y listo para empezar de nuevo")
            print("\n📋 Lo que se mantiene:")
            print("• Tipos de movimiento (para crear nuevas transacciones)")
            print("• Denominaciones de billetes y monedas")
            print("• Cuentas de tesorería (con saldo $0.00)")
            print("• Configuración del sistema")
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO: {str(e)}")
        print("La limpieza no se completó correctamente")
        return 1
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)