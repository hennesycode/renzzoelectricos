#!/usr/bin/env python
"""
Script para limpiar denominaciones duplicadas y dejar solo una de cada combinación (valor, tipo).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda
from django.db.models import Count, Min

print("=" * 70)
print("🧹 LIMPIEZA DE DENOMINACIONES DUPLICADAS")
print("=" * 70)
print()

# 1. Encontrar combinaciones duplicadas
print("🔍 [1/3] Buscando combinaciones duplicadas (valor + tipo)...")
duplicados = DenominacionMoneda.objects.values('valor', 'tipo').annotate(
    count=Count('id'),
    primer_id=Min('id')
).filter(count__gt=1)

if not duplicados:
    print("   ✅ No hay duplicados. La base de datos está limpia.")
    print()
    print("=" * 70)
    exit(0)

print(f"   ⚠️  Encontrados {len(duplicados)} grupos de duplicados:")
print()

total_a_eliminar = 0
for dup in duplicados:
    valor = dup['valor']
    tipo = dup['tipo']
    count = dup['count']
    primer_id = dup['primer_id']
    
    print(f"   • {tipo} de ${valor:,.0f}: {count} registros (mantendremos ID {primer_id})")
    
    # Contar cuántos eliminaremos
    total_a_eliminar += (count - 1)

print()
print(f"   📊 Total de registros a eliminar: {total_a_eliminar}")
print()

# 2. Confirmar eliminación
print("⚠️  [2/3] Confirmación de eliminación...")
print()
print("   Se mantendrá el registro MÁS ANTIGUO (menor ID) de cada grupo.")
print("   Los demás duplicados se eliminarán PERMANENTEMENTE.")
print()

respuesta = input("   ¿Desea continuar? (escriba 'SI' para confirmar): ")

if respuesta.strip().upper() != 'SI':
    print()
    print("   ❌ Operación cancelada por el usuario")
    print()
    print("=" * 70)
    exit(0)

print()
print("🗑️  [3/3] Eliminando registros duplicados...")
print()

eliminados = 0
errores = 0

for dup in duplicados:
    valor = dup['valor']
    tipo = dup['tipo']
    primer_id = dup['primer_id']
    
    try:
        # Obtener todos los registros de esta combinación
        registros = DenominacionMoneda.objects.filter(valor=valor, tipo=tipo).order_by('id')
        
        # Mantener el primero, eliminar el resto
        for registro in registros[1:]:  # Saltar el primero
            print(f"   🗑️  Eliminando: ID {registro.id} - {registro.tipo} ${registro.valor:,.0f}")
            registro.delete()
            eliminados += 1
            
    except Exception as e:
        print(f"   ❌ Error al eliminar {tipo} ${valor:,.0f}: {e}")
        errores += 1

print()
print("=" * 70)
print("📊 RESUMEN DE LA LIMPIEZA")
print("=" * 70)
print(f"   ✅ Registros eliminados: {eliminados}")
print(f"   ❌ Errores: {errores}")
print()

# Verificar que no quedan duplicados
print("🔍 Verificando que no quedan duplicados...")
duplicados_restantes = DenominacionMoneda.objects.values('valor', 'tipo').annotate(
    count=Count('id')
).filter(count__gt=1)

if duplicados_restantes:
    print(f"   ⚠️  Todavía hay {len(duplicados_restantes)} grupos duplicados")
    for dup in duplicados_restantes:
        print(f"      • {dup['tipo']} ${dup['valor']:,.0f}: {dup['count']} registros")
else:
    print("   ✅ No quedan duplicados. Base de datos limpia.")

print()

# Listar denominaciones finales
print("📋 Denominaciones actuales:")
print(f"{'ID':<6} {'Tipo':<10} {'Valor':>15} {'Activo':<8}")
print("-" * 45)
for d in DenominacionMoneda.objects.all().order_by('-valor', 'tipo'):
    tipo_icon = '💵' if d.tipo == 'BILLETE' else '🪙'
    activo_str = '✓' if d.activo else '✗'
    print(f"{d.id:<6} {tipo_icon} {d.tipo:<8} ${d.valor:>12,.0f} {activo_str:<8}")

print()
print("=" * 70)
print("✅ Limpieza completada")
print("=" * 70)
print()
print("💡 Próximos pasos:")
print("   1. Reiniciar el servidor/contenedor")
print("   2. Limpiar caché del navegador")
print("   3. Intentar acceder a /admin/caja/denominacionmoneda/")
print()
