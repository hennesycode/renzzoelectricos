# 🚀 Guía de Despliegue: Fix Error 500 Admin Cajas

**Proyecto:** Renzzo Eléctricos - Villavicencio, Meta  
**Fecha:** Enero 2025  
**Cambios:** Protección masiva contra error 500 en admin de Caja + Script tipos de movimientos

---

## 📋 Resumen de Cambios

### ✅ Commit: `1de1ad4`

**Archivos modificados:**
- `caja/admin.py` - 26+ métodos protegidos con try/except
- `crear_tipos_movimientos.py` - Script nuevo para categorías

**Problema solucionado:**
- ❌ Error 500 al acceder a múltiples páginas de admin: `/admin/caja/*`
- ❌ Faltaban categorías de entrada/salida de caja

**Solución implementada:**
- ✅ Protección masiva con try/except en TODOS los métodos custom
- ✅ float() casting en campos Decimal
- ✅ Eliminación de get_X_display() vulnerable
- ✅ Script para crear 15 tipos de movimientos predefinidos

---

## 🎯 Páginas Admin Afectadas (Ahora Corregidas)

Las siguientes páginas ahora están protegidas contra error 500:

1. ✅ **Cajas Registradoras** - `/admin/caja/cajaregistradora/`
   - 11 métodos protegidos
   - Formatos de moneda seguros
   - Cálculo de duraciones protegido

2. ✅ **Movimientos de Caja** - `/admin/caja/movimientocaja/`
   - 4 métodos protegidos
   - Badges de tipo seguros
   - Info de usuario protegida

3. ✅ **Tipos de Movimientos** - `/admin/caja/tipomovimiento/`
   - 2 métodos protegidos
   - ⭐ **AQUÍ SE AGREGAN LAS CATEGORÍAS** ⭐

4. ✅ **Denominaciones Moneda** - `/admin/caja/denominacionmoneda/`
   - Ya estaba protegido desde commit anterior

5. ✅ **Conteos de Efectivo** - `/admin/caja/conteoefectivo/`
   - 5 métodos protegidos
   - Cálculos de totales seguros

6. ✅ **Detalles de Conteo** - `/admin/caja/detalleconteo/`
   - 3 métodos protegidos
   - Cálculo de subtotales seguro

---

## 🚀 Proceso de Despliegue en Producción

### 📡 Paso 1: Conectarse al Servidor

```bash
# Conectar por SSH
ssh hennesy@ubuntu-server-hennesy
# Password: Comandos555123*
```

### 🔄 Paso 2: Actualizar el Código

```bash
# Navegar al directorio del proyecto
cd /ruta/al/proyecto/renzzoelectricos

# Traer los últimos cambios
git pull origin main

# Verificar que se haya bajado el commit correcto
git log --oneline -1
# Debe mostrar: 1de1ad4 fix: Protección masiva contra error 500...
```

### 🐳 Paso 3: Reiniciar el Contenedor

```bash
# Reiniciar el contenedor Docker
sudo docker restart web-gg0wswocg8c4soc80kk88g8g-150356494831

# Esperar 10-15 segundos para que Django recargue
sleep 15

# Verificar que el contenedor esté corriendo
sudo docker ps | grep web-gg0wswocg8c4soc80kk88g8g-150356494831
```

### 📊 Paso 4: Verificar Logs

```bash
# Ver los últimos logs del contenedor
sudo docker logs --tail=50 -f web-gg0wswocg8c4soc80kk88g8g-150356494831

# Buscar estas líneas (indica recarga exitosa):
# - "Booting worker with pid: ..."
# - "Application startup complete"

# Presionar Ctrl+C para salir de logs
```

---

## ✅ Lista de Verificación Post-Despliegue

### 🌐 Verificar Páginas Admin (limpiar caché del navegador)

Abre estas URLs y verifica que carguen sin error 500:

