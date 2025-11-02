"""
Script para verificar que las denominaciones se estén retornando correctamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda

print("🔍 Verificando denominaciones en la base de datos...")
print("=" * 70)

denominaciones = DenominacionMoneda.objects.filter(activo=True).order_by('-valor')

if not denominaciones.exists():
    print("❌ No hay denominaciones activas en la base de datos")
    exit(1)

print(f"✅ Se encontraron {denominaciones.count()} denominaciones activas\n")

# Simular lo que hace la vista
billetes = denominaciones.filter(tipo='BILLETE').order_by('-valor')
monedas = denominaciones.filter(tipo='MONEDA').order_by('-valor')

print("💵 BILLETES:")
print("-" * 70)
for b in billetes:
    data = {
        'id': b.id,
        'valor': float(b.valor),
        'tipo': b.tipo,
        'label': str(b)
    }
    print(f"   ID: {data['id']:3d} | Valor: ${data['valor']:>10,.0f} | Tipo: {data['tipo']:10s} | Label: {data['label']}")

print("\n🪙 MONEDAS:")
print("-" * 70)
for m in monedas:
    data = {
        'id': m.id,
        'valor': float(m.valor),
        'tipo': m.tipo,
        'label': str(m)
    }
    print(f"   ID: {data['id']:3d} | Valor: ${data['valor']:>10,.0f} | Tipo: {data['tipo']:10s} | Label: {data['label']}")

# Simular el JSON completo que debe retornar la vista
print("\n📦 JSON QUE DEBE RETORNAR LA VISTA:")
print("=" * 70)
import json
data = [
    {
        'id': d.id,
        'valor': float(d.valor),
        'tipo': d.tipo,
        'label': str(d)
    }
    for d in denominaciones
]
print(json.dumps({'success': True, 'denominaciones': data}, indent=2, ensure_ascii=False))

print("\n✅ Las denominaciones están correctamente configuradas en la base de datos")
print("💡 El problema debe estar en el JavaScript o en la vista obtener_denominaciones()")
