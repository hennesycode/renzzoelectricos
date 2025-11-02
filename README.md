# 🔌 Renzzo Eléctricos - Sistema de Gestión Empresarial

Sistema de gestión empresarial completo desarrollado con **Django 5.2.7** y **Django Oscar** para Renzzo Eléctricos en **Villavicencio, Meta - Colombia**.

[![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange.svg)](https://www.mysql.com/)

---

## ✨ Características Principales

### 🔐 Sistema de Usuarios Avanzado
- **6 Roles Predefinidos**: Usuario, Cliente, Administrador, Contador, Ventas, Soporte
- **Permisos Personalizados**: Sistema CRUD completo por rol
- **Autenticación AJAX**: Login moderno con SweetAlert2
- **Dashboard Personalizado**: Interfaz específica por rol

#### 💾 Sistema "Recordarme" (Remember Me)
Sistema avanzado de persistencia de credenciales que mantiene sincronizado el último usuario ingresado entre el cliente y el servidor.

**Funcionamiento:**
- **Cuando está ACTIVO** (`recordarme` marcado):
  - Guarda **SOLO el último usuario/email** ingresado en:
    - **Cookie httponly** `saved_username` (30 días, servidor → cliente)
    - **localStorage** `renzzoelectricos_saved_username` (cliente)
  - **Limpia automáticamente** el usuario anterior cuando ingresa uno nuevo
  - **Elimina** la lista de usuarios recientes (sin dropdown de autocompletado)
  - **Sesión persistente**: 30 días de duración
  
- **Cuando está DESACTIVADO**:
  - **Elimina** el usuario guardado permanentemente del cache
  - **Mantiene** una lista de hasta 5 usuarios recientes para dropdown de autocompletado
  - **Sesión temporal**: expira al cerrar el navegador

**Sincronización Automática:**
- **Prioridad**: Cookie (servidor) > localStorage (cliente)
- **Al cargar página**: si cookie y localStorage difieren, se sincroniza automáticamente
- **Al hacer login AJAX**: servidor actualiza cookie → cliente acepta con `credentials: 'same-origin'` → localStorage se actualiza

**Ubicación de código:**
- Frontend: `users/static/users/js/login.js` (métodos `loadCachedCredentials`, `handleLoginResponse`, `clearRememberMeCache`)
- Backend: `users/views.py` (vista `login_view` con lógica de Set-Cookie)

**Claves de almacenamiento:**
```javascript
// localStorage
renzzoelectricos_saved_username    // Usuario permanente (recordarme ON)
renzzoelectricos_recent_users      // Lista recientes (recordarme OFF)
renzzoelectricos_user_prefs        // Preferencias { rememberMe: true/false }
renzzoelectricos_last_login        // Timestamp último login

// Cookies (httponly, secure, samesite=Strict)
saved_username                     // Usuario guardado (servidor)
```

**Ejemplos de flujo:**
1. **Login con "recordarme" activo (admin → admin@renzzoelectricos.com)**:
   ```
   Cache antes: admin
   Login con: admin@renzzoelectricos.com
   Cache después: admin@renzzoelectricos.com
   → Limpia 'admin', guarda 'admin@renzzoelectricos.com'
   ```

2. **Desactivar "recordarme"**:
   ```
   Cache antes: admin@renzzoelectricos.com
   Login sin marcar recordarme
   Cache después: [vacío]
   Lista recientes: ['admin@renzzoelectricos.com', ...]
   ```

### 🛒 E-commerce con Django Oscar
- Catálogo de productos eléctricos | Carrito de compras | Gestión de pedidos | Reportes de ventas

### 🎨 Diseño Moderno y Responsive
- **Landing Page** animada con CSS
- **Colores**: Verde oscuro profesional
- **Responsive**: Móvil, tablet y desktop
- **Bootstrap 5** con iconos personalizados

### 🌍 Localización Colombia
- **Idioma**: Español | **Zona Horaria**: America/Bogota | **Moneda**: COP | **Ubicación**: Villavicencio, Meta

---

## 🚀 Instalación Rápida

### Opción 1: Docker (Recomendado para Producción) 🐳

```bash
# 1. Clonar repositorio
git clone https://github.com/hennesycode/renzzoelectricos.git
cd renzzoelectricos

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env y cambiar contraseñas!

# 3. Iniciar con Make (más fácil)
make init

# O iniciar manualmente:
docker-compose build
docker-compose up -d
```

**Acceso:**
- 🌐 Aplicación: http://localhost
- 🔐 Admin: http://localhost/admin
- 📊 Dashboard: http://localhost/dashboard

**📚 Ver documentación completa:** [DOCKER.md](DOCKER.md) | [DEPLOY.md](DEPLOY.md)

### Opción 2: Instalación Local (Desarrollo)

```bash
# 1. Clonar y Configurar
git clone https://github.com/hennesycode/renzzoelectricos.git
cd renzzoelectricos
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### 2. Configurar `.env`
```env
DATABASE_NAME=renzzoelectricos
DATABASE_USER=root
DATABASE_PASSWORD=tu_contraseña
```

### 3. Base de Datos y Servidor
```bash
# MySQL
CREATE DATABASE renzzoelectricos CHARACTER SET utf8mb4;

# Django
python manage.py migrate
python manage.py createsuperuser  # admin/admin
python manage.py collectstatic --noinput
python manage.py runserver
```

Acceder: **http://127.0.0.1:8000/**

---

## 📁 Estructura del Proyecto

```
renzzoelectricos/
├── config/              # ⚙️ Configuración (settings, urls)
├── static/              # 🎨 Archivos estáticos GLOBALES
│   ├── css/            # landing.css
│   └── js/             # landing.js
├── templates/           # 📄 Templates GLOBALES (home.html)
├── users/               # 👤 App Usuarios
│   ├── static/users/   # CSS/JS específicos (login.css, login.js)
│   ├── templates/users/# Templates (login, dashboard)
│   └── models.py       # User + Permisos
├── docs/                # 📚 Documentación técnica
└── .env                 # 🔐 Variables de entorno
```

### 🎯 Organización de Archivos

- **`static/`**: Archivos compartidos (landing page)
- **`app/static/app/`**: Archivos por app (users/static/users/)
- **`templates/`**: Templates globales (base.html, home.html)
- **`app/templates/app/`**: Templates por app (users/templates/users/)

---

## 🛠️ Tecnologías

**Backend**: Django 5.2.7 | Django Oscar | MySQL 8.0+ | mysqlclient  
**Frontend**: Bootstrap 5 | SweetAlert2 | Google Fonts (Poppins) | CSS Grid & Flexbox  
**Deploy**: Whitenoise | Gunicorn

---

## 🎮 Acceso al Sistema

| Página | URL |
|--------|-----|
| 🏠 Landing Page | `http://127.0.0.1:8000/` |
| 🔐 Login | `http://127.0.0.1:8000/login/` |
| 📊 Dashboard | `http://127.0.0.1:8000/dashboard/` |
| ⚙️ Admin Django | `http://127.0.0.1:8000/admin/` |
| 🛍️ Tienda Oscar | `http://127.0.0.1:8000/shop/` |

**Credenciales**: `admin` / `admin` ⚠️ Cambiar en producción

---

## 👥 Roles y Permisos

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| 👨‍💼 **Administrador** | Acceso total | Todos |
| 🧮 **Contador** | Gestión contable | Reportes, contabilidad |
| 💼 **Ventas** | Gestión comercial | Productos, ventas, clientes |
| 🛠️ **Soporte** | Atención cliente | Tickets, consultas |
| 🛍️ **Cliente** | Cliente final | Ver productos, pedidos |
| 👤 **Usuario** | Básico | Limitado |

---

## ⚙️ Configuración

### Variables de Entorno (`.env`)
```env
SECRET_KEY=tu-clave-secreta
DEBUG=True
DATABASE_NAME=renzzoelectricos
DATABASE_USER=root
DATABASE_PASSWORD=tu_password
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Settings Principal
```python
# Base de Datos
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'renzzoelectricos',
}}

