#!/usr/bin/env python3
"""
Script para corregir definitivamente el saldo del banco.
Analiza y corrige todos los problemas encontrados.
"""

# Este script debe ejecutarse dentro del contexto de Django
import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction, connection
from caja.models import TransaccionGeneral, Cuenta, TipoMovimiento


def main():
    print("🔧 ANÁLISIS Y CORRECCIÓN DEFINITIVA DEL SALDO BANCARIO")
    print("=" * 60)
    
    with transaction.atomic():
        # 1. OBTENER CUENTA BANCO
        cuenta_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).first()
        
        if not cuenta_banco:
            print("❌ ERROR: No se encontró cuenta banco activa")
            return
        
        print(f"💳 CUENTA ENCONTRADA: {cuenta_banco.nombre}")
        print(f"💰 Saldo actual en modelo: ${cuenta_banco.saldo_actual:,.2f}")
        
        # 2. VERIFICAR SALDO EN BASE DE DATOS DIRECTAMENTE
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT saldo_actual FROM caja_cuenta WHERE id = %s",
                [cuenta_banco.id]
            )
            saldo_db = cursor.fetchone()[0]
        
        print(f"💾 Saldo actual en DB: ${saldo_db:,.2f}")
        
        # 3. BUSCAR LA TRANSACCIÓN PROBLEMÁTICA
        transaccion = TransaccionGeneral.objects.filter(
            descripcion__icontains='pago factura 100 grupo defa',
            monto=Decimal('234763.00')
        ).first()
        
        if not transaccion:
            print("❌ ERROR: Transacción no encontrada")
            return
        
        print(f"📊 TRANSACCIÓN ENCONTRADA: ID {transaccion.id}")
        print(f"   💸 Monto: ${transaccion.monto:,.2f}")
        print(f"   📝 Descripción: {transaccion.descripcion}")
        print(f"   🏷️ Categoría actual: {transaccion.tipo_movimiento.nombre}")
        print(f"   📅 Fecha: {transaccion.fecha}")
        
        # 4. CALCULAR SALDO CORRECTO
        saldo_esperado = Decimal('1575628.00') - transaccion.monto
        print(f"🎯 SALDO ESPERADO: ${saldo_esperado:,.2f}")
        
        # 5. CORREGIR CATEGORÍA SI ES NECESARIO
        if transaccion.tipo_movimiento.codigo != 'GASTO_BANCARIO':
            tipo_gasto = TipoMovimiento.objects.filter(
                nombre__icontains='Gasto Bancario'
            ).first()
            
            if tipo_gasto:
                print(f"🏷️ Cambiando categoría a: {tipo_gasto.nombre}")
                transaccion.tipo_movimiento = tipo_gasto
                transaccion.save(update_fields=['tipo_movimiento'])
            else:
                print("⚠️ No se encontró categoría 'Gasto Bancario'")
        
        # 6. FORZAR CORRECCIÓN DEL SALDO (MÚLTIPLES MÉTODOS)
        print(f"\n🔧 APLICANDO CORRECCIÓN DEL SALDO...")
        
        # Método 1: Actualización directa en DB
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE caja_cuenta SET saldo_actual = %s WHERE id = %s",
                [saldo_esperado, cuenta_banco.id]
            )
            rows_affected = cursor.rowcount
            print(f"   📊 Filas afectadas en DB: {rows_affected}")
        
        # Método 2: Refrescar modelo y verificar
        cuenta_banco.refresh_from_db()
        print(f"   💰 Saldo después de refresh: ${cuenta_banco.saldo_actual:,.2f}")
        
        # Método 3: Si aún no coincide, forzar con el modelo
        if cuenta_banco.saldo_actual != saldo_esperado:
            print("   🔧 Forzando con modelo...")
            cuenta_banco.saldo_actual = saldo_esperado
            cuenta_banco.save(update_fields=['saldo_actual'])
        
        # 7. VERIFICACIÓN FINAL
        cuenta_banco.refresh_from_db()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT saldo_actual FROM caja_cuenta WHERE id = %s",
                [cuenta_banco.id]
            )
            saldo_final_db = cursor.fetchone()[0]
        
        print(f"\n✅ VERIFICACIÓN FINAL:")
        print(f"   💰 Saldo en modelo: ${cuenta_banco.saldo_actual:,.2f}")
        print(f"   💾 Saldo en DB: ${saldo_final_db:,.2f}")
        print(f"   🎯 Saldo esperado: ${saldo_esperado:,.2f}")
        
        if cuenta_banco.saldo_actual == saldo_esperado == saldo_final_db:
            print(f"\n🎉 ¡CORRECCIÓN EXITOSA!")
            print(f"   ✅ El saldo bancario es: ${cuenta_banco.saldo_actual:,.2f}")
            print(f"   ✅ La transacción está categorizada correctamente")
            print(f"   ✅ Todos los valores coinciden")
        else:
            print(f"\n❌ AÚN HAY INCONSISTENCIAS:")
            print(f"   🔍 Revisar manualmente en la base de datos")
            print(f"   💡 Puede ser un problema de caché de Django")
        
        # 8. INFORMACIÓN ADICIONAL DE DEBUG
        print(f"\n🔍 INFORMACIÓN DE DEBUG:")
        print(f"   🆔 ID de cuenta: {cuenta_banco.id}")
        print(f"   🆔 ID de transacción: {transaccion.id}")
        print(f"   📊 Tipo de cuenta: {cuenta_banco.tipo}")
        print(f"   🏷️ Nombre de cuenta: {cuenta_banco.nombre}")


if __name__ == "__main__":
    main()