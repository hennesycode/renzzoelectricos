# Guía de Configuración - Renzzo Eléctricos

## 🚀 Pasos para ejecutar el proyecto

### 1. Configurar MySQL

Abre MySQL Workbench o la consola de MySQL y ejecuta:

```sql
CREATE DATABASE renzzoelectricos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Configurar archivo .env

Edita el archivo `.env` y configura tu contraseña de MySQL:

```env
DATABASE_PASSWORD=tu_contraseña_mysql
```

### 3. Activar entorno virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Aplicar migraciones

```bash
python manage.py migrate
```

### 5. Crear superusuario

```bash
python manage.py createsuperuser
```

Ingresa:
- Username: admin
- Email: admin@renzzoelectricos.com
- Password: (elige una contraseña segura)
- Rol: ADMINISTRADOR

### 6. Recolectar archivos estáticos

```bash
python manage.py collectstatic --noinput
```

### 7. Ejecutar servidor

```bash
python manage.py runserver
```

### 8. Acceder al sistema

- **Dashboard**: http://localhost:8000/dashboard/
- **Login**: http://localhost:8000/login/
- **Admin**: http://localhost:8000/admin/

## ✅ Verificación

Después de crear el superusuario:
1. Ve a http://localhost:8000/login/
2. Ingresa tus credenciales
3. Deberías ver el dashboard con tu rol de Administrador

## 📁 Estructura del Proyecto

```
renzzoelectricos/
├── .venv/                          # Entorno virtual
├── config/                         # Configuración Django
│   ├── settings.py                 # Configuración principal
│   └── urls.py                     # URLs principales
├── users/                          # App de usuarios
│   ├── templates/users/            # Templates de la app
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── user_list.html
│   │   └── user_form.html
│   └── static/users/               # Archivos estáticos
│       ├── css/
│       └── js/
├── templates/                      # Templates globales
│   └── base.html
├── manage.py
├── requirements.txt
└── .env                            # Configuración de entorno
```

## 🔧 Comandos útiles

### Ver migraciones
```bash
python manage.py showmigrations
```

### Crear nueva app
```bash
python manage.py startapp nombre_app
```

### Shell de Django
```bash
python manage.py shell
```

### Ver todas las URLs
```bash
python manage.py show_urls
```

## 🐛 Solución de problemas

### Error de conexión a MySQL
- Verifica que MySQL esté corriendo
- Verifica la contraseña en `.env`
- Verifica que la base de datos `renzzoelectricos` exista

### Error de migraciones
```bash
python manage.py migrate --run-syncdb
```

### Recrear base de datos
```bash
python manage.py flush
python manage.py migrate
python manage.py createsuperuser
```

## 📝 Siguientes pasos

1. ✅ Proyecto configurado y subido a GitHub
2. ⏳ Configurar base de datos MySQL
3. ⏳ Crear superusuario
4. ⏳ Probar login y dashboard
5. ⏳ Configurar Django Oscar completamente
6. ⏳ Crear productos y categorías
7. ⏳ Configurar métodos de pago

---

**Nota**: Este proyecto sigue las mejores prácticas de Django 5.2.7 con estructura modular y escalable.
