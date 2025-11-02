"""
Script para verificar la configuración de OSCAR_DASHBOARD_NAVIGATION
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print("\n═══════════════════════════════════════════════════════════")
print("  OSCAR_DASHBOARD_NAVIGATION - Menús del Dashboard")
print("═══════════════════════════════════════════════════════════\n")

for idx, item in enumerate(settings.OSCAR_DASHBOARD_NAVIGATION, 1):
    print(f"{idx}. {item.get('label', 'Sin label')}")
    print(f"   URL: {item.get('url_name', 'Sin URL')}")
    print(f"   Icon: {item.get('icon', 'Sin icono')}")
    print(f"   Access_fn: {item.get('access_fn', 'Sin access_fn')}")
    
    # Verificar si tiene children
    children = item.get('children', [])
    if children:
        print(f"   Children: {len(children)} items")
        for child in children[:3]:  # Mostrar solo los primeros 3
            print(f"      - {child.get('label', 'Sin label')}")
    print()

print(f"\nTotal de menús: {len(settings.OSCAR_DASHBOARD_NAVIGATION)}")
print("═══════════════════════════════════════════════════════════\n")
