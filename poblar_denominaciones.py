#!/usr/bin/env python
"""
Script para poblar las denominaciones de moneda colombiana por defecto.
Renzzo Eléctricos - Villavicencio, Meta

Ejecutar con: python poblar_denominaciones.py
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda
from decimal import Decimal

def poblar_denominaciones():
    """Crea las denominaciones de moneda colombiana estándar."""
    
    denominaciones_default = [
        # Billetes (de mayor a menor)
        {'valor': Decimal('100000'), 'tipo': 'BILLETE', 'orden': 1},
        {'valor': Decimal('50000'), 'tipo': 'BILLETE', 'orden': 2},
        {'valor': Decimal('20000'), 'tipo': 'BILLETE', 'orden': 3},
        {'valor': Decimal('10000'), 'tipo': 'BILLETE', 'orden': 4},
        {'valor': Decimal('5000'), 'tipo': 'BILLETE', 'orden': 5},
        {'valor': Decimal('2000'), 'tipo': 'BILLETE', 'orden': 6},
        {'valor': Decimal('1000'), 'tipo': 'BILLETE', 'orden': 7},
        
        # Monedas (de mayor a menor)
        {'valor': Decimal('1000'), 'tipo': 'MONEDA', 'orden': 8},
        {'valor': Decimal('500'), 'tipo': 'MONEDA', 'orden': 9},
        {'valor': Decimal('200'), 'tipo': 'MONEDA', 'orden': 10},
        {'valor': Decimal('100'), 'tipo': 'MONEDA', 'orden': 11},
        {'valor': Decimal('50'), 'tipo': 'MONEDA', 'orden': 12},
    ]
    
    print("🏦 Poblando denominaciones de moneda colombiana...")
    creadas = 0
    actualizadas = 0
    
    for denom_data in denominaciones_default:
        denominacion, created = DenominacionMoneda.objects.get_or_create(
            valor=denom_data['valor'],
            tipo=denom_data['tipo'],
            defaults={
                'orden': denom_data['orden'],
                'activo': True
            }
        )
        
        if created:
            creadas += 1
            print(f"✅ Creada: ${denominacion.valor:,.0f} ({denominacion.get_tipo_display()})")
        else:
            # Actualizar el orden si es diferente
            if denominacion.orden != denom_data['orden']:
                denominacion.orden = denom_data['orden']
                denominacion.save()
                actualizadas += 1
                print(f"🔄 Actualizada: ${denominacion.valor:,.0f} ({denominacion.get_tipo_display()})")
            else:
                print(f"ℹ️  Ya existe: ${denominacion.valor:,.0f} ({denominacion.get_tipo_display()})")
    
    print(f"\n📊 Resumen:")
    print(f"   • Denominaciones creadas: {creadas}")
    print(f"   • Denominaciones actualizadas: {actualizadas}")
    print(f"   • Total denominaciones: {DenominacionMoneda.objects.count()}")
    
    # Verificar que todas están activas
    inactivas = DenominacionMoneda.objects.filter(activo=False).count()
    if inactivas > 0:
        print(f"   ⚠️  Denominaciones inactivas: {inactivas}")
    
    print("\n✅ ¡Denominaciones pobladas exitosamente!")

if __name__ == '__main__':
    try:
        poblar_denominaciones()
    except Exception as e:
        print(f"❌ Error al poblar denominaciones: {e}")
        sys.exit(1)