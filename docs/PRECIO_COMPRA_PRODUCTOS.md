# Precio de Compra en Productos - Django Oscar

**Fecha:** 3 de noviembre de 2025  
**Estado:** ✅ IMPLEMENTADO

## Resumen

Se ha agregado el campo **"Precio de Compra"** (cost_price) al sistema de productos de Django Oscar. Este campo permite registrar el costo al que se adquirió el producto, diferenciándolo del precio de venta.

## Cambios Implementados

### 1. App Partner Personalizada

Se creó una app `partner` personalizada que extiende el modelo `StockRecord` de Oscar:

**Ubicación:** `partner/models.py`

```python
class StockRecord(AbstractStockRecord):
    """
    Modelo extendido de StockRecord que incluye el precio de compra.
    """
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Precio de Compra',
        help_text='Precio al que se compró el producto (costo)'
    )
```

**Archivos creados:**
- `partner/__init__.py`
- `partner/apps.py`
- `partner/models.py`
- `partner/admin.py`
- `partner/migrations/` (copiadas de Oscar + nueva migración)

### 2. Migración de Base de Datos

Se creó la migración `0007_add_cost_price_to_stockrecord.py` que agrega el campo a la tabla `partner_stockrecord`:

**Ejecutar:**
```bash
python manage.py migrate partner
```

**Campo agregado:**
- **Nombre:** `cost_price`
- **Tipo:** `DECIMAL(12,2)`
- **Nullable:** Sí (opcional)
- **Default:** NULL

### 3. Formulario del Dashboard Personalizado

Se creó una app `dashboard.catalogue` personalizada que extiende el formulario de StockRecord:

**Ubicación:** `dashboard/catalogue/forms.py`

```python
class StockRecordForm(CoreStockRecordForm):
    """
    Formulario extendido de StockRecord que incluye el campo cost_price.
    """
    
    class Meta:
        model = StockRecord
        fields = [
            "partner",
            "partner_sku",
            "price_currency",
            "price",
            "cost_price",  # ← Campo nuevo
            "num_in_stock",
            "low_stock_threshold",
        ]
```

**Archivos creados:**
- `dashboard/__init__.py`
- `dashboard/catalogue/__init__.py`
- `dashboard/catalogue/apps.py`
- `dashboard/catalogue/forms.py` (formulario personalizado con campo cost_price)
- `dashboard/catalogue/templates/oscar/dashboard/catalogue/product_update.html` (template con columna de precio de compra)

### 4. Configuración Actualizada

Se modificó `config/settings.py` para usar las apps personalizadas:

**Cambios en INSTALLED_APPS:**

```python
INSTALLED_APPS = [
    # ...
    'partner.apps.PartnerConfig',  # ← Antes: oscar.apps.partner.apps.PartnerConfig
    # ...
    'dashboard.catalogue.apps.CatalogueDashboardConfig',  # ← Antes: oscar.apps.dashboard.catalogue...
    # ...
]
```

## Estructura del Campo

### Modelo de Datos

```
StockRecord
├─ partner (FK)
├─ partner_sku
├─ price_currency
├─ price               ← Precio de VENTA (existente)
├─ cost_price          ← Precio de COMPRA (nuevo) ✅
├─ num_in_stock
└─ low_stock_threshold
```

### Diferencias Clave

| Campo | Descripción | Uso |
|-------|-------------|-----|
| **price** | Precio de venta al público | Lo que se cobra al cliente |
| **cost_price** | Precio de compra/costo | Lo que costó adquirir el producto |

### Cálculos Útiles

```python
# Margen de ganancia (en dinero)
margen = stockrecord.price - stockrecord.cost_price

# Margen de ganancia (en porcentaje)
if stockrecord.cost_price:
    margen_porcentaje = ((stockrecord.price - stockrecord.cost_price) / stockrecord.cost_price) * 100
```

## Uso en el Dashboard

### Crear un Producto

1. Ir a: **Catálogo → Productos → Crear nuevo producto**
2. Seleccionar tipo de producto
3. Completar información básica
4. En la sección **"Stock y precios"**:
   - **Partner:** Seleccionar proveedor
   - **Partner SKU:** Código del proveedor
   - **Price currency:** COP
   - **Price:** $50,000 (precio de venta) ← Campo existente
   - **Precio de Compra:** $35,000 (precio de compra) ← **Campo nuevo** ✅
   - **Num in stock:** Cantidad disponible
   - **Low stock threshold:** Alerta de stock bajo

### Visualización

El campo "Precio de Compra" aparece **entre** el campo "Price" (precio de venta) y "Num in stock" (cantidad en stock).

```
┌─────────────────────────────────────┐
│ Stock y precios                     │
├─────────────────────────────────────┤
│ Partner: [Seleccionar...]           │
│ Partner SKU: [ABC123]               │
│ Price currency: [COP]               │
│ Precio de Compra: [$35,000]   ← ✅  │
│ Price: [$50,000]                    │
│ Num in stock: [100]                 │
│ Low stock threshold: [10]           │
└─────────────────────────────────────┘
```

## API y Consultas

### Acceder al Precio de Compra

