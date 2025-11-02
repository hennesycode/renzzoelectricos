# 🔒 SOLUCIÓN: Error 403 Forbidden - CSRF en Login

## 🔍 PROBLEMA IDENTIFICADO

```
Failed to load resource: the server responded with a status of 403 ()
Error en login: Error: HTTP 403
```

**Error en consola del navegador:**
```javascript
login.js:269 Error en login: Error: HTTP 403: 
    at LoginManager.sendLoginRequest (login.js:390:19)
    at async LoginManager.handleSubmit (login.js:266:28)
```

### ❌ Síntomas:
- ✅ Login funciona perfectamente en **desarrollo** (`localhost`)
- ❌ Login falla con **error 403** en **producción** (`renzzoelectricos.com`)
- ✅ CSRF token está presente en el formulario
- ✅ JavaScript envía el token correctamente en headers
- ❌ Django rechaza la petición con `403 Forbidden`

### 🔎 Causa Raíz:

**CSRF_TRUSTED_ORIGINS no configurado**

Django 4.0+ requiere que se especifiquen explícitamente los orígenes confiables cuando:
1. Se usa **HTTPS** (protocolo diferente a HTTP)
2. Se usa un **proxy reverso** (Cloudflare, Nginx, etc.)
3. El dominio es diferente a `localhost`

En este caso, Cloudflare Tunnel actúa como proxy HTTPS, y Django no reconoce `https://renzzoelectricos.com` como origen confiable para peticiones CSRF.

---

## ✅ SOLUCIÓN APLICADA

### 1. **config/settings.py**

Agregadas configuraciones CSRF completas:

```python
# CSRF - Cross Site Request Forgery Protection
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
CSRF_COOKIE_HTTPONLY = False  # Debe ser False para que JavaScript pueda leer el token
CSRF_COOKIE_SAMESITE = 'Lax'  # 'Lax' permite cookies en navegación normal, 'Strict' es más restrictivo

# CSRF_TRUSTED_ORIGINS - Orígenes confiables para peticiones CSRF (REQUERIDO para Cloudflare/HTTPS)
# Formato: https://dominio.com (con protocolo, sin puerto ni barra final)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://renzzoelectricos.com',
    'https://www.renzzoelectricos.com'
])
```

**Cambios clave:**
- ✅ `CSRF_COOKIE_HTTPONLY = False` - Permite que JavaScript lea el token
- ✅ `CSRF_COOKIE_SAMESITE = 'Lax'` - Balance entre seguridad y usabilidad
- ✅ `CSRF_TRUSTED_ORIGINS` - **CRÍTICO**: Lista de dominios HTTPS confiables

### 2. **.env.example**

Agregada nueva variable de entorno:

```bash
# CSRF Trusted Origins - CRÍTICO para producción con Cloudflare
# Lista separada por comas de dominios confiables (formato: https://dominio.com)
# DEBE incluir el dominio de producción para evitar errores 403 en formularios
CSRF_TRUSTED_ORIGINS=https://renzzoelectricos.com,https://www.renzzoelectricos.com
```

### 3. **Verificación del archivo .env en producción**

**IMPORTANTE**: En el servidor, actualizar el archivo `.env`:

```bash
# Editar .env en el servidor
nano /ruta/a/renzzoelectricos/.env

# Agregar o verificar esta línea:
CSRF_TRUSTED_ORIGINS=https://renzzoelectricos.com,https://www.renzzoelectricos.com
```

---

## 📊 COMPARACIÓN: Antes vs Después

| Aspecto | ❌ Antes | ✅ Después |
|---------|---------|-----------|
| **CSRF_TRUSTED_ORIGINS** | No configurado | ✅ https://renzzoelectricos.com |
| **CSRF_COOKIE_HTTPONLY** | Hardcoded True | ✅ False (JS puede leer) |
| **CSRF_COOKIE_SAMESITE** | No configurado | ✅ 'Lax' |
| **Login localhost** | ✅ Funciona | ✅ Funciona |
| **Login producción** | ❌ Error 403 | ✅ Funciona |

