# 🏦 Módulo de Tesorería - Manual Completo

## 📋 Índice
1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Instalación y Configuración](#instalación-y-configuración)
4. [Uso del Sistema](#uso-del-sistema)
5. [API Endpoints](#api-endpoints)
6. [Integración con Caja](#integración-con-caja)
7. [Casos de Uso](#casos-de-uso)

---

## 📖 Descripción General

El **Módulo de Tesorería** es el centro neurálgico financiero de Renzzo Eléctricos. Centraliza la visualización y gestión de **todos los fondos del negocio**:

- 💰 **Dinero en Caja**: Efectivo disponible en la caja registradora abierta
- 🏦 **Dinero en Banco**: Fondos depositados en cuentas bancarias
- 🔒 **Dinero Guardado**: Reservas de efectivo fuera de caja

### Características Principales

✅ **Visualización en Tiempo Real**: Dashboard con saldos actualizados  
✅ **Registro Centralizado de Egresos**: Gastos y compras desde un solo lugar  
✅ **Validación de Fondos**: Previene registros sin fondos suficientes  
✅ **Múltiples Orígenes**: Opera con Caja, Banco o Reserva  
✅ **Integración con Caja**: Los egresos desde caja se reflejan automáticamente  
✅ **Trazabilidad Completa**: Log detallado de todas las transacciones  
✅ **Filtrado Inteligente**: Separa Gastos Operativos de Inversiones  

---

## 🏗️ Arquitectura del Sistema

### Modelos de Datos

#### 1. **TipoMovimiento** (Modificado)

```python
class TipoMovimiento(models.Model):
    nombre = CharField(max_length=50, unique=True)
    codigo = CharField(max_length=20, unique=True)
    descripcion = TextField(blank=True)
    activo = BooleanField(default=True)
    tipo_base = CharField(max_length=20)  # ← NUEVO
    
    # Tipos Base:
    # - INGRESO: Ventas, Cobros
    # - GASTO: Gastos operativos
    # - INVERSION: Compras, Inversiones
    # - INTERNO: Movimientos internos
```

**Asignación de tipos_base a categorías existentes:**

| Código | Nombre | tipo_base |
|--------|--------|-----------|
| VENTA | Venta | INGRESO |
| COBRO_CXC | Cobro de Cuentas por Cobrar | INGRESO |
| DEV_PAGO | Devolución de un Pago | INGRESO |
| REC_GASTOS | Recuperación de Gastos | INGRESO |
| GASTO | Gasto general | GASTO |
| SUELDOS | Sueldos y Salarios | GASTO |
| SUMINISTROS | Suministros | GASTO |
| ALQUILER | Alquiler y Servicios | GASTO |
| MANTENIMIENTO | Mantenimiento y Reparaciones | GASTO |
| DEV_VENTA | Devolución de Venta | GASTO |
| COMPRA | Compra de Mercadería | INVERSION |
| FLETES | Fletes y Transporte | INVERSION |
| APERTURA | Apertura de Caja | INTERNO |

#### 2. **Cuenta** (Nuevo)

```python
class Cuenta(models.Model):
    nombre = CharField(max_length=100, unique=True)
    tipo = CharField(max_length=20)  # BANCO | RESERVA
    saldo_actual = DecimalField(max_digits=12, decimal_places=2)
    activo = BooleanField(default=True)
    fecha_creacion = DateTimeField(auto_now_add=True)
    
    # Métodos útiles:
    def tiene_fondos_suficientes(monto): bool
    def agregar_fondos(monto): void
    def retirar_fondos(monto): void  # Con validación
```

**Cuentas por defecto:**
- Banco Principal (tipo: BANCO, saldo: $0)
- Dinero Guardado (tipo: RESERVA, saldo: $0)

#### 3. **TransaccionGeneral** (Nuevo)

```python
class TransaccionGeneral(models.Model):
    fecha = DateTimeField(auto_now_add=True)
    tipo = CharField(max_length=20)  # INGRESO | EGRESO | TRANSFERENCIA
    monto = DecimalField(max_digits=12, decimal_places=2)
    descripcion = TextField(blank=True)
    referencia = CharField(max_length=100, blank=True)
    
    # Relaciones
    tipo_movimiento = ForeignKey(TipoMovimiento)
    cuenta = ForeignKey(Cuenta)  # Origen para egresos, destino para ingresos
    usuario = ForeignKey(User)
    cuenta_destino = ForeignKey(Cuenta, null=True)  # Solo para transferencias
    movimiento_caja_asociado = OneToOneField(MovimientoCaja, null=True)
```

### Diagrama de Flujo de Datos

```
┌─────────────────────────────────────────────┐
│         DASHBOARD TESORERÍA                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │  CAJA   │  │  BANCO  │  │ RESERVA │    │
│  │ $150k   │  │  $50k   │  │  $30k   │    │
│  └─────────┘  └─────────┘  └─────────┘    │
└─────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│   REGISTRAR EGRESO (Gasto o Compra)        │
│   1. Seleccionar categoría                  │
│   2. Seleccionar origen (Caja/Banco/Reserva)│
│   3. Ingresar monto                         │
│   4. Validar fondos suficientes             │
└─────────────────────────────────────────────┘
           │
           ▼
    ┌──────┴──────┐
    │ Origen?     │
    └──────┬──────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐  ┌──────────────┐
│  CAJA   │  │ BANCO/RESERVA│
└─────────┘  └──────────────┘
     │              │
     ▼              ▼
┌─────────┐  ┌──────────────┐
│Movement │  │ Transaccion  │
│  Caja   │  │   General    │
└─────────┘  └──────────────┘
     │              │
     └──────┬───────┘
            ▼
   ✅ Actualiza Saldos
```

---

## 🚀 Instalación y Configuración

### 1. Aplicar Migraciones

```bash
python manage.py migrate caja
```

Esto aplicará:
- **0008**: Crea Cuenta, TransaccionGeneral, agrega tipo_base a TipoMovimiento
- **0009**: Asigna tipo_base correcto a los 13 tipos existentes

### 2. Crear Cuentas Iniciales

```bash
python manage.py crear_cuentas_tesoreria
```

Salida esperada:
```
🏦 Creando cuentas de Tesorería...
✅ Creada: Banco Principal (Banco)
✅ Creada: Dinero Guardado (Reserva)

✨ Proceso completado!

📊 Resumen de cuentas:
  - Banco Principal (Banco) - Saldo: $0 - ✓ Activa
  - Dinero Guardado (Reserva / Dinero Guardado) - Saldo: $0 - ✓ Activa
```

### 3. Copiar Archivos Estáticos (Producción)

```bash
python manage.py collectstatic --noinput
```

### 4. Verificar Instalación

1. Acceder a: http://localhost:8000/caja/tesoreria/
2. Verificar que se muestran 3 tarjetas (Caja, Banco, Reserva)
3. Verificar que los botones "Registrar Gasto" y "Registrar Compra" funcionen

---

## 💼 Uso del Sistema

### Dashboard Principal

**URL**: `/caja/tesoreria/`

#### Tarjetas de Saldos

1. **💰 Dinero en Caja**
   - Muestra el saldo de la caja abierta actual
   - Si no hay caja abierta: fondo rojo, "Caja Cerrada"
   - Se actualiza automáticamente cada 30 segundos

2. **🏦 Dinero en Banco**
   - Muestra el saldo de la cuenta bancaria
   - Color verde
   - Actualizable manualmente con botón "Actualizar"

3. **🔒 Dinero Guardado**
   - Muestra el saldo de la reserva
   - Color naranja
   - Actualizable manualmente

### Registrar Gastos

**Botón**: "Registrar Gasto" (color rosa/rojo)

1. Click en "Registrar Gasto"
2. Se abre modal con formulario:
   - **Categoría**: Dropdown filtrado con categorías tipo GASTO
     - Gasto general
     - Sueldos y Salarios
     - Suministros
     - Alquiler y Servicios
     - Mantenimiento y Reparaciones
     - Devolución de Venta
   
   - **Origen del Dinero**: Dropdown con opciones disponibles
     - 💰 Caja (solo si hay caja abierta)
     - 🏦 Banco Principal
     - 🔒 Dinero Guardado
   
   - **Monto**: Input con formateo automático ($X,XXX)
   
   - **Referencia**: Opcional (ej: Factura #123)
   
   - **Descripción**: Opcional (detalles adicionales)

3. Click en "Registrar"
4. Sistema valida:
   - ✅ Campos requeridos completos
   - ✅ Monto > 0
   - ✅ Fondos suficientes en origen
5. Si OK: Registro exitoso, actualiza saldos
6. Si Error: Muestra mensaje específico

### Registrar Compras

**Botón**: "Registrar Compra" (color azul)

Flujo idéntico a Gastos, pero el dropdown de categorías muestra:
- Compra de Mercadería
- Fletes y Transporte

---

## 🔌 API Endpoints

### 1. GET `/caja/tesoreria/saldos/`

**Descripción**: Obtiene los saldos actuales de todas las cuentas.

**Response**:
```json
{
  "success": true,
  "caja": {
    "disponible": true,
    "saldo": 150000.00
  },
  "banco": {
    "id": 1,
    "saldo": 50000.00
  },
  "reserva": {
    "id": 2,
    "saldo": 30000.00
  }
}
```

### 2. GET `/caja/tesoreria/tipos-movimiento/?filtro=GASTO`

**Descripción**: Obtiene tipos de movimiento filtrados por tipo_base.

**Parámetros**:
- `filtro`: "GASTO" o "INVERSION"

**Response**:
```json
{
  "success": true,
  "tipos": [
    {"id": 5, "codigo": "GASTO", "nombre": "Gasto general"},
    {"id": 9, "codigo": "SUELDOS", "nombre": "Sueldos y Salarios"},
    ...
  ]
}
```

### 3. POST `/caja/tesoreria/registrar-egreso/`

**Descripción**: Registra un egreso (gasto o compra).

**Body**:
```json
{
  "tipo_movimiento_id": 5,
  "origen": "CAJA",  // o ID de cuenta
  "monto": 10000,
  "descripcion": "Compra de insumos",
  "referencia": "Factura #123"
}
```

**Response Success**:
```json
{
  "success": true,
  "message": "Egreso registrado exitosamente desde Caja",
  "origen": "CAJA"
}
```

**Response Error**:
```json
{
  "error": "Fondos insuficientes en caja. Disponible: $5,000"
}
```

### 4. POST `/caja/tesoreria/transferir-fondos/`

**Descripción**: Transfiere fondos entre cuentas.

**Body**:
```json
{
  "origen": "CAJA",  // o ID de cuenta
  "destino_id": 1,   // ID de cuenta destino
  "monto": 50000,
  "descripcion": "Depósito al banco"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Transferencia exitosa de Caja a Banco Principal",
  "origen": "CAJA",
  "destino": 1
}
```

---

## 🔗 Integración con Caja

### Cómo Funciona

Cuando registras un egreso desde **Tesorería** con origen = "CAJA":

1. ✅ Sistema valida que haya una caja abierta
2. ✅ Calcula el saldo disponible (apertura + entradas - salidas)
3. ✅ Valida fondos suficientes
4. ✅ Crea un `MovimientoCaja` tipo EGRESO
5. ✅ El movimiento aparece en el dashboard de Caja automáticamente
6. ✅ El "Total Disponible" de Caja se actualiza en tiempo real

### Ejemplo Visual

**Antes del Egreso:**
```
Dashboard Caja:
  Total Disponible: $150,000
  Movimientos: 3

Dashboard Tesorería:
  Dinero en Caja: $150,000
```

**Usuario registra gasto de $10,000 desde Tesorería (origen: Caja)**

**Después del Egreso:**
```
Dashboard Caja:
  Total Disponible: $140,000  ✅
  Movimientos: 4  ✅
  Último: "Gasto general - $10,000"  ✅

Dashboard Tesorería:
  Dinero en Caja: $140,000  ✅
```

### Ventajas de Esta Integración

✅ **Un Solo Sistema**: No duplicidad de registros  
✅ **Consistencia**: Los datos siempre están sincronizados  
✅ **Auditoría**: Todo movimiento queda registrado con usuario y fecha  
✅ **Flexibilidad**: Puedes registrar desde Caja o desde Tesorería  

---

## 📊 Casos de Uso

### Caso 1: Pagar Sueldos desde Banco

**Escenario**: Día de pago, necesitas pagar $500,000 en sueldos.

**Flujo**:
1. Acceder a Tesorería
2. Click en "Registrar Gasto"
3. Seleccionar:
   - Categoría: "Sueldos y Salarios"
   - Origen: "🏦 Banco Principal"
   - Monto: 500000
   - Referencia: "Nómina Noviembre 2025"
4. Click "Registrar"
5. Sistema:
   - Valida fondos en banco
   - Crea TransaccionGeneral
   - Actualiza saldo de banco: -$500,000
   - Muestra transacción en tabla

**Resultado**:
- ✅ Gasto registrado
- ✅ Saldo banco actualizado
- ✅ Trazabilidad completa

### Caso 2: Comprar Mercadería desde Caja

**Escenario**: Proveedor llega y debes pagar $200,000 en efectivo.

**Flujo**:
1. Acceder a Tesorería
2. Click en "Registrar Compra"
3. Seleccionar:
   - Categoría: "Compra de Mercadería"
   - Origen: "💰 Caja"
   - Monto: 200000
   - Referencia: "Factura Proveedor ABC #456"
4. Click "Registrar"
5. Sistema:
   - Valida que haya caja abierta
   - Valida fondos en caja ($300k disponibles)
   - Crea MovimientoCaja en caja actual
   - Actualiza "Total Disponible" en Caja: -$200,000

**Resultado**:
- ✅ Compra registrada en Tesorería
- ✅ Movimiento visible en Dashboard Caja
- ✅ Saldo caja: $100,000
- ✅ Al cerrar caja, el sistema cuenta los $200k menos

### Caso 3: Transferir Fondos al Banco (Pendiente - TODO)

**Escenario**: Al cerrar caja con $300,000, decides depositar $200,000 al banco.

**Flujo** (cuando se implemente):
1. Cerrar caja normalmente
2. Sistema muestra modal: "¿Qué hacer con los $300,000?"
3. Opciones:
   - "Transferir a Banco" → Abre formulario
   - "Transferir a Reserva" → Abre formulario
   - "Dejar en Caja" → Usa para próxima apertura
4. Usuario selecciona "Transferir a Banco"
5. Ingresa monto: $200,000
6. Sistema:
   - Crea TransaccionGeneral tipo INGRESO en Banco
   - Actualiza saldo banco: +$200,000
   - Los otros $100,000 quedan para próxima apertura

---

## 🛠️ Mantenimiento

### Ver Cuentas en Admin

1. Acceder a: http://localhost:8000/admin/caja/cuenta/
2. Ver listado de cuentas con saldos
3. Editar nombres o desactivar cuentas

### Ver Transacciones en Admin

1. Acceder a: http://localhost:8000/admin/caja/transacciongeneral/
2. Filtrar por:
   - Tipo (INGRESO/EGRESO/TRANSFERENCIA)
   - Fecha
   - Usuario
   - Cuenta
3. Ver detalles completos de cada transacción

### Ajustar Saldos Manualmente

**⚠️ Solo en casos excepcionales (ej: error de migración)**

```python
from caja.models import Cuenta

# Ajustar saldo de banco
banco = Cuenta.objects.get(tipo='BANCO')
banco.saldo_actual = 50000
banco.save()
```

---

## 🔒 Permisos y Seguridad

### Permisos Requeridos

- **Ver Tesorería**: `users.can_view_caja`
- **Registrar Egresos**: `users.can_manage_caja`
- **Transferir Fondos**: `users.can_manage_caja`

### Validaciones Implementadas

✅ Monto > 0  
✅ Cuenta origen existe y está activa  
✅ Fondos suficientes antes de registrar  
✅ Caja abierta (si origen = CAJA)  
✅ CSRF tokens en todos los POST  
✅ Usuario autenticado  

---

## 📝 Notas Técnicas

### Stack Tecnológico

- **Backend**: Django 5.1.4, Python 3.11
- **Base de Datos**: MySQL 8.0
- **Frontend**: Bootstrap 5.3, Vanilla JavaScript
- **AJAX**: Fetch API
- **Alerts**: SweetAlert2

### Performance

- Actualización automática de saldos cada 30 segundos
- Queries optimizadas con `select_related()`
- Índices en campos clave (fecha, tipo, cuenta)

### Logging

Todas las transacciones incluyen:
- Usuario que registró
- Timestamp exacto
- Tipo de movimiento
- Cuenta(s) involucrada(s)
- Monto y descripción

---

## 🚧 Pendientes (TODO)

- [ ] Integrar modal de transferencia en cierre de caja
- [ ] Reportes de Tesorería (gráficas, exportar a Excel)
- [ ] Módulo de conciliación bancaria
- [ ] Múltiples cuentas bancarias
- [ ] Historial de transferencias con filtros

---

## 📞 Soporte

Para dudas o problemas:
- Email: soporte@renzzoelectricos.com
- Documentación: /docs/TESORERIA.md

---

**© 2025 Renzzo Eléctricos - Bogotá, Colombia**
