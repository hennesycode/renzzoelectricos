"""
Script para verificar el usuario y sus permisos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

print("\n═══════════════════════════════════════════════════════════")
print("  VERIFICACIÓN DE USUARIOS")
print("═══════════════════════════════════════════════════════════\n")

# Buscar usuario por email
email = 'info.hennesy.co@gmail.com'
try:
    user = User.objects.get(email=email)
    print(f"Usuario encontrado: {user.username}")
    print(f"Email: {user.email}")
    print(f"Nombre completo: {user.get_full_name()}")
    print(f"\n🔑 Permisos:")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    print(f"   is_active: {user.is_active}")
    
    print(f"\n📋 Permisos específicos:")
    print(f"   can_view_caja: {user.has_perm('users.can_view_caja')}")
    print(f"   can_manage_caja: {user.has_perm('users.can_manage_caja')}")
    
except User.DoesNotExist:
    print(f"❌ Usuario con email '{email}' no encontrado")
    print("\n📋 Usuarios existentes:")
    for u in User.objects.all()[:10]:
        print(f"   - {u.username} ({u.email}) - staff:{u.is_staff}")

print("\n═══════════════════════════════════════════════════════════\n")