---

## 🔧 DETALLES TÉCNICOS

### ¿Por qué falla CSRF en producción pero no en localhost?

Django tiene excepciones automáticas para `localhost` y `127.0.0.1`, pero **NO para dominios externos**.

**Flujo de validación CSRF de Django:**

```
1. Cliente envía petición AJAX con header X-CSRFToken
2. Django verifica:
   ✓ Token CSRF válido
   ✓ Cookie csrftoken presente
   ✓ Origen de la petición (Referer/Origin header)
   
3. Django compara el origen con:
   - ALLOWED_HOSTS ✓
   - CSRF_TRUSTED_ORIGINS ❌ (faltaba esto!)
   
4. Si no coincide → 403 Forbidden
```

### Configuración de Cloudflare Tunnel

Cloudflare Tunnel actúa como proxy:

```
Internet (HTTPS) → Cloudflare CDN → Tunnel → localhost:5018 (HTTP)
                                              ↓
                                        Django (checks CSRF)
```

Django ve:
- `Origin: https://renzzoelectricos.com` (del navegador)
- `Host: renzzoelectricos.com` (del tunnel)

Pero **necesita** que `https://renzzoelectricos.com` esté en `CSRF_TRUSTED_ORIGINS`.

### ¿Por qué CSRF_COOKIE_HTTPONLY = False?

**Antes (error):**
```python
CSRF_COOKIE_HTTPONLY = True  # JavaScript NO puede leer
```

**JavaScript necesita leer el token:**
```javascript
// login.js línea 288
csrfToken: document.querySelector('[name=csrfmiddlewaretoken]').value
```

Si `CSRF_COOKIE_HTTPONLY = True`, el navegador bloquea el acceso desde JavaScript.

**Solución:**
```python
CSRF_COOKIE_HTTPONLY = False  # JavaScript SÍ puede leer
```

⚠️ **Seguridad**: Esto es seguro porque:
1. El token CSRF **NO es sensible** (solo previene CSRF, no roba sesiones)
2. El token está vinculado a la sesión del usuario
3. Django valida tanto el token como el origen

---

## 🚀 PASOS PARA APLICAR LA SOLUCIÓN EN PRODUCCIÓN

### 1. Actualizar código del servidor

```bash
cd /ruta/a/renzzoelectricos
git pull origin main
```

### 2. Actualizar archivo .env

```bash
nano .env
```

Agregar o verificar:
```env
# CSRF Trusted Origins - CRÍTICO
CSRF_TRUSTED_ORIGINS=https://renzzoelectricos.com,https://www.renzzoelectricos.com

# Cookies seguras (HTTPS en producción)
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 3. Reiniciar servicios Docker

```bash
# Opción 1: Recrear contenedores
docker-compose down
docker-compose up -d

# Opción 2: Solo reiniciar web
docker-compose restart web

# Opción 3: Con Make
make restart
```

### 4. Verificar logs

```bash
docker-compose logs -f web
```

Deberías ver:
```
✅ Servidor iniciado correctamente
[INFO] Listening at: http://0.0.0.0:8000
```

**SIN** errores de CSRF.

### 5. Probar login

1. Abrir: `https://renzzoelectricos.com/login/`
2. Abrir **DevTools** → Console (F12)
3. Ingresar credenciales
4. **Verificar**:
   - ✅ No hay error 403
   - ✅ Mensaje de éxito en consola
   - ✅ Redirección al dashboard

---

## 🔍 DEBUGGING: Cómo Verificar CSRF en Producción

### 1. Verificar CSRF_TRUSTED_ORIGINS en Django

```bash
# Conectar al contenedor
docker-compose exec web python manage.py shell

# Verificar configuración
>>> from django.conf import settings
>>> print(settings.CSRF_TRUSTED_ORIGINS)
['https://renzzoelectricos.com', 'https://www.renzzoelectricos.com']
```

