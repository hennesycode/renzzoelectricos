# 🔌 Renzzo Eléctricos - Despliegue con Docker

Sistema de gestión comercial con Django Oscar y módulo de caja integrado.

## 📋 Requisitos Previos

- Docker 20.10+
- Docker Compose 2.0+
- Git

## 🚀 Despliegue Rápido (Producción)

### 1. Clonar el repositorio

```bash
git clone https://github.com/hennesycode/renzzoelectricos.git
cd renzzoelectricos
```

### 2. Configurar variables de entorno

Copiar el archivo de ejemplo y editarlo con tus valores:

```bash
cp .env.example .env
```

**⚠️ IMPORTANTE:** Editar `.env` y cambiar:
- `SECRET_KEY` - Generar una clave secreta única
- `DATABASE_PASSWORD` - Contraseña segura para la base de datos
- `DATABASE_ROOT_PASSWORD` - Contraseña segura para root
- `DJANGO_SUPERUSER_PASSWORD` - Contraseña del administrador
- `ALLOWED_HOSTS` - Dominios de tu servidor

### 3. Generar SECRET_KEY segura

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 4. Inicializar el proyecto

```bash
# Opción 1: Usando Makefile (recomendado)
make init

# Opción 2: Comandos manuales
docker-compose build
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

### 5. Verificar que todo funciona

```bash
# Ver logs
docker-compose logs -f

# Ver estado de servicios
docker-compose ps
```

## 🌐 Acceder a la Aplicación

- **Aplicación:** http://localhost (o tu dominio)
- **Admin Django:** http://localhost/admin
- **Dashboard Oscar:** http://localhost/dashboard

**Credenciales por defecto:**
- Usuario: `admin`
- Email: `admin@renzzoelectricos.com`
- Contraseña: La que configuraste en `DJANGO_SUPERUSER_PASSWORD`

## 📦 Comandos Útiles (Makefile)

```bash
make help              # Ver todos los comandos disponibles
make build             # Construir imágenes
make up                # Iniciar servicios
make down              # Detener servicios
make restart           # Reiniciar servicios
make logs              # Ver logs de todos los servicios
make logs-web          # Ver logs solo de la aplicación
make shell             # Abrir shell en contenedor web
make django-shell      # Abrir Django shell
make migrate           # Ejecutar migraciones
make makemigrations    # Crear migraciones
make collectstatic     # Recolectar archivos estáticos
make createsuperuser   # Crear superusuario adicional
make backup-db         # Hacer backup de la base de datos
make clean             # Limpiar todo (¡cuidado!)
make deploy            # Desplegar cambios
```

## 🔄 Actualizar la Aplicación

```bash
# Pull de últimos cambios
git pull origin main

# Redesplegar
make deploy
```

## 🗄️ Backups

### Crear backup de la base de datos

```bash
make backup-db
```

Los backups se guardan en `backups/mysql/backup_YYYYMMDD_HHMMSS.sql`

### Restaurar backup

```bash
make restore-db FILE=backups/mysql/backup_20250102_120000.sql
```

## 🔒 Seguridad en Producción

### 1. Configurar SSL/HTTPS

1. Obtener certificados SSL (Let's Encrypt recomendado):
```bash
# Con Certbot
sudo certbot certonly --standalone -d renzzoelectricos.com
```

2. Copiar certificados a `docker/nginx/ssl/`:
```bash
cp /etc/letsencrypt/live/renzzoelectricos.com/fullchain.pem docker/nginx/ssl/
cp /etc/letsencrypt/live/renzzoelectricos.com/privkey.pem docker/nginx/ssl/
```

3. Descomentar configuración SSL en `docker/nginx/conf.d/renzzo.conf`

4. Actualizar `.env`:
```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 2. Cambiar todas las contraseñas por defecto

- `SECRET_KEY`
- `DATABASE_PASSWORD`
- `DATABASE_ROOT_PASSWORD`
- `DJANGO_SUPERUSER_PASSWORD`
- `REDIS_PASSWORD`

### 3. Configurar firewall

```bash
# Permitir solo puertos necesarios
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

## 📊 Monitoreo

### Ver estado de servicios
```bash
docker-compose ps
```

### Ver recursos utilizados
```bash
make stats
```

### Ver logs en tiempo real
```bash
make logs
```

## 🐛 Troubleshooting

### La aplicación no inicia

1. Verificar logs:
```bash
make logs-web
```

2. Verificar conexión a base de datos:
```bash
docker-compose exec web python manage.py check --database default
```

### Error de conexión a MySQL

1. Verificar que el servicio de base de datos esté funcionando:
```bash
docker-compose ps db
```

2. Verificar credenciales en `.env`

### Archivos estáticos no se cargan

```bash
make collectstatic
make restart
```

### Reiniciar todo desde cero

```bash
make clean
make init
```

## 🏗️ Estructura del Proyecto

```
renzzoelectricos/
├── Dockerfile              # Imagen Docker de la aplicación
├── docker-compose.yml      # Orquestación de servicios
├── entrypoint.sh          # Script de inicialización
├── Makefile               # Comandos útiles
├── .env.example           # Ejemplo de variables de entorno
├── docker/
│   ├── mysql/
│   │   └── my.cnf        # Configuración de MySQL
│   └── nginx/
│       ├── nginx.conf    # Configuración principal de Nginx
│       └── conf.d/
│           └── renzzo.conf  # Configuración del sitio
├── config/                # Configuración de Django
├── users/                 # App de usuarios
├── caja/                  # App de gestión de caja
├── static/                # Archivos estáticos
└── templates/             # Plantillas HTML
```

## 📝 Variables de Entorno Importantes

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DEBUG` | Modo debug (False en producción) | `False` |
| `SECRET_KEY` | Clave secreta de Django | *(generar)* |
| `ALLOWED_HOSTS` | Dominios permitidos | `localhost,127.0.0.1` |
| `DATABASE_NAME` | Nombre de la base de datos | `renzzoelectricos_db` |
| `DATABASE_USER` | Usuario de MySQL | `renzzo_admin` |
| `DATABASE_PASSWORD` | Contraseña de MySQL | *(cambiar)* |
| `WEB_PORT` | Puerto de la aplicación | `8000` |
| `NGINX_HTTP_PORT` | Puerto HTTP | `80` |
| `NGINX_HTTPS_PORT` | Puerto HTTPS | `443` |

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto es propiedad de Renzzo Eléctricos.

## 📞 Soporte

Para soporte técnico, contactar a: info@renzzoelectricos.com
