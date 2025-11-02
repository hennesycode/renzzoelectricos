#!/usr/bin/env python
"""
Script para crear TODAS las denominaciones correctas de Colombia.
Monedas: $50, $100, $500, $1,000
Billetes: $1,000, $2,000, $5,000, $10,000, $20,000, $50,000, $100,000
Renzzo Eléctricos - Villavicencio, Meta
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda

print("\n" + "=" * 70)
print("💵 CREAR DENOMINACIONES CORRECTAS - COLOMBIA")
print("=" * 70 + "\n")

# Definir denominaciones correctas
monedas = [
    {'valor': 50, 'orden': 12},
    {'valor': 100, 'orden': 11},
    {'valor': 500, 'orden': 9},
    {'valor': 1000, 'orden': 8},
]

billetes = [
    {'valor': 1000, 'orden': 7},
    {'valor': 2000, 'orden': 6},
    {'valor': 5000, 'orden': 5},
    {'valor': 10000, 'orden': 4},
    {'valor': 20000, 'orden': 3},
    {'valor': 50000, 'orden': 2},
    {'valor': 100000, 'orden': 1},
]

print("📋 Se crearán las siguientes denominaciones:\n")
print("🪙 MONEDAS (4):")
for m in monedas:
    print(f"   • ${m['valor']:>6,}")

print("\n💵 BILLETES (7):")
for b in billetes:
    print(f"   • ${b['valor']:>7,}")

print(f"\n   Total: {len(monedas) + len(billetes)} denominaciones\n")

# Confirmar
respuesta = input("¿Desea continuar con la creación? (escriba 'SI' para confirmar): ")

if respuesta.strip().upper() != 'SI':
    print("\n❌ Operación CANCELADA por el usuario")
    print("   No se creó ninguna denominación\n")
    print("=" * 70 + "\n")
    exit(0)

print()
print("💵 Creando denominaciones...\n")

creadas = 0
ya_existian = 0
errores = 0

# Crear MONEDAS
print("🪙 CREANDO MONEDAS:")
print("-" * 70)

for m in monedas:
    try:
        moneda, created = DenominacionMoneda.objects.get_or_create(
            valor=m['valor'],
            tipo='MONEDA',
            defaults={
                'activo': True,
                'orden': m['orden']
            }
        )
        
        if created:
            print(f"   ✅ CREADA: Moneda de ${moneda.valor:>6,} (ID: {moneda.id})")
            creadas += 1
        else:
            print(f"   ℹ️  Ya existe: Moneda de ${moneda.valor:>6,} (ID: {moneda.id})")
            ya_existian += 1
            
            # Actualizar si está inactiva
            if not moneda.activo:
                moneda.activo = True
                moneda.save()
                print(f"      ↪️  Activada")
                
    except Exception as e:
        print(f"   ❌ ERROR al crear moneda de ${m['valor']:,}: {e}")
        errores += 1

# Crear BILLETES
print("\n💵 CREANDO BILLETES:")
print("-" * 70)

for b in billetes:
    try:
        billete, created = DenominacionMoneda.objects.get_or_create(
            valor=b['valor'],
            tipo='BILLETE',
            defaults={
                'activo': True,
                'orden': b['orden']
            }
        )
        
        if created:
            print(f"   ✅ CREADO: Billete de ${billete.valor:>7,} (ID: {billete.id})")
            creadas += 1
        else:
            print(f"   ℹ️  Ya existe: Billete de ${billete.valor:>7,} (ID: {billete.id})")
            ya_existian += 1
            
            # Actualizar si está inactivo
            if not billete.activo:
                billete.activo = True
                billete.save()
                print(f"      ↪️  Activado")
                
    except Exception as e:
        print(f"   ❌ ERROR al crear billete de ${b['valor']:,}: {e}")
        errores += 1

print()
print("=" * 70)
print("📊 RESUMEN DE LA CREACIÓN")
print("=" * 70)
print(f"   ✅ Denominaciones creadas: {creadas}")
print(f"   ℹ️  Ya existían: {ya_existian}")
print(f"   ❌ Errores: {errores}")
print()

# Verificar totales
total_monedas = DenominacionMoneda.objects.filter(tipo='MONEDA', activo=True).count()
total_billetes = DenominacionMoneda.objects.filter(tipo='BILLETE', activo=True).count()
total = DenominacionMoneda.objects.filter(activo=True).count()

print("📊 ESTADO FINAL EN LA BASE DE DATOS:")
print("-" * 70)
print(f"   🪙 Monedas activas: {total_monedas}/4")
print(f"   💵 Billetes activos: {total_billetes}/7")
print(f"   ✅ Total denominaciones activas: {total}/11")

print()

if total_monedas == 4 and total_billetes == 7:
    print("✅ ¡PERFECTO! Todas las denominaciones están creadas correctamente")
    print()
    print("💡 Próximos pasos:")
    print("   1. Si está en producción, ejecute: python manage.py collectstatic --noinput")
    print("   2. Reinicie el servidor/contenedor")
    print("   3. Limpie caché del navegador (Ctrl+Shift+Delete)")
    print("   4. Acceda a: https://renzzoelectricos.com/admin/caja/denominacionmoneda/")
else:
    print("⚠️  ADVERTENCIA: No se completó correctamente")
    print(f"   Esperado: 4 monedas y 7 billetes")
    print(f"   Encontrado: {total_monedas} monedas y {total_billetes} billetes")
    print()
    print("   Ejecute: python validar_denominaciones.py")

print()
print("=" * 70)
print("✅ PROCESO COMPLETADO")
print("=" * 70 + "\n")
