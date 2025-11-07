# Migraciones de Tipos de Movimiento - Guía de Despliegue

## 📋 Resumen
Este documento detalla las migraciones necesarias para implementar los tipos de movimiento por defecto en cualquier servidor.

## 🎯 Objetivo
Garantizar que las categorías de movimientos de caja existan por defecto en todos los servidores sin necesidad de crearlas manualmente.

## 📦 Migraciones Incluidas

### 1. Migración 0006: Ajuste de Esquema
**Archivo:** `caja/migrations/0006_alter_tipomovimiento_codigo_max_length.py`

**Propósito:** Aumentar el tamaño del campo `codigo` de 10 a 20 caracteres para soportar códigos como `MANTENIMIENTO` y `SUMINISTROS`.

**SQL Ejecutado:**
```sql
ALTER TABLE `caja_tipomovimiento` MODIFY `codigo` varchar(20) NOT NULL;
```

**Dependencias:** `0005_cajaregistradora_dinero_en_caja_and_more`

### 2. Migración 0007: Datos por Defecto
**Archivo:** `caja/migrations/0007_create_default_tipos.py`

**Propósito:** Insertar los tipos de movimiento por defecto en la base de datos.

**Tipos de INGRESO creados (en orden):**
1. `VENTA` - Venta
2. `COBRO_CXC` - Cobro de Cuentas por Cobrar
3. `DEV_PAGO` - Devolución de un Pago
4. `REC_GASTOS` - Recuperación de Gastos

**Tipos de EGRESO creados (en orden):**
1. `GASTO` - Gasto general
2. `COMPRA` - Compra de Mercadería
3. `FLETES` - Fletes y Transporte
4. `DEV_VENTA` - Devolución de Venta
5. `SUELDOS` - Sueldos y Salarios
6. `SUMINISTROS` - Suministros
7. `ALQUILER` - Alquiler y Servicios
8. `MANTENIMIENTO` - Mantenimiento y Reparaciones

**Tipo especial:**
- `APERTURA` - Apertura

**Dependencias:** `0006_alter_tipomovimiento_codigo_max_length`

**Comportamiento:**
- Usa `update_or_create()` para ser idempotente (puede ejecutarse múltiples veces sin duplicar datos)
- Si un tipo ya existe, solo actualiza el nombre y lo marca como activo
- La función reversa desactiva los tipos en lugar de eliminarlos

## 🚀 Instrucciones de Despliegue

### Para Servidor Nuevo (Base de datos limpia)

```bash
# 1. Subir el código al servidor
git pull origin main

# 2. Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate   # Windows

# 3. Instalar dependencias (si es necesario)
pip install -r requirements.txt

# 4. Ejecutar todas las migraciones
python manage.py migrate

# 5. Verificar que los tipos se crearon
python manage.py shell -c "from caja.models import TipoMovimiento; print(f'Total tipos: {TipoMovimiento.objects.count()}')"
```

### Para Servidor Existente (Con base de datos)

```bash
# 1. Hacer backup de la base de datos
mysqldump -u usuario -p nombre_bd > backup_antes_migracion.sql

# 2. Subir el código
git pull origin main

# 3. Ejecutar solo las nuevas migraciones
python manage.py migrate caja

# 4. Verificar los tipos de movimiento
python manage.py shell -c "from caja.models import TipoMovimiento; tipos = TipoMovimiento.objects.all(); [print(f'{t.codigo}: {t.nombre}') for t in tipos]"

# 5. Reiniciar servicios (si aplica)
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## ✅ Verificación Post-Despliegue

### 1. Verificar conteo de tipos
```bash
python manage.py shell -c "from caja.models import TipoMovimiento; print(f'Total: {TipoMovimiento.objects.count()}')"
```
**Resultado esperado:** `Total: 13`

### 2. Verificar todos los tipos
```bash
python manage.py shell
```
```python
from caja.models import TipoMovimiento
tipos = TipoMovimiento.objects.all().order_by('id')
for t in tipos:
    print(f'{t.id}: {t.codigo} - {t.nombre}')
