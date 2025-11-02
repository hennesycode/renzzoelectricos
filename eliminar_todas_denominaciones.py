#!/usr/bin/env python
"""
Script para ELIMINAR TODAS las denominaciones de la base de datos.
⚠️  ADVERTENCIA: Esta operación es IRREVERSIBLE
Renzzo Eléctricos - Villavicencio, Meta
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda

print("\n" + "=" * 70)
print("🗑️  ELIMINAR TODAS LAS DENOMINACIONES")
print("=" * 70 + "\n")

# Contar cuántas hay
total = DenominacionMoneda.objects.count()

if total == 0:
    print("✅ No hay denominaciones en la base de datos")
    print("   La base de datos ya está limpia\n")
    print("=" * 70 + "\n")
    exit(0)

print(f"⚠️  Se encontraron {total} registros de denominaciones\n")

# Listar qué se va a eliminar
print("📋 Denominaciones que serán ELIMINADAS:")
print("-" * 70)
print(f"{'ID':<6} {'Tipo':<12} {'Valor':>15}")
print("-" * 70)

for d in DenominacionMoneda.objects.all().order_by('tipo', '-valor'):
    tipo_icon = '💵' if d.tipo == 'BILLETE' else '🪙'
    print(f"{d.id:<6} {tipo_icon} {d.tipo:<10} ${d.valor:>12,.0f}")

print()
print("⚠️  ADVERTENCIA:")
print("   Esta operación eliminará TODOS los registros de denominaciones")
print("   Esta acción es IRREVERSIBLE")
print("   Asegúrese de que no haya conteos de caja activos que dependan de estas denominaciones\n")

# Confirmar
respuesta = input("¿Está SEGURO que desea continuar? (escriba 'SI' para confirmar): ")

if respuesta.strip().upper() != 'SI':
    print("\n❌ Operación CANCELADA por el usuario")
    print("   No se eliminó ningún registro\n")
    print("=" * 70 + "\n")
    exit(0)

print()
print("🗑️  Eliminando todas las denominaciones...")

try:
    eliminados, detalles = DenominacionMoneda.objects.all().delete()
    print(f"✅ Eliminados {eliminados} registros correctamente")
    
    # Verificar que no quede nada
    restantes = DenominacionMoneda.objects.count()
    if restantes == 0:
        print("✅ Base de datos limpia - No quedan denominaciones")
    else:
        print(f"⚠️  Todavía quedan {restantes} registros (revisar manualmente)")
    
except Exception as e:
    print(f"❌ ERROR al eliminar: {e}")

print()
print("=" * 70)
print("✅ PROCESO COMPLETADO")
print("=" * 70 + "\n")
print("💡 Próximo paso:")
print("   Ejecute: python crear_denominaciones_correctas.py\n")
