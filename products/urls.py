from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('sell/', views.add_product, name='add_product'),
    path('subcategory/<int:subcategory_id>/', views.products_by_subcategory, name='products_by_subcategory'),
    path('api/subcategories/', views.get_subcategories, name='get_subcategories'),
]