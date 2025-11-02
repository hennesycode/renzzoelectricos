# 🔧 Fix: Error al crear denominaciones con el mismo valor

**Fecha:** 2 de Noviembre de 2025  
**Problema:** Error 500 al intentar crear billete de $1,000 después de haber creado moneda de $1,000  
**Estado:** ✅ SOLUCIONADO

---

## 📋 Descripción del Problema

### Síntoma
Al intentar crear una denominación de **billete de $1,000** desde `/admin/caja/denominacionmoneda/add/`, el sistema devuelve un error 500:

```
Server Error (500)
denominacionmoneda/:1  Failed to load resource: the server responded with a status of 500 ()
```

### Causa Raíz
El modelo `DenominacionMoneda` tenía una restricción de unicidad en el campo `valor`:

```python
# ❌ ANTES (INCORRECTO):
valor = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    unique=True,  # ← Esto impedía tener billete y moneda de $1,000
    verbose_name=_('Valor')
)
```

Esta restricción **NO permitía** tener dos denominaciones con el mismo valor, incluso si eran de **tipos diferentes** (BILLETE vs MONEDA).

### Escenario del Error
1. Usuario crea **Moneda de $1,000** ✅
2. Usuario intenta crear **Billete de $1,000** ❌
3. Django lanza `IntegrityError` porque el valor 1000 ya existe
4. Se muestra error 500 al usuario

---

## ✅ Solución Implementada

### Cambio en el Modelo

Se modificó `caja/models.py` para permitir el mismo valor si son tipos diferentes:

```python
# ✅ DESPUÉS (CORRECTO):
class DenominacionMoneda(models.Model):
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        # unique=True REMOVIDO ← Ahora permite valores duplicados
        verbose_name=_('Valor')
    )
    
    tipo = models.CharField(
        max_length=10,
        choices=TipoChoices.choices,
        verbose_name=_('Tipo')
    )
    
    class Meta:
        unique_together = ['valor', 'tipo']  # ← Nueva restricción compuesta
```

### ¿Qué hace `unique_together`?

La restricción `unique_together = ['valor', 'tipo']` significa:

- ✅ **PERMITIDO:** Billete de $1,000 + Moneda de $1,000
- ✅ **PERMITIDO:** Billete de $500 + Moneda de $500
- ❌ **NO PERMITIDO:** Dos billetes de $1,000
- ❌ **NO PERMITIDO:** Dos monedas de $1,000

### Migración Creada

Se generó automáticamente la migración:

```bash
python manage.py makemigrations caja
# Crea: caja/migrations/0004_alter_denominacionmoneda_valor_and_more.py
```

**Contenido de la migración:**
- Remueve índice `UNIQUE` del campo `valor`
- Crea nuevo índice compuesto `UNIQUE (valor, tipo)`

---

## 🚀 Aplicar en Producción

### Opción 1: Script Automatizado (Recomendado)

```bash
# 1. SSH al servidor
ssh hennesy@ubuntu-server-hennesy
# Contraseña: Comandos555123*

# 2. Navegar al proyecto
cd /ruta/a/renzzoelectricos

# 3. Ejecutar script automatizado
chmod +x fix_denominaciones_produccion.sh
sudo ./fix_denominaciones_produccion.sh
```

El script automáticamente:
- ✅ Hace `git pull` para obtener los cambios
- ✅ Ejecuta `migrate caja` para aplicar la migración
- ✅ Crea todas las denominaciones (billetes y monedas)
- ✅ Ejecuta `collectstatic` para actualizar archivos
- ✅ Reinicia el contenedor

### Opción 2: Comandos Manuales

```bash
# 1. SSH al servidor
ssh hennesy@ubuntu-server-hennesy

# 2. Actualizar código
cd /ruta/a/renzzoelectricos
git pull origin main

# 3. Encontrar contenedor
sudo docker ps | grep web

# 4. Aplicar migración
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 python manage.py migrate caja

# 5. Ejecutar script de denominaciones
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 python crear_denominaciones.py

# 6. Recolectar estáticos
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 python manage.py collectstatic --noinput

# 7. Reiniciar
sudo docker restart web-gg0wswocg8c4soc80kk88g8g-150356494831
```

---

## 🧪 Verificación

### En el Admin de Django

1. Navega a: `https://renzzoelectricos.com/admin/caja/denominacionmoneda/`
2. Verifica que existen:
   - ✅ **Moneda de $1,000**
   - ✅ **Billete de $1,000**
3. Intenta crear una nueva denominación:
   - ✅ Debería funcionar sin errores
   - ✅ No más error 500

### Verificación de Base de Datos

Verifica que la restricción única esté correctamente aplicada:

