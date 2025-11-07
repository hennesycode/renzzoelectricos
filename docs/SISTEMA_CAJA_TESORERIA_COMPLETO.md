# Sistema de Caja y Tesorería - Documentación Técnica

## Resumen del Sistema Implementado

El sistema de caja y tesorería ha sido completamente reestructurado para cumplir con los siguientes requisitos:

### 1. Flujo de Apertura de Caja

**Cuando se abre una caja:**
- ✅ Se crea automáticamente un `MovimientoCaja` de tipo `APERTURA` con el monto inicial
- ✅ Se crea automáticamente una `TransaccionGeneral` en tesorería con:
  - **Origen**: Caja Virtual
  - **Tipo**: Apertura caja
  - **Monto**: Positivo (entrada)

### 2. Flujo de Entradas y Salidas en Caja

**Cuando se registra una ENTRADA en caja:**
- ✅ Se crea `MovimientoCaja` de tipo `INGRESO`
- ✅ Se crea automáticamente `TransaccionGeneral` con:
  - **Origen**: caja
  - **Tipo**: entrada:[categoría]
  - **Monto**: Positivo

**Cuando se registra una SALIDA en caja:**
- ✅ Se crea `MovimientoCaja` de tipo `EGRESO`
- ✅ Se crea automáticamente `TransaccionGeneral` con:
  - **Origen**: caja
  - **Tipo**: salida:[categoría]
  - **Monto**: Negativo

### 3. Flujo de Entradas al Banco

**Cuando se presiona "Entrada Banco" en caja:**
- ✅ Se crea `MovimientoCaja` con `[BANCO]` en la descripción
- ✅ Se crea automáticamente `TransaccionGeneral` con:
  - **Origen**: banco
  - **Tipo**: entrada:[categoría]
  - **Cuenta**: Banco Principal
  - **Saldo de banco se actualiza automáticamente**

### 4. Cálculos Automáticos

#### Dinero en Caja
```
Dinero en Caja = Total Ingresos Efectivo - Total Egresos
```
- **Total Ingresos Efectivo**: Suma de todos los ingresos (incluye apertura, excluye banco)
- **Total Egresos**: Suma de todas las salidas de caja

#### Banco Principal
```
Banco Principal = Saldo inicial + Entradas Banco - Gastos/Compras desde Banco
```
- Se actualiza automáticamente con cada transacción

#### Dinero Guardado
```
Dinero Guardado = Σ(dinero_guardado de cajas cerradas) + Transacciones de Reserva
```
- Se incrementa cuando se cierra una caja
- Se puede ajustar con gastos/compras desde reserva

#### Total Disponible
```
Total Disponible = Dinero en Caja + Banco Principal + Dinero Guardado
```

### 5. Sistema de Transferencia de Fondos

**Transferir fondos crea transacciones dobles:**
- ✅ `TransaccionGeneral` de EGRESO en cuenta origen
- ✅ `TransaccionGeneral` de INGRESO en cuenta destino
- ✅ Ambas con la misma referencia para tracking
- ✅ Saldos se actualizan automáticamente

### 6. Sistema de Balance

Permite ajustar diferencias entre dinero real y calculado:
- ✅ Crea transacciones de ajuste (positivas o negativas)
- ✅ Actualiza saldos al valor real reportado
- ✅ Mantiene historial de todos los ajustes

## Señales Automáticas Implementadas

### `crear_transaccion_apertura_caja`
- **Trigger**: Cuando se crea una `CajaRegistradora`
- **Acción**: Crea movimiento de apertura + transacción de tesorería

### `crear_transaccion_tesoreria_desde_movimiento`
- **Trigger**: Cuando se crea un `MovimientoCaja` (excepto apertura)
- **Acción**: Crea `TransaccionGeneral` correspondiente
- **Lógica**: Detecta si es banco por `[BANCO]` en descripción

### `eliminar_transaccion_tesoreria_asociada`
- **Trigger**: Cuando se elimina un `MovimientoCaja`
- **Acción**: Elimina transacción asociada y ajusta saldos

## Tipos de Movimiento

