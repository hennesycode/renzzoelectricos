# ============================================================================
# Script de Health Check para Renzzo Eléctricos
# ============================================================================

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from django.db.utils import OperationalError


def check_database():
    """Verificar conexión a la base de datos"""
    try:
        db_conn = connections['default']
        db_conn.cursor()
        return True, "Base de datos: ✅ Conectada"
    except OperationalError as e:
        return False, f"Base de datos: ❌ Error: {e}"


def check_migrations():
    """Verificar que todas las migraciones estén aplicadas"""
    from django.core.management import call_command
    from io import StringIO
    
    try:
        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out)
        output = out.getvalue()
        
        if '[X]' in output and '[ ]' not in output:
            return True, "Migraciones: ✅ Todas aplicadas"
        else:
            return False, "Migraciones: ⚠️  Hay migraciones pendientes"
    except Exception as e:
        return False, f"Migraciones: ❌ Error: {e}"


def check_static_files():
    """Verificar que los archivos estáticos existan"""
    from django.conf import settings
    
    static_root = settings.STATIC_ROOT
    if static_root and os.path.exists(static_root):
        files_count = len([f for f in os.listdir(static_root) if os.path.isfile(os.path.join(static_root, f))])
        return True, f"Archivos estáticos: ✅ {files_count} archivos en {static_root}"
    else:
        return False, "Archivos estáticos: ⚠️  Directorio no existe"


def check_media_directory():
    """Verificar que el directorio de media exista"""
    from django.conf import settings
    
    media_root = settings.MEDIA_ROOT
    if media_root and os.path.exists(media_root):
        return True, f"Directorio media: ✅ {media_root}"
    else:
        return False, f"Directorio media: ⚠️  No existe: {media_root}"


def main():
    """Ejecutar todos los checks"""
    print("\n" + "="*60)
    print("🔍 HEALTH CHECK - RENZZO ELÉCTRICOS")
    print("="*60 + "\n")
    
    checks = [
        check_database(),
        check_migrations(),
        check_static_files(),
        check_media_directory(),
    ]
    
    all_passed = True
    for passed, message in checks:
        print(f"  {message}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    
    if all_passed:
        print("✅ Todos los checks pasaron correctamente")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("❌ Algunos checks fallaron")
        print("="*60 + "\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
