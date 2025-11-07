"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from app.Http import views as app_views

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # URLs de usuarios (login, registro, etc.)
    path('accounts/', include('users.urls')),
    
    # Home / Landing page
    path('', app_views.home_view, name='home'),
    
    # Dashboard - Redirigir /dashboard/ a /dashboard/caja/
    path('dashboard/', RedirectView.as_view(url='/dashboard/caja/', permanent=False)),
    
    # URLs del dashboard
    path('dashboard/usuarios/', app_views.usuarios_list, name='dashboard_usuarios'),
    path('dashboard/estadisticas/', app_views.estadisticas_caja, name='dashboard_estadisticas'),
    path('dashboard/caja/', include('caja.urls')),
    path('dashboard/facturacion/', include('facturacion.urls')),
    
    # Mantener URLs antiguas por compatibilidad (redirigen a las nuevas)
    path('caja/', RedirectView.as_view(url='/dashboard/caja/', permanent=True)),
    path('facturacion/', RedirectView.as_view(url='/dashboard/facturacion/', permanent=True)),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configurar nombres del admin
admin.site.site_header = "Renzzo Eléctricos - Administración"
admin.site.site_title = "Renzzo Eléctricos"
admin.site.index_title = "Panel de Administración"

