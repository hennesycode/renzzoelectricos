from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = _('Gestión de Usuarios')
    
    def ready(self):
        """
        Importar signals cuando la app esté lista.
        """
        try:
            import users.signals  # noqa
        except ImportError:
            pass

