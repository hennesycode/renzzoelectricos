#!/usr/bin/env python
"""
Script para configurar las cuentas de tesorería necesarias.
Renzzo Eléctricos - Villavicencio, Meta

Ejecutar con: python configurar_cuentas.py
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import Cuenta

def configurar_cuentas_tesoreria():
    """Configura las cuentas de tesorería necesarias para el sistema."""
    
    print("🏛️ Configurando cuentas de tesorería...")
    
    cuentas_por_crear = [
        {
            'nombre': 'Banco Principal',
            'tipo': 'BANCO',
            'saldo_inicial': Decimal('0.00'),
            'descripcion': 'Cuenta bancaria principal del negocio'
        },
        {
            'nombre': 'Reserva General',
            'tipo': 'RESERVA',
            'saldo_inicial': Decimal('0.00'),
            'descripcion': 'Dinero guardado fuera del banco'
        },
        {
            'nombre': 'Caja Virtual',
            'tipo': 'RESERVA',
            'saldo_inicial': Decimal('0.00'),
            'descripcion': 'Cuenta virtual para tracking de movimientos de caja (no mostrar en listados)'
        }
    ]
    
    creadas = 0
    actualizadas = 0
    
    for cuenta_data in cuentas_por_crear:
        cuenta, created = Cuenta.objects.get_or_create(
            nombre=cuenta_data['nombre'],
            defaults={
                'tipo': cuenta_data['tipo'],
                'saldo_actual': cuenta_data['saldo_inicial'],
                'activo': cuenta_data['nombre'] != 'Caja Virtual'  # Caja Virtual inactiva
            }
        )
        
        if created:
            creadas += 1
            print(f"✅ Creada: {cuenta.nombre} ({cuenta.get_tipo_display()}) - ${cuenta.saldo_actual:,.2f}")
        else:
            # Verificar si necesita actualización
            if cuenta.tipo != cuenta_data['tipo']:
                cuenta.tipo = cuenta_data['tipo']
                cuenta.save()
                actualizadas += 1
                print(f"🔄 Actualizada: {cuenta.nombre} - Tipo corregido a {cuenta.get_tipo_display()}")
            else:
                print(f"ℹ️  Ya existe: {cuenta.nombre} ({cuenta.get_tipo_display()}) - ${cuenta.saldo_actual:,.2f}")
    
    # Verificar que solo hay una cuenta activa de cada tipo
    print("\n🔍 Verificando integridad de cuentas...")
    
    for tipo in ['BANCO', 'RESERVA']:
        cuentas_activas = Cuenta.objects.filter(tipo=tipo, activo=True)
        if cuentas_activas.count() > 1:
            print(f"⚠️  Hay {cuentas_activas.count()} cuentas {tipo} activas:")
            for cuenta in cuentas_activas:
                print(f"   - {cuenta.nombre}: ${cuenta.saldo_actual:,.2f}")
            print("   Considera desactivar las cuentas no utilizadas desde el admin.")
        elif cuentas_activas.count() == 1:
            cuenta = cuentas_activas.first()
            print(f"✅ Cuenta {tipo} principal: {cuenta.nombre} (${cuenta.saldo_actual:,.2f})")
        else:
            print(f"❌ No hay cuentas {tipo} activas")
    
    print(f"\n📊 Resumen:")
    print(f"   • Cuentas creadas: {creadas}")
    print(f"   • Cuentas actualizadas: {actualizadas}")
    print(f"   • Total cuentas: {Cuenta.objects.count()}")
    print(f"   • Cuentas activas: {Cuenta.objects.filter(activo=True).count()}")
    
    # Mostrar saldos totales
    saldo_total_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).aggregate(
        total=django.db.models.Sum('saldo_actual')
    )['total'] or Decimal('0.00')
    
    saldo_total_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).aggregate(
        total=django.db.models.Sum('saldo_actual')
    )['total'] or Decimal('0.00')
    
    print(f"\n💰 Saldos Actuales:")
    print(f"   • Total en Banco: ${saldo_total_banco:,.2f}")
    print(f"   • Total en Reserva: ${saldo_total_reserva:,.2f}")
    print(f"   • Total General: ${saldo_total_banco + saldo_total_reserva:,.2f}")
    
    print("\n✅ ¡Cuentas de tesorería configuradas correctamente!")

if __name__ == '__main__':
    try:
        import django.db.models
        configurar_cuentas_tesoreria()
    except Exception as e:
        print(f"❌ Error al configurar cuentas: {e}")
        sys.exit(1)