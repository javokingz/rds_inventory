"""
URL configuration for rds_dashboard project.

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
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views
from core import auth_views as custom_auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de autenticación
    path('login/', custom_auth_views.login_view, name='login'),
    path('register/', custom_auth_views.register_view, name='register'),
    path('logout/', custom_auth_views.logout_view, name='logout'),
    path('profile/', custom_auth_views.profile_view, name='profile'),
    path('change-password/', custom_auth_views.change_password_view, name='change_password'),
    
    # API endpoints para autenticación
    path('api/login/', custom_auth_views.login_api, name='login_api'),
    path('api/register/', custom_auth_views.register_api, name='register_api'),
    
    # Rutas principales (requieren autenticación)
    path('', views.home, name="home"),
    path('api/rds-data/', views.get_rds_data_ajax, name="rds_data_ajax"),
    path('instance/<str:instance_id>/', views.instance_details, name="instance_details"),
]
