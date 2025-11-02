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
from django.urls import reverse_lazy
from .models import User, PermisoPersonalizado
from .forms import CustomLoginForm, CustomUserCreationForm


def login_view(request):
    """
    Vista personalizada de login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _(f'Bienvenido, {user.get_full_name()}!'))
                return redirect('dashboard')
            else:
                messages.error(request, _('Usuario o contraseña incorrectos.'))
        else:
            messages.error(request, _('Por favor corrija los errores en el formulario.'))
    else:
        form = CustomLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """
    Vista para cerrar sesión.
    """
    logout(request)
    messages.info(request, _('Has cerrado sesión exitosamente.'))
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Vista del dashboard principal.
    """
    context = {
        'user': request.user,
        'titulo': _('Dashboard'),
    }
    return render(request, 'users/dashboard.html', context)


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

