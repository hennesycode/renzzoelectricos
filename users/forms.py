"""
Formularios para la app users.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import authenticate
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


class CustomLoginForm(forms.Form):
    """
    Formulario de login personalizado que soporta email/username y "recordarme".
    """
    username = forms.CharField(
        label=_('Usuario o Email'),
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su usuario o email'),
            'autofocus': True,
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label=_('Contraseña'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ingrese su contraseña'),
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        label=_('Recordarme'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'remember_me'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        """
        Inicializa el formulario con la request para autenticación.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Valida las credenciales del usuario.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            # Intentar autenticar con el valor ingresado (puede ser username o email)
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            
            # Si no funcionó, intentar con email (Oscar usa EmailBackend)
            if self.user_cache is None and '@' in username:
                try:
                    user = User.objects.get(email=username)
                    self.user_cache = authenticate(
                        self.request,
                        username=user.username,
                        password=password
                    )
                except User.DoesNotExist:
                    pass

            if self.user_cache is None:
                raise forms.ValidationError(
                    _('Por favor, ingrese un usuario/email y contraseña correctos. '
                      'Tenga en cuenta que ambos campos pueden ser sensibles a mayúsculas y minúsculas.')
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controla si al usuario se le permite iniciar sesión.
        """
        if not user.is_active:
            raise forms.ValidationError(
                _('Esta cuenta está inactiva.'),
                code='inactive',
            )

    def get_user(self):
        """
        Retorna el usuario autenticado.
        """
        return self.user_cache
