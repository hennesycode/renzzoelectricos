# 🐳 Configuración Docker - Renzzo Eléctricos

## 📁 Archivos Creados

### Archivos principales:
1. **Dockerfile** - Imagen Docker de la aplicación
2. **docker-compose.yml** - Configuración de producción
3. **docker-compose.dev.yml** - Configuración de desarrollo
4. **entrypoint.sh** - Script de inicialización con verificaciones
5. **.env.example** - Plantilla de variables de entorno
6. **.dockerignore** - Archivos a ignorar en la imagen
7. **Makefile** - Comandos útiles
8. **DEPLOY.md** - Guía completa de despliegue
9. **quickstart.sh** - Script de inicio rápido
10. **healthcheck.py** - Script de verificación de salud

### Configuraciones:
- **docker/mysql/my.cnf** - Configuración de MySQL
- **docker/nginx/nginx.conf** - Configuración principal de Nginx
- **docker/nginx/conf.d/renzzo.conf** - Configuración del sitio

## 🚀 Inicio Rápido

### Opción 1: Script Automático

```bash
chmod +x quickstart.sh
./quickstart.sh
```

### Opción 2: Make (Recomendado)

```bash
# Inicializar todo el proyecto
make init

# Ver todos los comandos disponibles
make help
```

### Opción 3: Docker Compose Manual

```bash
# 1. Copiar variables de entorno
cp .env.example .env

# 2. Editar .env con tus valores
nano .env

# 3. Construir e iniciar
docker-compose build
docker-compose up -d

# 4. Ver logs
docker-compose logs -f
```

## 📊 Servicios Incluidos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **web** | 5018 → 8000 | Django + Gunicorn (expuesto para Cloudflare Tunnel) |
| **db** | 3306 | MySQL 8.0 (interno, no expuesto) |
| **redis** | 6379 | Cache y cola de tareas (interno, no expuesto) |

**📝 Nota:** Nginx está deshabilitado porque Cloudflare Tunnel maneja el tráfico directamente al puerto 5018.

## 🔐 Credenciales por Defecto

**⚠️ CAMBIAR EN PRODUCCIÓN**

### Base de Datos:
- **Database:** renzzoelectricos_db
- **User:** renzzo_admin
- **Password:** RenzzoEl3ctr!c0s2024#Secure
- **Root Password:** R00tRenzz0!2024#MySQL

### Django Admin:
- **Usuario:** admin
- **Email:** admin@renzzoelectricos.com
- **Password:** Admin123!RenzzoElectricos

### Redis:
- **Password:** RenzzoR3d!s2024

## 📦 Lo que hace el entrypoint.sh automáticamente:

1. ✅ **Verifica conexión a base de datos**
   - Espera hasta 30 intentos (60 segundos)
   - Verifica que MySQL esté aceptando conexiones

2. ✅ **Ejecuta migraciones**
   - `python manage.py migrate --noinput`
   - Muestra el progreso de cada migración

3. ✅ **Recolecta archivos estáticos**
   - `python manage.py collectstatic --noinput --clear`
   - Copia todos los archivos a /app/staticfiles

4. ✅ **Compila traducciones**
   - `python manage.py compilemessages`
   - Solo si existe directorio locale/

5. ✅ **Crea superusuario**
   - Solo si no existe
   - Usa variables DJANGO_SUPERUSER_*

6. ✅ **Verifica configuración**
   - `python manage.py check --deploy`
   - Muestra advertencias de seguridad

## 🔧 Comandos Make Disponibles

```bash
make help              # Ver todos los comandos
make init              # Inicializar proyecto completo
make build             # Construir imágenes
make up                # Iniciar servicios
make down              # Detener servicios
make restart           # Reiniciar servicios
make logs              # Ver logs
make logs-web          # Ver logs de Django
make logs-db           # Ver logs de MySQL
make shell             # Shell en contenedor web
make django-shell      # Django shell
make migrate           # Ejecutar migraciones
make makemigrations    # Crear migraciones
make collectstatic     # Recolectar estáticos
make createsuperuser   # Crear superusuario
make backup-db         # Backup de base de datos
make restore-db        # Restaurar backup
make clean             # Limpiar todo
make deploy            # Desplegar cambios
make ps                # Ver estado de contenedores
make stats             # Ver uso de recursos
```

## � URLs de Acceso

**Desde Internet (vía Cloudflare Tunnel):**
- **Aplicación:** https://renzzoelectricos.com
- **Admin Django:** https://renzzoelectricos.com/admin
- **Dashboard Oscar:** https://renzzoelectricos.com/dashboard

**Desde Localhost (desarrollo):**
- **Aplicación:** http://localhost:5018
- **Admin Django:** http://localhost:5018/admin
- **Dashboard Oscar:** http://localhost:5018/dashboard

