"""
URL configuration for cafeteria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.urls import path

from fiores import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cliente/", views.panel_cliente, name="panel_cliente"),
    path("encargado/", views.panel_encargado, name="panel_encargado"),
    path(
        "iniciar-sesion/",
        auth_views.LoginView.as_view(template_name="fiores/login.html"),
        name="login",
    ),
    path(
        "cerrar-sesion/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path('admin/', admin.site.urls),
]
