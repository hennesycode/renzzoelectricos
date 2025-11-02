from django.contrib.auth import get_user_model


def caja_access_fn(user, url_name, url_args=None, url_kwargs=None):
    """
    Access function used by Oscar dashboard navigation.
    Returns True when the user has the 'users.can_view_caja' permission
    or is a staff/superuser. Signature matches Oscar's expected access_fn
    (user, url_name, url_args=None, url_kwargs=None).
    """
    try:
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        # allow superusers/staff by default
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        return user.has_perm('users.can_view_caja')
    except Exception:
        return False
