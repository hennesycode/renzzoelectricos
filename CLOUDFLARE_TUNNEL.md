# 🌐 Configuración Cloudflare Tunnel - Renzzo Eléctricos

## 📋 Resumen de Configuración

Este proyecto está configurado para funcionar con **Cloudflare Tunnel** que conecta el puerto **5018** local al dominio **renzzoelectricos.com**.

### 🔌 Arquitectura

```
Internet
   ↓
Cloudflare CDN + Tunnel
   ↓
renzzoelectricos.com → Detecta Puerto 5018
   ↓
Docker Container (Web)
   ↓ Puerto 5018:8000
Django + Gunicorn (puerto interno 8000)
   ↓
MySQL (puerto 3306)
```

## ⚙️ Configuración Actual

### Puerto Expuesto
- **Puerto Externo:** 5018 (para Cloudflare Tunnel)
- **Puerto Interno:** 8000 (Gunicorn dentro del contenedor)
- **Mapeo:** `5018:8000` en docker-compose.yml

### Dominio
- **Dominio Principal:** renzzoelectricos.com
- **Alternativo:** www.renzzoelectricos.com
- **Local:** localhost (para desarrollo)

### Servicios Activos
- ✅ **Web (Django + Gunicorn)** - Puerto 5018
- ✅ **MySQL** - Puerto 3306 (interno, no expuesto)
- ✅ **Redis** - Puerto 6379 (interno, no expuesto)
- ❌ **Nginx** - Deshabilitado (Cloudflare maneja el tráfico)

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
cp .env.example .env
nano .env
```

**Cambiar:**
```env
# IMPORTANTE: Cloudflare Tunnel detecta puerto 5018
ALLOWED_HOSTS=localhost,127.0.0.1,renzzoelectricos.com,www.renzzoelectricos.com

# Puerto para Cloudflare Tunnel (NO cambiar)
WEB_PORT=5018
```

### 2. Iniciar Servicios

```bash
# Opción 1: Make (recomendado)
make init

# Opción 2: Docker Compose
docker-compose build
docker-compose up -d
```

### 3. Verificar

```bash
# Ver logs
docker-compose logs -f web

# Verificar que está escuchando en puerto 5018
docker-compose ps
```

## 🌍 Acceso

### Desde Internet (vía Cloudflare Tunnel):
- **Aplicación:** https://renzzoelectricos.com
- **Admin:** https://renzzoelectricos.com/admin
- **Dashboard:** https://renzzoelectricos.com/dashboard

### Desde Localhost (desarrollo):
- **Aplicación:** http://localhost:5018
- **Admin:** http://localhost:5018/admin
- **Dashboard:** http://localhost:5018/dashboard

## 🔒 Seguridad

### SSL/TLS
- ✅ **Gestionado por Cloudflare** (automático)
- ✅ **Certificado:** Cloudflare Universal SSL
- ✅ **HTTPS:** Forzado por Cloudflare

### Configuración Django para Cloudflare

Asegúrate de tener en tu `settings.py`:

```python
# Confiar en headers de Cloudflare
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# En producción
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Cloudflare maneja esto
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

### Headers de Seguridad (Cloudflare)

Configurar en Cloudflare Dashboard → SSL/TLS → Origin Server:
- ✅ Always Use HTTPS
- ✅ Automatic HTTPS Rewrites
- ✅ Minimum TLS Version: 1.2

## 🔄 Actualizaciones

### Actualizar la Aplicación

```bash
# Pull cambios
git pull origin main

# Redesplegar
make deploy

# O manualmente:
docker-compose build
docker-compose down
docker-compose up -d
```

### Reiniciar Servicios

```bash
make restart

# O manualmente:
docker-compose restart
```

## 📊 Monitoreo

### Ver Estado

```bash
# Estado de contenedores
docker-compose ps

# Logs en tiempo real
docker-compose logs -f

# Solo logs de Django
docker-compose logs -f web
```

