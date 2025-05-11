from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('sell/', views.add_product, name='add_product'),
    path('get_subcategories/', views.get_subcategories, name='get_subcategories'),
    path('subcategory/<int:subcategory_id>/', views.products_by_subcategory, name='products_by_subcategory'),
    path('category/<int:category_id>/', views.products_by_category, name='products_by_category'),
    path('get_category_from_subcategory/', views.get_category_from_subcategory, name='get_category_from_subcategory'),
    path('product/<int:pk>/', views.product_details, name='product_details'),
]