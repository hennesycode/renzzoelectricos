# Renzzo Eléctricos - Sistema de Gestión

Sistema de gestión empresarial desarrollado con Django 5.2.7 y Django Oscar para Renzzo Eléctricos en Bogotá, Colombia.

## 🚀 Características

- **Gestión de Usuarios con Roles Avanzados**: Usuario, Cliente, Administrador, Contador, Ventas, Soporte
- **Sistema de Permisos Avanzado**: Permisos por rol y personalizados CRUD
- **E-commerce con Django Oscar**: Catálogo de productos, carrito de compras, gestión de pedidos
- **Localización**: Español (Colombia), America/Bogota, COP
- **Panel de Administración**: Dashboard personalizado con Bootstrap 5

## 🛠️ Tecnologías

- Django 5.2.7 | Django Oscar | MySQL 8.0+ | Bootstrap 5 | Whitenoise

## 📋 Instalación

### 1. Clonar y configurar entorno

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

### 3. Base de datos y servidor

```bash
# Crear base de datos MySQL
CREATE DATABASE renzzoelectricos CHARACTER SET utf8mb4;

# Migrar y ejecutar
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 📁 Estructura

```
renzzoelectricos/
├── config/              # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── templates/       # Templates base compartidos
├── users/               # App gestión de usuarios
│   ├── templates/users/ # Templates de la app
│   └── static/users/    # Archivos estáticos de la app
└── .venv/               # Entorno virtual
```

## 🔐 Roles

**Administrador**: Acceso completo | **Contador**: Reportes y contabilidad | **Ventas**: Ventas e inventario | **Soporte**: Atención al cliente | **Cliente**: Visualización limitada

## 📧 Contacto

Email: soporte@renzzoelectricos.com | Bogotá, Colombia

---

**Versión 1.0.0** | Django 5.2.7 | Python 3.11+ | MySQL 8.0+