# Usuario Personalizado
AUTH_USER_MODEL = 'users.User'

# Localización
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
OSCAR_DEFAULT_CURRENCY = 'COP'
```

---

## 📚 Documentación Técnica Detallada

Para información técnica completa, consultar la carpeta **`docs/`**:

- **[ARQUITECTURA.md](docs/ARQUITECTURA.md)**: Diseño del sistema
- **[DESARROLLO.md](docs/DESARROLLO.md)**: Guía de desarrollo
- **[INSTALLATION.md](docs/INSTALLATION.md)**: Instalación detallada
- **[PROBLEMAS_CONOCIDOS.md](docs/PROBLEMAS_CONOCIDOS.md)**: Troubleshooting

---

## 🔧 Comandos Útiles

```bash
# Archivos estáticos
python manage.py collectstatic
python manage.py findstatic css/landing.css

# Base de datos
python manage.py makemigrations
python manage.py migrate

# Usuarios
python manage.py createsuperuser

# Tests
python manage.py test

# Shell
python manage.py shell
```

---

## 🔄 Cambios Recientes

### ✅ v1.0.0 (Noviembre 2025)
- Sistema de 6 roles con permisos avanzados
- Landing page moderna (diseño verde oscuro)
- Login AJAX con SweetAlert2
- Integración Django Oscar completa
- Localización Villavicencio, Meta
- Estructura organizada (Django best practices)
- Archivos CSS/JS separados y documentados
- README consolidado y docs/ técnicos

---

## 📞 Contacto

**Renzzo Eléctricos**  
📍 Villavicencio, Meta - Colombia  
📧 info@renzzoelectricos.com  
📱 +57 300 123 4567  

👨‍💻 **Desarrollador**: HENNESY  
🔗 GitHub: [@hennesycode](https://github.com/hennesycode)

---

## 🚧 Próximas Características

- [ ] Sistema de inventario avanzado
- [ ] Reportes PDF
- [ ] Pasarelas de pago colombianas
- [ ] App móvil (React Native)
- [ ] Facturación electrónica DIAN

---

**© 2025 Renzzo Eléctricos - Villavicencio, Meta - Colombia**  
⚡ *Soluciones eléctricas profesionales* ⚡
