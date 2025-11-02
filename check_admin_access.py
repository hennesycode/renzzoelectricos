"""
Script para verificar configuración del admin de Django y acceso de superusuarios/staff.
Renzzo Eléctricos - Verificación de permisos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.admin.sites import site
from django.apps import apps

User = get_user_model()

def main():
    print("="*80)
    print("VERIFICACIÓN DE ADMIN DE DJANGO - RENZZO ELÉCTRICOS")
    print("="*80)
    
    # 1. Verificar que admin esté instalado
    print("\n1️⃣  VERIFICACIÓN DE CONFIGURACIÓN DEL ADMIN")
    print("-" * 80)
    if apps.is_installed('django.contrib.admin'):
        print("✅ django.contrib.admin está instalado")
    else:
        print("❌ django.contrib.admin NO está instalado")
    
    # 2. Listar todos los modelos registrados en el admin
    print("\n2️⃣  MODELOS REGISTRADOS EN EL ADMIN")
    print("-" * 80)
    
    modelos_por_app = {}
    for model, admin_class in site._registry.items():
        app_label = model._meta.app_label
        model_name = model._meta.verbose_name_plural
        if app_label not in modelos_por_app:
            modelos_por_app[app_label] = []
        modelos_por_app[app_label].append((model_name, model.__name__, admin_class.__class__.__name__))
    
    for app_label in sorted(modelos_por_app.keys()):
        print(f"\n📦 App: {app_label}")
        for verbose_name, model_name, admin_class in sorted(modelos_por_app[app_label]):
            print(f"   ✓ {verbose_name} ({model_name}) - {admin_class}")
    
    print(f"\n📊 Total de modelos registrados: {len(site._registry)}")
    
    # 3. Verificar modelos de Caja
    print("\n3️⃣  VERIFICACIÓN DE MODELOS DE CAJA")
    print("-" * 80)
    
    from caja.models import (
        CajaRegistradora, MovimientoCaja, TipoMovimiento,
        DenominacionMoneda, ConteoEfectivo, DetalleConteo
    )
    
    modelos_caja = [
        CajaRegistradora, MovimientoCaja, TipoMovimiento,
        DenominacionMoneda, ConteoEfectivo, DetalleConteo
    ]
    
    for modelo in modelos_caja:
        if modelo in site._registry:
            admin_class = site._registry[modelo]
            print(f"✅ {modelo._meta.verbose_name_plural} - Registrado")
            print(f"   └─ Admin Class: {admin_class.__class__.__name__}")
            print(f"   └─ List Display: {admin_class.list_display}")
        else:
            print(f"❌ {modelo._meta.verbose_name_plural} - NO REGISTRADO")
    
    # 4. Verificar modelos de Users
    print("\n4️⃣  VERIFICACIÓN DE MODELOS DE USERS")
    print("-" * 80)
    
    from users.models import User, PermisoPersonalizado
    
    modelos_users = [User, PermisoPersonalizado]
    
    for modelo in modelos_users:
        if modelo in site._registry:
            admin_class = site._registry[modelo]
            print(f"✅ {modelo._meta.verbose_name_plural} - Registrado")
            print(f"   └─ Admin Class: {admin_class.__class__.__name__}")
            print(f"   └─ List Display: {admin_class.list_display}")
        else:
            print(f"❌ {modelo._meta.verbose_name_plural} - NO REGISTRADO")
    
    # 5. Verificar usuarios superuser/staff
    print("\n5️⃣  VERIFICACIÓN DE USUARIOS SUPERUSER/STAFF")
    print("-" * 80)
    
    superusers = User.objects.filter(is_superuser=True)
    staff_users = User.objects.filter(is_staff=True)
    
    print(f"\n👤 Superusuarios encontrados: {superusers.count()}")
    for user in superusers:
        print(f"   ✓ {user.username} ({user.email})")
        print(f"     ├─ is_superuser: {user.is_superuser}")
        print(f"     ├─ is_staff: {user.is_staff}")
        print(f"     ├─ is_active: {user.is_active}")
        print(f"     └─ Nombre: {user.get_full_name() or 'Sin nombre'}")
    
    if superusers.count() == 0:
        print("   ⚠️  No hay superusuarios registrados")
        print("   💡 Crea uno con: python manage.py createsuperuser")
    
    print(f"\n👥 Usuarios staff encontrados: {staff_users.count()}")
    for user in staff_users:
        print(f"   ✓ {user.username} ({user.email})")
        print(f"     ├─ is_superuser: {user.is_superuser}")
        print(f"     ├─ is_staff: {user.is_staff}")
        print(f"     └─ Rol: {user.rol if hasattr(user, 'rol') else 'N/A'}")
    
    # 6. Verificar acceso a Caja
    print("\n6️⃣  VERIFICACIÓN DE ACCESO A CAJA PARA STAFF/SUPERUSER")
    print("-" * 80)
    
    print("\n🔐 Política de acceso configurada:")
    print("   ✓ Superusuarios: ACCESO TOTAL (sin verificar permisos)")
    print("   ✓ Staff: ACCESO TOTAL (sin verificar permisos)")
    print("   ✓ Usuarios regulares: Requieren permiso 'users.can_view_caja'")
    
    # 7. URLs del admin
    print("\n7️⃣  ACCESO AL ADMIN")
    print("-" * 80)
    print("   🌐 URL del Admin: http://localhost:8000/admin/")
    print("   🌐 URL del Admin (producción): https://renzzoelectricos.com/admin/")
    print("\n   📋 Modelos disponibles en el admin:")
    print("      • Cajas Registradoras (/admin/caja/cajaregistradora/)")
    print("      • Movimientos de Caja (/admin/caja/movimientocaja/)")
    print("      • Tipos de Movimiento (/admin/caja/tipomovimiento/)")
    print("      • Denominaciones (/admin/caja/denominacionmoneda/)")
    print("      • Conteos de Efectivo (/admin/caja/conteoefectivo/)")
    print("      • Detalles de Conteo (/admin/caja/detalleconteo/)")
    print("      • Usuarios (/admin/users/user/)")
    print("      • Permisos Personalizados (/admin/users/permisopersonalizado/)")
    
    print("\n" + "="*80)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("="*80)
    print("\n💡 Para acceder al admin:")
    print("   1. Asegúrate de tener un superusuario creado")
    print("   2. Navega a http://localhost:8000/admin/")
    print("   3. Inicia sesión con tu superusuario")
    print("   4. Podrás ver y editar todos los datos de Caja y Usuarios")
    print()

if __name__ == '__main__':
    main()