### Ingresos
- `VENTA`: Venta de productos
- `COBRO_CXC`: Cobro de cuentas por cobrar
- `DEV_PAGO`: Devolución de pagos
- `REC_GASTOS`: Recuperación de gastos

### Gastos Operativos
- `GASTO`: Gasto general
- `FLETES`: Transporte
- `DEV_VENTA`: Devoluciones
- `SUELDOS`: Nómina
- `SUMINISTROS`: Suministros
- `ALQUILER`: Servicios
- `MANTENIMIENTO`: Reparaciones

### Inversiones
- `COMPRA`: Mercadería e inventario

### Movimientos Internos
- `APERTURA`: Apertura de caja
- `CIERRE_CAJA`: Dinero guardado al cierre
- `TRANSFERENCIA`: Entre cuentas
- `BALANCE`: Ajustes de balance

## Estructura de Cuentas

### Caja Virtual
- **Tipo**: RESERVA (interna)
- **Propósito**: Tracking de movimientos de caja
- **Activa**: No (no se muestra en listados)

### Banco Principal
- **Tipo**: BANCO
- **Propósito**: Fondos bancarios
- **Saldo**: Se actualiza automáticamente

### Dinero Guardado
- **Tipo**: RESERVA
- **Propósito**: Efectivo guardado fuera de caja
- **Saldo**: Calculado dinámicamente

## Validaciones Implementadas

1. **Solo una caja abierta**: El sistema permite una sola caja global abierta
2. **Fondos suficientes**: Valida saldos antes de permitir egresos/transferencias
3. **Sincronización**: Movimientos y transacciones siempre vinculados
4. **Consistencia**: Todos los cálculos son coherentes entre módulos

## Comandos de Administración

### Configuración Inicial
```bash
python manage.py setup_caja_tesoreria
```
Crea todos los tipos de movimiento, cuentas base y denominaciones necesarias.

## Flujo Completo de Ejemplo

1. **Abrir Caja** ($100,000):
   - MovimientoCaja: APERTURA +$100,000
   - TransaccionGeneral: Caja Virtual +$100,000
   - **Dinero en Caja**: $100,000

2. **Venta** ($50,000):
   - MovimientoCaja: VENTA +$50,000
   - TransaccionGeneral: Caja Virtual +$50,000
   - **Dinero en Caja**: $150,000

3. **Entrada Banco** ($30,000):
   - MovimientoCaja: VENTA +$30,000 [BANCO]
   - TransaccionGeneral: Banco Principal +$30,000
   - **Dinero en Caja**: $150,000
   - **Banco Principal**: $30,000

4. **Gasto** ($20,000 desde caja):
   - MovimientoCaja: GASTO -$20,000
   - TransaccionGeneral: Caja Virtual -$20,000
   - **Dinero en Caja**: $130,000

5. **Cierre de Caja** (Dinero en caja: $80,000, Guardado: $50,000):
   - TransaccionGeneral: Dinero Guardado +$50,000
   - **Dinero Guardado**: $50,000
   - **Dinero en Caja**: $80,000 (para próxima apertura)

**Total Disponible**: $80,000 + $30,000 + $50,000 = $160,000 ✅

## Ventajas del Nuevo Sistema

1. **Consistencia Total**: Todos los cálculos están sincronizados
2. **Auditoría Completa**: Cada movimiento tiene su transacción asociada
3. **Automatización**: Menos errores manuales
4. **Flexibilidad**: Manejo de múltiples fuentes de fondos
5. **Transparencia**: Historial completo de todos los movimientos
6. **Escalabilidad**: Fácil agregar nuevos tipos de movimiento

## Troubleshooting

### Si los saldos no coinciden:
1. Ejecutar `python manage.py setup_caja_tesoreria` para verificar configuración
2. Usar el sistema de Balance para ajustar diferencias
3. Verificar que no hay movimientos huérfanos sin transacción asociada

### Si faltan tipos de movimiento:
- El comando `setup_caja_tesoreria` los creará automáticamente

### Si hay problemas con señales:
- Las señales se ejecutan automáticamente, no requieren configuración adicional
- Verificar que los modelos están importados correctamente