**📝 Nota:** Cloudflare Tunnel detecta automáticamente el puerto 5018 y lo conecta a renzzoelectricos.com con SSL incluido.

## 📝 Variables de Entorno Importantes

### Django:
- `DEBUG` - Modo debug (False en producción)
- `SECRET_KEY` - Clave secreta (generar única)
- `ALLOWED_HOSTS` - Dominios permitidos

### Base de Datos:
- `DATABASE_NAME` - Nombre de la BD
- `DATABASE_USER` - Usuario de MySQL
- `DATABASE_PASSWORD` - Contraseña
- `DATABASE_HOST` - Host (usar 'db' en Docker)
- `DATABASE_PORT` - Puerto (3306)

### Superusuario:
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

## 🔄 Flujo de Actualización

```bash
# 1. Pull de cambios
git pull origin main

# 2. Reconstruir y redesplegar
make deploy

# Esto ejecuta:
# - docker-compose build
# - docker-compose down
# - docker-compose up -d
# - collectstatic
```

## 💾 Backups

### Crear backup:
```bash
make backup-db
# Se guarda en: backups/mysql/backup_YYYYMMDD_HHMMSS.sql
```

### Restaurar backup:
```bash
make restore-db FILE=backups/mysql/backup_20250102_120000.sql
```

### Backup manual:
```bash
docker-compose exec db mysqldump -u root -p renzzoelectricos_db > backup.sql
```

## 🔒 Seguridad en Producción

### 1. Cambiar todas las contraseñas:
```bash
# Generar SECRET_KEY nueva:
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Cambiar en .env:
# - SECRET_KEY
# - DATABASE_PASSWORD
# - DATABASE_ROOT_PASSWORD
# - DJANGO_SUPERUSER_PASSWORD
# - REDIS_PASSWORD
```

### 2. Configurar SSL/HTTPS:
```bash
# Obtener certificado SSL:
sudo certbot certonly --standalone -d renzzoelectricos.com

# Copiar certificados:
cp /etc/letsencrypt/live/renzzoelectricos.com/fullchain.pem docker/nginx/ssl/
cp /etc/letsencrypt/live/renzzoelectricos.com/privkey.pem docker/nginx/ssl/

# Descomentar configuración SSL en:
# docker/nginx/conf.d/renzzo.conf

# Actualizar .env:
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 3. Configurar firewall:
```bash
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### 4. Limitar acceso a base de datos:
```bash
# La base de datos solo debe ser accesible desde la red interna de Docker
# No exponer puerto 3306 públicamente (comentar en docker-compose.yml)
```

## 🐛 Troubleshooting

### Error: Cannot connect to MySQL
```bash
# Verificar que el servicio esté corriendo:
docker-compose ps db

# Ver logs:
make logs-db

# Reiniciar servicio:
docker-compose restart db
```

### Error: Static files not loading
```bash
# Recolectar estáticos:
make collectstatic

# Reiniciar nginx:
docker-compose restart nginx
```

### Error: Permission denied
```bash
# Dar permisos a entrypoint:
chmod +x entrypoint.sh

# Reconstruir:
make build
```

### Ver estado de health checks:
```bash
docker-compose ps
```

## 📊 Monitoreo

### Ver logs en tiempo real:
```bash
make logs              # Todos los servicios
make logs-web          # Solo Django
make logs-db           # Solo MySQL
```

### Ver uso de recursos:
```bash
make stats
```

### Ejecutar health check manual:
```bash
docker-compose exec web python healthcheck.py
```

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────┐
│                   NGINX (:80, :443)             │
│           (Proxy Reverso + Estáticos)           │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│            Django + Gunicorn (:8000)            │
│        (Oscar E-commerce + Módulo Caja)         │
└────────────┬────────────────────┬────────────────┘
             │                    │
             ↓                    ↓
┌─────────────────────┐  ┌──────────────────────┐
│   MySQL 8.0 (:3306) │  │  Redis (:6379)       │
│   (Base de Datos)   │  │  (Cache/Colas)       │
└─────────────────────┘  └──────────────────────┘
```

## ✅ Checklist de Producción

- [ ] Copiar .env.example a .env
- [ ] Cambiar SECRET_KEY
- [ ] Cambiar todas las contraseñas
- [ ] Configurar ALLOWED_HOSTS con dominio real
- [ ] Configurar SSL/HTTPS
- [ ] DEBUG=False
- [ ] Configurar email (SMTP)
- [ ] Configurar backups automáticos
- [ ] Configurar monitoreo (Sentry opcional)
- [ ] Configurar firewall
- [ ] Probar restauración de backups
- [ ] Documentar credenciales de forma segura

## 📞 Soporte

Para más información, consultar:
- `DEPLOY.md` - Guía detallada de despliegue
- `README.md` - Documentación general del proyecto

---

**🔌 Renzzo Eléctricos - Sistema de Gestión Comercial**
