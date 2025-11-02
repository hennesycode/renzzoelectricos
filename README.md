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

### 1. Clonar y Configurar
```bash
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
