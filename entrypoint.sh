#!/bin/bash

# ============================================================================
# Entrypoint Script para Renzzo Eléctricos
# Este script se ejecuta cada vez que el contenedor inicia
# ============================================================================

set -e  # Salir si algún comando falla

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🔌 RENZZO ELÉCTRICOS - Sistema de Gestión             ║"
echo "║        Iniciando aplicación Django + Oscar                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# 1. VERIFICAR CONEXIÓN A LA BASE DE DATOS
# ============================================================================
echo "📊 [1/6] Verificando conexión a la base de datos..."
echo "   Host: ${DATABASE_HOST:-localhost}"
echo "   Puerto: ${DATABASE_PORT:-3306}"
echo "   Base de datos: ${DATABASE_NAME:-renzzoelectricos}"

# Esperar a que la base de datos esté lista (máximo 30 intentos)
MAX_TRIES=30
COUNT=0

until nc -z -v -w30 "${DATABASE_HOST:-localhost}" "${DATABASE_PORT:-3306}" 2>&1 | grep -q "succeeded\|open" || [ $COUNT -eq $MAX_TRIES ]; do
    COUNT=$((COUNT+1))
    echo "   ⏳ Intento ${COUNT}/${MAX_TRIES}: Esperando que la base de datos esté lista..."
    sleep 2
done

if [ $COUNT -eq $MAX_TRIES ]; then
    echo "   ❌ ERROR: No se pudo conectar a la base de datos después de ${MAX_TRIES} intentos"
    exit 1
fi

echo "   ✅ Conexión a la base de datos establecida correctamente"
echo ""

# ============================================================================
# 2. EJECUTAR MIGRACIONES DE BASE DE DATOS
# ============================================================================
echo "🔄 [2/6] Ejecutando migraciones de base de datos..."

# Mostrar el estado actual de las migraciones
echo "   📋 Estado actual de las migraciones:"
python manage.py showmigrations --list 2>&1 | head -n 20

echo ""
echo "   🚀 Aplicando migraciones pendientes..."
python manage.py migrate --noinput 2>&1 | while IFS= read -r line; do
    echo "      $line"
done

echo "   ✅ Migraciones aplicadas correctamente"
echo ""

# ============================================================================
# 3. RECOLECTAR ARCHIVOS ESTÁTICOS
# ============================================================================
echo "📦 [3/6] Recolectando archivos estáticos (collectstatic)..."
echo "   Origen: /app/static"
echo "   Destino: /app/staticfiles"

python manage.py collectstatic --noinput --clear 2>&1 | while IFS= read -r line; do
    # Filtrar líneas muy largas para mantener el log limpio
    if [ ${#line} -lt 120 ]; then
        echo "      $line"
    fi
done

echo "   ✅ Archivos estáticos recolectados correctamente"
echo ""

# ============================================================================
# 4. COMPILAR TRADUCCIONES
# ============================================================================
echo "🌍 [4/6] Compilando traducciones (i18n)..."

if [ -d "locale" ]; then
    python manage.py compilemessages 2>&1 | while IFS= read -r line; do
        echo "      $line"
    done
    echo "   ✅ Traducciones compiladas correctamente"
else
    echo "   ℹ️  No hay directorio 'locale', omitiendo compilación de traducciones"
fi
echo ""

# ============================================================================
# 5. CREAR SUPERUSUARIO SI NO EXISTE (solo en primera ejecución)
# ============================================================================
echo "👤 [5/6] Verificando superusuario..."

# Solo crear si las variables están definidas
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME}').exists():
    User.objects.create_superuser('${DJANGO_SUPERUSER_USERNAME}', '${DJANGO_SUPERUSER_EMAIL}', '${DJANGO_SUPERUSER_PASSWORD}');
    print('   ✅ Superusuario creado: ${DJANGO_SUPERUSER_USERNAME}');
else:
    print('   ℹ️  Superusuario ya existe: ${DJANGO_SUPERUSER_USERNAME}');
" 2>&1
else
    echo "   ℹ️  Variables de superusuario no definidas, omitiendo creación"
fi
echo ""

# ============================================================================
# 6. VERIFICAR CONFIGURACIÓN DE DJANGO
# ============================================================================
echo "🔍 [6/6] Verificando configuración de Django..."
python manage.py check --deploy 2>&1 | while IFS= read -r line; do
    echo "      $line"
done
echo ""

# ============================================================================
# RESUMEN DE CONFIGURACIÓN
# ============================================================================
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              📋 RESUMEN DE CONFIGURACIÓN                   ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║ DEBUG: ${DEBUG:-False}                                     "
echo "║ ALLOWED_HOSTS: ${ALLOWED_HOSTS:-*}                         "
echo "║ DATABASE: ${DATABASE_ENGINE:-mysql}                        "
echo "║ STATIC_ROOT: /app/staticfiles                              ║"
echo "║ MEDIA_ROOT: /app/media                                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# INICIAR LA APLICACIÓN
# ============================================================================
echo "🚀 Iniciando servidor de aplicación..."
echo "   Comando: $@"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ejecutar el comando pasado como argumentos
exec "$@"