```python
# Dentro del contenedor de producción
python manage.py shell

from caja.models import DenominacionMoneda

# Ver todas las denominaciones
for d in DenominacionMoneda.objects.all().order_by('-valor', 'tipo'):
    print(f"{d.tipo:10s} ${d.valor:>10,.0f}")

# Salida esperada:
# BILLETE    $  100,000
# BILLETE    $   50,000
# BILLETE    $   20,000
# BILLETE    $   10,000
# BILLETE    $    5,000
# BILLETE    $    2,000
# BILLETE    $    1,000  ← Billete de $1,000
# MONEDA     $    1,000  ← Moneda de $1,000 (AHORA AMBOS EXISTEN)
# MONEDA     $      500
# MONEDA     $      200
# MONEDA     $      100
# MONEDA     $       50
```

---

## 📊 Denominaciones Colombianas Correctas

### 💵 Billetes (7 denominaciones)
- $100,000 (Cien mil pesos)
- $50,000 (Cincuenta mil pesos)
- $20,000 (Veinte mil pesos)
- $10,000 (Diez mil pesos)
- $5,000 (Cinco mil pesos)
- $2,000 (Dos mil pesos)
- **$1,000 (Mil pesos)** ← Existe como billete

### 🪙 Monedas (5 denominaciones)
- **$1,000 (Mil pesos)** ← También existe como moneda
- $500 (Quinientos pesos)
- $200 (Doscientos pesos)
- $100 (Cien pesos)
- $50 (Cincuenta pesos)

**Total: 12 denominaciones** (7 billetes + 5 monedas)

> **Nota:** En Colombia, $1,000 existe tanto en formato de **billete** como de **moneda**. Por eso era crítico permitir ambos en el sistema.

---

## 🔍 Troubleshooting

### ❌ Error: "UNIQUE constraint failed"

**Problema:** La migración falla porque ya existen registros duplicados.

**Solución:**
```python
# Shell de Django
python manage.py shell

from caja.models import DenominacionMoneda

# Verificar duplicados
duplicados = DenominacionMoneda.objects.values('valor').annotate(
    count=models.Count('id')
).filter(count__gt=1)

# Si hay duplicados, eliminar manualmente y volver a crear
```

### ❌ Error 500 persiste después de migración

**Causa:** Caché del navegador o archivos estáticos no actualizados.

**Solución:**
1. Ejecutar `collectstatic`:
   ```bash
   sudo docker exec web python manage.py collectstatic --noinput
   ```

2. Limpiar caché del navegador:
   - Chrome: `Ctrl + Shift + Delete`
   - O usar modo incógnito: `Ctrl + Shift + N`

3. Reiniciar contenedor:
   ```bash
   sudo docker restart web-gg0wswocg8c4soc80kk88g8g-150356494831
   ```

---

## 📚 Referencias

- **Archivo modificado:** `caja/models.py` (líneas 219-246)
- **Migración:** `caja/migrations/0004_alter_denominacionmoneda_valor_and_more.py`
- **Script de fix:** `fix_denominaciones_produccion.sh`
- **Django Docs:** [Constraints](https://docs.djangoproject.com/en/5.1/ref/models/options/#unique-together)

---

## 📝 Notas Técnicas

### Diferencia entre `unique` y `unique_together`

```python
# unique=True en un campo individual
valor = models.DecimalField(unique=True)
# SQL: CREATE UNIQUE INDEX ON denominacionmoneda (valor)
# Comportamiento: Solo puede haber UN registro con cada valor

# unique_together en Meta
class Meta:
    unique_together = ['valor', 'tipo']
# SQL: CREATE UNIQUE INDEX ON denominacionmoneda (valor, tipo)
# Comportamiento: Solo puede haber UN registro con cada COMBINACIÓN (valor+tipo)
```

### Impacto en la Base de Datos

**Antes:**
```sql
-- Índice único simple
CREATE UNIQUE INDEX denominacionmoneda_valor ON caja_denominacionmoneda(valor);
```

**Después:**
```sql
-- Índice único compuesto
CREATE UNIQUE INDEX denominacionmoneda_valor_tipo ON caja_denominacionmoneda(valor, tipo);
```

---

## ✅ Checklist de Implementación

- [x] Modificar modelo `DenominacionMoneda`
- [x] Crear migración `0004_alter_denominacionmoneda_valor_and_more.py`
- [x] Aplicar migración en local (desarrollo)
- [x] Crear script `fix_denominaciones_produccion.sh`
- [x] Commit y push a GitHub
- [ ] **SSH al servidor de producción** ← PENDIENTE
- [ ] **Ejecutar script de fix en producción** ← PENDIENTE
- [ ] **Verificar funcionamiento en admin** ← PENDIENTE
- [ ] **Crear denominaciones faltantes** ← PENDIENTE

---

**Última actualización:** 2 de Noviembre de 2025  
**Autor:** GitHub Copilot  
**Proyecto:** Renzzo Eléctricos - Sistema de Caja
