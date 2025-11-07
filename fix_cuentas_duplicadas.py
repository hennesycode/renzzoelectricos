"""
Script para verificar y corregir cuentas duplicadas.

PROBLEMA:
- El usuario creó 1 cuenta BANCO (OK)
- Intentó crear una cuenta RESERVA pero falló con error 500
- El sistema solo permite 1 cuenta activa de cada tipo

Este script:
1. Lista todas las cuentas existentes
2. Identifica duplicados del mismo tipo
3. Ofrece opciones para resolverlo
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import Cuenta
from django.db.models import Count


def main():
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE CUENTAS")
    print("=" * 80)
    
    # Listar todas las cuentas
    cuentas = Cuenta.objects.all()
    print(f"\n📊 Total de cuentas en la base de datos: {cuentas.count()}\n")
    
    if cuentas.count() == 0:
        print("✅ No hay cuentas en la base de datos.")
        print("\n💡 Puedes crear:")
        print("   - 1 cuenta tipo BANCO")
        print("   - 1 cuenta tipo RESERVA")
        return
    
    # Mostrar todas las cuentas
    print("📋 CUENTAS EXISTENTES:")
    print("-" * 80)
    for cuenta in cuentas:
        estado = "✓ ACTIVA" if cuenta.activo else "✗ INACTIVA"
        print(f"ID: {cuenta.id:3d} | {cuenta.nombre:30s} | Tipo: {cuenta.tipo:10s} | {estado} | Saldo: ${cuenta.saldo_actual:,.2f}")
    
    # Verificar duplicados de cada tipo
    print("\n" + "=" * 80)
    print("🔍 VERIFICACIÓN DE DUPLICADOS")
    print("=" * 80)
    
    duplicados_encontrados = False
    
    for tipo in ['BANCO', 'RESERVA']:
        cuentas_tipo = Cuenta.objects.filter(tipo=tipo)
        cuentas_activas = cuentas_tipo.filter(activo=True)
        
        tipo_nombre = "BANCO" if tipo == "BANCO" else "RESERVA (Dinero Guardado)"
        
        print(f"\n📦 Cuentas tipo {tipo_nombre}:")
        print(f"   Total: {cuentas_tipo.count()} | Activas: {cuentas_activas.count()}")
        
        if cuentas_activas.count() > 1:
            duplicados_encontrados = True
            print(f"   ⚠️  PROBLEMA: Hay {cuentas_activas.count()} cuentas ACTIVAS (debería haber solo 1)")
            print(f"\n   Cuentas activas de tipo {tipo_nombre}:")
            for c in cuentas_activas:
                print(f"      - ID {c.id}: {c.nombre} (Saldo: ${c.saldo_actual:,.2f})")
        elif cuentas_activas.count() == 1:
            print(f"   ✅ OK: 1 cuenta activa")
        else:
            print(f"   ⚠️  No hay ninguna cuenta activa de este tipo")
    
    # Sugerencias
    print("\n" + "=" * 80)
    print("💡 RECOMENDACIONES")
    print("=" * 80)
    
    if duplicados_encontrados:
        print("\n⚠️  Se encontraron cuentas duplicadas activas.")
        print("\n🔧 SOLUCIÓN:")
        print("   1. Ve a Django Admin: /admin/caja/cuenta/")
        print("   2. Para cada tipo (BANCO/RESERVA), deja solo 1 cuenta con activo=True")
        print("   3. Desactiva las demás (activo=False)")
        print("\n   O ejecuta este comando para desactivar automáticamente:")
        print(f"   python manage.py shell < fix_cuentas_auto.py")
    else:
        cuentas_banco = Cuenta.objects.filter(tipo='BANCO', activo=True).count()
        cuentas_reserva = Cuenta.objects.filter(tipo='RESERVA', activo=True).count()
        
        if cuentas_banco == 0:
            print("\n📝 Falta crear cuenta tipo BANCO")
        else:
            print(f"\n✅ Cuenta BANCO: OK")
        
        if cuentas_reserva == 0:
            print("📝 Falta crear cuenta tipo RESERVA (Dinero Guardado)")
        else:
            print(f"✅ Cuenta RESERVA: OK")
    
    print("\n" + "=" * 80)
    print("📚 INFORMACIÓN ADICIONAL")
    print("=" * 80)
    print("""
¿Para qué sirven las Cuentas?

🏦 CUENTA BANCO:
   - Representa el dinero en tu cuenta bancaria
   - Se usa para: transferencias bancarias, pagos con tarjeta, depósitos
   - Aparece en las opciones de Tesorería cuando registras gastos/ingresos

🔒 CUENTA RESERVA (Dinero Guardado):
   - Representa efectivo guardado físicamente (caja fuerte, etc.)
   - Se usa para: guardar efectivo de manera segura fuera de la caja diaria
   - NO es la caja del cajero (esa se maneja con CajaRegistradora)

🔄 FLUJO TÍPICO:
   1. El cajero abre caja con $X de monto inicial
   2. Al cierre, si sobra mucho efectivo, se "guarda" parte en RESERVA
   3. El efectivo guardado se puede:
      - Depositar en el BANCO (transferencia RESERVA → BANCO)
      - Sacar para gastos grandes
      - Usar como monto inicial de futuras cajas

⚠️ LIMITACIÓN ACTUAL:
   - Solo 1 cuenta BANCO activa
   - Solo 1 cuenta RESERVA activa
   - Si necesitas cambiar de banco, desactiva la cuenta vieja primero
""")


if __name__ == '__main__':
    main()
