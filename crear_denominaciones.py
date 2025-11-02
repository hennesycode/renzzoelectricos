"""
Script para crear denominaciones de monedas y billetes colombianos.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda
from decimal import Decimal


def crear_denominaciones():
    """Crea las denominaciones estándar de Colombia si no existen."""
    
    # Billetes colombianos (de mayor a menor)
    billetes = [
        100000,
        50000,
        20000,
        10000,
        5000,
        2000,
        1000,
    ]
    
    # Monedas colombianas (de mayor a menor)
    monedas = [
        1000,
        500,
        200,
        100,
        50,
    ]
    
    print("🪙 Creando denominaciones de monedas y billetes colombianos...")
    print("-" * 60)
    
    creadas = 0
    existentes = 0
    
    # Crear billetes
    for orden, valor in enumerate(billetes, start=1):
        valor_decimal = Decimal(str(valor))
        denom, created = DenominacionMoneda.objects.get_or_create(
            valor=valor_decimal,
            defaults={
                'tipo': 'BILLETE',
                'activo': True,
                'orden': orden
            }
        )
        if created:
            print(f"✅ Billete creado: ${valor:,}")
            creadas += 1
        else:
            print(f"ℹ️  Billete ya existe: ${valor:,}")
            existentes += 1
    
    # Crear monedas
    for orden, valor in enumerate(monedas, start=len(billetes) + 1):
        valor_decimal = Decimal(str(valor))
        denom, created = DenominacionMoneda.objects.get_or_create(
            valor=valor_decimal,
            defaults={
                'tipo': 'MONEDA',
                'activo': True,
                'orden': orden
            }
        )
        if created:
            print(f"✅ Moneda creada: ${valor:,}")
            creadas += 1
        else:
            print(f"ℹ️  Moneda ya existe: ${valor:,}")
            existentes += 1
    
    print("-" * 60)
    print(f"📊 Resumen:")
    print(f"   - Denominaciones creadas: {creadas}")
    print(f"   - Denominaciones existentes: {existentes}")
    print(f"   - Total en base de datos: {DenominacionMoneda.objects.count()}")
    print()
    
    # Mostrar todas las denominaciones activas
    print("💰 Denominaciones activas en el sistema:")
    print("-" * 60)
    
    billetes_activos = DenominacionMoneda.objects.filter(tipo='BILLETE', activo=True).order_by('-valor')
    if billetes_activos.exists():
        print("💵 BILLETES:")
        for b in billetes_activos:
            print(f"   - {b}")
    
    monedas_activas = DenominacionMoneda.objects.filter(tipo='MONEDA', activo=True).order_by('-valor')
    if monedas_activas.exists():
        print("\n🪙 MONEDAS:")
        for m in monedas_activas:
            print(f"   - {m}")
    
    print("\n✅ Script completado exitosamente!")


if __name__ == '__main__':
    crear_denominaciones()
