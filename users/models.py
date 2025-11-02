"""
Modelos de usuario personalizados con sistema de roles avanzado.
"""
from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType


class User(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    """
    
    class RoleChoices(models.TextChoices):
        """Roles disponibles en el sistema"""
        USUARIO = 'USUARIO', _('Usuario')
        CLIENTE = 'CLIENTE', _('Cliente')
        ADMINISTRADOR = 'ADMINISTRADOR', _('Administrador')
        CONTADOR = 'CONTADOR', _('Contador')
        VENTAS = 'VENTAS', _('Ventas')
        SOPORTE = 'SOPORTE', _('Soporte')
    
    # Campos adicionales
    rol = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.USUARIO,
        verbose_name=_('Rol'),
        help_text=_('Rol del usuario en el sistema')
    )
    
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Teléfono')
    )
    
    direccion = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Dirección')
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de modificación')
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name=_('Activo'),
        help_text=_('Designa si el usuario debe ser tratado como activo')
    )
    
    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['-fecha_creacion']
        permissions = [
            ('can_view_dashboard', 'Puede ver el dashboard'),
            ('can_manage_users', 'Puede gestionar usuarios'),
            ('can_view_reports', 'Puede ver reportes'),
            ('can_manage_sales', 'Puede gestionar ventas'),
            ('can_manage_inventory', 'Puede gestionar inventario'),
            ('can_manage_accounting', 'Puede gestionar contabilidad'),
            ('can_provide_support', 'Puede brindar soporte'),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"
    
    def save(self, *args, **kwargs):
        """
        Guarda el usuario y asigna permisos basados en el rol.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new or 'rol' in kwargs.get('update_fields', []):
            self.asignar_permisos_por_rol()
    
    def asignar_permisos_por_rol(self):
        """
        Asigna permisos automáticamente basándose en el rol del usuario.
        """
        # Limpiar permisos actuales
        self.user_permissions.clear()
        
        # Definir permisos por rol
        permisos_por_rol = {
            self.RoleChoices.USUARIO: [],
            
            self.RoleChoices.CLIENTE: [
                'can_view_dashboard',
            ],
            
            self.RoleChoices.ADMINISTRADOR: [
                'can_view_dashboard',
                'can_manage_users',
                'can_view_reports',
                'can_manage_sales',
                'can_manage_inventory',
                'can_manage_accounting',
                'can_provide_support',
            ],
            
            self.RoleChoices.CONTADOR: [
                'can_view_dashboard',
                'can_view_reports',
                'can_manage_accounting',
            ],
            
            self.RoleChoices.VENTAS: [
                'can_view_dashboard',
                'can_manage_sales',
                'can_manage_inventory',
                'can_view_reports',
            ],
            
            self.RoleChoices.SOPORTE: [
                'can_view_dashboard',
                'can_provide_support',
            ],
        }
        
        # Obtener permisos para el rol actual
        permisos_nombres = permisos_por_rol.get(self.rol, [])
        
        # Asignar permisos
        content_type = ContentType.objects.get_for_model(User)
        for permiso_nombre in permisos_nombres:
            try:
                permiso = Permission.objects.get(
                    codename=permiso_nombre,
                    content_type=content_type
                )
                self.user_permissions.add(permiso)
            except Permission.DoesNotExist:
                pass
        
        # Si es administrador, hacer staff y superuser
        if self.rol == self.RoleChoices.ADMINISTRADOR:
            self.is_staff = True
            self.is_superuser = True
            self.save(update_fields=['is_staff', 'is_superuser'])
        else:
            if self.is_superuser and self.rol != self.RoleChoices.ADMINISTRADOR:
                self.is_superuser = False
                self.save(update_fields=['is_superuser'])


class PermisoPersonalizado(models.Model):
    """
    Modelo para gestionar permisos personalizados adicionales.
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='permisos_personalizados',
        verbose_name=_('Usuario')
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name=_('Nombre del permiso')
    )
    
    descripcion = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    
    recurso = models.CharField(
        max_length=100,
        verbose_name=_('Recurso'),
        help_text=_('Recurso al que aplica el permiso (ej: productos, ventas, etc.)')
    )
    
    puede_crear = models.BooleanField(
        default=False,
        verbose_name=_('Puede crear')
    )
    
    puede_leer = models.BooleanField(
        default=False,
        verbose_name=_('Puede leer')
    )
    
    puede_actualizar = models.BooleanField(
        default=False,
        verbose_name=_('Puede actualizar')
    )
    
    puede_eliminar = models.BooleanField(
        default=False,
        verbose_name=_('Puede eliminar')
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de creación')
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    class Meta:
        verbose_name = _('Permiso Personalizado')
        verbose_name_plural = _('Permisos Personalizados')
        unique_together = ['usuario', 'recurso', 'nombre']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.nombre} ({self.recurso})"

