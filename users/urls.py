"""
URLs para la app users.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Dashboard personalizado eliminado - usamos el de Oscar
    path('usuarios/', views.UserListView.as_view(), name='user_list'),
    path('usuarios/crear/', views.UserCreateView.as_view(), name='user_create'),
]
