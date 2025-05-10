from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('', include('userapp.urls')),
    path('adminapp/', include('adminapp.urls')),
    path('products/', include('products.urls')),
]
