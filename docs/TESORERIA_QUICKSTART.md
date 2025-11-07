# 🚀 Tesorería - Guía Rápida de Inicio

## ✅ Paso 1: Verificar Instalación

```bash
# Verificar que las migraciones se aplicaron
python manage.py showmigrations caja

# Debes ver:
# [X] 0008_cuenta_tipomovimiento_tipo_base_transacciongeneral
# [X] 0009_asignar_tipo_base_tipos
```

## ✅ Paso 2: Crear Cuentas

```bash
python manage.py crear_cuentas_tesoreria
```

**Salida esperada:**
```
🏦 Creando cuentas de Tesorería...
✅ Creada: Banco Principal (Banco)
✅ Creada: Dinero Guardado (Reserva)
```

## ✅ Paso 3: Acceder al Sistema

1. **URL**: http://localhost:8000/caja/tesoreria/
2. **Login**: Usuario con permiso `users.can_view_caja`
3. **Verificar**:
   - ✅ Se muestran 3 tarjetas (Caja, Banco, Reserva)
   - ✅ Botones "Registrar Gasto" y "Registrar Compra" visibles
   - ✅ Tabla "Últimas Transacciones" (vacía inicialmente)

## 🎯 Paso 4: Primer Registro

### Opción A: Registrar Gasto desde Banco

1. Click en **"Registrar Gasto"** (botón rosa)
2. Seleccionar:
   - **Categoría**: Suministros
   - **Origen**: 🏦 Banco Principal
   - **Monto**: 50000
   - **Referencia**: Compra Papelería
3. Click **"Registrar"**
4. ✅ Debe aparecer SweetAlert de éxito
5. ✅ Tabla muestra la transacción
6. ✅ Saldo Banco debe ser $0 (ya que inicialmente es $0)

**⚠️ NOTA**: Si el banco está en $0, obtendrás error "Fondos insuficientes". Primero debes agregar fondos al banco.

### Opción B: Agregar Fondos al Banco (Admin)

1. Ir a: http://localhost:8000/admin/caja/cuenta/
2. Click en "Banco Principal"
3. Cambiar **Saldo actual** de $0 a $100,000
4. Guardar
5. Volver a Tesorería y verificar que ahora muestra $100,000

### Opción C: Registrar desde Caja (Requiere Caja Abierta)

1. Ir a: http://localhost:8000/caja/
2. Click **"Abrir Caja"**
3. Ingresar monto inicial (ej: $150,000)
4. Confirmar apertura
5. Ir a Tesorería: http://localhost:8000/caja/tesoreria/
6. Verificar que "Dinero en Caja" muestra $150,000
7. Click **"Registrar Gasto"**
8. Seleccionar:
   - **Categoría**: Gasto general
   - **Origen**: 💰 Caja
   - **Monto**: 10000
9. Click **"Registrar"**
10. ✅ Egreso registrado
11. ✅ Saldo Caja ahora $140,000
12. ✅ También visible en Dashboard de Caja

## 📊 Paso 5: Verificar Integración

### Test de Integración Caja-Tesorería

1. **Abrir dos pestañas:**
   - Tab 1: http://localhost:8000/caja/ (Dashboard Caja)
   - Tab 2: http://localhost:8000/caja/tesoreria/ (Dashboard Tesorería)

2. **En Tab 2 (Tesorería):**
   - Registrar gasto de $5,000 desde Caja
   
3. **En Tab 1 (Caja):**
   - Presionar F5 para recargar
   - ✅ Debe aparecer el gasto en la tabla
   - ✅ "Total Disponible" debe reducirse en $5,000

**✅ Si esto funciona, la integración es perfecta!**

## 🏦 Paso 6: Explorar Admin

### Ver Cuentas
- **URL**: http://localhost:8000/admin/caja/cuenta/
- Puedes:
  - Ver saldos actuales
  - Editar nombres de cuentas
  - Agregar fondos manualmente (para testing)
  - Desactivar cuentas

### Ver Transacciones
- **URL**: http://localhost:8000/admin/caja/transacciongeneral/
- Puedes:
  - Ver log completo de transacciones
  - Filtrar por tipo (INGRESO/EGRESO/TRANSFERENCIA)
  - Filtrar por fecha
  - Filtrar por usuario
  - Exportar datos

### Ver Tipos de Movimiento
- **URL**: http://localhost:8000/admin/caja/tipomovimiento/
- Verás el nuevo campo **"Tipo Base"**:
  - INGRESO: 4 tipos
  - GASTO: 6 tipos
  - INVERSION: 2 tipos
  - INTERNO: 1 tipo

## 🧪 Paso 7: Casos de Prueba

### Test 1: Fondos Insuficientes

1. Ir a Admin → Banco Principal
2. Establecer saldo: $10,000
3. Ir a Tesorería
4. Intentar registrar gasto de $15,000 desde Banco
5. ✅ Debe mostrar error: "Fondos insuficientes en Banco Principal. Disponible: $10,000"