```

**Resultado esperado:**
```
1: VENTA - Venta
2: COBRO_CXC - Cobro de Cuentas por Cobrar
3: DEV_PAGO - Devolución de un Pago
4: REC_GASTOS - Recuperación de Gastos
5: GASTO - Gasto general
6: COMPRA - Compra de Mercadería
7: FLETES - Fletes y Transporte
8: DEV_VENTA - Devolución de Venta
9: SUELDOS - Sueldos y Salarios
10: ALQUILER - Alquiler y Servicios
11: SUMINISTROS - Suministros
12: MANTENIMIENTO - Mantenimiento y Reparaciones
13: APERTURA - Apertura
```

### 3. Verificar en el navegador
1. Acceder al dashboard de caja
2. Intentar registrar un nuevo movimiento
3. Verificar que las categorías aparezcan en el modal de selección

## 🔄 Rollback (Si es necesario)

Si necesitas revertir las migraciones:

```bash
# Revertir a la migración 0005 (antes de los cambios)
python manage.py migrate caja 0005

# Esto ejecutará:
# - La función reversa de 0007 (desactivará los tipos por defecto)
# - Revertirá el cambio de tamaño del campo codigo a 10 caracteres
```

**⚠️ Advertencia:** Si ya existen movimientos usando los nuevos tipos, el rollback puede causar problemas de integridad referencial.

## 🔒 Protecciones Implementadas

### En el Modelo (`caja/models.py`)
```python
class TipoMovimiento(models.Model):
    # Campo codigo ahora soporta hasta 20 caracteres
    codigo = models.CharField(max_length=20, unique=True)
    
    # Códigos protegidos que no pueden eliminarse
    DEFAULT_CODES = {
        'VENTA', 'COBRO_CXC', 'DEV_PAGO', 'REC_GASTOS',
        'GASTO', 'COMPRA', 'FLETES', 'DEV_VENTA', 'SUELDOS', 
        'SUMINISTROS', 'ALQUILER', 'MANTENIMIENTO', 'APERTURA'
    }
    
    def delete(self, *args, **kwargs):
        """Impedir la eliminación de tipos de movimiento por defecto."""
        if self.codigo in self.DEFAULT_CODES:
            raise Exception('No se permite eliminar tipos de movimiento por defecto')
        return super().delete(*args, **kwargs)
```

### En el Admin (`caja/admin.py`)
- Deshabilitado el botón "Agregar" para tipos de movimiento
- Deshabilitada la acción de eliminación masiva

## 🐛 Solución de Problemas

### Error: "Data too long for column 'codigo'"
**Causa:** La migración 0007 se intentó aplicar antes que la 0006.

**Solución:**
```bash
# Verificar estado de migraciones
python manage.py showmigrations caja

# Si 0006 no está aplicada, aplicarla primero
python manage.py migrate caja 0006

# Luego aplicar 0007
python manage.py migrate caja 0007
```

### Error: "Duplicate entry for key 'codigo'"
**Causa:** Intentar crear tipos que ya existen.

**Solución:** La migración usa `update_or_create()`, así que esto no debería ocurrir. Si ocurre:
```bash
python manage.py migrate caja 0007 --fake
```

### Los tipos no aparecen en el frontend
**Causa:** El frontend usa listas fijas, no consulta la BD para las opciones.

**Solución:** Las listas están en `caja/views.py` en la función `obtener_tipos_movimiento()`. Ya están sincronizadas con los tipos de la BD.

## 📝 Notas Adicionales

1. **Idempotencia:** Las migraciones son idempotentes y pueden ejecutarse múltiples veces sin causar errores.

2. **Sin pérdida de datos:** Si ya existían tipos de movimiento con los mismos códigos, la migración los actualizará sin perder movimientos asociados.

3. **Orden garantizado:** Los tipos se crean en el orden especificado para mantener consistencia en el frontend.

4. **Compatibilidad:** Compatible con MySQL 5.7+, MySQL 8.0+, MariaDB 10.3+.

5. **Testing local:** Antes de desplegar, probar en local con:
   ```bash
   python manage.py migrate --plan
   ```

## 📞 Soporte

Si encuentras problemas durante el despliegue:
1. Revisa los logs: `tail -f /var/log/gunicorn/error.log`
2. Verifica la conectividad a la BD: `python manage.py dbshell`
3. Consulta el estado de migraciones: `python manage.py showmigrations`

---

**Fecha de creación:** 6 de noviembre de 2025
**Versión:** 1.0
**Autor:** Sistema de Caja - Renzzoelectricos
