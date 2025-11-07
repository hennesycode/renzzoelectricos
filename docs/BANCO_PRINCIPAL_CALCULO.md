# 📊 BANCO PRINCIPAL - LÓGICA DE CÁLCULO

**Fecha:** 7 de noviembre de 2025  
**Versión:** 1.0

---

## 📌 RESUMEN

El **Banco Principal** es una cuenta virtual que acumula todas las entradas de banco registradas en la caja y se ajusta dinámicamente con los gastos, compras y transferencias.

---

## 🧮 FÓRMULA DE CÁLCULO

```
Banco Principal = 
    Σ(Entradas [BANCO] en MovimientoCaja)
    + Transferencias HACIA Banco (TransaccionGeneral tipo=INGRESO)
    - Gastos/Compras DESDE Banco (TransaccionGeneral tipo=EGRESO)
```

---

## 📝 COMPONENTES DEL CÁLCULO

### 1️⃣ **BASE: Entradas de Banco en Caja**

**Origen:** Tabla `MovimientoCaja`  
**Filtro:**
- `tipo = 'INGRESO'`
- `descripcion ICONTAINS '[BANCO]'`

**Ejemplo:**
```
Entrada Banco #1: $100,000
Entrada Banco #2: $50,000
Entrada Banco #3: $75,000
------------------------
TOTAL BASE: $225,000
```

---

### 2️⃣ **INGRESOS: Transferencias hacia Banco**

**Origen:** Tabla `TransaccionGeneral`  
**Filtro:**
- `cuenta = Banco`
- `tipo = 'INGRESO'`

**Ejemplo:**
```
Transferencia desde Caja: +$30,000
Transferencia desde Guardado: +$20,000
------------------------
TOTAL INGRESOS: +$50,000
```

---

### 3️⃣ **EGRESOS: Gastos y Compras desde Banco**

**Origen:** Tabla `TransaccionGeneral`  
**Filtro:**
- `cuenta = Banco`
- `tipo = 'EGRESO'`

**Ejemplo:**
```
Gasto "Alquiler": -$15,000
Compra "Inventario": -$40,000
------------------------
TOTAL EGRESOS: -$55,000
```

---

## 💰 CÁLCULO FINAL

```
Banco Principal = $225,000 (base) + $50,000 (ingresos) - $55,000 (egresos)
Banco Principal = $220,000
```

---

## 🔄 FLUJO DE OPERACIONES

### ➡️ **Registrar Entrada de Banco en Caja**

1. Usuario registra "Entrada BANCO" por $100,000 en caja
2. Se crea `MovimientoCaja` con `descripcion="[BANCO] Depósito cliente"`
3. **Banco Principal aumenta en $100,000**

### ➡️ **Registrar Gasto desde Banco**

1. Usuario selecciona "Gasto" desde "Banco Principal"
2. Elige tipo de gasto (ej: "Servicios Públicos") y monto $15,000
3. Se crea `TransaccionGeneral` con:
   - `tipo = 'EGRESO'`
   - `cuenta = Banco`
   - `monto = $15,000`
4. **Banco Principal disminuye en $15,000**

### ➡️ **Transferir desde Banco hacia Dinero Guardado**

1. Usuario hace click en "Transferir Fondos"
2. Selecciona origen "Banco Principal" y destino "Dinero Guardado"
3. Se crean 2 `TransaccionGeneral`:
   - **EGRESO** de Banco por $20,000
   - **INGRESO** a Dinero Guardado por $20,000
4. **Banco Principal disminuye en $20,000**
5. **Dinero Guardado aumenta en $20,000**

---

## ⚠️ VALIDACIONES

### ❌ **Fondos Insuficientes**

Al intentar registrar un gasto o transferencia desde Banco:

```python
if monto > saldo_banco_disponible:
    return error("Fondos insuficientes en Banco Principal. Disponible: $XXX")
```

### ✅ **Validación Exitosa**

- Monto > 0
- Banco tiene fondos suficientes
- Cuenta de banco existe y está activa

---

## 📊 DIFERENCIAS CON EL MODELO ANTERIOR

### ❌ **ANTES (Incorrecto)**
```
Banco = cuenta_banco.saldo_actual  # Campo fijo en BD
```
- Requería actualizar manualmente `saldo_actual` en cada operación
- Propenso a errores y descuadres
- No reflejaba el flujo real del dinero

### ✅ **AHORA (Correcto)**
```
Banco = Σ(Entradas) + Ingresos - Egresos  # Cálculo dinámico
```
- Se calcula automáticamente en tiempo real
- Refleja TODAS las entradas de banco desde el inicio
- Ajusta por gastos y transferencias posteriores
- Imposible descuadrar

---

## 🧪 PRUEBAS RECOMENDADAS

### Test 1: Entrada de Banco
1. Abrir caja con $50,000
2. Registrar "Entrada BANCO" por $100,000
3. Ir a Tesorería
4. **VERIFICAR:** Banco Principal muestra $100,000

### Test 2: Gasto desde Banco
1. Con Banco en $100,000
2. Registrar gasto "Servicios" por $20,000 desde Banco
3. **VERIFICAR:** Banco Principal muestra $80,000

### Test 3: Transferencia desde Banco
1. Con Banco en $80,000
2. Transferir $30,000 a Dinero Guardado
3. **VERIFICAR:** 
   - Banco Principal: $50,000
   - Dinero Guardado: +$30,000

### Test 4: Múltiples Entradas Banco
1. Registrar 3 entradas banco: $50k, $75k, $100k
2. Registrar gasto de $25k desde banco
3. **VERIFICAR:** Banco = $50k + $75k + $100k - $25k = $200,000

### Test 5: Validación de Fondos
1. Con Banco en $50,000
2. Intentar registrar gasto de $60,000
3. **VERIFICAR:** Error "Fondos insuficientes"

---

## 📁 ARCHIVOS MODIFICADOS

### `caja/views_tesoreria.py`
- **Función:** `tesoreria_dashboard()`
  - Calcula Banco Principal dinámicamente
  
- **Función:** `get_saldos_tesoreria()`
  - API endpoint con cálculo dinámico de Banco
  
- **Función:** `registrar_egreso_tesoreria()`
  - Valida fondos con cálculo dinámico
  - Crea `TransaccionGeneral` de egreso
  
- **Función:** `transferir_fondos()`
  - Valida fondos con cálculo dinámico
  - Crea transacciones de egreso/ingreso

---

## 🎯 VENTAJAS DE ESTE MODELO

✅ **Trazabilidad Total:** Cada peso ingresado por banco queda registrado  
✅ **Cálculo Automático:** No requiere actualizar campos manualmente  
✅ **Sin Descuadres:** El saldo siempre refleja la suma de transacciones  
✅ **Auditable:** Se puede rastrear cada entrada y salida  
✅ **Consistente:** Mismo modelo que Dinero Guardado  

---

## 🔗 RELACIONADO

- [DINERO_GUARDADO_CALCULO.md](./DINERO_GUARDADO_CALCULO.md) - Lógica de cálculo de Dinero Guardado
- [TESORERIA.md](./TESORERIA.md) - Documentación general del módulo de Tesorería
- [CIERRE_CAJA_MEJORADO.md](./CIERRE_CAJA_MEJORADO.md) - Flujo de cierre de caja

---

**✅ IMPLEMENTADO Y VERIFICADO**
