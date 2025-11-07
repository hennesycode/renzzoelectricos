"""
Script para analizar el estado actual de la cuenta reserva
"""
from caja.models import Cuenta, TransaccionGeneral, CajaRegistradora
from django.db.models import Sum
from decimal import Decimal

print('=== ANÁLISIS DE BASE DE DATOS ===')
print()

# Verificar cuenta reserva
cuenta_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).first()
if cuenta_reserva:
    print(f'Cuenta Reserva: {cuenta_reserva.nombre}')
    print(f'Saldo actual en BD: ${cuenta_reserva.saldo_actual:,.2f}')
    print(f'ID de cuenta: {cuenta_reserva.id}')
else:
    print('❌ No hay cuenta reserva activa')

print()

# Verificar transacciones de balance
transacciones_balance = TransaccionGeneral.objects.filter(
    descripcion__icontains='Balance:'
).order_by('-fecha')[:5]

print(f'Últimas {len(transacciones_balance)} transacciones de balance:')
for t in transacciones_balance:
    fecha_str = t.fecha.strftime('%d/%m/%Y %H:%M')
    print(f'- {fecha_str} | {t.tipo} | ${t.monto:,.0f} | {t.descripcion[:50]}...')

print()

# Verificar dinero guardado en cajas cerradas
total_cajas = CajaRegistradora.objects.filter(
    estado='CERRADA',
    dinero_guardado__gt=0
).aggregate(total=Sum('dinero_guardado'))['total'] or Decimal('0.00')

print(f'Total dinero guardado en cajas cerradas: ${total_cajas:,.2f}')

print()

# Verificar transacciones en cuenta reserva
if cuenta_reserva:
    ingresos = TransaccionGeneral.objects.filter(
        cuenta=cuenta_reserva,
        tipo='INGRESO'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    egresos = TransaccionGeneral.objects.filter(
        cuenta=cuenta_reserva,
        tipo='EGRESO'
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    
    print(f'Ingresos en cuenta reserva: ${ingresos:,.2f}')
    print(f'Egresos en cuenta reserva: ${egresos:,.2f}')
    print(f'Balance neto: ${ingresos - egresos:,.2f}')

print()
print('=== RECOMENDACIÓN ===')
if cuenta_reserva:
    saldo_correcto = Decimal('100000.00')  # El balance que se hizo
    if cuenta_reserva.saldo_actual != saldo_correcto:
        print(f'❌ El saldo debe ser ${saldo_correcto:,.2f} pero está en ${cuenta_reserva.saldo_actual:,.2f}')
        print('Ejecutar: cuenta_reserva.saldo_actual = Decimal("100000.00"); cuenta_reserva.save()')
    else:
        print('✅ El saldo está correcto')