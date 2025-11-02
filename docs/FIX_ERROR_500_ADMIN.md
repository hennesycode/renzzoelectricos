# 🔧 Solución Error 500 en Admin Denominaciones

**Fecha:** 2 de Noviembre de 2025  
**Problema:** Error 500 al acceder a `/admin/caja/denominacionmoneda/`  
**Solución:** Admin mejorado con manejo de errores

---

## ⚡ Aplicar Fix en Producción (5 minutos)

### 1️⃣ SSH al Servidor

```bash
ssh hennesy@ubuntu-server-hennesy
# Password: Comandos555123*
```

### 2️⃣ Actualizar Código

```bash
cd /ruta/a/renzzoelectricos
git pull origin main
```

### 3️⃣ Reiniciar Contenedor

```bash
# Reiniciar (código Python se recarga automáticamente)
sudo docker restart web-gg0wswocg8c4soc80kk88g8g-150356494831

# Ver logs (Ctrl+C para salir)
sudo docker logs -f --tail=50 web-gg0wswocg8c4soc80kk88g8g-150356494831
```

### 4️⃣ Verificar en Navegador

1. Limpiar caché: `Ctrl + Shift + Delete`
2. O modo incógnito: `Ctrl + Shift + N`
3. Ir a: `https://renzzoelectricos.com/admin/caja/denominacionmoneda/`
4. **Debe cargar sin error 500** ✅

---

## 🔍 Si el Error Persiste

### Opción A: Diagnosticar el Problema

```bash
# Acceder al contenedor
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 bash

# Ejecutar diagnóstico
python diagnosticar_error_admin.py

# Si muestra errores específicos, copia el mensaje
```

### Opción B: Ver Logs Completos

```bash
# Buscar el traceback completo del error
sudo docker logs web-gg0wswocg8c4soc80kk88g8g-150356494831 2>&1 | grep -A 30 "Traceback"

# O ver últimas 100 líneas
sudo docker logs --tail=100 web-gg0wswocg8c4soc80kk88g8g-150356494831
```

### Opción C: Revisar Base de Datos

```bash
# Dentro del contenedor
sudo docker exec -it web-gg0wswocg8c4soc80kk88g8g-150356494831 bash

# Validar denominaciones
python validar_denominaciones.py

# Si hay problemas, recrear
python eliminar_todas_denominaciones.py  # Escribe: SI
python crear_denominaciones_correctas.py  # Escribe: SI
```

---

## 📝 Cambios Realizados

### Antes (Causaba error 500):
```python
def tipo_badge(self, obj):
    if obj.tipo == 'BILLETE':
        icon = '💵'
    else:
        icon = '🪙'
    return format_html('{} {}', icon, obj.get_tipo_display())
    # ↑ get_tipo_display() falla si tipo tiene valor inválido
```

### Después (Maneja errores):
```python
def tipo_badge(self, obj):
    try:
        if obj.tipo == 'BILLETE':
            icon = '💵'
            tipo_display = 'Billete'
        elif obj.tipo == 'MONEDA':
            icon = '🪙'
            tipo_display = 'Moneda'
        else:
            icon = '❓'
            tipo_display = obj.tipo
        return format_html('{} {}', icon, tipo_display)
    except Exception as e:
        return format_html('<span style="color: red;">Error: {}</span>', str(e))
```

### Mejoras:
- ✅ Manejo de errores con `try/except`
- ✅ No usa `get_tipo_display()` que puede fallar
- ✅ Muestra errores en rojo si hay problemas
- ✅ Añade campo `id` en `list_display` para debugging
- ✅ Casting explícito a `float()` en `valor_fmt`

---

## ✅ Resultado Esperado

Después de aplicar el fix:

1. **Admin carga correctamente:**
   - URL: `https://renzzoelectricos.com/admin/caja/denominacionmoneda/`
   - Lista con todas las denominaciones visible
   - Columnas: ID, Valor, Tipo, Estado, Orden

2. **Si hay datos corruptos:**
   - Se mostrarán en **rojo** con mensaje de error
   - Puedes identificar qué registro tiene problemas
   - Elimínalo manualmente o recrea denominaciones

3. **Modal "Abrir Caja":**
   - También debe funcionar correctamente
   - Endpoint `/caja/denominaciones/` devuelve JSON válido

---

## 🚨 Troubleshooting

### ❌ Error: "Server responded with a status of 500"

**Causa:** El error persiste después del fix.

**Solución:**
```bash
# 1. Verificar que el código se actualizó
sudo docker exec web-xxx cat /app/caja/admin.py | grep -A 5 "def tipo_badge"

# 2. Forzar recarga de código Python
sudo docker restart web-xxx

# 3. Verificar denominaciones
sudo docker exec -it web-xxx python validar_denominaciones.py
```

### ❌ Admin muestra errores en rojo

**Causa:** Hay registros con datos inválidos en la BD.

**Solución:**
```bash
# Ver qué registros tienen problemas
sudo docker exec -it web-xxx python diagnosticar_error_admin.py

# Recrear denominaciones limpias
sudo docker exec -it web-xxx bash
python eliminar_todas_denominaciones.py  # SI
python crear_denominaciones_correctas.py  # SI
exit
```

### ❌ Logs muestran "TemplateDoesNotExist"

**Causa:** Archivos estáticos no recolectados.

**Solución:**
```bash
sudo docker exec web-xxx python manage.py collectstatic --clear --noinput
sudo docker restart web-xxx
```

---

## 📞 Si Nada Funciona

Activar DEBUG temporalmente para ver el error completo:

```bash
# 1. Editar settings.py dentro del contenedor
sudo docker exec -it web-xxx bash
nano /app/config/settings.py

# 2. Cambiar DEBUG = False a DEBUG = True
# Guardar: Ctrl+O, Enter, Ctrl+X

# 3. Acceder al admin y ver el error completo en el navegador
# 4. NO OLVIDES volver a poner DEBUG = False después
```

---

**Última actualización:** 2 de Noviembre de 2025  
**Autor:** GitHub Copilot  
**Proyecto:** Renzzo Eléctricos
