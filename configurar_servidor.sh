#!/bin/bash
# Script para configurar permisos de usuario en contenedor Docker
# Renzzo Eléctricos - Configuración de Producción

set -e  # Detener en caso de error

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🔧 CONFIGURACIÓN DE PERMISOS - RENZZO ELÉCTRICOS                             ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Paso 1: Buscar el contenedor
echo "🔍 Buscando contenedor web..."
CONTAINER_ID=$(sudo docker ps --filter "name=web" --format "{{.ID}}" | head -n 1)

if [ -z "$CONTAINER_ID" ]; then
    print_error "No se encontró ningún contenedor web en ejecución"
    echo ""
    print_info "Contenedores disponibles:"
    sudo docker ps
    exit 1
fi

CONTAINER_NAME=$(sudo docker ps --filter "id=$CONTAINER_ID" --format "{{.Names}}")
print_success "Contenedor encontrado: $CONTAINER_NAME (ID: $CONTAINER_ID)"
echo ""

# Paso 2: Crear script temporal de configuración
echo "📝 Creando script de configuración de permisos..."
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOFPYTHON'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

print("=" * 70)
print("CONFIGURANDO PERMISOS DE USUARIOS")
print("=" * 70)

# Listar todos los usuarios
print("\n📋 Usuarios actuales:")
all_users = User.objects.all()
if not all_users:
    print("❌ No hay usuarios en la base de datos")
    exit(1)

for u in all_users:
    status = []
    if u.is_superuser:
        status.append("SUPERUSER")
    if u.is_staff:
        status.append("STAFF")
    if u.is_active:
        status.append("ACTIVO")
    status_str = ", ".join(status) if status else "SIN PERMISOS"
    print(f"  - {u.username:20s} ({u.email:30s}) [{status_str}]")

# Buscar usuario admin o el primer usuario
print("\n🔍 Buscando usuario para configurar...")
try:
    user = User.objects.get(username='admin')
    print(f"✅ Usuario 'admin' encontrado")
except User.DoesNotExist:
    print("⚠️  Usuario 'admin' no encontrado, usando el primer usuario...")
    user = all_users.first()
    print(f"✅ Usando usuario: {user.username}")

# Configurar permisos
print(f"\n🔧 Configurando permisos para: {user.username}")
print(f"   Email: {user.email}")

user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()

print("\n✅ PERMISOS ACTUALIZADOS EXITOSAMENTE")
print("=" * 70)
print(f"Usuario: {user.username}")
print(f"Email: {user.email}")
print(f"Staff: {user.is_staff}")
print(f"Superuser: {user.is_superuser}")
print(f"Activo: {user.is_active}")
print("=" * 70)

# Verificar acceso a Caja
print("\n🔐 Verificando permisos de acceso a Caja...")
if user.is_staff or user.is_superuser:
    print("✅ El usuario tiene acceso TOTAL a Caja (staff/superuser)")
else:
    # Verificar permisos específicos
    has_view = user.has_perm('users.can_view_caja')
    has_manage = user.has_perm('users.can_manage_caja')
    print(f"   - can_view_caja: {has_view}")
    print(f"   - can_manage_caja: {has_manage}")

print("\n✅ CONFIGURACIÓN COMPLETADA")
EOFPYTHON

print_success "Script de configuración creado"
echo ""

# Paso 3: Copiar script al contenedor y ejecutar
echo "📤 Copiando script al contenedor..."
sudo docker cp $TEMP_SCRIPT $CONTAINER_ID:/tmp/configurar_permisos.py
print_success "Script copiado al contenedor"
echo ""

echo "🚀 Ejecutando configuración de permisos..."
echo "─────────────────────────────────────────────────────────────────────────────"
sudo docker exec $CONTAINER_ID python /tmp/configurar_permisos.py
echo "─────────────────────────────────────────────────────────────────────────────"
echo ""

# Paso 4: Limpiar
echo "🧹 Limpiando archivos temporales..."
sudo docker exec $CONTAINER_ID rm /tmp/configurar_permisos.py
rm $TEMP_SCRIPT
print_success "Limpieza completada"
echo ""

# Paso 5: Verificar denominaciones
echo "🪙 Verificando denominaciones..."
if sudo docker exec $CONTAINER_ID test -f crear_denominaciones.py; then
    sudo docker exec $CONTAINER_ID python crear_denominaciones.py
    print_success "Denominaciones verificadas"
else
    print_info "Script crear_denominaciones.py no encontrado (puede que no esté en producción aún)"
fi
echo ""

# Paso 6: Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
sudo docker exec $CONTAINER_ID python manage.py collectstatic --noinput
print_success "Archivos estáticos actualizados"
echo ""

# Paso 7: Reiniciar contenedor
echo "🔄 Reiniciando contenedor..."
sudo docker restart $CONTAINER_ID
print_success "Contenedor reiniciado"
echo ""

# Paso 8: Esperar a que el contenedor esté listo
echo "⏳ Esperando a que el contenedor esté listo (10 segundos)..."
sleep 10
print_success "Contenedor listo"
echo ""

# Paso 9: Verificar logs
echo "📋 Últimos logs del contenedor:"
echo "─────────────────────────────────────────────────────────────────────────────"
sudo docker logs --tail=20 $CONTAINER_ID
echo "─────────────────────────────────────────────────────────────────────────────"
echo ""

# Resumen final
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE                                     ║"
echo "╠═══════════════════════════════════════════════════════════════════════════════╣"
echo "║  📋 SIGUIENTE PASO:                                                           ║"
echo "║     1. Limpiar caché del navegador (Ctrl + Shift + Delete)                   ║"
echo "║     2. Ir a: https://renzzoelectricos.com                                     ║"
echo "║     3. Iniciar sesión con el usuario configurado                              ║"
echo "║     4. Ir al Dashboard → Caja                                                 ║"
echo "║     5. Hacer clic en 'Abrir Caja'                                             ║"
echo "║     6. Verificar que aparecen las denominaciones                              ║"
echo "╠═══════════════════════════════════════════════════════════════════════════════╣"
echo "║  🔒 ACCESO AL ADMIN:                                                          ║"
echo "║     URL: https://renzzoelectricos.com/admin/                                  ║"
echo "║     El usuario configurado ahora tiene acceso total                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

print_success "Script finalizado correctamente"