### Verificar Puerto

```bash
# Verificar que el puerto 5018 está escuchando
netstat -an | grep 5018

# O en PowerShell:
Get-NetTCPConnection -LocalPort 5018
```

### Health Check

```bash
# Desde localhost
curl http://localhost:5018/admin/login/

# Verificar base de datos
docker-compose exec web python manage.py check --database default
```

## 🐛 Troubleshooting

### El sitio no carga (502/503)

1. **Verificar que el contenedor está corriendo:**
```bash
docker-compose ps
```

2. **Ver logs de errores:**
```bash
docker-compose logs web | tail -50
```

3. **Reiniciar servicios:**
```bash
docker-compose restart
```

### Error de conexión a base de datos

```bash
# Verificar MySQL
docker-compose logs db

# Verificar conexión
docker-compose exec web python manage.py check --database default
```

### Puerto 5018 no responde

1. **Verificar que el puerto está mapeado:**
```bash
docker-compose ps
# Debe mostrar: 0.0.0.0:5018->8000/tcp
```

2. **Verificar desde el host:**
```bash
curl http://localhost:5018/admin/login/
```

3. **Verificar Cloudflare Tunnel:**
```bash
# En el servidor donde corre cloudflared
systemctl status cloudflared
# O
cloudflared tunnel info
```

### Archivos estáticos no cargan

```bash
# Recolectar estáticos
docker-compose exec web python manage.py collectstatic --noinput

# Verificar permisos
docker-compose exec web ls -la /app/staticfiles
```

## 📝 Notas Importantes

### ⚠️ Nginx está Deshabilitado
- Cloudflare Tunnel maneja todo el tráfico HTTP/HTTPS
- Django sirve archivos estáticos vía WhiteNoise
- No necesitas configurar SSL manualmente

### ⚠️ Puerto 5018 es Fijo
- El túnel de Cloudflare detecta específicamente el puerto **5018**
- **NO cambiar** este puerto sin actualizar Cloudflare Tunnel
- Para cambiar, actualiza también la configuración del túnel

### ⚠️ WhiteNoise Sirve Estáticos
- Django sirve archivos estáticos en producción vía WhiteNoise
- `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`
- Los archivos se comprimen automáticamente (Gzip/Brotli)

## 🔧 Configuración Avanzada

### Habilitar Nginx (Opcional)

Si quieres usar Nginx como proxy adicional:

1. **Descomentar sección nginx en `docker-compose.yml`**

2. **Cambiar puerto de Django:**
```yaml
web:
  ports:
    - "8000:8000"  # Interno, no exponer
```

3. **Configurar Nginx para escuchar en 5018:**
```nginx
server {
    listen 5018;
    # ... resto de configuración
}
```

4. **Reiniciar:**
```bash
docker-compose up -d
```

### Múltiples Dominios

Si tienes más dominios apuntando al mismo túnel:

```env
ALLOWED_HOSTS=localhost,renzzoelectricos.com,www.renzzoelectricos.com,otro-dominio.com
```

### Cache de Cloudflare

Configurar en Cloudflare Dashboard → Caching:
- **Browser Cache TTL:** 4 horas
- **Crawler Hints:** Activado
- **Cache Static Content:** Activado

**Cache Rules:**
```
URL Path: /static/*
Cache Level: Cache Everything
Edge TTL: 1 month
```

## 📚 Recursos

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Django WhiteNoise](http://whitenoise.evans.io/)
- [Gunicorn Deployment](https://docs.gunicorn.org/en/stable/deploy.html)

## 📞 Soporte

Para problemas relacionados con:
- **Docker:** Ver `DOCKER.md`
- **Despliegue:** Ver `DEPLOY.md`
- **Configuración general:** Ver `README.md`

---

**🔌 Renzzo Eléctricos**  
🌐 renzzoelectricos.com (Puerto 5018 → Cloudflare Tunnel)
