#!/usr/bin/env python
"""Script para revisar la última caja cerrada"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import CajaRegistradora, MovimientoCaja
from decimal import Decimal

# Obtener última caja
caja = CajaRegistradora.objects.order_by('-id').first()

print("\n" + "="*60)
print(f"ÚLTIMA CAJA - ID: {caja.id}")
print("="*60)
print(f"Estado: {caja.estado}")
print(f"Cajero: {caja.cajero}")
print(f"Apertura: {caja.fecha_apertura}")
print(f"Cierre: {caja.fecha_cierre}")

print(f"\n{'APERTURA':=^60}")
print(f"Monto Inicial: ${caja.monto_inicial:,.0f}")

print(f"\n{'MOVIMIENTOS':=^60}")
movimientos = caja.movimientos.all().order_by('fecha_movimiento')
total_ingresos = Decimal('0')
total_egresos = Decimal('0')

for i, mov in enumerate(movimientos, 1):
    tipo_nombre = mov.tipo_movimiento.nombre if mov.tipo_movimiento else "Sin tipo"
    print(f"{i}. [{mov.tipo}] ${mov.monto:,.0f} - {tipo_nombre}")
    if mov.tipo == 'INGRESO':
        total_ingresos += mov.monto
    else:
        total_egresos += mov.monto

print(f"\nTotal Ingresos: ${total_ingresos:,.0f}")
print(f"Total Egresos: ${total_egresos:,.0f}")

print(f"\n{'CIERRE':=^60}")
print(f"Monto Final Sistema (esperado): ${caja.monto_final_sistema:,.0f}")
print(f"Monto Final Declarado (contado): ${caja.monto_final_declarado:,.0f}")
print(f"Diferencia: ${caja.diferencia:,.0f}")

print(f"\n{'VERIFICACIÓN CÁLCULO':=^60}")
calculo_esperado = caja.monto_inicial + total_ingresos - total_egresos
print(f"Monto Inicial:     ${caja.monto_inicial:>12,.0f}")
print(f"+ Ingresos:        ${total_ingresos:>12,.0f}")
print(f"- Egresos:         ${total_egresos:>12,.0f}")
print(f"{'-'*40}")
print(f"= Debería haber:   ${calculo_esperado:>12,.0f}")
print(f"Sistema guardó:    ${caja.monto_final_sistema:>12,.0f}")

if calculo_esperado == caja.monto_final_sistema:
    print(f"\n✅ El cálculo del sistema es CORRECTO")
else:
    print(f"\n❌ ERROR: El sistema guardó ${caja.monto_final_sistema:,.0f} pero debería ser ${calculo_esperado:,.0f}")

print(f"\n{'DIFERENCIA':=^60}")
print(f"Esperado:  ${caja.monto_final_sistema:,.0f}")
print(f"Contado:   ${caja.monto_final_declarado:,.0f}")
print(f"{'-'*40}")
dif_real = caja.monto_final_declarado - caja.monto_final_sistema
if dif_real > 0:
    print(f"Sobrante:  ${dif_real:,.0f}")
elif dif_real < 0:
    print(f"Faltante:  ${abs(dif_real):,.0f}")
else:
    print(f"Cuadre perfecto: $0")

print("\n" + "="*60 + "\n")
