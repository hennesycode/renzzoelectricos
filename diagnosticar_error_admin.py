#!/usr/bin/env python
"""
Script para obtener el traceback completo del error 500 en el admin.
Se conecta directamente y simula la petición del admin.
"""
import os
import django
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.admin.sites import site
from caja.models import DenominacionMoneda
from caja.admin import DenominacionMonedaAdmin
from django.test import RequestFactory
from django.contrib.auth import get_user_model

print("\n" + "=" * 70)
print("🔍 DIAGNÓSTICO DE ERROR 500 EN ADMIN - DenominacionMoneda")
print("=" * 70 + "\n")

User = get_user_model()

# Obtener un superusuario
try:
    superuser = User.objects.filter(is_superuser=True, is_staff=True).first()
    if not superuser:
        print("❌ No se encontró ningún superusuario")
        print("   Crea uno con: python manage.py createsuperuser")
        sys.exit(1)
    print(f"✅ Usando superusuario: {superuser.username}\n")
except Exception as e:
    print(f"❌ Error al obtener superusuario: {e}")
    sys.exit(1)

# Obtener el admin
print("📋 Verificando registro del admin...")
try:
    admin_instance = site._registry.get(DenominacionMoneda)
    if not admin_instance:
        print("❌ DenominacionMoneda no está registrado en el admin")
        sys.exit(1)
    print(f"✅ Admin registrado: {admin_instance.__class__.__name__}\n")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Crear una petición falsa
print("🔧 Simulando petición al admin...\n")
factory = RequestFactory()
request = factory.get('/admin/caja/denominacionmoneda/')
request.user = superuser

print("=" * 70)
print("PROBANDO MÉTODOS DEL ADMIN")
print("=" * 70 + "\n")

# Obtener todas las denominaciones
denominaciones = DenominacionMoneda.objects.all()
print(f"📊 Total denominaciones: {denominaciones.count()}\n")

if denominaciones.count() == 0:
    print("⚠️  No hay denominaciones en la base de datos")
    print("   Ejecuta: python crear_denominaciones_correctas.py\n")
    sys.exit(0)

# Probar cada método del admin
print("🧪 Probando métodos personalizados del admin:\n")

errores = []

for i, denom in enumerate(denominaciones, 1):
    print(f"[{i}/{denominaciones.count()}] Probando ID {denom.id} - {denom.tipo} ${denom.valor:,.0f}")
    
    # Probar valor_fmt
    try:
        result = admin_instance.valor_fmt(denom)
        print(f"   ✅ valor_fmt: {result}")
    except Exception as e:
        error_msg = f"valor_fmt falló para ID {denom.id}: {str(e)}"
        print(f"   ❌ {error_msg}")
        errores.append({
            'metodo': 'valor_fmt',
            'denominacion_id': denom.id,
            'error': str(e),
            'traceback': traceback.format_exc()
        })
    
    # Probar tipo_badge
    try:
        result = admin_instance.tipo_badge(denom)
        print(f"   ✅ tipo_badge: OK")
    except Exception as e:
        error_msg = f"tipo_badge falló para ID {denom.id}: {str(e)}"
        print(f"   ❌ {error_msg}")
        errores.append({
            'metodo': 'tipo_badge',
            'denominacion_id': denom.id,
            'error': str(e),
            'traceback': traceback.format_exc()
        })
    
    # Probar activo_badge
    try:
        result = admin_instance.activo_badge(denom)
        print(f"   ✅ activo_badge: OK")
    except Exception as e:
        error_msg = f"activo_badge falló para ID {denom.id}: {str(e)}"
        print(f"   ❌ {error_msg}")
        errores.append({
            'metodo': 'activo_badge',
            'denominacion_id': denom.id,
            'error': str(e),
            'traceback': traceback.format_exc()
        })
    
    print()

print("=" * 70)
print("RESULTADOS DEL DIAGNÓSTICO")
print("=" * 70 + "\n")

if errores:
    print(f"❌ SE ENCONTRARON {len(errores)} ERROR(ES):\n")
    
    for i, error in enumerate(errores, 1):
        print(f"ERROR #{i}:")
        print(f"  Método: {error['metodo']}")
        print(f"  Denominación ID: {error['denominacion_id']}")
        print(f"  Mensaje: {error['error']}")
        print(f"\n  Traceback completo:")
        print("  " + "-" * 66)
        for line in error['traceback'].split('\n'):
            if line.strip():
                print(f"  {line}")
        print("  " + "-" * 66)
        print()
    
    print("💡 RECOMENDACIONES:")
    print("  1. Revisa el código del método que falla en caja/admin.py")
    print("  2. El error probablemente es un problema de formato o tipo de dato")
    print("  3. Verifica que los campos de la denominación tengan valores válidos")
    
else:
    print("✅ TODOS LOS MÉTODOS FUNCIONAN CORRECTAMENTE\n")
    print("El error 500 podría ser causado por:")
    print("  • Problema en la consulta QuerySet (list_display)")
    print("  • Error en el template del admin")
    print("  • Permisos insuficientes")
    print("  • Problema de caché")
    print()
    print("💡 SOLUCIONES:")
    print("  1. Ejecuta: python manage.py collectstatic --clear --noinput")
    print("  2. Reinicia el servidor")
    print("  3. Limpia caché del navegador")
    print("  4. Revisa logs completos: docker logs web-xxx 2>&1 | grep -A 20 'Traceback'")

print()
print("=" * 70)
print("✅ DIAGNÓSTICO COMPLETADO")
print("=" * 70 + "\n")
