"""
Decorators personalizados para la app Caja.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_or_permission_required(perm):
    """
    Decorator que permite acceso si el usuario:
    1. Es staff/superuser, O
    2. Tiene el permiso específico
    
    Uso:
        @staff_or_permission_required('users.can_view_caja')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Permitir si es staff o superuser
            if user.is_staff or user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Permitir si tiene el permiso específico
            if user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            
            # Denegar acceso
            raise PermissionDenied
        
        return wrapped_view
    return decorator
