#!/bin/bash

# ============================================================================
# Script de Inicio Rápido para Renzzo Eléctricos
# ============================================================================

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🔌 RENZZO ELÉCTRICOS - Configuración Inicial             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar que Docker Compose esté instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker y Docker Compose están instalados"
echo ""

# Verificar si existe .env
if [ ! -f .env ]; then
    echo "📝 Archivo .env no encontrado. Creando desde .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita el archivo .env y cambia las contraseñas por defecto"
    echo ""
    read -p "¿Deseas editar el archivo .env ahora? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo "✅ Archivo .env encontrado"
fi

echo ""
echo "🚀 Iniciando despliegue..."
echo ""

# Construir imágenes
echo "🔨 [1/4] Construyendo imágenes Docker..."
docker-compose build --no-cache

# Iniciar servicios
echo ""
echo "🚀 [2/4] Iniciando servicios..."
docker-compose up -d

# Esperar a que la base de datos esté lista
echo ""
echo "⏳ [3/4] Esperando a que la base de datos esté lista..."
sleep 15

# Ejecutar migraciones y collectstatic (esto lo hace el entrypoint.sh automáticamente)
echo ""
echo "✅ [4/4] Servicios iniciados correctamente"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🎉 INSTALACIÓN COMPLETADA                        ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║  📱 Aplicación: http://localhost                          ║"
echo "║  🔐 Admin: http://localhost/admin                         ║"
echo "║  📊 Dashboard: http://localhost/dashboard                 ║"
echo "║                                                            ║"
echo "║  Usuario: admin                                           ║"
echo "║  Email: admin@renzzoelectricos.com                        ║"
echo "║  Contraseña: (la configurada en .env)                     ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Mostrar logs
echo "📋 Mostrando logs (Ctrl+C para salir):"
echo ""
docker-compose logs -f
