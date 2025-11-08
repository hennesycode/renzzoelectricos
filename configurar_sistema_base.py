#!/usr/bin/env python
"""
Script para configurar el sistema con datos base necesarios.
Crea cuentas de tesorería, denominaciones de monedas y tipos de movimiento.

Renzzo Eléctricos - Villavicencio, Meta
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.db import transaction
from caja.models import Cuenta, DenominacionMoneda, TipoMovimiento

def crear_cuentas_tesoreria():
    """Crea las cuentas básicas de tesorería si no existen."""
    print("🏦 Configurando cuentas de tesorería...")
    
    cuentas_base = [
        {
            'nombre': 'Banco Principal',
            'tipo': 'BANCO',
            'descripcion': 'Cuenta bancaria principal de la empresa',
            'saldo_inicial': Decimal('0.00')
        },
        {
            'nombre': 'Reserva General',
            'tipo': 'RESERVA',
            'descripcion': 'Dinero en efectivo guardado/reservado',
            'saldo_inicial': Decimal('0.00')
        },
        {
            'nombre': 'Caja Virtual',
            'tipo': 'VIRTUAL',
            'descripcion': 'Cuenta virtual para transacciones digitales',
            'saldo_inicial': Decimal('0.00')
        }
    ]
    
    cuentas_creadas = 0
    cuentas_existentes = 0
    
    for cuenta_data in cuentas_base:
        cuenta, created = Cuenta.objects.get_or_create(
            nombre=cuenta_data['nombre'],
            defaults={
                'tipo': cuenta_data['tipo'],
                'descripcion': cuenta_data['descripcion'],
                'saldo_actual': cuenta_data['saldo_inicial'],
                'activo': True
            }
        )
        
        if created:
            print(f"   ✅ Creada: {cuenta.nombre} ({cuenta.get_tipo_display()})")
            cuentas_creadas += 1
        else:
            print(f"   ℹ️ Ya existe: {cuenta.nombre} ({cuenta.get_tipo_display()}) - ${cuenta.saldo_actual or 0:.2f}")
            cuentas_existentes += 1
    
    print(f"   📊 Resultado: {cuentas_creadas} creadas, {cuentas_existentes} ya existían")
    return cuentas_creadas

def crear_denominaciones_moneda():
    """Crea las denominaciones de billetes y monedas colombianos."""
    print("\n💵 Configurando denominaciones de monedas...")
    
    # Denominaciones en pesos colombianos
    denominaciones_base = [
        # Billetes
        (100000, 'BILLETE', 'Billete de $100.000'),
        (50000, 'BILLETE', 'Billete de $50.000'),
        (20000, 'BILLETE', 'Billete de $20.000'),
        (10000, 'BILLETE', 'Billete de $10.000'),
        (5000, 'BILLETE', 'Billete de $5.000'),
        (2000, 'BILLETE', 'Billete de $2.000'),
        (1000, 'BILLETE', 'Billete de $1.000'),
        
        # Monedas
        (1000, 'MONEDA', 'Moneda de $1.000'),
        (500, 'MONEDA', 'Moneda de $500'),
        (200, 'MONEDA', 'Moneda de $200'),
        (100, 'MONEDA', 'Moneda de $100'),
        (50, 'MONEDA', 'Moneda de $50'),
        (20, 'MONEDA', 'Moneda de $20'),
        (10, 'MONEDA', 'Moneda de $10'),
    ]
    
    denominaciones_creadas = 0
    denominaciones_existentes = 0
    
    for valor, tipo, descripcion in denominaciones_base:
        denominacion, created = DenominacionMoneda.objects.get_or_create(
            valor=Decimal(str(valor)),
            tipo=tipo,
            defaults={
                'descripcion': descripcion,
                'activo': True
            }
        )
        
        if created:
            print(f"   ✅ Creada: {descripcion}")
            denominaciones_creadas += 1
        else:
            print(f"   ℹ️ Ya existe: {descripcion}")
            denominaciones_existentes += 1
    
    print(f"   📊 Resultado: {denominaciones_creadas} creadas, {denominaciones_existentes} ya existían")
    return denominaciones_creadas

def crear_tipos_movimiento():
    """Crea los tipos de movimiento básicos para el sistema."""
    print("\n🏷️ Configurando tipos de movimiento...")
    
    tipos_base = [
        # INGRESOS
        ('SERVICIO', 'Prestación de Servicio', 'INGRESO', 'Servicios técnicos o reparaciones'),
        ('DEPOSITO', 'Depósito Bancario', 'INGRESO', 'Dinero depositado en cuenta'),
        ('INGRESO_OTROS', 'Otros Ingresos', 'INGRESO', 'Ingresos varios no categorizados'),
        
        # GASTOS OPERATIVOS
        ('SERVICIOS', 'Servicios Públicos', 'GASTO', 'Luz, agua, internet, teléfono'),
        ('SUMINISTROS', 'Suministros', 'GASTO', 'Papelería, limpieza, materiales'),
        ('MANTENIMIENTO', 'Mantenimiento', 'GASTO', 'Reparaciones y mantenimiento'),
        ('GASTO_OTROS', 'Otros Gastos', 'GASTO', 'Gastos operativos varios'),
        
        # COMPRAS E INVERSIONES
        ('INVENTARIO', 'Compra de Inventario', 'INVERSION', 'Productos para reventa'),
        ('EQUIPOS', 'Compra de Equipos', 'INVERSION', 'Herramientas, maquinaria, activos'),
        ('INVERSION_OTROS', 'Otras Inversiones', 'INVERSION', 'Inversiones varias'),
        
        # PERSONAL
        ('SUELDOS', 'Sueldos y Salarios', 'GASTO', 'Pagos a empleados'),
        ('PRESTACIONES', 'Prestaciones Sociales', 'GASTO', 'Cesantías, primas, vacaciones'),
        
        # OTROS
        ('IMPUESTOS', 'Impuestos y Tasas', 'GASTO', 'IVA, retenciones, impuestos'),
        ('PRESTAMO', 'Préstamo/Crédito', 'GASTO', 'Pagos de préstamos o créditos'),
        
        # MOVIMIENTOS INTERNOS
        ('TRANSFERENCIA', 'Transferencia', 'INTERNO', 'Movimiento entre cuentas'),
        ('RETIRO_BANCO', 'Retiro de Banco', 'INTERNO', 'Retiro de dinero del banco'),
        ('DEPOSITO_BANCO', 'Depósito a Banco', 'INTERNO', 'Depósito de dinero al banco'),
    ]
    
    tipos_creados = 0
    tipos_existentes = 0
    
    for codigo, nombre, tipo_base, descripcion in tipos_base:
        tipo_movimiento, created = TipoMovimiento.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'tipo_base': tipo_base,
                'descripcion': descripcion,
                'activo': True
            }
        )
        
        if created:
            print(f"   ✅ Creado: {nombre} ({tipo_base})")
            tipos_creados += 1
        else:
            print(f"   ℹ️ Ya existe: {nombre} ({tipo_base})")
            tipos_existentes += 1
    
    print(f"   📊 Resultado: {tipos_creados} creados, {tipos_existentes} ya existían")
    return tipos_creados

def mostrar_resumen_final():
    """Muestra un resumen de todo lo configurado."""
    print("\n📋 RESUMEN FINAL DEL SISTEMA")
    print("=" * 50)
    
    # Cuentas
    print("🏦 CUENTAS DE TESORERÍA:")
    for cuenta in Cuenta.objects.filter(activo=True).order_by('tipo', 'nombre'):
        print(f"   • {cuenta.nombre} ({cuenta.get_tipo_display()}): ${cuenta.saldo_actual or 0:.2f}")
    
    # Denominaciones
    print(f"\n💵 DENOMINACIONES: {DenominacionMoneda.objects.filter(activo=True).count()} configuradas")
    billetes = DenominacionMoneda.objects.filter(tipo='BILLETE', activo=True).order_by('-valor')
    monedas = DenominacionMoneda.objects.filter(tipo='MONEDA', activo=True).order_by('-valor')
    
    print("   Billetes:", ", ".join([f"${int(b.valor):,}" for b in billetes]))
    print("   Monedas:", ", ".join([f"${int(m.valor):,}" for m in monedas]))
    
    # Tipos de movimiento
    tipos_por_categoria = {}
    for tipo in TipoMovimiento.objects.filter(activo=True).order_by('tipo_base', 'nombre'):
        if tipo.tipo_base not in tipos_por_categoria:
            tipos_por_categoria[tipo.tipo_base] = []
        tipos_por_categoria[tipo.tipo_base].append(tipo.nombre)
    
    print(f"\n🏷️ TIPOS DE MOVIMIENTO: {TipoMovimiento.objects.filter(activo=True).count()} configurados")
    for categoria, tipos in tipos_por_categoria.items():
        print(f"   {categoria}: {len(tipos)} tipos")
        for tipo in tipos[:3]:  # Mostrar solo los primeros 3
            print(f"     • {tipo}")
        if len(tipos) > 3:
            print(f"     • ... y {len(tipos) - 3} más")

def main():
    """Función principal del script."""
    print("⚙️ CONFIGURACIÓN INICIAL DEL SISTEMA")
    print("Renzzo Eléctricos - Sistema de Caja Registradora")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Crear configuraciones base
            cuentas_nuevas = crear_cuentas_tesoreria()
            denominaciones_nuevas = crear_denominaciones_moneda()
            tipos_nuevos = crear_tipos_movimiento()
            
            # Mostrar resumen
            mostrar_resumen_final()
            
            # Resultado final
            total_nuevos = cuentas_nuevas + denominaciones_nuevas + tipos_nuevos
            
            print("\n🎉 CONFIGURACIÓN COMPLETADA")
            if total_nuevos > 0:
                print(f"Se crearon {total_nuevos} nuevos elementos en el sistema")
            else:
                print("Todos los elementos ya existían - Sistema ya configurado")
            
            print("\n✅ El sistema está listo para:")
            print("• Abrir cajas registradoras")
            print("• Registrar movimientos de efectivo")
            print("• Gestionar tesorería")
            print("• Crear transacciones administrativas")
            
    except Exception as e:
        print(f"\n❌ ERROR durante la configuración: {str(e)}")
        raise
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)