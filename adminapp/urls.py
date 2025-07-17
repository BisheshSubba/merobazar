from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('users/', views.manage_users, name='manage_users'),
    path('toggle-user-status/<int:pk>/', views.toggle_user_status, name='toggle_user_status'),
    path('delete-user/<int:pk>/', views.delete_user, name='delete_user'),
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-category/<int:pk>/', views.edit_category, name='edit_category'),
    path('add-subcategory/', views.add_subcategory, name='add_subcategory'),
    path('edit-subcategory/<int:pk>/', views.edit_subcategory, name='edit_subcategory'),
    path('add-subsubcategory/', views.add_subsubcategory, name='add_subsubcategory'),
    path('edit-subsubcategory/<int:pk>/', views.edit_subsubcategory, name='edit_subsubcategory'),
    path('add-attribute/', views.add_attribute, name='add_attribute'),
    path('edit-attribute/<int:pk>/', views.edit_attribute, name='edit_attribute'),
    path('products/', views.manage_products, name='manage_products'),
    path('products/<int:pk>/', views.product_detail_admin, name='product_detail_admin'),
    path('products/<int:pk>/toggle-status/', views.toggle_product_status, name='toggle_product_status'),
    path('products/<int:pk>/delete/', views.delete_product, name='delete_product'),
]