1. 🔗 https://renzzoelectricos.com/admin/caja/cajaregistradora/
   - ✅ Debe mostrar lista de cajas con formatos de moneda
   - ✅ Badges de estado visibles (🟢 Abierta / ⚫ Cerrada)

2. 🔗 https://renzzoelectricos.com/admin/caja/movimientocaja/
   - ✅ Lista de movimientos con tipos (↑ INGRESO / ↓ EGRESO)
   - ✅ Montos formateados correctamente

3. 🔗 https://renzzoelectricos.com/admin/caja/tipomovimiento/
   - ✅ Lista de tipos de movimientos
   - ✅ Botón "Añadir tipo de movimiento" visible

4. 🔗 https://renzzoelectricos.com/admin/caja/denominacionmoneda/
   - ✅ Lista de 11 denominaciones (4 monedas + 7 billetes)
   - ✅ Badges de tipo (💵 Billete / 🪙 Moneda)

5. 🔗 https://renzzoelectricos.com/admin/caja/conteoefectivo/
   - ✅ Lista de conteos con totales calculados
   - ✅ Badges de tipo (APERTURA / CIERRE)

6. 🔗 https://renzzoelectricos.com/admin/caja/detalleconteo/
   - ✅ Lista de detalles con subtotales
   - ✅ Info de conteo visible

### 🎯 Comportamiento Esperado

**Si hay datos correctos:**
- ✅ Todas las páginas cargan sin error
- ✅ Formatos de moneda: `$1,000`, `$50,000`, `$100,000`
- ✅ Badges de colores visibles
- ✅ Cálculos automáticos funcionando

**Si hay datos problemáticos:**
- ⚠️ Páginas cargan correctamente (NO error 500)
- ⚠️ Campos con problemas muestran: `<span style="color: red;">Error: ...</span>`
- ✅ El admin sigue funcional para debugging

---

## 📝 Crear Tipos de Movimientos (Categorías)

### 🤖 Opción 1: Usar el Script Automático

```bash
# Entrar al contenedor Docker
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 bash

# Ejecutar el script
python crear_tipos_movimientos.py

# El script pedirá confirmación
# Escribir: SI

# Salir del contenedor
exit
```

**El script crea automáticamente:**

💰 **6 Tipos de INGRESO (Entradas):**
- `VENTA` - Venta de productos o servicios
- `COBRO` - Cobro de facturas pendientes
- `ABONO` - Abono parcial de un cliente
- `DEVOLUCION` - Devolución de proveedor
- `REEMBOLSO` - Reembolso de gastos
- `OTRO_INGRESO` - Otros ingresos

💸 **9 Tipos de EGRESO (Salidas):**
- `COMPRA` - Compra de productos
- `PAGO_PROV` - Pago a proveedor
- `GASTO_OPER` - Gastos operativos
- `GASTO_ADMIN` - Gastos administrativos
- `NOMINA` - Pago de nómina
- `DEVOLUCION_CLI` - Devolución a cliente
- `CAMBIO` - Cambio/vuelto
- `RETIRO` - Retiro de caja
- `OTRO_EGRESO` - Otros egresos

### 🖱️ Opción 2: Crear Manualmente en el Admin

1. Ve a: https://renzzoelectricos.com/admin/caja/tipomovimiento/
2. Click en **"Añadir tipo de movimiento"**
3. Completa los campos:
   - **Código:** VENTA (identificador único, sin espacios)
   - **Nombre:** Venta (nombre legible)
   - **Descripción:** Venta de productos o servicios
   - ✅ **Activo:** Marcado
4. Click en **"Guardar"**

---

## 💡 Cómo Usar los Tipos de Movimientos

### Cuando crees un MovimientoCaja:

1. Ve a: https://renzzoelectricos.com/admin/caja/movimientocaja/add/
2. Selecciona:
   - **Caja:** La caja abierta actual
   - **Tipo:** INGRESO (💰) o EGRESO (💸)
   - **Tipo de movimiento:** Selecciona de la lista (Venta, Gasto, etc.)
   - **Monto:** Cantidad en pesos colombianos
   - **Descripción:** Detalle del movimiento
