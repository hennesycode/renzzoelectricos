#!/usr/bin/env python
"""Script para eliminar movimientos duplicados de apertura"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import CajaRegistradora, MovimientoCaja, TipoMovimiento
from django.db import transaction

print("\n" + "="*60)
print("LIMPIANDO MOVIMIENTOS DUPLICADOS DE APERTURA")
print("="*60 + "\n")

try:
    # Buscar tipo de movimiento APERTURA
    tipo_apertura = TipoMovimiento.objects.filter(codigo='APERTURA').first()
    
    if not tipo_apertura:
        print("✅ No hay tipo de movimiento 'APERTURA'. No hay nada que limpiar.")
    else:
        # Buscar todos los movimientos de apertura
        movimientos_apertura = MovimientoCaja.objects.filter(
            tipo_movimiento=tipo_apertura,
            tipo='INGRESO'
        )
        
        count = movimientos_apertura.count()
        
        if count == 0:
            print("✅ No hay movimientos de apertura duplicados.")
        else:
            print(f"⚠️  Encontrados {count} movimiento(s) de apertura duplicado(s):")
            
            with transaction.atomic():
                for mov in movimientos_apertura:
                    print(f"   - Caja #{mov.caja.id}: ${mov.monto:,.0f}")
                    mov.delete()
            
            print(f"\n✅ Se eliminaron {count} movimiento(s) duplicado(s)")
            
            # Recalcular monto_final_sistema para cajas cerradas
            print("\n" + "="*60)
            print("RECALCULANDO CAJAS CERRADAS")
            print("="*60 + "\n")
            
            cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA')
            
            for caja in cajas_cerradas:
                # Saltar cajas que no tienen monto_final_declarado
                if caja.monto_final_declarado is None:
                    print(f"Caja #{caja.id}: ⚠️  Sin monto_final_declarado, se omite")
                    continue
                    
                monto_sistema_viejo = caja.monto_final_sistema
                monto_sistema_nuevo = caja.calcular_monto_sistema()
                diferencia_vieja = caja.diferencia
                diferencia_nueva = caja.monto_final_declarado - monto_sistema_nuevo
                
                print(f"Caja #{caja.id}:")
                print(f"  Monto Sistema: ${monto_sistema_viejo:,.0f} → ${monto_sistema_nuevo:,.0f}")
                print(f"  Diferencia: ${diferencia_vieja:,.0f} → ${diferencia_nueva:,.0f}")
                
                caja.monto_final_sistema = monto_sistema_nuevo
                caja.diferencia = diferencia_nueva
                caja.save(update_fields=['monto_final_sistema', 'diferencia'])
                
            print(f"\n✅ Se recalcularon {cajas_cerradas.count()} caja(s) cerrada(s)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("PROCESO COMPLETADO")
print("="*60 + "\n")