```python
from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')

# Obtener producto
producto = Product.objects.get(id=1)

# Obtener stockrecord
stockrecord = producto.stockrecords.first()

# Acceder a los precios
precio_venta = stockrecord.price         # Decimal('50000.00')
precio_compra = stockrecord.cost_price   # Decimal('35000.00')

# Calcular margen
if precio_compra:
    margen = precio_venta - precio_compra
    margen_porcentaje = (margen / precio_compra) * 100
```

### Filtrar por Margen

```python
from django.db.models import F, ExpressionWrapper, DecimalField

# Productos con margen mayor al 30%
productos_alto_margen = StockRecord.objects.annotate(
    margen_porcentaje=ExpressionWrapper(
        ((F('price') - F('cost_price')) / F('cost_price')) * 100,
        output_field=DecimalField()
    )
).filter(
    cost_price__isnull=False,
    margen_porcentaje__gt=30
)
```

## Validación

### ✅ Verificaciones Realizadas

1. **Migración aplicada correctamente:**
   ```bash
   python manage.py migrate partner
   # ✅ Applying partner.0007_add_cost_price_to_stockrecord... OK
   ```

2. **Sin errores de configuración:**
   ```bash
   python manage.py check
   # ✅ System check identified no issues (0 silenced).
   ```

3. **Estructura de archivos correcta:**
   ```
   ✅ partner/
      ✅ __init__.py
      ✅ apps.py
      ✅ models.py
      ✅ admin.py
      ✅ migrations/
   
   ✅ dashboard/
      ✅ __init__.py
      ✅ catalogue/
         ✅ __init__.py
         ✅ apps.py
         ✅ forms.py
   ```

## Casos de Uso

### Caso 1: Producto con Precio de Compra
```python
producto = Product.objects.create(
    title="Cable THHN 12 AWG",
    upc="7701234567890",
    # ...
)

StockRecord.objects.create(
    product=producto,
    partner=partner,
    partner_sku="THHN12-100M",
    price=Decimal('50000.00'),      # Precio de venta
    cost_price=Decimal('35000.00'),  # Precio de compra ← Nuevo
    num_in_stock=100
)
```

**Resultado:**
- Precio de venta: $50,000
- Precio de compra: $35,000
- Margen: $15,000 (30%)

### Caso 2: Producto sin Precio de Compra
```python
# El campo es opcional, puede dejarse NULL
StockRecord.objects.create(
    product=producto,
    partner=partner,
    partner_sku="PRODUCTO-X",
    price=Decimal('100000.00'),
    cost_price=None,  # ← Opcional
    num_in_stock=50
)
```

### Caso 3: Reporte de Rentabilidad
```python
# Calcular ganancia total del inventario
total_inventario = 0
total_costo = 0

for sr in StockRecord.objects.filter(cost_price__isnull=False):
    valor_venta = sr.price * sr.num_in_stock
    valor_costo = sr.cost_price * sr.num_in_stock
    
    total_inventario += valor_venta
    total_costo += valor_costo

ganancia_potencial = total_inventario - total_costo
```

## Consideraciones Importantes

### 1. Campo Opcional
- El campo `cost_price` es **opcional** (puede ser NULL)
- Esto permite registrar productos sin precio de compra conocido
- Útil para productos donados, servicios, o cuando aún no se conoce el costo

### 2. Compatibilidad con Oscar
- Se mantiene **100% compatible** con Django Oscar
- Solo se **agrega** un campo, no se modifican campos existentes
- Todas las funcionalidades de Oscar siguen funcionando normalmente

### 3. Migraciones
- Las migraciones de Oscar partner se copiaron a nuestra app personalizada
- Esto evita conflictos con otras apps de Oscar que dependen de partner
- La migración 0007 agrega el campo sin afectar datos existentes

### 4. Seguridad
- El precio de compra **no** se muestra en el frontend público
- Solo visible en el dashboard de administración
- Útil para mantener confidencialidad de costos

## Próximos Pasos Recomendados

### 1. Agregar Reportes de Rentabilidad
Crear vistas en el dashboard que muestren:
- Margen de ganancia por producto
- Productos más/menos rentables
- Comparación precio compra vs precio venta

### 2. Validaciones Adicionales
Implementar validación para:
- `cost_price` no puede ser mayor que `price` (alerta)
- Sugerir precio de venta basado en margen deseado

### 3. Historial de Precios
Considerar agregar tabla de histórico para:
- Cambios en precio de compra a lo largo del tiempo
- Análisis de variación de costos

### 4. Integración con Facturación
Usar `cost_price` en el módulo de facturación para:
- Calcular ganancia real por factura
- Reportes de rentabilidad por período

## Conclusión

✅ **Implementación Completa**

El campo "Precio de Compra" está correctamente implementado y listo para usar en el sistema. El campo aparecerá automáticamente en el formulario de creación/edición de productos en el dashboard de administración, entre el campo "Price" (precio de venta) y "Num in stock" (cantidad en stock).

**Ventajas:**
- ✅ Diferenciación clara entre costo y precio de venta
- ✅ Base para cálculos de rentabilidad
- ✅ Campo opcional (no obliga a registrarlo)
- ✅ Compatible con Oscar
- ✅ Fácil de consultar desde código

---

**Documentación creada el:** 3 de noviembre de 2025  
**Estado:** ✅ LISTO PARA PRODUCCIÓN
