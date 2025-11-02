#!/bin/bash

# ============================================================================
# Script para corregir problema de denominaciones en producción
# Renzzo Eléctricos - Villavicencio, Meta
# ============================================================================

set -e  # Salir en caso de error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}   FIX DENOMINACIONES - PRODUCCIÓN${NC}"
echo -e "${YELLOW}   Permite crear billetes y monedas con el mismo valor${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Detectar contenedor web
echo -e "${YELLOW}🔍 Detectando contenedor web...${NC}"
CONTAINER_ID=$(sudo docker ps --filter "name=web" --format "{{.ID}}" | head -n 1)

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}❌ ERROR: No se encontró contenedor web en ejecución${NC}"
    echo "   Ejecuta: sudo docker ps"
    exit 1
fi

CONTAINER_NAME=$(sudo docker ps --filter "id=$CONTAINER_ID" --format "{{.Names}}")
echo -e "${GREEN}✅ Contenedor encontrado: $CONTAINER_NAME ($CONTAINER_ID)${NC}"
echo ""

# Paso 1: Hacer pull de los cambios
echo -e "${YELLOW}📥 Paso 1/4: Descargando cambios desde GitHub...${NC}"
git pull origin main
echo -e "${GREEN}✅ Código actualizado${NC}"
echo ""

# Paso 2: Aplicar migración
echo -e "${YELLOW}🔄 Paso 2/4: Aplicando migración de base de datos...${NC}"
sudo docker exec -it $CONTAINER_ID python manage.py migrate caja
echo -e "${GREEN}✅ Migración aplicada${NC}"
echo ""

# Paso 3: Crear denominaciones correctamente
echo -e "${YELLOW}💵 Paso 3/4: Creando denominaciones (billetes y monedas)...${NC}"

# Crear script Python inline para configurar denominaciones
cat > /tmp/crear_denominaciones_fix.py << 'PYTHON_SCRIPT'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from caja.models import DenominacionMoneda

# Denominaciones de billetes (valor en pesos colombianos)
billetes = [
    (100000, 1),   # $100,000
    (50000, 2),    # $50,000
    (20000, 3),    # $20,000
    (10000, 4),    # $10,000
    (5000, 5),     # $5,000
    (2000, 6),     # $2,000
    (1000, 7),     # $1,000
]

# Denominaciones de monedas
monedas = [
    (1000, 8),     # $1,000
    (500, 9),      # $500
    (200, 10),     # $200
    (100, 11),     # $100
    (50, 12),      # $50
]

print("\n💵 Creando/Actualizando BILLETES:")
print("=" * 50)
for valor, orden in billetes:
    billete, created = DenominacionMoneda.objects.get_or_create(
        valor=valor,
        tipo='BILLETE',
        defaults={'activo': True, 'orden': orden}
    )
    if created:
        print(f"  ✅ CREADO: Billete de ${valor:,}")
    else:
        print(f"  ℹ️  Ya existe: Billete de ${valor:,}")

print("\n🪙 Creando/Actualizando MONEDAS:")
print("=" * 50)
for valor, orden in monedas:
    moneda, created = DenominacionMoneda.objects.get_or_create(
        valor=valor,
        tipo='MONEDA',
        defaults={'activo': True, 'orden': orden}
    )
    if created:
        print(f"  ✅ CREADO: Moneda de ${valor:,}")
    else:
        print(f"  ℹ️  Ya existe: Moneda de ${valor:,}")

# Verificar total
total_billetes = DenominacionMoneda.objects.filter(tipo='BILLETE', activo=True).count()
total_monedas = DenominacionMoneda.objects.filter(tipo='MONEDA', activo=True).count()

print("\n📊 RESUMEN:")
print("=" * 50)
print(f"  💵 Billetes activos: {total_billetes}")
print(f"  🪙 Monedas activas: {total_monedas}")
print(f"  ✅ Total denominaciones: {total_billetes + total_monedas}")
print("")
PYTHON_SCRIPT

# Copiar script al contenedor y ejecutar
sudo docker cp /tmp/crear_denominaciones_fix.py $CONTAINER_ID:/tmp/crear_denominaciones_fix.py
sudo docker exec -it $CONTAINER_ID python /tmp/crear_denominaciones_fix.py
sudo docker exec -it $CONTAINER_ID rm /tmp/crear_denominaciones_fix.py
rm /tmp/crear_denominaciones_fix.py

echo -e "${GREEN}✅ Denominaciones creadas/actualizadas${NC}"
echo ""

# Paso 4: Recargar archivos estáticos
echo -e "${YELLOW}📦 Paso 4/4: Recolectando archivos estáticos...${NC}"
sudo docker exec -it $CONTAINER_ID python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Archivos estáticos actualizados${NC}"
echo ""

# Reiniciar contenedor
echo -e "${YELLOW}🔄 Reiniciando contenedor...${NC}"
sudo docker restart $CONTAINER_ID
echo -e "${GREEN}✅ Contenedor reiniciado${NC}"
echo ""

# Verificar logs
echo -e "${YELLOW}📋 Verificando logs del contenedor...${NC}"
echo -e "${YELLOW}   (Presiona Ctrl+C para salir)${NC}"
echo ""
sleep 3
sudo docker logs -f --tail=20 $CONTAINER_ID

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ PROCESO COMPLETADO${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Ahora puedes:"
echo -e "  1. Acceder a ${YELLOW}https://renzzoelectricos.com/admin/${NC}"
echo -e "  2. Ir a ${YELLOW}Caja > Denominaciones de monedas${NC}"
echo -e "  3. Crear denominaciones de billetes y monedas"
echo -e "  4. Ahora ${GREEN}SÍ${NC} puedes crear billete de \$1,000 y moneda de \$1,000"
echo ""
