#!/bin/bash

# ============================================================================
# Script de Construcción Docker para Renzzo Eléctricos
# ============================================================================

set -e

echo "� Construyendo imagen Docker para Renzzo Eléctricos..."
echo ""

# Variables
IMAGE_NAME="renzzoelectricos"
TAG="latest"

# Limpiar construcciones anteriores
echo "🧹 Limpiando imágenes anteriores..."
docker rmi "${IMAGE_NAME}:${TAG}" 2>/dev/null || true

# Construir imagen
echo "🏗️ Construyendo nueva imagen..."
docker build -t "${IMAGE_NAME}:${TAG}" .

echo ""
echo "✅ Imagen construida exitosamente: ${IMAGE_NAME}:${TAG}"
echo ""
echo "� Para ejecutar el contenedor:"
echo "   docker run -p 5018:8000 ${IMAGE_NAME}:${TAG}"
echo ""