# ============================================================================
# Dockerfile para Renzzo Eléctricos - Django + Oscar E-commerce
# ============================================================================

# Imagen base con Python 3.11
FROM python:3.11-slim-bullseye

# Información del mantenedor
LABEL maintainer="Renzzo Eléctricos <info@renzzoelectricos.com>"
LABEL description="Sistema de gestión comercial con Django Oscar y módulo de caja"

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Crear usuario no-root para seguridad
RUN groupadd -r renzzo && useradd -r -g renzzo renzzo

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Compiladores y herramientas de desarrollo
    gcc \
    g++ \
    make \
    # Librerías para MySQL
    default-libmysqlclient-dev \
    pkg-config \
    # Librerías para Pillow (imágenes)
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    zlib1g-dev \
    # Librerías para WeasyPrint (PDFs)
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    # Utilidades
    gettext \
    curl \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de requerimientos primero (para aprovechar cache de Docker)
COPY requirements.txt /app/

# Instalar dependencias de Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install psycopg2-binary  # Por si se usa PostgreSQL en el futuro

# Copiar el código de la aplicación
COPY . /app/

# Crear directorios necesarios y ajustar permisos
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R renzzo:renzzo /app && \
    chmod +x /app/entrypoint.sh

# Exponer puerto 5018 para Cloudflare Tunnel
# Cloudflare Tunnel detecta este puerto y lo conecta a renzzoelectricos.com
EXPOSE 5018

# Cambiar al usuario no-root
USER renzzo

# Punto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando por defecto - Gunicorn escucha en 0.0.0.0:8000 (interno)
# Docker mapea el puerto interno 8000 al puerto 5018 (externo) para Cloudflare Tunnel
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
