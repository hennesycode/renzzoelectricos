#!/usr/bin/env python
"""
Script para validar el estado actual de las denominaciones en la base de datos.
Renzzo Eléctricos - Villavicencio, Meta
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda
from django.db.models import Count

print("\n" + "=" * 70)
print("🔍 VALIDACIÓN DE DENOMINACIONES - RENZZO ELÉCTRICOS")
print("=" * 70 + "\n")

# Contar total
total = DenominacionMoneda.objects.count()
print(f"📊 Total de registros en la base de datos: {total}\n")

if total == 0:
    print("❌ No hay denominaciones en la base de datos")
    print("   Ejecute: python crear_denominaciones_correctas.py\n")
    print("=" * 70 + "\n")
    exit(0)

# Listar todas
print("📋 LISTADO COMPLETO DE DENOMINACIONES:")
print("-" * 70)
print(f"{'ID':<6} {'Tipo':<12} {'Valor':>15} {'Activo':<10} {'Orden':<6}")
print("-" * 70)

for d in DenominacionMoneda.objects.all().order_by('tipo', '-valor'):
    tipo_icon = '💵' if d.tipo == 'BILLETE' else '🪙'
    activo_str = '✓ Sí' if d.activo else '✗ No'
    print(f"{d.id:<6} {tipo_icon} {d.tipo:<10} ${d.valor:>12,.0f} {activo_str:<10} {d.orden:<6}")

print()

# Verificar duplicados
print("🔍 VERIFICACIÓN DE DUPLICADOS:")
print("-" * 70)

duplicados = DenominacionMoneda.objects.values('valor', 'tipo').annotate(
    count=Count('id')
).filter(count__gt=1)

if duplicados:
    print(f"⚠️  ENCONTRADOS {len(duplicados)} grupos duplicados:\n")
    for dup in duplicados:
        print(f"   • {dup['tipo']} ${dup['valor']:,.0f} → {dup['count']} registros")
        # Mostrar IDs
        registros = DenominacionMoneda.objects.filter(
            valor=dup['valor'], 
            tipo=dup['tipo']
        ).values_list('id', flat=True)
        print(f"     IDs: {list(registros)}")
    print()
    print("⚠️  ACCIÓN REQUERIDA: Ejecute python eliminar_todas_denominaciones.py")
else:
    print("✅ No hay duplicados\n")

# Verificar denominaciones esperadas
print("✅ DENOMINACIONES ESPERADAS:")
print("-" * 70)

monedas_esperadas = [50, 100, 500, 1000]
billetes_esperados = [1000, 2000, 5000, 10000, 20000, 50000, 100000]

print("🪙 MONEDAS:")
for valor in monedas_esperadas:
    existe = DenominacionMoneda.objects.filter(valor=valor, tipo='MONEDA', activo=True).exists()
    status = "✅" if existe else "❌"
    print(f"   {status} ${valor:>6,}")

print("\n💵 BILLETES:")
for valor in billetes_esperados:
    existe = DenominacionMoneda.objects.filter(valor=valor, tipo='BILLETE', activo=True).exists()
    status = "✅" if existe else "❌"
    print(f"   {status} ${valor:>7,}")

print()

# Resumen
monedas_correctas = sum(1 for v in monedas_esperadas if DenominacionMoneda.objects.filter(valor=v, tipo='MONEDA', activo=True).exists())
billetes_correctos = sum(1 for v in billetes_esperados if DenominacionMoneda.objects.filter(valor=v, tipo='BILLETE', activo=True).exists())

print("📊 RESUMEN:")
print("-" * 70)
print(f"   Monedas correctas: {monedas_correctas}/4")
print(f"   Billetes correctos: {billetes_correctos}/7")
print(f"   Total esperado: 11 denominaciones")
print(f"   Total actual: {total} registros")

if monedas_correctas == 4 and billetes_correctos == 7 and total == 11:
    print("\n✅ ¡PERFECTO! Todas las denominaciones están correctas")
else:
    print("\n⚠️  ACCIÓN REQUERIDA:")
    print("   1. Ejecute: python eliminar_todas_denominaciones.py")
    print("   2. Ejecute: python crear_denominaciones_correctas.py")

print("\n" + "=" * 70 + "\n")
