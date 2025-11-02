"""
Vistas para la app users.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from .models import User, PermisoPersonalizado
from .forms import CustomLoginForm, CustomUserCreationForm


def login_view(request):
    """
    Vista personalizada de login con soporte AJAX y recordarme.
    """
    if request.user.is_authenticated:
        # Si es staff, enviar al dashboard de Oscar, si no al perfil de cliente
        if request.user.is_staff:
            return redirect('/dashboard/')
        else:
            return redirect('customer:summary')
    
    # Verificar si es una petición AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Obtener credenciales guardadas desde cookies para prellenar el formulario
    saved_username = request.COOKIES.get('saved_username', '')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember_me = form.cleaned_data.get('remember_me')
            
            if user is not None:
                # Configurar duración de sesión según "recordarme"
                if not remember_me:
                    # Sesión expira al cerrar navegador
                    request.session.set_expiry(0)
                else:
                    # Sesión dura 30 días
                    request.session.set_expiry(30 * 24 * 60 * 60)
                
                login(request, user)
                
                # Determinar URL de redirección según el tipo de usuario
                if user.is_staff:
                    redirect_url = '/dashboard/'
                else:
                    redirect_url = str(reverse('customer:summary'))
                
                # Respuesta AJAX
                if is_ajax:
                    from django.http import JsonResponse
                    response = JsonResponse({
                        'success': True,
                        'message': f'Bienvenido, {user.get_full_name() or user.username}!',
                        'user': {
                            'username': user.username,
                            'full_name': user.get_full_name(),
                            'email': user.email,
                            'rol': user.get_rol_display() if hasattr(user, 'get_rol_display') else ('Administrador' if user.is_staff else 'Cliente')
                        },
                        'redirect_url': redirect_url,
                        'remember_me': remember_me
                    })
                    
                    # Guardar username/email en cookie para próximo login si "recordarme" está activado
                    if remember_me:
                        response.set_cookie(
                            'saved_username', 
                            form.cleaned_data.get('username'),
                            max_age=30*24*60*60,  # 30 días
                            secure=request.is_secure(),
                            httponly=True,
                            samesite='Strict'
                        )
                    else:
                        # Eliminar cookie si no quiere ser recordado
                        response.delete_cookie('saved_username')
                    
                    return response
                
                # Respuesta normal (no AJAX)
                messages.success(request, _(f'Bienvenido, {user.get_full_name()}!'))
                response = redirect(redirect_url)
                
                # Manejar cookie también en respuesta normal
                if remember_me:
                    response.set_cookie(
                        'saved_username', 
                        form.cleaned_data.get('username'),
                        max_age=30*24*60*60,  # 30 días
                        secure=request.is_secure(),
                        httponly=True,
                        samesite='Strict'
                    )
                else:
                    response.delete_cookie('saved_username')
                
                return response
        else:
            # Formulario inválido
            if is_ajax:
                from django.http import JsonResponse
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                return JsonResponse({
                    'success': False,
                    'message': 'Por favor corrija los errores en el formulario',
                    'errors': errors
                })
            # Los errores se mostrarán en el formulario
    else:
        # Pre-llenar el formulario con credenciales guardadas
        initial_data = {}
        if saved_username:
            initial_data['username'] = saved_username
            initial_data['remember_me'] = True
        
        form = CustomLoginForm(initial=initial_data)
    
    return render(request, 'users/login.html', {
        'form': form,
        'saved_username': saved_username  # Para el JavaScript
    })


def logout_view(request):
    """
    Vista para cerrar sesión.
    """
    logout(request)
    messages.info(request, _('Has cerrado sesión exitosamente.'))
    return redirect('login')


# La vista dashboard_view se ha eliminado - usamos el dashboard nativo de Oscar


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Vista para listar usuarios.
    """
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'usuarios'
    permission_required = 'users.can_manage_users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                username__icontains=search
            ) | queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                first_name__icontains=search
            ) | queryset.filter(
                last_name__icontains=search
            )
        return queryset


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Vista para crear usuarios.
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    permission_required = 'users.can_manage_users'
    
    def form_valid(self, form):
        messages.success(self.request, _('Usuario creado exitosamente.'))
        return super().form_valid(form)