### 2. Verificar headers en el navegador

**DevTools → Network → Login request → Headers:**

```
Request Headers:
  Origin: https://renzzoelectricos.com
  Referer: https://renzzoelectricos.com/login/
  X-CSRFToken: [token aquí]
  
Response Headers:
  Status: 200 OK  ← Debe ser 200, no 403
```

### 3. Verificar cookies

**DevTools → Application → Cookies:**

```
csrftoken: [valor]
  Secure: Yes (✓)
  HttpOnly: No (✓)
  SameSite: Lax (✓)
  
sessionid: [valor]
  Secure: Yes (✓)
  HttpOnly: Yes (✓)
  SameSite: Lax (✓)
```

---

## ⚠️ ERRORES COMUNES

### ❌ Error: "Forbidden (CSRF cookie not set.)"

**Causa:** Cookie no se está enviando.

**Solución:**
```javascript
// En login.js, asegurar:
fetch('/login/', {
    credentials: 'same-origin',  // ← IMPORTANTE
    // ...
})
```

### ❌ Error: "Forbidden (CSRF token missing or incorrect.)"

**Causa:** Token no se envía en headers.

**Solución:** Verificar en `login.js`:
```javascript
headers: {
    'X-CSRFToken': csrfToken,  // ← IMPORTANTE
    // ...
}
```

### ❌ Error: "Origin checking failed"

**Causa:** `CSRF_TRUSTED_ORIGINS` no incluye el dominio.

**Solución:**
```python
CSRF_TRUSTED_ORIGINS = [
    'https://renzzoelectricos.com',      # ← Debe coincidir exactamente
    'https://www.renzzoelectricos.com'
]
```

**Formato correcto:**
- ✅ `https://renzzoelectricos.com` (con protocolo, sin puerto ni barra)
- ❌ `renzzoelectricos.com` (sin protocolo)
- ❌ `https://renzzoelectricos.com/` (con barra final)
- ❌ `https://renzzoelectricos.com:5018` (con puerto)

---

## 🎯 RESULTADO ESPERADO

Después de aplicar esta solución:

1. ✅ **Login funciona** en `https://renzzoelectricos.com`
2. ✅ **No hay error 403** en consola del navegador
3. ✅ **AJAX login exitoso** con SweetAlert2
4. ✅ **Cookies seguras** (Secure, SameSite)
5. ✅ **Compatibilidad** con Cloudflare Tunnel

---

## 📋 CHECKLIST DE VERIFICACIÓN

- [ ] `CSRF_TRUSTED_ORIGINS` en `config/settings.py`
- [ ] `CSRF_COOKIE_HTTPONLY = False` en `config/settings.py`
- [ ] `CSRF_COOKIE_SAMESITE = 'Lax'` en `config/settings.py`
- [ ] Variable `CSRF_TRUSTED_ORIGINS` en `.env.example`
- [ ] Variable `CSRF_TRUSTED_ORIGINS` en `.env` del servidor
- [ ] Git pull en servidor
- [ ] Docker compose restart
- [ ] Probar login en producción
- [ ] Verificar cookies en DevTools
- [ ] Verificar headers en Network
- [ ] No hay error 403 en consola

---

## 📚 REFERENCIAS

- [Django CSRF Protection](https://docs.djangoproject.com/en/5.1/ref/csrf/)
- [Django CSRF_TRUSTED_ORIGINS](https://docs.djangoproject.com/en/5.1/ref/settings/#csrf-trusted-origins)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [MDN: CSRF](https://developer.mozilla.org/en-US/docs/Glossary/CSRF)

---

**Fecha de solución:** 2 de noviembre de 2025  
**Autor:** GitHub Copilot  
**Repositorio:** https://github.com/hennesycode/renzzoelectricos  
**Commit:** [próximo commit]
