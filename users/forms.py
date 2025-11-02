"""
Formularios para la app users.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Formulario personalizado para crear usuarios.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'telefono', 'direccion')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class CustomUserChangeForm(UserChangeForm):
    """
    Formulario personalizado para editar usuarios.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'telefono', 'direccion')


class CustomLoginForm(AuthenticationForm):
    """
    Formulario de login personalizado con estilos Bootstrap.
    """
    username = forms.CharField(
        label=_('Usuario'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su usuario'),
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_('Contraseña'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su contraseña')
        })
    )