### Test 2: Caja Cerrada

1. Cerrar la caja si está abierta
2. Ir a Tesorería
3. Verificar:
   - ✅ Tarjeta "Caja" con fondo rojo
   - ✅ Texto "Caja Cerrada"
   - ✅ Saldo $0
   - ✅ En modal, opción "Caja" no disponible en dropdown de origen

### Test 3: Actualización Automática

1. Abrir Tesorería
2. Esperar 30 segundos
3. Verificar en consola del navegador (F12):
   - ✅ Debe aparecer: "✅ Saldos actualizados"
4. Los saldos se actualizan automáticamente cada 30s

### Test 4: Múltiples Categorías

**Registrar Gasto:**
1. Click "Registrar Gasto"
2. Verificar dropdown "Categoría" muestra:
   - Gasto general
   - Sueldos y Salarios
   - Suministros
   - Alquiler y Servicios
   - Mantenimiento y Reparaciones
   - Devolución de Venta

**Registrar Compra:**
1. Click "Registrar Compra"
2. Verificar dropdown "Categoría" muestra:
   - Compra de Mercadería
   - Fletes y Transporte

✅ Las categorías son diferentes según el botón presionado

## 📱 Paso 8: Verificar Responsiveness

1. Abrir Tesorería
2. Presionar F12 (DevTools)
3. Toggle Device Toolbar (Ctrl+Shift+M)
4. Probar diferentes resoluciones:
   - **Desktop (1920x1080)**: 3 tarjetas en fila
   - **Tablet (768x1024)**: 2-3 tarjetas
   - **Mobile (375x667)**: 1 tarjeta por fila

✅ El diseño debe adaptarse correctamente

## 🎨 Paso 9: Verificar Diseño

### Colores Esperados:

**Tarjetas:**
- Caja: Borde azul (#2196F3)
- Banco: Borde verde (#4CAF50)
- Reserva: Borde naranja (#FF9800)

**Botones:**
- Gasto: Gradiente rosa/rojo
- Compra: Gradiente azul

**Modal:**
- Header: Gradiente morado (#667eea → #764ba2)
- Inputs: Borde gris suave, focus azul

**Tabla:**
- Header: Gradiente morado
- Filas: Hover con fondo gris claro

## ❓ Troubleshooting

### Problema: "No module named 'caja.views_tesoreria'"

**Solución:**
```bash
# Verificar que el archivo existe
ls caja/views_tesoreria.py

# Si no existe, recrearlo desde docs/TESORERIA.md
```

### Problema: "Cuenta matching query does not exist"

**Solución:**
```bash
# Re-ejecutar comando de creación
python manage.py crear_cuentas_tesoreria
```

### Problema: Modal no se abre

**Solución:**
```bash
# Verificar que el archivo JS existe
ls caja/static/caja/js/tesoreria.js

# Copiar a staticfiles
Copy-Item "caja\static\caja\js\tesoreria.js" "staticfiles\caja\js\tesoreria.js" -Force

# Limpiar caché del navegador (Ctrl+Shift+R)
```

### Problema: SweetAlert no aparece

**Solución:**
- Verificar que el template incluye: `<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>`
- Verificar en consola (F12) si hay errores de carga

### Problema: "Permission denied" al acceder

**Solución:**
```python
# Asignar permiso al usuario en Django Admin
# User → Permissions → "Can view caja"
```

## 📚 Paso 10: Leer Documentación

Para uso avanzado, casos de uso y referencia completa:

- **Manual de Usuario**: `/docs/TESORERIA.md`
- **Implementación**: `/docs/TESORERIA_IMPLEMENTACION.md`

## ✅ Checklist Final

Marca cada item cuando lo pruebes:

- [ ] Migraciones aplicadas
- [ ] Cuentas creadas (Banco + Reserva)
- [ ] Dashboard carga correctamente
- [ ] 3 tarjetas visibles
- [ ] Modal "Gasto" abre y cierra
- [ ] Modal "Compra" abre y cierra
- [ ] Categorías filtran correctamente
- [ ] Registro desde Banco funciona
- [ ] Registro desde Caja funciona (con caja abierta)
- [ ] Validación de fondos funciona
- [ ] Error "Caja cerrada" aparece si aplica
- [ ] Tabla muestra transacciones
- [ ] Actualización automática funciona
- [ ] Admin de Cuentas accesible
- [ ] Admin de Transacciones accesible
- [ ] Responsive en mobile
- [ ] Integración con Caja verificada
- [ ] Menú lateral muestra "Tesorería"

## 🎉 ¡Listo!

Si completaste todos los pasos y el checklist, el módulo de Tesorería está **100% operativo**.

Para soporte o consultas, revisar:
- `/docs/TESORERIA.md` - Manual completo
- `/docs/TESORERIA_IMPLEMENTACION.md` - Detalles técnicos

---

**¡Bienvenido al nuevo centro de control financiero!** 💰🏦🔒
