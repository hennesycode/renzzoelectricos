#!/usr/bin/env python
"""
Script de diagnóstico para encontrar problemas en DenominacionMoneda
que causan error 500 al listar en el admin.
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda
from django.db import connection

print("=" * 70)
print("🔍 DIAGNÓSTICO DE DENOMINACIONES - RENZZO ELÉCTRICOS")
print("=" * 70)
print()

# 1. Verificar cuántas denominaciones hay
print("📊 [1/5] Contando denominaciones en la base de datos...")
total = DenominacionMoneda.objects.count()
print(f"   Total de registros: {total}")
print()

# 2. Buscar valores duplicados
print("🔎 [2/5] Buscando valores duplicados...")
from django.db.models import Count

duplicados = DenominacionMoneda.objects.values('valor').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-valor')

if duplicados:
    print(f"   ⚠️  ENCONTRADOS {len(duplicados)} valores duplicados:")
    for dup in duplicados:
        valor = dup['valor']
        count = dup['count']
        print(f"      • Valor ${valor:,.0f} aparece {count} veces")
        
        # Mostrar detalles de cada duplicado
        denom_duplicadas = DenominacionMoneda.objects.filter(valor=valor)
        for d in denom_duplicadas:
            print(f"        - ID: {d.id}, Tipo: {d.tipo}, Activo: {d.activo}, Orden: {d.orden}")
else:
    print("   ✅ No hay valores duplicados")
print()

# 3. Buscar combinaciones duplicadas (valor + tipo)
print("🔎 [3/5] Buscando combinaciones duplicadas (valor + tipo)...")
duplicados_tipo = DenominacionMoneda.objects.values('valor', 'tipo').annotate(
    count=Count('id')
).filter(count__gt=1).order_by('-valor')

if duplicados_tipo:
    print(f"   ⚠️  ENCONTRADOS {len(duplicados_tipo)} combinaciones duplicadas:")
    for dup in duplicados_tipo:
        valor = dup['valor']
        tipo = dup['tipo']
        count = dup['count']
        print(f"      • {tipo} de ${valor:,.0f} aparece {count} veces")
        
        # Mostrar detalles
        denom_duplicadas = DenominacionMoneda.objects.filter(valor=valor, tipo=tipo)
        for d in denom_duplicadas:
            print(f"        - ID: {d.id}, Activo: {d.activo}, Orden: {d.orden}")
else:
    print("   ✅ No hay combinaciones duplicadas (valor + tipo)")
print()

# 4. Listar todas las denominaciones
print("📋 [4/5] Listando todas las denominaciones:")
print(f"{'ID':<6} {'Tipo':<10} {'Valor':>15} {'Activo':<8} {'Orden':<6}")
print("-" * 50)

try:
    for d in DenominacionMoneda.objects.all().order_by('-valor', 'tipo'):
        tipo_icon = '💵' if d.tipo == 'BILLETE' else '🪙'
        activo_str = '✓' if d.activo else '✗'
        print(f"{d.id:<6} {tipo_icon} {d.tipo:<8} ${d.valor:>12,.0f} {activo_str:<8} {d.orden:<6}")
    print()
except Exception as e:
    print(f"   ❌ ERROR al listar denominaciones: {e}")
    print()

# 5. Verificar estructura de la tabla
print("🔧 [5/5] Verificando estructura de la tabla en la base de datos...")
with connection.cursor() as cursor:
    # Ver índices
    cursor.execute("""
        SHOW INDEX FROM caja_denominacionmoneda
    """)
    indices = cursor.fetchall()
    
    print("   Índices en la tabla:")
    unique_indices = []
    for idx in indices:
        index_name = idx[2]  # Key_name
        column_name = idx[4]  # Column_name
        non_unique = idx[1]   # Non_unique (0 = unique, 1 = non-unique)
        
        if non_unique == 0:  # Es único
            unique_indices.append((index_name, column_name))
            print(f"      • UNIQUE: {index_name} en columna '{column_name}'")
    
    # Verificar si existe el índice correcto
    print()
    print("   Verificación de índice correcto:")
    
    # Buscar índice que incluya tanto 'valor' como 'tipo'
    cursor.execute("""
        SHOW INDEX FROM caja_denominacionmoneda
        WHERE Column_name IN ('valor', 'tipo')
    """)
    indices_valor_tipo = cursor.fetchall()
    
    indices_dict = {}
    for idx in indices_valor_tipo:
        index_name = idx[2]
        column_name = idx[4]
        non_unique = idx[1]
        
        if index_name not in indices_dict:
            indices_dict[index_name] = {'columns': [], 'unique': non_unique == 0}
        indices_dict[index_name]['columns'].append(column_name)
    
    # Buscar índice compuesto (valor, tipo)
    tiene_indice_correcto = False
    for idx_name, idx_data in indices_dict.items():
        columns = set(idx_data['columns'])
        if 'valor' in columns and 'tipo' in columns and idx_data['unique']:
            print(f"      ✅ Índice correcto encontrado: {idx_name} en (valor, tipo)")
            tiene_indice_correcto = True
            break
    
    if not tiene_indice_correcto:
        print("      ⚠️  NO se encontró índice único compuesto en (valor, tipo)")
        print("          La migración podría no haberse aplicado correctamente")

print()
print("=" * 70)
print("💡 RECOMENDACIONES:")
print("=" * 70)

# Analizar y dar recomendaciones
problemas = []

if duplicados:
    problemas.append("valores_duplicados")
    print("⚠️  PROBLEMA: Hay valores duplicados")
    print("   Solución: Eliminar duplicados manualmente o ejecutar script de limpieza")
    print()

if duplicados_tipo:
    problemas.append("combinaciones_duplicadas")
    print("⚠️  PROBLEMA: Hay combinaciones (valor + tipo) duplicadas")
    print("   Solución: Eliminar registros duplicados, dejando solo uno de cada combinación")
    print()

if not tiene_indice_correcto:
    problemas.append("indice_incorrecto")
    print("⚠️  PROBLEMA: El índice único compuesto no está configurado correctamente")
    print("   Solución: Volver a ejecutar la migración 0004")
    print("   Comando: python manage.py migrate caja 0004")
    print()

if not problemas:
    print("✅ No se encontraron problemas obvios")
    print("   El error 500 podría ser causado por:")
    print("   - Permisos insuficientes del usuario en el admin")
    print("   - Problema en el código del admin (revisar logs)")
    print("   - Caché del navegador o servidor")
    print()
    print("   Recomendaciones:")
    print("   1. Revisar logs del contenedor: docker logs web-xxx")
    print("   2. Activar DEBUG=True temporalmente para ver el error completo")
    print("   3. Limpiar caché: collectstatic --clear --noinput")
else:
    print(f"Se encontraron {len(problemas)} problema(s) que deben solucionarse")

print()
print("=" * 70)
print("✅ Diagnóstico completado")
print("=" * 70)
