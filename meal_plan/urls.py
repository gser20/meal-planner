"""
URL configuration for meal_plan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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

from django.urls import path, include

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,  
    TokenRefreshView,  
    TokenVerifyView  
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/jwt/login/', TokenObtainPairView.as_view(), name='jwt-login'),  
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),  
    path('auth/jwt/verify/', TokenVerifyView.as_view(), name='jwt-verify'),  
    path('api/', include('recipes.urls')),

]
