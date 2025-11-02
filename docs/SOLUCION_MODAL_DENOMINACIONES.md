# 🪙 Solución: Modal de Abrir Caja Sin Denominaciones

## 📋 Problema Identificado

El usuario reportó que al hacer clic en "Abrir Caja", el modal aparece pero **NO muestra las denominaciones de billetes y monedas** como se esperaba. En su lugar, solo muestra campos vacíos sin la grilla de denominaciones.

### ✅ Estado Actual Verificado

1. **Denominaciones en Base de Datos**: ✅ Verificadas y presentes
   - 7 Billetes: $100,000, $50,000, $20,000, $10,000, $5,000, $2,000, $1,000
   - 4 Monedas: $500, $200, $100, $50
   
2. **Código Frontend**: ✅ Correcto (`caja/static/caja/js/abrir_ajax.js`)
3. **Código Backend**: ✅ Correcto (`caja/views.py` - función `obtener_denominaciones`)
4. **CSS**: ✅ Correcto (`caja/static/caja/css/caja-modern.css`)
5. **URLs**: ✅ Configuradas correctamente

## 🔍 Diagnóstico

El problema ocurre en **producción (renzzoelectricos.com)** pero NO en **localhost**. Esto sugiere:

1. Los archivos estáticos NO están actualizados en el servidor
2. El servidor necesita reinicio después de pull
3. Puede haber caché de navegador o CDN

## 🛠️ Solución Completa

### Paso 1: Actualizar Repositorio en Producción

```bash
# Conectarse al servidor (vía SSH o acceso directo)
cd /ruta/a/renzzoelectricos

# Hacer pull de los últimos cambios
git pull origin main

# Verificar que se descargaron los cambios
git log --oneline -5
```

### Paso 2: Ejecutar Script de Denominaciones

```bash
# Asegurarse de que las denominaciones están en la base de datos
python crear_denominaciones.py
```

**Salida esperada:**
```
🪙 Creando denominaciones de monedas y billetes colombianos...
------------------------------------------------------------
ℹ️  Billete ya existe: $100,000
ℹ️  Billete ya existe: $50,000
... (etc)
✅ Script completado exitosamente!
```

### Paso 3: Recolectar Archivos Estáticos

```bash
# IMPORTANTE: Recolectar archivos estáticos para que WhiteNoise los sirva
python manage.py collectstatic --noinput
```

**¿Por qué esto es crítico?**
- En producción, Django + WhiteNoise sirve archivos estáticos desde `staticfiles/`
- Los archivos JavaScript y CSS deben estar actualizados en esa carpeta
- El archivo `abrir_ajax.js` (que carga denominaciones) debe estar actualizado

### Paso 4: Reiniciar Servidor con Docker

```bash
# Reiniciar solo el contenedor web
docker-compose restart web

# O reiniciar todos los servicios
docker-compose down
docker-compose up -d

# Verificar logs
docker-compose logs -f web
```

### Paso 5: Limpiar Caché del Navegador

1. Abrir **renzzoelectricos.com** en el navegador
2. Presionar **Ctrl + Shift + Delete** (Windows) o **Cmd + Shift + Delete** (Mac)
3. Seleccionar:
   - ✅ Imágenes y archivos en caché
   - ✅ Cookies y otros datos del sitio
4. Hacer clic en **Limpiar datos**
5. Alternativamente, probar en **modo incógnito** (Ctrl + Shift + N)

### Paso 6: Verificar en Producción

1. Iniciar sesión en **https://renzzoelectricos.com**
2. Ir al dashboard de **Caja**
3. Hacer clic en **"Abrir Caja"**

**Resultado Esperado:**
```
✅ El modal debe mostrar:
   💵 BILLETES
   - $100,000 [ input ]
   - $50,000  [ input ]
   - $20,000  [ input ]
   ... (etc)
   
   🪙 MONEDAS
   - $500 [ input ]
   - $200 [ input ]
   ... (etc)
   
   💰 Total a Abrir
   $0
```

## 🐛 Troubleshooting

### Problema 1: El modal sigue sin mostrar denominaciones

**Verificar que el endpoint funciona:**

1. Abrir **Consola del Navegador** (F12)
2. Ir a la pestaña **Network** (Red)
3. Hacer clic en **"Abrir Caja"**
4. Buscar la petición a `/caja/denominaciones/`
5. Verificar la respuesta:

