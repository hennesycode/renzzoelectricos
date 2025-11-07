#!/usr/bin/env python
"""
Script de prueba para verificar que el campo cost_price funciona correctamente.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')
ProductClass = get_model('catalogue', 'ProductClass')
StockRecord = get_model('partner', 'StockRecord')
Partner = get_model('partner', 'Partner')

def test_cost_price():
    """Prueba que el campo cost_price se puede guardar y leer correctamente."""
    
    print("🔍 Verificando campo cost_price...\n")
    
    # 1. Verificar que el modelo tiene el campo
    print("1. ✅ Verificando que StockRecord tiene el campo cost_price...")
    assert hasattr(StockRecord, 'cost_price'), "❌ StockRecord no tiene el campo cost_price"
    print("   ✅ Campo cost_price existe en el modelo\n")
    
    # 2. Crear o obtener un partner de prueba
    print("2. 📦 Obteniendo o creando Partner de prueba...")
    partner, created = Partner.objects.get_or_create(
        name="Partner de Prueba",
        defaults={'code': 'TEST_PARTNER'}
    )
    if created:
        print(f"   ✅ Partner creado: {partner.name}")
    else:
        print(f"   ✅ Partner encontrado: {partner.name}")
    print()
    
    # 3. Crear o obtener un producto de prueba
    print("3. 🏷️  Obteniendo o creando Producto de prueba...")
    product_class = ProductClass.objects.first()
    if not product_class:
        print("   ⚠️  No hay ProductClass, creando uno...")
        product_class = ProductClass.objects.create(
            name="Tipo Prueba",
            requires_shipping=True,
            track_stock=True
        )
    
    product, created = Product.objects.get_or_create(
        title="Producto de Prueba Cost Price",
        defaults={
            'product_class': product_class,
            'structure': 'standalone'
        }
    )
    if created:
        print(f"   ✅ Producto creado: {product.title}")
    else:
        print(f"   ✅ Producto encontrado: {product.title}")
    print()
    
    # 4. Crear o actualizar StockRecord con cost_price
    print("4. 💰 Creando/Actualizando StockRecord con cost_price...")
    stockrecord, created = StockRecord.objects.get_or_create(
        product=product,
        partner=partner,
        defaults={
            'partner_sku': 'TEST-SKU-001',
            'price': Decimal('100000.00'),
            'cost_price': Decimal('70000.00'),
            'num_in_stock': 50
        }
    )
    
    if not created:
        stockrecord.cost_price = Decimal('70000.00')
        stockrecord.price = Decimal('100000.00')
        stockrecord.save()
        print(f"   ✅ StockRecord actualizado")
    else:
        print(f"   ✅ StockRecord creado")
    print()
    
    # 5. Verificar que se guardó correctamente
    print("5. 🔍 Verificando que se guardó correctamente...")
    stockrecord.refresh_from_db()
    
    print(f"   📊 Datos del StockRecord:")
    print(f"      • ID: {stockrecord.id}")
    print(f"      • Partner: {stockrecord.partner.name}")
    print(f"      • SKU: {stockrecord.partner_sku}")
    print(f"      • Precio Venta: ${stockrecord.price:,.2f}")
    print(f"      • Precio Costo: ${stockrecord.cost_price:,.2f}")
    print(f"      • Stock: {stockrecord.num_in_stock}")
    print()
    
    # 6. Calcular margen
    if stockrecord.cost_price:
        margen = stockrecord.price - stockrecord.cost_price
        margen_porcentaje = (margen / stockrecord.cost_price) * 100
        print(f"   💵 Análisis de Rentabilidad:")
        print(f"      • Margen: ${margen:,.2f}")
        print(f"      • Margen %: {margen_porcentaje:.2f}%")
        print()
    
    # 7. Verificar que se puede actualizar
    print("6. 🔄 Probando actualización del cost_price...")
    nuevo_costo = Decimal('65000.00')
    stockrecord.cost_price = nuevo_costo
    stockrecord.save()
    stockrecord.refresh_from_db()
    
    assert stockrecord.cost_price == nuevo_costo, f"❌ Error: cost_price no se actualizó correctamente"
    print(f"   ✅ cost_price actualizado correctamente a ${nuevo_costo:,.2f}")
    print()
    
    # 8. Verificar que puede ser NULL
    print("7. ❓ Probando que cost_price puede ser NULL...")
    stockrecord.cost_price = None
    stockrecord.save()
    stockrecord.refresh_from_db()
    
    assert stockrecord.cost_price is None, "❌ Error: cost_price no puede ser NULL"
    print("   ✅ cost_price puede ser NULL (opcional)")
    print()
    
    # Restaurar valor
    stockrecord.cost_price = Decimal('70000.00')
    stockrecord.save()
    
    print("=" * 60)
    print("✅ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
    print("=" * 60)
    print()
    print(f"🎯 Resultado:")
    print(f"   • El campo cost_price funciona correctamente")
    print(f"   • Se puede guardar y leer sin problemas")
    print(f"   • Es opcional (puede ser NULL)")
    print(f"   • StockRecord de prueba ID: {stockrecord.id}")
    print()

if __name__ == '__main__':
    test_cost_price()
