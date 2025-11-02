from django.shortcuts import render


def home_view(request):
    """Vista para la página de inicio (landing page)"""
    return render(request, 'home.html')