```json
{
  "success": true,
  "denominaciones": [
    {
      "id": 1,
      "valor": 100000.0,
      "tipo": "BILLETE",
      "label": "$100,000 (Billete)"
    },
    ...
  ]
}
```

**Si el endpoint retorna error 403 o 500:**
- Verificar que el usuario esté autenticado
- Verificar que el usuario sea **staff** o **superuser**
- Revisar logs del servidor: `docker-compose logs web`

### Problema 2: Error de permisos

```bash
# Verificar permisos del usuario en Django admin
# Ir a: https://renzzoelectricos.com/admin/users/customuser/

# O ejecutar script:
docker-compose exec web python check_user.py
```

**El usuario debe tener:**
- ✅ `is_staff = True` o `is_superuser = True`
- ✅ Permiso: `users.can_view_caja` o `users.can_manage_caja`

### Problema 3: JavaScript no se está cargando

**Verificar en Consola del Navegador (F12):**

```javascript
// Ejecutar en la consola:
console.log(window.CAJA_URLS);

// Debe retornar:
{
  abrir: "/caja/abrir/",
  cerrar: "/caja/cerrar/",
  denominaciones: "/caja/denominaciones/",
  ... (etc)
}
```

**Si retorna `undefined`:**
1. Los archivos estáticos NO están actualizados
2. Ejecutar nuevamente: `python manage.py collectstatic --noinput`
3. Reiniciar servidor: `docker-compose restart web`

### Problema 4: Error en la petición AJAX

**Consola del Navegador muestra error:**

```
Failed to fetch denominaciones
```

**Solución:**
1. Verificar que el usuario esté logueado
2. Verificar CSRF token en las cookies (F12 → Application → Cookies)
3. Verificar que `CSRF_TRUSTED_ORIGINS` incluya el dominio:
   ```python
   # config/settings.py
   CSRF_TRUSTED_ORIGINS = [
       'https://renzzoelectricos.com',
       'https://www.renzzoelectricos.com'
   ]
   ```

## 📝 Comandos Rápidos de Verificación

```bash
# 1. Verificar denominaciones en BD
docker-compose exec web python -c "
from caja.models import DenominacionMoneda
print(f'Denominaciones activas: {DenominacionMoneda.objects.filter(activo=True).count()}')
"

# 2. Verificar archivos estáticos
docker-compose exec web ls -la staticfiles/caja/js/abrir_ajax.js

# 3. Verificar permisos de usuario
docker-compose exec web python check_user.py

# 4. Ver logs en tiempo real
docker-compose logs -f web
```

## 🔄 Flujo Completo de Actualización

```bash
# En el servidor de producción
cd /ruta/a/renzzoelectricos

# 1. Pull de cambios
git pull origin main

# 2. Crear/verificar denominaciones
docker-compose exec web python crear_denominaciones.py

# 3. Recolectar estáticos (CRÍTICO)
docker-compose exec web python manage.py collectstatic --noinput

# 4. Reiniciar servicios
docker-compose restart web

# 5. Verificar logs
docker-compose logs --tail=50 web

# 6. Limpiar caché del navegador y probar
```

## ✅ Checklist Final

- [ ] Git pull ejecutado
- [ ] Denominaciones verificadas en BD
- [ ] `collectstatic` ejecutado sin errores
- [ ] Servidor reiniciado (docker-compose restart web)
- [ ] Logs sin errores
- [ ] Caché del navegador limpiado
- [ ] Modal muestra denominaciones correctamente
- [ ] Cálculo en tiempo real funciona (al ingresar cantidades)
- [ ] Botón "Abrir Caja" funciona sin errores

## 📞 Soporte Adicional

Si después de seguir todos los pasos el problema persiste:

1. **Capturar logs del servidor:**
   ```bash
   docker-compose logs web > logs_caja.txt
   ```

2. **Capturar consola del navegador:**
   - F12 → Console → Captura de pantalla del error

3. **Verificar respuesta del endpoint:**
   ```bash
   # Desde el servidor
   docker-compose exec web python test_denominaciones.py
   ```

---

**Última actualización:** 2 de noviembre de 2025  
**Versión:** 1.0  
**Estado:** ✅ Solución Completa Documentada
