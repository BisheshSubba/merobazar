from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('subcategory/<int:subcategory_id>/', views.products_by_subcategory, name='products_by_subcategory'),
    path('category/<int:category_id>/', views.products_by_category, name='products_by_category'),
    path('subsubcategory/<int:subsubcategory_id>/', views.products_by_subsubcategory, name='products_by_subsubcategory'),
    path('get_category_from_subcategory/', views.get_category_from_subcategory, name='get_category_from_subcategory'),
    path('get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('get-subsubcategories/', views.get_subsubcategories, name='get_subsubcategories'),
    path('create/', views.create_product, name='create_product'),
    path('product/<int:pk>/update/', views.update_product, name='update_product'),
    path('product/<int:pk>/', views.product_details, name='product_details'),
]