#!/usr/bin/env python
"""
Script para cerrar todas las cajas abiertas automáticamente.
Renzzo Eléctricos - Villavicencio, Meta

Ejecutar con: python cerrar_cajas_abiertas.py
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import CajaRegistradora
from django.utils import timezone

def cerrar_cajas_abiertas():
    """Cierra todas las cajas que estén abiertas automáticamente."""
    
    cajas_abiertas = CajaRegistradora.objects.filter(estado='ABIERTA')
    
    if not cajas_abiertas.exists():
        print("✅ No hay cajas abiertas en el sistema.")
        return
    
    print(f"🔍 Encontradas {cajas_abiertas.count()} cajas abiertas:")
    
    for caja in cajas_abiertas:
        print(f"\n📋 Procesando Caja #{caja.id}:")
        print(f"   • Cajero: {caja.cajero.username}")
        print(f"   • Apertura: {caja.fecha_apertura}")
        print(f"   • Monto inicial: ${caja.monto_inicial:,.2f}")
        
        try:
            # Calcular el monto que debería haber según el sistema
            monto_sistema = caja.calcular_monto_sistema()
            
            # Cerrar con el monto calculado por el sistema
            diferencia = caja.cerrar_caja(
                monto_final_declarado=monto_sistema,
                observaciones_cierre='Cierre automático por script administrativo'
            )
            
            # Distribuir el dinero: todo va a "dinero guardado" (más seguro)
            caja.dinero_en_caja = Decimal('0.00')
            caja.dinero_guardado = monto_sistema
            caja.save()
            
            print(f"   ✅ Caja cerrada exitosamente")
            print(f"   • Monto sistema: ${monto_sistema:,.2f}")
            print(f"   • Diferencia: ${diferencia:,.2f}")
            print(f"   • Dinero guardado: ${monto_sistema:,.2f}")
            
        except Exception as e:
            print(f"   ❌ Error al cerrar caja: {str(e)}")
    
    print(f"\n📊 Resumen:")
    cajas_cerradas = CajaRegistradora.objects.filter(estado='CERRADA').count()
    cajas_abiertas_restantes = CajaRegistradora.objects.filter(estado='ABIERTA').count()
    
    print(f"   • Total cajas cerradas: {cajas_cerradas}")
    print(f"   • Cajas abiertas restantes: {cajas_abiertas_restantes}")
    
    if cajas_abiertas_restantes == 0:
        print("\n✅ ¡Todas las cajas han sido cerradas exitosamente!")
    else:
        print(f"\n⚠️  Quedan {cajas_abiertas_restantes} cajas abiertas")

if __name__ == '__main__':
    try:
        cerrar_cajas_abiertas()
    except Exception as e:
        print(f"❌ Error general: {e}")
        sys.exit(1)