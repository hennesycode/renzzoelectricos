"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from app.Http.views import home_view

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Dashboard temporal - redirige al admin por ahora
from django.shortcuts import redirect
def temp_dashboard(request):
    if request.user.is_staff:
        return redirect('/admin/')
    else:
        return redirect('/login/')

urlpatterns += [
    path('shop/dashboard/', temp_dashboard, name='dashboard'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configurar nombres del admin
admin.site.site_header = "Renzzo Eléctricos - Administración"
admin.site.site_title = "Renzzo Eléctricos"
admin.site.index_title = "Panel de Administración"

