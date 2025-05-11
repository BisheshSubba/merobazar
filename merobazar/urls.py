from django.contrib import admin
from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('userapp.urls')),
    path('adminapp/', include('adminapp.urls')),
    path('products/', include('products.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
