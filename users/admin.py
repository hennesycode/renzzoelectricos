"""
Configuración del administrador para la app users.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, PermisoPersonalizado


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Administrador personalizado para el modelo User.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_staff', 'activo', 'fecha_creacion')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active', 'activo', 'fecha_creacion')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-fecha_creacion',)
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO, incluidas fechas.
        """
        if request.user.is_superuser:
            return ('last_login', 'date_joined')  # Solo las generadas automáticamente
        return ('last_login', 'date_joined', 'fecha_creacion', 'fecha_modificacion')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Información Personal'), {'fields': ('first_name', 'last_name', 'email', 'telefono', 'direccion')}),
        (_('Rol y Permisos'), {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Fechas Importantes'), {'fields': ('last_login', 'date_joined', 'fecha_creacion', 'fecha_modificacion')}),
        (_('Estado'), {'fields': ('activo',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'rol'),
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar usuarios.
        """
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """
        Guarda el modelo y asigna permisos automáticamente.
        """
        super().save_model(request, obj, form, change)
        if 'rol' in form.changed_data:
            obj.asignar_permisos_por_rol()


@admin.register(PermisoPersonalizado)
class PermisoPersonalizadoAdmin(admin.ModelAdmin):
    """
    Administrador para permisos personalizados.
    """
    list_display = ('usuario', 'nombre', 'recurso', 'puede_crear', 'puede_leer', 'puede_actualizar', 'puede_eliminar', 'activo')
    list_filter = ('recurso', 'activo', 'puede_crear', 'puede_leer', 'puede_actualizar', 'puede_eliminar')
    search_fields = ('usuario__username', 'nombre', 'recurso', 'descripcion')
    ordering = ('-fecha_creacion',)
    
    def get_readonly_fields(self, request, obj=None):
        """
        Superusuarios pueden editar TODO, incluida fecha_creacion.
        """
        if request.user.is_superuser:
            return ()  # Pueden editar todo
        return ('fecha_creacion',)
    
    fieldsets = (
        (_('Usuario y Recurso'), {
            'fields': ('usuario', 'nombre', 'recurso', 'descripcion')
        }),
        (_('Permisos CRUD'), {
            'fields': ('puede_crear', 'puede_leer', 'puede_actualizar', 'puede_eliminar'),
        }),
        (_('Estado'), {
            'fields': ('activo',)
        }),
        (_('Metadata'), {
            'fields': ('fecha_creacion',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo superusuarios pueden eliminar permisos personalizados.
        """
        return request.user.is_superuser