3. Guardar

**Ejemplos de uso:**

```
INGRESO + VENTA + $50,000
→ Registra una venta de $50,000

EGRESO + GASTO_OPER + $20,000
→ Registra un gasto operativo de $20,000

INGRESO + COBRO + $100,000
→ Registra el cobro de una factura pendiente
```

---

## 🔍 Troubleshooting

### ❌ Problema: Sigue apareciendo error 500

**Diagnóstico:**

```bash
# Ver logs en tiempo real
sudo docker logs -f web-gg0wswocg8c4soc80kk88g8g-150356494831

# Buscar líneas con "Traceback" o "Error"
sudo docker logs web-gg0wswocg8c4soc80kk88g8g-150356494831 2>&1 | grep -A 30 "Traceback"
```

**Posibles causas:**
1. Código no actualizado → Verificar `git log --oneline -1`
2. Contenedor no reiniciado → `sudo docker restart web-xxx`
3. Error en base de datos → Ejecutar script de diagnóstico

### ❌ Problema: Aparecen mensajes rojos en el admin

**Esto es NORMAL y ESPERADO:**
- ✅ El admin está funcionando correctamente
- ⚠️ Los mensajes rojos indican datos problemáticos
- 🔧 Identifica qué dato está causando el problema
- 🗑️ Corrige o elimina el registro problemático

**Ejemplo de mensaje rojo:**
```
<span style="color: red;">Error: could not convert string to float: 'abc'</span>
```
→ Indica que hay un valor inválido en un campo numérico

### ❌ Problema: No aparecen los tipos de movimientos

**Solución:**

```bash
# Entrar al contenedor
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 bash

# Ejecutar el script
python crear_tipos_movimientos.py

# Verificar creación
python manage.py shell
>>> from caja.models import TipoMovimiento
>>> TipoMovimiento.objects.filter(activo=True).count()
15  # Debe mostrar 15
>>> exit()
```

---

## 📚 Recursos Adicionales

**Documentos relacionados:**
- `docs/FIX_ERROR_500_ADMIN.md` - Diagnóstico de errores admin
- `docs/GUIA_SCRIPTS_DENOMINACIONES.md` - Manejo de denominaciones
- `docs/SOLUCION_MODAL_DENOMINACIONES.md` - Fix modal denominaciones
- `docs/COMANDOS_SERVIDOR_PRODUCCION.md` - Comandos servidor

**Scripts útiles:**
- `crear_tipos_movimientos.py` - Crear categorías
- `validar_denominaciones.py` - Verificar denominaciones
- `diagnosticar_error_admin.py` - Detectar errores admin

---

## ✅ Checklist Final de Despliegue

```
□ Conectado al servidor por SSH
□ git pull ejecutado correctamente
□ Commit 1de1ad4 verificado
□ Contenedor Docker reiniciado
□ Logs verificados (sin errores)
□ 6 páginas admin verificadas (todas cargan)
□ Script crear_tipos_movimientos.py ejecutado
□ 15 tipos de movimientos verificados en admin
□ Caché del navegador limpiado
□ Prueba de creación de MovimientoCaja exitosa
□ Todo funciona correctamente ✅
```

---

## 🆘 Soporte

Si encuentras problemas durante el despliegue:

1. **Revisa los logs:** `sudo docker logs web-xxx 2>&1 | grep Error`
2. **Verifica el commit:** `git log --oneline -5`
3. **Valida la base de datos:** Ejecuta scripts de diagnóstico
4. **Limpia caché:** Ctrl+Shift+R en el navegador

**Contacto:** hennesy@renzzoelectricos.com

---

**✅ ¡Despliegue Completado con Éxito!**

*Ahora todas las páginas de admin de Caja están protegidas contra error 500 y las categorías de movimientos están disponibles para uso.*
