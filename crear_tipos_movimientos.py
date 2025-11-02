#!/usr/bin/env python
"""
Script para crear los Tipos de Movimientos de Caja iniciales.
Categorías de INGRESOS (entradas) y EGRESOS (salidas) de caja.
Renzzo Eléctricos - Villavicencio, Meta
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import TipoMovimiento

print("\n" + "=" * 70)
print("📝 CREAR TIPOS DE MOVIMIENTOS DE CAJA")
print("=" * 70 + "\n")

# Definir tipos de movimientos de INGRESO (entradas)
tipos_ingreso = [
    {
        'codigo': 'VENTA',
        'nombre': 'Venta',
        'descripcion': 'Venta de productos o servicios',
    },
    {
        'codigo': 'COBRO',
        'nombre': 'Cobro de Factura',
        'descripcion': 'Cobro de facturas pendientes',
    },
    {
        'codigo': 'ABONO',
        'nombre': 'Abono a Cuenta',
        'descripcion': 'Abono parcial de un cliente',
    },
    {
        'codigo': 'DEVOLUCION',
        'nombre': 'Devolución de Proveedor',
        'descripcion': 'Devolución de dinero por productos devueltos a proveedor',
    },
    {
        'codigo': 'REEMBOLSO',
        'nombre': 'Reembolso',
        'descripcion': 'Reembolso de gastos o anticipos',
    },
    {
        'codigo': 'OTRO_INGRESO',
        'nombre': 'Otro Ingreso',
        'descripcion': 'Otros ingresos no categorizados',
    },
]

# Definir tipos de movimientos de EGRESO (salidas)
tipos_egreso = [
    {
        'codigo': 'COMPRA',
        'nombre': 'Compra de Productos',
        'descripcion': 'Compra de productos o mercancía',
    },
    {
        'codigo': 'PAGO_PROV',
        'nombre': 'Pago a Proveedor',
        'descripcion': 'Pago a proveedores',
    },
    {
        'codigo': 'GASTO_OPER',
        'nombre': 'Gasto Operativo',
        'descripcion': 'Gastos operativos del negocio (luz, agua, internet, etc.)',
    },
    {
        'codigo': 'GASTO_ADMIN',
        'nombre': 'Gasto Administrativo',
        'descripcion': 'Gastos administrativos y de oficina',
    },
    {
        'codigo': 'NOMINA',
        'nombre': 'Pago de Nómina',
        'descripcion': 'Pago de salarios y prestaciones',
    },
    {
        'codigo': 'DEVOLUCION_CLI',
        'nombre': 'Devolución a Cliente',
        'descripcion': 'Devolución de dinero por productos devueltos por cliente',
    },
    {
        'codigo': 'CAMBIO',
        'nombre': 'Cambio/Vuelto',
        'descripcion': 'Dinero entregado como cambio o vuelto',
    },
    {
        'codigo': 'RETIRO',
        'nombre': 'Retiro de Caja',
        'descripcion': 'Retiro de efectivo de la caja',
    },
    {
        'codigo': 'OTRO_EGRESO',
        'nombre': 'Otro Egreso',
        'descripcion': 'Otros egresos no categorizados',
    },
]

print("📋 Se crearán los siguientes tipos de movimientos:\n")

print("💰 INGRESOS (ENTRADAS) - " + str(len(tipos_ingreso)) + " categorías:")
for tipo in tipos_ingreso:
    print(f"   • [{tipo['codigo']}] {tipo['nombre']}")
    print(f"     {tipo['descripcion']}")

print(f"\n💸 EGRESOS (SALIDAS) - {len(tipos_egreso)} categorías:")
for tipo in tipos_egreso:
    print(f"   • [{tipo['codigo']}] {tipo['nombre']}")
    print(f"     {tipo['descripcion']}")

print(f"\n   Total: {len(tipos_ingreso) + len(tipos_egreso)} tipos de movimientos\n")

# Confirmar
respuesta = input("¿Desea continuar con la creación? (escriba 'SI' para confirmar): ")

if respuesta.strip().upper() != 'SI':
    print("\n❌ Operación CANCELADA por el usuario")
    print("   No se creó ningún tipo de movimiento\n")
    print("=" * 70 + "\n")
    exit(0)

print()
print("📝 Creando tipos de movimientos...\n")

creados = 0
ya_existian = 0
errores = 0

# Crear tipos de INGRESO
print("💰 CREANDO TIPOS DE INGRESO:")
print("-" * 70)

for tipo in tipos_ingreso:
    try:
        tipo_mov, created = TipoMovimiento.objects.get_or_create(
            codigo=tipo['codigo'],
            defaults={
                'nombre': tipo['nombre'],
                'descripcion': tipo['descripcion'],
                'activo': True
            }
        )
        
        if created:
            print(f"   ✅ CREADO: [{tipo_mov.codigo}] {tipo_mov.nombre}")
            creados += 1
        else:
            print(f"   ℹ️  Ya existe: [{tipo_mov.codigo}] {tipo_mov.nombre}")
            ya_existian += 1
            
            # Actualizar si está inactivo
            if not tipo_mov.activo:
                tipo_mov.activo = True
                tipo_mov.save()
                print(f"      ↪️  Activado")
                
    except Exception as e:
        print(f"   ❌ ERROR al crear [{tipo['codigo']}]: {e}")
        errores += 1

# Crear tipos de EGRESO
print("\n💸 CREANDO TIPOS DE EGRESO:")
print("-" * 70)

for tipo in tipos_egreso:
    try:
        tipo_mov, created = TipoMovimiento.objects.get_or_create(
            codigo=tipo['codigo'],
            defaults={
                'nombre': tipo['nombre'],
                'descripcion': tipo['descripcion'],
                'activo': True
            }
        )
        
        if created:
            print(f"   ✅ CREADO: [{tipo_mov.codigo}] {tipo_mov.nombre}")
            creados += 1
        else:
            print(f"   ℹ️  Ya existe: [{tipo_mov.codigo}] {tipo_mov.nombre}")
            ya_existian += 1
            
            # Actualizar si está inactivo
            if not tipo_mov.activo:
                tipo_mov.activo = True
                tipo_mov.save()
                print(f"      ↪️  Activado")
                
    except Exception as e:
        print(f"   ❌ ERROR al crear [{tipo['codigo']}]: {e}")
        errores += 1

print()
print("=" * 70)
print("📊 RESUMEN DE LA CREACIÓN")
print("=" * 70)
print(f"   ✅ Tipos creados: {creados}")
print(f"   ℹ️  Ya existían: {ya_existian}")
print(f"   ❌ Errores: {errores}")
print()

# Verificar totales
total_activos = TipoMovimiento.objects.filter(activo=True).count()

print("📊 ESTADO FINAL EN LA BASE DE DATOS:")
print("-" * 70)
print(f"   ✅ Total tipos de movimientos activos: {total_activos}")

# Listar todos los tipos activos
print("\n📋 TIPOS DE MOVIMIENTOS ACTIVOS:")
print("-" * 70)

for tipo in TipoMovimiento.objects.filter(activo=True).order_by('codigo'):
    print(f"   [{tipo.codigo:15s}] {tipo.nombre}")

print()

if errores == 0:
    print("✅ ¡PERFECTO! Todos los tipos de movimientos fueron creados correctamente")
    print()
    print("💡 Próximos pasos:")
    print("   1. Accede a: https://renzzoelectricos.com/admin/caja/tipomovimiento/")
    print("   2. Verifica que todos los tipos estén listados")
    print("   3. Ahora puedes crear movimientos de caja con estas categorías")
else:
    print(f"⚠️  ADVERTENCIA: Se encontraron {errores} error(es)")
    print("   Revisa los mensajes de error arriba")

print()
print("=" * 70)
print("✅ PROCESO COMPLETADO")
print("=" * 70 + "\n")

print("📝 INFORMACIÓN IMPORTANTE:")
print("-" * 70)
print("Estos tipos de movimientos se usan para categorizar:")
print("  • 💰 INGRESOS: Ventas, cobros, abonos, devoluciones de proveedor")
print("  • 💸 EGRESOS: Compras, pagos, gastos, devoluciones a cliente, retiros")
print()
print("Para agregar MÁS categorías:")
print("  1. Ve al admin: /admin/caja/tipomovimiento/")
print("  2. Click en 'Añadir tipo de movimiento'")
print("  3. Completa: Código, Nombre, Descripción, Estado")
print()
